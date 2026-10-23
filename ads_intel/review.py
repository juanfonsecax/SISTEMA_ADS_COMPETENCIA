from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .util import canonical_json, normalize_relpath, utc_now

REVIEW_ITEM_STATUSES = {"pending", "in_review", "needs_evidence", "resolved", "rejected"}

CATEGORY_BY_ISSUE = {
    "missing_advertiser_name": "identity",
    "orphan_copy": "copy",
    "combined_confidence_label": "taxonomy",
    "documentation_stale": "documentation",
}


def _insert_item(
    connection: sqlite3.Connection,
    *,
    item_key: str,
    category: str,
    object_type: str,
    object_id: int | None,
    title: str,
    description: str,
    evidence: dict[str, Any],
    now: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO review_item
            (item_key, category, object_type, object_id, title, description,
             evidence_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            item_key,
            category,
            object_type,
            object_id,
            title,
            description,
            canonical_json(evidence),
            now,
            now,
        ),
    )
    return int(cursor.rowcount)


def _line_evidence(root: Path, relative: str, terms: tuple[str, ...]) -> list[dict[str, Any]]:
    path = root / relative
    if not path.is_file():
        return [{"path": relative, "exists": False, "line": None, "text": None}]
    evidence = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(term in line for term in terms):
            evidence.append(
                {
                    "path": normalize_relpath(root, path),
                    "exists": True,
                    "line": number,
                    "text": line.strip(),
                }
            )
    return evidence


def seed_review_queue(connection: sqlite3.Connection, root: Path) -> int:
    now = utc_now()
    inserted = 0
    source = connection.execute(
        "SELECT id, name, permission_basis, review_status, permission_evidence_ref FROM source ORDER BY id LIMIT 1"
    ).fetchone()
    if source is not None and source["permission_basis"] == "pending_review":
        inserted += _insert_item(
            connection,
            item_key=f"source:{source['id']}:permission",
            category="source_rights",
            object_type="source",
            object_id=int(source["id"]),
            title="Source permission remains pending",
            description=(
                "The legacy source has no recorded authorization. Keep it non-exportable "
                "until a human records an evidence-backed permission decision."
            ),
            evidence={
                "source": source["name"],
                "permission_basis": source["permission_basis"],
                "review_status": source["review_status"],
                "permission_evidence_ref": source["permission_evidence_ref"],
            },
            now=now,
        )

    unknown_assets = connection.execute(
        "SELECT COUNT(*) AS n FROM asset WHERE rights_status = 'unknown'"
    ).fetchone()["n"]
    if unknown_assets:
        inserted += _insert_item(
            connection,
            item_key="assets:rights_unknown",
            category="asset_rights",
            object_type="asset",
            object_id=None,
            title=f"{unknown_assets} assets have unknown rights",
            description=(
                "Per-asset rights remain unknown. Do not export these assets as approved "
                "until each one has evidence, a reviewer, and a review date."
            ),
            evidence={"assets_unknown_rights": int(unknown_assets)},
            now=now,
        )

    for issue in connection.execute(
        "SELECT id, issue_key, severity, issue_type, source_file, source_row, external_id, message, payload_json "
        "FROM import_issue ORDER BY id"
    ):
        category = CATEGORY_BY_ISSUE.get(issue["issue_type"], "import_issue")
        inserted += _insert_item(
            connection,
            item_key=f"import_issue:{issue['issue_key']}",
            category=category,
            object_type="import_issue",
            object_id=int(issue["id"]),
            title=issue["message"],
            description=(
                f"Legacy import issue preserved for human review: {issue['issue_type']} "
                f"({issue['severity']})."
            ),
            evidence={
                "issue_type": issue["issue_type"],
                "severity": issue["severity"],
                "source_file": issue["source_file"],
                "source_row": issue["source_row"],
                "external_id": issue["external_id"],
                "payload_json": issue["payload_json"],
            },
            now=now,
        )

    c6_rows = connection.execute(
        """
        SELECT d.id AS tag_definition_id, d.tag_key, COUNT(*) AS n,
               GROUP_CONCAT(t.ad_creative_id) AS ad_ids
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE d.dimension = 'legacy_concepto_crudo' AND d.tag_key LIKE 'C6%'
        GROUP BY d.id, d.tag_key
        ORDER BY d.tag_key
        """
    ).fetchall()
    if c6_rows:
        inserted += _insert_item(
            connection,
            item_key="taxonomy:c6_retired",
            category="taxonomy",
            object_type="tag_definition",
            object_id=int(c6_rows[0]["tag_definition_id"]),
            title="Retired C6 tag remains in legacy raw labels",
            description=(
                "C6 is not part of the active concept catalog. Preserve the raw legacy tag "
                "and decide whether to map it manually; do not recreate a canonical C6."
            ),
            evidence={
                "rows": [
                    {
                        "tag_key": row["tag_key"],
                        "ad_count": int(row["n"]),
                        "ad_creative_ids": row["ad_ids"],
                    }
                    for row in c6_rows
                ]
            },
            now=now,
        )

    doc_evidence = _line_evidence(root, "_BLUEPRINTS/_LEEME.md", ("FDA", "INVIMA", "MSPAS"))
    doc_evidence.extend(_line_evidence(root, "_BLUEPRINTS/_ESQUEMA_FICHA.md", ("FDA", "INVIMA", "MSPAS")))
    inserted += _insert_item(
        connection,
        item_key="documentation:fda_mspas_conflict",
        category="documentation",
        object_type="document",
        object_id=None,
        title="FDA and MSPAS guidance conflict",
        description=(
            "One blueprint document prohibits FDA while the ficha schema retains FDA. "
            "A human must resolve the regulatory rule before any new copy is approved."
        ),
        evidence={"lines": doc_evidence},
        now=now,
    )

    dead_page = connection.execute(
        "SELECT id, external_page_id, name, reported_active_ads "
        "FROM advertiser WHERE external_page_id = '1125291077325276'"
    ).fetchone()
    if dead_page is not None:
        creative_count = connection.execute(
            "SELECT COUNT(*) AS n FROM ad_creative WHERE advertiser_id = ?",
            (dead_page["id"],),
        ).fetchone()["n"]
        inserted += _insert_item(
            connection,
            item_key="page:1125291077325276:reported_active_without_creatives",
            category="page",
            object_type="advertiser",
            object_id=int(dead_page["id"]),
            title="Dead page still reports active ads",
            description=(
                "The page reports active ads but has no verified creatives in the canonical base. "
                "Keep the discrepancy visible; do not invent creatives or erase the page."
            ),
            evidence={
                "external_page_id": dead_page["external_page_id"],
                "name": dead_page["name"],
                "reported_active_ads": dead_page["reported_active_ads"],
                "imported_creatives": int(creative_count),
            },
            now=now,
        )

    for claim in connection.execute(
        "SELECT id, claim_text, claim_type, status, source_file, evidence_refs FROM claim ORDER BY id"
    ):
        inserted += _insert_item(
            connection,
            item_key=f"claim:{claim['id']}",
            category="claim",
            object_type="claim",
            object_id=int(claim["id"]),
            title=f"Claim requires evidence: {claim['claim_text']}",
            description=(
                "The claim is preserved with pending evidence status. A human must review "
                "the source evidence before any approval or export."
            ),
            evidence={
                "claim_text": claim["claim_text"],
                "claim_type": claim["claim_type"],
                "status": claim["status"],
                "source_file": claim["source_file"],
                "evidence_refs": claim["evidence_refs"],
            },
            now=now,
        )

    return inserted


def list_review_items(
    connection: sqlite3.Connection,
    *,
    status: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    clauses = []
    parameters: list[Any] = []
    if status is not None:
        if status not in REVIEW_ITEM_STATUSES:
            raise ValueError(f"Invalid review item status: {status!r}")
        clauses.append("status = ?")
        parameters.append(status)
    if category is not None:
        clauses.append("category = ?")
        parameters.append(category)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return [
        dict(row)
        for row in connection.execute(
            f"""
            SELECT id, item_key, category, object_type, object_id, title, description,
                   evidence_json, status, decision, reviewer, reviewed_at, notes,
                   created_at, updated_at
            FROM review_item
            {where}
            ORDER BY category, id
            """,
            parameters,
        )
    ]


def record_review_decision(
    connection: sqlite3.Connection,
    item_id: int,
    *,
    status: str,
    decision: str,
    reviewer: str,
    notes: str | None = None,
    reviewed_at: str | None = None,
) -> int:
    if status not in REVIEW_ITEM_STATUSES - {"pending"}:
        raise ValueError(f"Invalid decision status: {status!r}")
    if not decision.strip():
        raise ValueError("A review decision requires an explicit decision")
    if not reviewer.strip():
        raise ValueError("A review decision requires a reviewer")
    item = connection.execute(
        "SELECT id, item_key, category, object_type, object_id FROM review_item WHERE id = ?",
        (item_id,),
    ).fetchone()
    if item is None:
        raise ValueError(f"Unknown review item: {item_id}")
    now = utc_now()
    timestamp = reviewed_at or now
    with connection:
        connection.execute(
            """
            UPDATE review_item
            SET status = ?, decision = ?, reviewer = ?, reviewed_at = ?,
                notes = COALESCE(?, notes), updated_at = ?
            WHERE id = ?
            """,
            (status, decision.strip(), reviewer.strip(), timestamp, notes, now, item_id),
        )
        connection.execute(
            """
            INSERT INTO review_event
                (object_type, object_id, review_type, status, evidence_ref, reviewer,
                 reviewed_at, notes, payload_json, created_at)
            VALUES ('review_item', ?, 'human_decision', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                status,
                decision.strip(),
                reviewer.strip(),
                timestamp,
                notes,
                canonical_json(
                    {
                        "item_key": item["item_key"],
                        "category": item["category"],
                        "object_type": item["object_type"],
                        "object_id": item["object_id"],
                        "decision": decision.strip(),
                    }
                ),
                now,
            ),
        )
    return item_id
