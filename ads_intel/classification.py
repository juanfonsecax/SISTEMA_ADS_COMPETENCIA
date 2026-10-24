from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .taxonomy import (
    LEGACY_AMBIGUOUS,
    LEGACY_MAPPINGS,
    TAXONOMY_VERSION,
    seed_taxonomy,
    tag_definition_id,
    validate_tag,
)
from .util import canonical_json, utc_now

CLASSIFICATION_STATUSES = {
    "suggested",
    "pending_review",
    "reviewed",
    "approved",
    "rejected",
    "superseded",
}
REVIEW_ACTIONS = {"approve", "correct", "reject", "defer"}
LEGACY_DIMENSIONS = (
    "legacy_concepto_crudo",
    "legacy_gallery_auto",
    "legacy_preclasificacion",
)
AUTOMATIC_ASSIGNER = "ads_intel.legacy_mapping"
MAPPING_METHOD = "deterministic_legacy_mapping_v1"


def _json(value: Any) -> str:
    return canonical_json(value)


def _load_json(value: str | None) -> Any:
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {"raw": value}


def _event(
    connection: sqlite3.Connection,
    ad_tag_id: int,
    event_type: str,
    from_status: str | None,
    to_status: str | None,
    actor: str,
    reason: str | None,
    payload: dict[str, Any] | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO ad_tag_event
            (ad_tag_id, event_type, from_status, to_status, actor, reason, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ad_tag_id,
            event_type,
            from_status,
            to_status,
            actor,
            reason,
            _json(payload) if payload is not None else None,
            utc_now(),
        ),
    )
    return int(cursor.lastrowid)


def _review_event(
    connection: sqlite3.Connection,
    ad_tag_id: int,
    status: str,
    reviewer: str,
    reviewed_at: str,
    notes: str | None,
    payload: dict[str, Any],
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO review_event
            (object_type, object_id, review_type, status, evidence_ref, reviewer,
             reviewed_at, notes, payload_json, created_at)
        VALUES ('ad_tag', ?, 'classification', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ad_tag_id,
            status,
            notes,
            reviewer,
            reviewed_at,
            notes,
            _json(payload),
            utc_now(),
        ),
    )
    return int(cursor.lastrowid)


def start_run(
    connection: sqlite3.Connection,
    *,
    run_type: str,
    method: str,
    taxonomy_version: str = TAXONOMY_VERSION,
    model_version: str | None = None,
    prompt_version: str | None = None,
    contract_version: str | None = None,
    notes: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO classification_run
            (taxonomy_version, run_type, method, model_version, prompt_version,
             contract_version, started_at, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?)
        """,
        (
            taxonomy_version,
            run_type,
            method,
            model_version,
            prompt_version,
            contract_version,
            utc_now(),
            notes,
        ),
    )
    return int(cursor.lastrowid)


def finish_run(
    connection: sqlite3.Connection,
    run_id: int,
    *,
    status: str,
    counts: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    cost: dict[str, Any] | None = None,
) -> None:
    if status not in {"completed", "completed_with_errors", "failed"}:
        raise ValueError(f"Invalid classification run status: {status!r}")
    connection.execute(
        """
        UPDATE classification_run
        SET finished_at = ?, status = ?, counts_json = ?, errors_json = ?, cost_json = ?
        WHERE id = ?
        """,
        (
            utc_now(),
            status,
            _json(counts) if counts is not None else None,
            _json(errors) if errors is not None else None,
            _json(cost) if cost is not None else None,
            run_id,
        ),
    )


def _mapping_row(
    connection: sqlite3.Connection,
    source_dimension: str,
    source_tag_key: str,
    taxonomy_version: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM taxonomy_mapping
        WHERE taxonomy_version = ? AND source_dimension = ? AND source_tag_key = ?
        """,
        (taxonomy_version, source_dimension, source_tag_key),
    ).fetchone()


def _upsert_mapping(
    connection: sqlite3.Connection,
    *,
    source_dimension: str,
    source_tag_key: str,
    target_dimension: str | None,
    target_tag_key: str | None,
    status: str,
    rationale: str,
    taxonomy_version: str,
    evidence: dict[str, Any],
) -> int:
    existing = _mapping_row(connection, source_dimension, source_tag_key, taxonomy_version)
    if existing is not None:
        if existing["reviewed_by"]:
            return int(existing["id"])
        connection.execute(
            """
            UPDATE taxonomy_mapping
            SET target_taxonomy_version = ?, target_dimension = ?, target_tag_key = ?,
                mapping_status = ?, method = ?, confidence_basis = ?, rationale = ?,
                evidence_json = ?
            WHERE id = ?
            """,
            (
                taxonomy_version if target_dimension else None,
                target_dimension,
                target_tag_key,
                status,
                MAPPING_METHOD,
                "legacy_mapping_without_numeric_confidence",
                rationale,
                _json(evidence),
                existing["id"],
            ),
        )
        return int(existing["id"])
    cursor = connection.execute(
        """
        INSERT INTO taxonomy_mapping
            (taxonomy_version, source_dimension, source_tag_key, target_taxonomy_version,
             target_dimension, target_tag_key, mapping_status, method, confidence,
             confidence_basis, rationale, evidence_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
        """,
        (
            taxonomy_version,
            source_dimension,
            source_tag_key,
            taxonomy_version if target_dimension else None,
            target_dimension,
            target_tag_key,
            status,
            MAPPING_METHOD,
            "legacy_mapping_without_numeric_confidence",
            rationale,
            _json(evidence),
            utc_now(),
        ),
    )
    return int(cursor.lastrowid)


def _mapping_decision(
    connection: sqlite3.Connection,
    source_dimension: str,
    source_tag_key: str,
    taxonomy_version: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    existing = _mapping_row(connection, source_dimension, source_tag_key, taxonomy_version)
    if existing is not None:
        if existing["mapping_status"] == "mapped" and existing["target_dimension"]:
            return {
                "mapping_id": int(existing["id"]),
                "status": "mapped",
                "target_dimension": existing["target_dimension"],
                "target_tag_key": existing["target_tag_key"],
                "rationale": existing["rationale"],
            }
        if existing["mapping_status"] == "rejected":
            return {
                "mapping_id": int(existing["id"]),
                "status": "rejected",
                "target_dimension": None,
                "target_tag_key": None,
                "rationale": existing["rationale"],
            }
        return {
            "mapping_id": int(existing["id"]),
            "status": "needs_review",
            "target_dimension": None,
            "target_tag_key": None,
            "rationale": existing["rationale"],
        }
    mapped = LEGACY_MAPPINGS.get((source_dimension, source_tag_key))
    if mapped is not None:
        target_dimension, target_tag_key, rationale = mapped
        mapping_id = _upsert_mapping(
            connection,
            source_dimension=source_dimension,
            source_tag_key=source_tag_key,
            target_dimension=target_dimension,
            target_tag_key=target_tag_key,
            status="mapped",
            rationale=rationale,
            taxonomy_version=taxonomy_version,
            evidence=evidence,
        )
        return {
            "mapping_id": mapping_id,
            "status": "mapped",
            "target_dimension": target_dimension,
            "target_tag_key": target_tag_key,
            "rationale": rationale,
        }
    rationale = LEGACY_AMBIGUOUS.get(
        (source_dimension, source_tag_key),
        "No existe una equivalencia inequivoca en el catalogo canonico; requiere revision humana.",
    )
    mapping_id = _upsert_mapping(
        connection,
        source_dimension=source_dimension,
        source_tag_key=source_tag_key,
        target_dimension=None,
        target_tag_key=None,
        status="needs_review",
        rationale=rationale,
        taxonomy_version=taxonomy_version,
        evidence=evidence,
    )
    return {
        "mapping_id": mapping_id,
        "status": "needs_review",
        "target_dimension": None,
        "target_tag_key": None,
        "rationale": rationale,
    }


def _existing_target(
    connection: sqlite3.Connection,
    creative_id: int,
    target_tag_id: int,
    target_dimension: str,
) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE t.ad_creative_id = ?
          AND d.dimension = ?
          AND t.review_status IN ('approved', 'reviewed')
        LIMIT 1
        """,
        (creative_id, target_dimension),
    ).fetchone()
    if row is not None:
        return True
    row = connection.execute(
        """
        SELECT 1
        FROM ad_tag
        WHERE ad_creative_id = ? AND tag_definition_id = ?
          AND method = 'legacy_mapping_v1'
        LIMIT 1
        """,
        (creative_id, target_tag_id),
    ).fetchone()
    return row is not None


def _insert_assignment(
    connection: sqlite3.Connection,
    *,
    creative_id: int,
    asset_id: int | None,
    target_tag_id: int,
    confidence: float | None,
    confidence_label: str | None,
    confidence_basis: str,
    assigned_by: str,
    method: str,
    review_status: str,
    evidence: dict[str, Any],
    source_file: str | None,
    source_row: int | None,
    taxonomy_version: str,
    run_id: int | None,
    legacy_review_status: str | None = None,
    is_primary: int = 0,
    reviewed_by: str | None = None,
    reviewed_at: str | None = None,
    review_notes: str | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
) -> int | None:
    if review_status not in CLASSIFICATION_STATUSES:
        raise ValueError(f"Invalid assignment status: {review_status!r}")
    now = utc_now()
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO ad_tag
            (ad_creative_id, asset_id, tag_definition_id, confidence, confidence_label,
             assigned_by, method, model_version, prompt_version, review_status,
             evidence_json, source_file, source_row, created_at, taxonomy_version,
             classification_run_id, legacy_review_status, confidence_basis,
             reviewed_by, reviewed_at, review_notes, is_primary, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            creative_id,
            asset_id,
            target_tag_id,
            confidence,
            confidence_label,
            assigned_by,
            method,
            model_version,
            prompt_version,
            review_status,
            _json(evidence),
            source_file,
            source_row,
            now,
            taxonomy_version,
            run_id,
            legacy_review_status,
            confidence_basis,
            reviewed_by,
            reviewed_at,
            review_notes,
            1 if is_primary else 0,
            now,
        ),
    )
    if cursor.rowcount:
        return int(cursor.lastrowid)
    row = connection.execute(
        """
        SELECT id
        FROM ad_tag
        WHERE ad_creative_id = ? AND tag_definition_id = ? AND method = ? AND assigned_by = ?
        """,
        (creative_id, target_tag_id, method, assigned_by),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def classify_legacy(
    connection: sqlite3.Connection,
    *,
    root: Path | None = None,
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[str, Any]:
    seed_taxonomy(connection, root)
    run_id = start_run(
        connection,
        run_type="legacy_mapping",
        method=MAPPING_METHOD,
        taxonomy_version=taxonomy_version,
        notes="Mapea etiquetas heredadas a dimensiones canonicas; no aprueba etiquetas.",
    )
    counts = {
        "source_labels": 0,
        "mapped_labels": 0,
        "needs_review_labels": 0,
        "rejected_labels": 0,
        "assignments_inserted": 0,
        "assignments_skipped_protected": 0,
        "assignments_skipped_existing": 0,
    }
    errors: list[dict[str, Any]] = []
    sources = connection.execute(
        """
        SELECT d.dimension, d.tag_key, COUNT(*) AS n
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE d.dimension IN (?, ?, ?)
        GROUP BY d.dimension, d.tag_key
        ORDER BY d.dimension, d.tag_key
        """,
        LEGACY_DIMENSIONS,
    ).fetchall()
    try:
        for source in sources:
            source_dimension = source["dimension"]
            source_tag_key = source["tag_key"]
            counts["source_labels"] += 1
            evidence = {
                "source_dimension": source_dimension,
                "source_tag_key": source_tag_key,
                "source_rows": int(source["n"]),
                "run_id": run_id,
            }
            decision = _mapping_decision(
                connection,
                source_dimension,
                source_tag_key,
                taxonomy_version,
                evidence,
            )
            if decision["status"] == "needs_review":
                counts["needs_review_labels"] += 1
                continue
            if decision["status"] == "rejected":
                counts["rejected_labels"] += 1
                continue
            target_dimension = decision["target_dimension"]
            target_tag_key = decision["target_tag_key"]
            try:
                target_tag_id = validate_tag(
                    connection,
                    target_dimension,
                    target_tag_key,
                    version=taxonomy_version,
                )
            except ValueError as exc:
                errors.append(
                    {
                        "source_dimension": source_dimension,
                        "source_tag_key": source_tag_key,
                        "error": str(exc),
                    }
                )
                continue
            counts["mapped_labels"] += 1
            rows = connection.execute(
                """
                SELECT t.id, t.ad_creative_id, t.asset_id, t.confidence, t.confidence_label,
                       t.assigned_by, t.method, t.review_status, t.evidence_json,
                       t.source_file, t.source_row, t.created_at
                FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE d.dimension = ? AND d.tag_key = ?
                ORDER BY t.id
                """,
                (source_dimension, source_tag_key),
            ).fetchall()
            for row in rows:
                if _existing_target(
                    connection,
                    int(row["ad_creative_id"]),
                    target_tag_id,
                    target_dimension,
                ):
                    counts["assignments_skipped_protected"] += 1
                    continue
                evidence_payload = {
                    "source_ad_tag_id": int(row["id"]),
                    "source_dimension": source_dimension,
                    "source_tag_key": source_tag_key,
                    "source_method": row["method"],
                    "source_assigned_by": row["assigned_by"],
                    "source_review_status": row["review_status"],
                    "source_source_file": row["source_file"],
                    "source_source_row": row["source_row"],
                    "source_created_at": row["created_at"],
                    "source_evidence": _load_json(row["evidence_json"]),
                    "mapping_id": decision["mapping_id"],
                    "mapping_rationale": decision["rationale"],
                    "classification_run_id": run_id,
                }
                confidence = row["confidence"]
                confidence_basis = (
                    "copied_from_legacy_source_confidence"
                    if confidence is not None
                    else "legacy_mapping_without_numeric_confidence"
                )
                tag_id = _insert_assignment(
                    connection,
                    creative_id=int(row["ad_creative_id"]),
                    asset_id=int(row["asset_id"]) if row["asset_id"] is not None else None,
                    target_tag_id=target_tag_id,
                    confidence=confidence,
                    confidence_label=row["confidence_label"],
                    confidence_basis=confidence_basis,
                    assigned_by=AUTOMATIC_ASSIGNER,
                    method="legacy_mapping_v1",
                    review_status="pending_review",
                    evidence=evidence_payload,
                    source_file=row["source_file"],
                    source_row=row["source_row"],
                    taxonomy_version=taxonomy_version,
                    run_id=run_id,
                    legacy_review_status=row["review_status"],
                )
                if tag_id is None:
                    counts["assignments_skipped_existing"] += 1
                    continue
                _event(
                    connection,
                    tag_id,
                    "created_from_legacy_mapping",
                    None,
                    "pending_review",
                    AUTOMATIC_ASSIGNER,
                    decision["rationale"],
                    evidence_payload,
                )
                counts["assignments_inserted"] += 1
        finish_run(
            connection,
            run_id,
            status="completed_with_errors" if errors else "completed",
            counts=counts,
            errors=errors,
        )
    except Exception as exc:
        finish_run(
            connection,
            run_id,
            status="failed",
            counts=counts,
            errors=errors + [{"error": str(exc)}],
        )
        raise
    return {"run_id": run_id, **counts, "errors": errors}


def list_mappings(
    connection: sqlite3.Connection,
    *,
    status: str | None = None,
    source_dimension: str | None = None,
) -> list[dict[str, Any]]:
    clauses = []
    parameters: list[Any] = []
    if status is not None:
        if status not in {"mapped", "needs_review", "rejected"}:
            raise ValueError(f"Invalid mapping status: {status!r}")
        clauses.append("mapping_status = ?")
        parameters.append(status)
    if source_dimension is not None:
        clauses.append("source_dimension = ?")
        parameters.append(source_dimension)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return [
        dict(row)
        for row in connection.execute(
            f"""
            SELECT id, taxonomy_version, source_dimension, source_tag_key,
                   target_taxonomy_version, target_dimension, target_tag_key,
                   mapping_status, method, confidence, confidence_basis, rationale,
                   evidence_json, created_at, reviewed_by, reviewed_at
            FROM taxonomy_mapping
            {where}
            ORDER BY source_dimension, source_tag_key
            """,
            parameters,
        )
    ]


def record_mapping_decision(
    connection: sqlite3.Connection,
    *,
    source_dimension: str,
    source_tag_key: str,
    target_dimension: str,
    target_tag_key: str,
    reviewer: str,
    reason: str,
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[str, Any]:
    if not reviewer.strip():
        raise ValueError("A mapping decision requires a reviewer")
    if not reason.strip():
        raise ValueError("A mapping decision requires a reason")
    target_tag_id = validate_tag(
        connection,
        target_dimension,
        target_tag_key,
        version=taxonomy_version,
    )
    existing = _mapping_row(connection, source_dimension, source_tag_key, taxonomy_version)
    now = utc_now()
    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO taxonomy_mapping
                (taxonomy_version, source_dimension, source_tag_key, target_taxonomy_version,
                 target_dimension, target_tag_key, mapping_status, method, confidence,
                 confidence_basis, rationale, evidence_json, created_at, reviewed_by, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?, 'mapped', 'human_mapping', NULL, ?, ?, ?, ?, ?, ?)
            """,
            (
                taxonomy_version,
                source_dimension,
                source_tag_key,
                taxonomy_version,
                target_dimension,
                target_tag_key,
                "human_mapping_without_numeric_confidence",
                reason.strip(),
                _json({"target_tag_definition_id": target_tag_id}),
                now,
                reviewer.strip(),
                now,
            ),
        )
        mapping_id = int(cursor.lastrowid)
    else:
        mapping_id = int(existing["id"])
        connection.execute(
            """
            UPDATE taxonomy_mapping
            SET target_taxonomy_version = ?, target_dimension = ?, target_tag_key = ?,
                mapping_status = 'mapped', method = 'human_mapping',
                confidence_basis = ?, rationale = ?, reviewed_by = ?, reviewed_at = ?
            WHERE id = ?
            """,
            (
                taxonomy_version,
                target_dimension,
                target_tag_key,
                "human_mapping_without_numeric_confidence",
                reason.strip(),
                reviewer.strip(),
                now,
                mapping_id,
            ),
        )
    connection.execute(
        """
        INSERT INTO audit_event
            (actor, event_type, object_type, object_id, timestamp, before_hash, after_hash, reason)
        VALUES (?, 'taxonomy_mapping_decided', 'taxonomy_mapping', ?, ?, NULL, NULL, ?)
        """,
        (reviewer.strip(), mapping_id, now, reason.strip()),
    )
    return {
        "mapping_id": mapping_id,
        "source_dimension": source_dimension,
        "source_tag_key": source_tag_key,
        "target_dimension": target_dimension,
        "target_tag_key": target_tag_key,
        "target_tag_definition_id": target_tag_id,
        "reviewed_by": reviewer.strip(),
        "reviewed_at": now,
    }


def _assignment_row(connection: sqlite3.Connection, tag_id: int) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT t.*, d.dimension, d.tag_key, d.label, d.definition
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE t.id = ?
        """,
        (tag_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Unknown classification assignment: {tag_id}")
    return row


def list_classifications(
    connection: sqlite3.Connection,
    *,
    status: str | None = None,
    dimension: str | None = None,
    limit: int | None = None,
    include_legacy: bool = False,
) -> list[dict[str, Any]]:
    clauses = []
    parameters: list[Any] = []
    if status is not None:
        if status not in CLASSIFICATION_STATUSES:
            raise ValueError(f"Invalid classification status: {status!r}")
        clauses.append("t.review_status = ?")
        parameters.append(status)
    if dimension is not None:
        clauses.append("d.dimension = ?")
        parameters.append(dimension)
    if not include_legacy:
        clauses.append(
            "d.dimension NOT IN ('legacy_concepto_crudo', 'legacy_gallery_auto', "
            "'legacy_preclasificacion', 'curaduria')"
        )
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT t.id, t.ad_creative_id, a.external_ad_id, adv.name AS advertiser,
               t.asset_id, d.dimension, d.tag_key, d.label, d.definition,
               t.confidence, t.confidence_label, t.confidence_basis,
               t.assigned_by, t.method, t.model_version, t.prompt_version,
               t.review_status, t.legacy_review_status, t.is_primary,
               t.reviewed_by, t.reviewed_at, t.review_notes, t.evidence_json,
               t.source_file, t.source_row, t.created_at, t.updated_at,
               t.taxonomy_version, t.classification_run_id
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        JOIN ad_creative a ON a.id = t.ad_creative_id
        LEFT JOIN advertiser adv ON adv.id = a.advertiser_id
        {where}
        ORDER BY t.review_status, d.dimension, d.tag_key, t.id
    """
    if limit is not None:
        sql += " LIMIT ?"
        parameters.append(limit)
    return [dict(row) for row in connection.execute(sql, parameters)]


def classification_context(
    connection: sqlite3.Connection,
    tag_id: int,
) -> dict[str, Any]:
    assignment = dict(_assignment_row(connection, tag_id))
    creative_id = int(assignment["ad_creative_id"])
    creative = connection.execute(
        """
        SELECT a.id, a.external_ad_id, a.first_seen_at, a.last_seen_at,
               a.canonical_hash, a.review_state,
               adv.id AS advertiser_id, adv.name AS advertiser, adv.country
        FROM ad_creative a
        LEFT JOIN advertiser adv ON adv.id = a.advertiser_id
        WHERE a.id = ?
        """,
        (creative_id,),
    ).fetchone()
    copies = [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, primary_text, headline, description, cta, language,
                   extraction_method, confidence, is_canonical
            FROM ad_copy
            WHERE ad_creative_id = ?
            ORDER BY is_canonical DESC, id
            """,
            (creative_id,),
        )
    ]
    assets = [
        dict(row)
        for row in connection.execute(
            """
            SELECT s.id, s.asset_type, s.storage_key, s.mime_type, s.sha256,
                   s.rights_status, aa.role, aa.sequence
            FROM ad_asset aa
            JOIN asset s ON s.id = aa.asset_id
            WHERE aa.ad_creative_id = ?
            ORDER BY aa.sequence, s.id
            """,
            (creative_id,),
        )
    ]
    tags = [
        dict(row)
        for row in connection.execute(
            """
            SELECT t.id, d.dimension, d.tag_key, d.label, t.review_status,
                   t.is_primary, t.confidence, t.confidence_basis,
                   t.assigned_by, t.method, t.reviewed_by, t.reviewed_at
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.ad_creative_id = ?
            ORDER BY d.dimension, t.is_primary DESC, t.id
            """,
            (creative_id,),
        )
    ]
    history = [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, event_type, from_status, to_status, actor, reason,
                   payload_json, created_at
            FROM ad_tag_event
            WHERE ad_tag_id = ?
            ORDER BY id
            """,
            (tag_id,),
        )
    ]
    return {
        "assignment": assignment,
        "creative": dict(creative) if creative is not None else None,
        "copies": copies,
        "assets": assets,
        "tags": tags,
        "history": history,
    }


def _demote_primary(
    connection: sqlite3.Connection,
    *,
    creative_id: int,
    dimension: str,
    keep_tag_id: int,
    reviewer: str,
    reason: str,
) -> None:
    rows = connection.execute(
        """
        SELECT t.id
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE t.ad_creative_id = ? AND d.dimension = ? AND t.is_primary = 1
          AND t.id != ?
        """,
        (creative_id, dimension, keep_tag_id),
    ).fetchall()
    now = utc_now()
    for row in rows:
        connection.execute(
            "UPDATE ad_tag SET is_primary = 0, updated_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        _event(
            connection,
            int(row["id"]),
            "demoted_primary",
            None,
            None,
            reviewer,
            reason,
            {"kept_tag_id": keep_tag_id, "dimension": dimension},
        )


def record_classification_review(
    connection: sqlite3.Connection,
    tag_id: int,
    *,
    action: str,
    reviewer: str,
    reason: str | None = None,
    target_dimension: str | None = None,
    target_tag_key: str | None = None,
    approve_correction: bool = False,
    primary: bool | None = None,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    if action not in REVIEW_ACTIONS:
        raise ValueError(f"Invalid review action: {action!r}")
    if not reviewer.strip():
        raise ValueError("A classification review requires a reviewer")
    if action in {"correct", "reject", "defer"} and not (reason or "").strip():
        raise ValueError(f"Action {action} requires a reason")
    row = _assignment_row(connection, tag_id)
    current_status = row["review_status"]
    if current_status == "superseded":
        raise ValueError("A superseded assignment cannot be reviewed again")
    now = utc_now()
    timestamp = reviewed_at or now
    dimension = target_dimension or row["dimension"]
    notes = (reason or "").strip() or None
    payload = {
        "tag_id": tag_id,
        "dimension": row["dimension"],
        "tag_key": row["tag_key"],
        "previous_status": current_status,
        "action": action,
        "reason": notes,
    }
    if action == "approve":
        should_be_primary = row["is_primary"] if primary is None else primary
        if should_be_primary:
            _demote_primary(
                connection,
                creative_id=int(row["ad_creative_id"]),
                dimension=row["dimension"],
                keep_tag_id=tag_id,
                reviewer=reviewer.strip(),
                reason="A human approved a new primary tag for this dimension.",
            )
        connection.execute(
            """
            UPDATE ad_tag
            SET review_status = 'approved', reviewed_by = ?, reviewed_at = ?,
                review_notes = COALESCE(?, review_notes), is_primary = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                reviewer.strip(),
                timestamp,
                notes,
                1 if should_be_primary else 0,
                now,
                tag_id,
            ),
        )
        _event(
            connection,
            tag_id,
            "approved",
            current_status,
            "approved",
            reviewer.strip(),
            notes,
            payload,
        )
        _review_event(connection, tag_id, "approved", reviewer.strip(), timestamp, notes, payload)
        return {"tag_id": tag_id, "action": action, "status": "approved"}

    if action == "reject":
        connection.execute(
            """
            UPDATE ad_tag
            SET review_status = 'rejected', reviewed_by = ?, reviewed_at = ?,
                review_notes = ?, is_primary = 0, updated_at = ?
            WHERE id = ?
            """,
            (reviewer.strip(), timestamp, notes, now, tag_id),
        )
        _event(connection, tag_id, "rejected", current_status, "rejected", reviewer.strip(), notes, payload)
        _review_event(connection, tag_id, "rejected", reviewer.strip(), timestamp, notes, payload)
        return {"tag_id": tag_id, "action": action, "status": "rejected"}

    if action == "defer":
        connection.execute(
            """
            UPDATE ad_tag
            SET review_status = 'pending_review', reviewed_by = ?, reviewed_at = ?,
                review_notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (reviewer.strip(), timestamp, notes, now, tag_id),
        )
        _event(connection, tag_id, "deferred", current_status, "pending_review", reviewer.strip(), notes, payload)
        _review_event(connection, tag_id, "pending", reviewer.strip(), timestamp, notes, payload)
        return {"tag_id": tag_id, "action": action, "status": "pending_review"}

    if not (target_tag_key or "").strip():
        raise ValueError("Action correct requires --tag-key")
    try:
        target_tag_id = validate_tag(
            connection,
            dimension,
            target_tag_key.strip(),
            version=row["taxonomy_version"],
        )
    except ValueError:
        target_tag_id = validate_tag(connection, dimension, target_tag_key.strip())
    if target_tag_id == int(row["tag_definition_id"]):
        raise ValueError("Correction target is the same tag")
    new_status = "approved" if approve_correction else "reviewed"
    should_be_primary = bool(row["is_primary"]) if primary is None else primary
    if should_be_primary and new_status == "approved":
        _demote_primary(
            connection,
            creative_id=int(row["ad_creative_id"]),
            dimension=dimension,
            keep_tag_id=tag_id,
            reviewer=reviewer.strip(),
            reason="A human correction selected a new primary tag.",
        )
    correction_evidence = {
        "previous_tag_id": tag_id,
        "previous_dimension": row["dimension"],
        "previous_tag_key": row["tag_key"],
        "previous_status": current_status,
        "reason": notes,
        "original_evidence": _load_json(row["evidence_json"]),
    }
    new_id = _insert_assignment(
        connection,
        creative_id=int(row["ad_creative_id"]),
        asset_id=int(row["asset_id"]) if row["asset_id"] is not None else None,
        target_tag_id=target_tag_id,
        confidence=None,
        confidence_label=None,
        confidence_basis="human_correction",
        assigned_by=reviewer.strip(),
        method="human_correction",
        review_status=new_status,
        evidence=correction_evidence,
        source_file=row["source_file"],
        source_row=row["source_row"],
        taxonomy_version=row["taxonomy_version"],
        run_id=None,
        legacy_review_status=row["legacy_review_status"],
        is_primary=1 if should_be_primary else 0,
        reviewed_by=reviewer.strip(),
        reviewed_at=timestamp,
        review_notes=notes,
    )
    if new_id is None:
        raise RuntimeError("Could not create correction assignment")
    connection.execute(
        """
        UPDATE ad_tag
        SET review_status = 'superseded', superseded_by_id = ?, reviewed_by = ?,
            reviewed_at = ?, review_notes = ?, is_primary = 0, updated_at = ?
        WHERE id = ?
        """,
        (new_id, reviewer.strip(), timestamp, notes, now, tag_id),
    )
    _event(
        connection,
        tag_id,
        "superseded",
        current_status,
        "superseded",
        reviewer.strip(),
        notes,
        {"new_tag_id": new_id, "new_dimension": dimension, "new_tag_key": target_tag_key},
    )
    _event(
        connection,
        new_id,
        "created_from_correction",
        None,
        new_status,
        reviewer.strip(),
        notes,
        {"previous_tag_id": tag_id, "previous_tag_key": row["tag_key"]},
    )
    _review_event(
        connection,
        tag_id,
        "resolved",
        reviewer.strip(),
        timestamp,
        notes,
        {**payload, "new_tag_id": new_id, "new_dimension": dimension, "new_tag_key": target_tag_key},
    )
    return {
        "tag_id": tag_id,
        "action": action,
        "status": "superseded",
        "new_tag_id": new_id,
        "new_status": new_status,
        "new_dimension": dimension,
        "new_tag_key": target_tag_key,
    }
