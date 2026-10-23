from __future__ import annotations

import json
import sqlite3
from typing import Any

from .util import canonical_json, utc_now

REVIEW_STATUSES = {"pending", "approved", "restricted", "rejected", "needs_evidence"}
CLAIM_REVIEW_STATUSES = REVIEW_STATUSES | {"evidence_needed"}
ASSET_RIGHTS_STATUSES = {"unknown", "pending", "approved", "restricted", "rejected"}
REVIEW_ITEM_STATUSES = {"pending", "in_review", "needs_evidence", "resolved", "rejected"}
REVIEW_EVENT_STATUSES = (
    REVIEW_STATUSES | CLAIM_REVIEW_STATUSES | ASSET_RIGHTS_STATUSES | REVIEW_ITEM_STATUSES
)


class ApprovalError(ValueError):
    pass


def _clean(value: str | None) -> str | None:
    text = value.strip() if value is not None else None
    return text or None


def _validate_status(status: str, allowed: set[str], label: str) -> str:
    if status not in allowed:
        raise ValueError(f"Invalid {label} status: {status!r}")
    return status


def _require_reviewer(status: str, reviewer: str | None) -> str | None:
    if status in {"approved", "restricted", "rejected"} and not _clean(reviewer):
        raise ApprovalError(f"Status {status!r} requires a reviewer")
    return _clean(reviewer)


def _require_approval_evidence(
    status: str,
    evidence_ref: str | None,
    reviewer: str | None,
    reviewed_at: str | None,
) -> tuple[str, str, str]:
    if status != "approved":
        raise ApprovalError("Only an approved review can be exported")
    evidence = _clean(evidence_ref)
    actor = _clean(reviewer)
    timestamp = _clean(reviewed_at)
    if not evidence:
        raise ApprovalError("Approved export requires an evidence reference")
    if not actor:
        raise ApprovalError("Approved export requires a reviewer")
    if not timestamp:
        raise ApprovalError("Approved export requires a review date")
    return evidence, actor, timestamp


def _has_claim_evidence(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return bool(value.strip())
    if isinstance(parsed, list):
        return any(str(item).strip() for item in parsed)
    return bool(str(parsed).strip())


def _event(
    connection: sqlite3.Connection,
    object_type: str,
    object_id: int,
    review_type: str,
    status: str,
    evidence_ref: str | None,
    reviewer: str | None,
    reviewed_at: str | None,
    notes: str | None,
    payload: dict[str, Any] | None,
    now: str,
) -> int:
    _validate_status(status, REVIEW_EVENT_STATUSES, "review event")
    cursor = connection.execute(
        """
        INSERT INTO review_event
            (object_type, object_id, review_type, status, evidence_ref, reviewer,
             reviewed_at, notes, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            object_type,
            object_id,
            review_type,
            status,
            _clean(evidence_ref),
            _clean(reviewer),
            _clean(reviewed_at),
            _clean(notes),
            canonical_json(payload) if payload is not None else None,
            now,
        ),
    )
    return int(cursor.lastrowid)


def record_source_review(
    connection: sqlite3.Connection,
    source_id: int,
    *,
    status: str,
    permission_basis: str | None = None,
    evidence_ref: str | None = None,
    reviewer: str | None = None,
    reviewed_at: str | None = None,
    notes: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    _validate_status(status, REVIEW_STATUSES, "source")
    actor = _require_reviewer(status, reviewer)
    if status == "approved":
        _require_approval_evidence(status, evidence_ref, actor, reviewed_at)
        basis = _clean(permission_basis)
        if not basis or basis == "pending_review":
            raise ApprovalError("Approved source requires a non-pending permission basis")
    row = connection.execute("SELECT id FROM source WHERE id = ?", (source_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown source: {source_id}")
    now = utc_now()
    timestamp = _clean(reviewed_at) or (now if status != "pending" else None)
    with connection:
        connection.execute(
            """
            UPDATE source
            SET review_status = ?,
                permission_basis = COALESCE(?, permission_basis),
                permission_evidence_ref = ?,
                permission_reviewer = ?,
                permission_reviewed_at = ?,
                notes = COALESCE(?, notes)
            WHERE id = ?
            """,
            (
                status,
                _clean(permission_basis),
                _clean(evidence_ref),
                actor,
                timestamp,
                _clean(notes),
                source_id,
            ),
        )
        return _event(
            connection,
            "source",
            source_id,
            "permission",
            status,
            evidence_ref,
            actor,
            timestamp,
            notes,
            payload,
            now,
        )


def record_asset_rights_review(
    connection: sqlite3.Connection,
    asset_id: int,
    *,
    status: str,
    evidence_ref: str | None = None,
    reviewer: str | None = None,
    reviewed_at: str | None = None,
    notes: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    _validate_status(status, ASSET_RIGHTS_STATUSES, "asset rights")
    actor = _require_reviewer(status, reviewer)
    if status == "approved":
        _require_approval_evidence(status, evidence_ref, actor, reviewed_at)
    row = connection.execute("SELECT id FROM asset WHERE id = ?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown asset: {asset_id}")
    now = utc_now()
    timestamp = _clean(reviewed_at) or (now if status not in {"unknown", "pending"} else None)
    with connection:
        connection.execute(
            """
            UPDATE asset
            SET rights_status = ?,
                rights_evidence_ref = ?,
                rights_reviewer = ?,
                rights_reviewed_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (status, _clean(evidence_ref), actor, timestamp, now, asset_id),
        )
        return _event(
            connection,
            "asset",
            asset_id,
            "rights",
            status,
            evidence_ref,
            actor,
            timestamp,
            notes,
            payload,
            now,
        )


def record_claim_review(
    connection: sqlite3.Connection,
    claim_id: int,
    *,
    status: str,
    evidence_refs: list[str] | str | None = None,
    reviewer: str | None = None,
    reviewed_at: str | None = None,
    notes: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    _validate_status(status, CLAIM_REVIEW_STATUSES, "claim")
    actor = _require_reviewer(status, reviewer)
    evidence_value: str | None
    if isinstance(evidence_refs, list):
        evidence_value = canonical_json(evidence_refs) if evidence_refs else None
    else:
        evidence_value = _clean(evidence_refs)
    if status == "approved":
        if not _has_claim_evidence(evidence_value):
            raise ApprovalError("Approved claim requires a non-empty evidence list")
        _require_approval_evidence(status, evidence_value, actor, reviewed_at)
    row = connection.execute("SELECT id, source_file FROM claim WHERE id = ?", (claim_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown claim: {claim_id}")
    now = utc_now()
    timestamp = _clean(reviewed_at) or (now if status in {"approved", "rejected", "restricted"} else None)
    with connection:
        connection.execute(
            """
            UPDATE claim
            SET status = ?,
                evidence_refs = COALESCE(?, evidence_refs),
                approved_by = ?,
                reviewed_at = ?
            WHERE id = ?
            """,
            (status, evidence_value, actor, timestamp, claim_id),
        )
        return _event(
            connection,
            "claim",
            claim_id,
            "claim",
            status,
            evidence_value,
            actor,
            timestamp,
            notes,
            payload or {"claim_source_file": row["source_file"]},
            now,
        )


def _assert_source(connection: sqlite3.Connection, source_id: int) -> None:
    row = connection.execute(
        """
        SELECT review_status, permission_basis, permission_evidence_ref,
               permission_reviewer, permission_reviewed_at
        FROM source WHERE id = ?
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        raise ApprovalError(f"Unknown source: {source_id}")
    if row["review_status"] != "approved":
        raise ApprovalError(f"Source {source_id} is not approved for export")
    _require_approval_evidence(
        row["review_status"],
        row["permission_evidence_ref"],
        row["permission_reviewer"],
        row["permission_reviewed_at"],
    )
    if not row["permission_basis"] or row["permission_basis"] == "pending_review":
        raise ApprovalError(f"Source {source_id} has no approved permission basis")


def _assert_asset(connection: sqlite3.Connection, asset_id: int) -> None:
    row = connection.execute(
        """
        SELECT rights_status, rights_evidence_ref, rights_reviewer, rights_reviewed_at
        FROM asset WHERE id = ?
        """,
        (asset_id,),
    ).fetchone()
    if row is None:
        raise ApprovalError(f"Unknown asset: {asset_id}")
    if row["rights_status"] != "approved":
        raise ApprovalError(f"Asset {asset_id} rights are not approved for export")
    _require_approval_evidence(
        row["rights_status"],
        row["rights_evidence_ref"],
        row["rights_reviewer"],
        row["rights_reviewed_at"],
    )


def _assert_claim(connection: sqlite3.Connection, claim_id: int) -> None:
    row = connection.execute(
        "SELECT status, evidence_refs, approved_by, reviewed_at FROM claim WHERE id = ?",
        (claim_id,),
    ).fetchone()
    if row is None:
        raise ApprovalError(f"Unknown claim: {claim_id}")
    if row["status"] != "approved":
        raise ApprovalError(f"Claim {claim_id} is not approved for export")
    if not _has_claim_evidence(row["evidence_refs"]):
        raise ApprovalError(f"Claim {claim_id} has no usable evidence")
    _require_approval_evidence(
        row["status"],
        row["evidence_refs"],
        row["approved_by"],
        row["reviewed_at"],
    )


def assert_exportable(connection: sqlite3.Connection, object_type: str, object_id: int) -> None:
    if object_type == "source":
        _assert_source(connection, object_id)
    elif object_type == "asset":
        _assert_asset(connection, object_id)
    elif object_type == "claim":
        _assert_claim(connection, object_id)
    else:
        raise ValueError(f"Unsupported export object type: {object_type}")


def exportable_asset_ids(connection: sqlite3.Connection) -> list[int]:
    rows = connection.execute(
        """
        SELECT id FROM asset
        WHERE rights_status = 'approved'
          AND rights_evidence_ref IS NOT NULL
          AND rights_reviewer IS NOT NULL
          AND rights_reviewed_at IS NOT NULL
        ORDER BY id
        """
    ).fetchall()
    return [int(row["id"]) for row in rows]
