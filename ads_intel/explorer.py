from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .taxonomy import TAXONOMY_VERSION

CANONICAL_DIMENSION_EXCLUSIONS = (
    "legacy_concepto_crudo",
    "legacy_gallery_auto",
    "legacy_preclasificacion",
    "curaduria",
)


def _date_bound(value: str | None, *, end: bool = False) -> str | None:
    if not value:
        return None
    text = value.strip()
    if len(text) == 10:
        return f"{text}T23:59:59Z" if end else f"{text}T00:00:00Z"
    return text


def _creative_tags(
    connection,
    creative_ids: list[int],
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[int, list[dict[str, Any]]]:
    if not creative_ids:
        return {}
    placeholders = ",".join("?" for _ in creative_ids)
    rows = connection.execute(
        f"""
        SELECT t.ad_creative_id, t.id, d.dimension, d.tag_key, d.label,
               t.review_status, t.is_primary, t.confidence, t.confidence_basis,
               t.evidence_json, t.assigned_by, t.method, t.reviewed_by, t.reviewed_at
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        WHERE t.ad_creative_id IN ({placeholders})
          AND d.taxonomy_version = ?
          AND d.dimension NOT IN (?, ?, ?, ?)
        ORDER BY t.ad_creative_id, d.dimension, t.is_primary DESC, d.tag_key
        """,
        [*creative_ids, taxonomy_version, *CANONICAL_DIMENSION_EXCLUSIONS],
    ).fetchall()
    result: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        result.setdefault(int(row["ad_creative_id"]), []).append(dict(row))
    return result


def search_creatives(
    connection,
    *,
    text: str | None = None,
    advertiser: str | None = None,
    tag_filters: list[tuple[str, str]] | None = None,
    market: str | None = None,
    language: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    unclassified: bool = False,
    low_evidence: bool = False,
    dimension_missing: str | None = None,
    taxonomy_version: str = TAXONOMY_VERSION,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    clauses = ["1 = 1"]
    parameters: list[Any] = []
    if text:
        like = f"%{text.strip()}%"
        clauses.append(
            """
            (
                a.external_ad_id LIKE ?
                OR adv.name LIKE ?
                OR EXISTS (
                    SELECT 1 FROM ad_copy c
                    WHERE c.ad_creative_id = a.id
                      AND (c.primary_text LIKE ? OR c.headline LIKE ? OR c.description LIKE ?)
                )
            )
            """
        )
        parameters.extend([like, like, like, like, like])
    if advertiser:
        clauses.append("adv.name LIKE ?")
        parameters.append(f"%{advertiser.strip()}%")
    if market:
        clauses.append(
            """
            (
                adv.country = ?
                OR EXISTS (
                    SELECT 1 FROM ad_tag t
                    JOIN tag_definition d ON d.id = t.tag_definition_id
                    WHERE t.ad_creative_id = a.id
                      AND d.taxonomy_version = ?
                      AND d.dimension = 'mercado'
                      AND d.tag_key = ?
                      AND t.review_status NOT IN ('rejected', 'superseded')
                )
            )
            """
        )
        parameters.extend([market.strip(), taxonomy_version, market.strip()])
    if language:
        clauses.append(
            """
            (
                EXISTS (
                    SELECT 1 FROM ad_copy c
                    WHERE c.ad_creative_id = a.id AND c.language = ?
                )
                OR EXISTS (
                    SELECT 1 FROM ad_tag t
                    JOIN tag_definition d ON d.id = t.tag_definition_id
                    WHERE t.ad_creative_id = a.id
                      AND d.taxonomy_version = ?
                      AND d.dimension = 'idioma'
                      AND d.tag_key = ?
                      AND t.review_status NOT IN ('rejected', 'superseded')
                )
            )
            """
        )
        parameters.extend([language.strip(), taxonomy_version, language.strip()])
    date_from_value = _date_bound(date_from)
    if date_from_value:
        clauses.append("a.first_seen_at >= ?")
        parameters.append(date_from_value)
    date_to_value = _date_bound(date_to, end=True)
    if date_to_value:
        clauses.append("a.first_seen_at <= ?")
        parameters.append(date_to_value)
    for dimension, tag_key in tag_filters or []:
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE t.ad_creative_id = a.id
                  AND d.taxonomy_version = ?
                  AND d.dimension = ?
                  AND d.tag_key = ?
                  AND t.review_status NOT IN ('rejected', 'superseded')
            )
            """
        )
        parameters.extend([taxonomy_version, dimension, tag_key])
    if unclassified:
        clauses.append(
            """
            NOT EXISTS (
                SELECT 1 FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE t.ad_creative_id = a.id
                  AND d.taxonomy_version = ?
                  AND d.dimension = 'concepto'
                  AND d.tag_key != 'SIN_CLASIFICAR'
                  AND t.review_status NOT IN ('rejected', 'superseded')
            )
            """
        )
        parameters.append(taxonomy_version)
    if dimension_missing:
        clauses.append(
            """
            NOT EXISTS (
                SELECT 1 FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE t.ad_creative_id = a.id
                  AND d.taxonomy_version = ?
                  AND d.dimension = ?
                  AND t.review_status NOT IN ('rejected', 'superseded')
            )
            """
        )
        parameters.extend([taxonomy_version, dimension_missing])
    if low_evidence:
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE t.ad_creative_id = a.id
                  AND d.taxonomy_version = ?
                  AND (
                      t.review_status IN ('suggested', 'pending_review')
                      OR t.evidence_json IS NULL
                  )
            )
            """
        )
        parameters.append(taxonomy_version)
    sql = f"""
        SELECT a.id, a.external_ad_id, adv.name AS advertiser, adv.country,
               a.first_seen_at, a.last_seen_at,
               (
                   SELECT c.primary_text FROM ad_copy c
                   WHERE c.ad_creative_id = a.id AND c.is_canonical = 1
                   LIMIT 1
               ) AS primary_text,
               (
                   SELECT c.headline FROM ad_copy c
                   WHERE c.ad_creative_id = a.id AND c.is_canonical = 1
                   LIMIT 1
               ) AS headline,
               (
                   SELECT c.language FROM ad_copy c
                   WHERE c.ad_creative_id = a.id AND c.is_canonical = 1
                   LIMIT 1
               ) AS language,
               (
                   SELECT s.storage_key
                   FROM ad_asset aa
                   JOIN asset s ON s.id = aa.asset_id
                   WHERE aa.ad_creative_id = a.id
                   ORDER BY aa.sequence, s.id
                   LIMIT 1
               ) AS storage_key
        FROM ad_creative a
        LEFT JOIN advertiser adv ON adv.id = a.advertiser_id
        WHERE {' AND '.join(clauses)}
        ORDER BY a.id
        LIMIT ? OFFSET ?
    """
    parameters.extend([max(1, min(limit, 500)), max(0, offset)])
    rows = [dict(row) for row in connection.execute(sql, parameters)]
    tags = _creative_tags(connection, [int(row["id"]) for row in rows], taxonomy_version)
    for row in rows:
        row_tags = tags.get(int(row["id"]), [])
        row["tags"] = row_tags
        row["has_pending_classification"] = any(
            tag["review_status"] in {"suggested", "pending_review"} for tag in row_tags
        )
        row["has_low_evidence"] = any(
            tag["review_status"] in {"suggested", "pending_review"}
            or tag["evidence_json"] is None
            for tag in row_tags
        )
        row["market"] = row["country"]
    return rows


def creative_detail(connection, creative_id: int) -> dict[str, Any]:
    creative = connection.execute(
        """
        SELECT a.id, a.external_ad_id, a.first_seen_at, a.last_seen_at, a.canonical_hash,
               a.review_state, a.is_catalog, adv.id AS advertiser_id, adv.name AS advertiser,
               adv.country, adv.page_url
        FROM ad_creative a
        LEFT JOIN advertiser adv ON adv.id = a.advertiser_id
        WHERE a.id = ?
        """,
        (creative_id,),
    ).fetchone()
    if creative is None:
        raise ValueError(f"Unknown creative: {creative_id}")
    copies = [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, primary_text, headline, description, cta, destination_url,
                   language, extraction_method, confidence, is_canonical
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
            SELECT t.id, d.taxonomy_version, d.dimension, d.tag_key, d.label,
                   t.review_status, t.is_primary, t.confidence, t.confidence_basis,
                   t.assigned_by, t.method, t.reviewed_by, t.reviewed_at,
                   t.review_notes, t.evidence_json
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.ad_creative_id = ?
            ORDER BY d.dimension, t.is_primary DESC, t.id
            """,
            (creative_id,),
        )
    ]
    observations = [
        dict(row)
        for row in connection.execute(
            """
            SELECT id, observed_on, observed_at, reported_status, active_days_reported,
                   observed_rank, observed_total, page_active_ads_reported,
                   reported_velocity
            FROM ad_observation
            WHERE ad_creative_id = ?
            ORDER BY observed_at, id
            """,
            (creative_id,),
        )
    ]
    return {
        "creative": dict(creative),
        "copies": copies,
        "assets": assets,
        "tags": tags,
        "observations": observations,
    }


EXPORT_COLUMNS = (
    "assignment_id",
    "taxonomy_version",
    "dimension",
    "tag_key",
    "label",
    "assignment_status",
    "is_primary",
    "confidence",
    "confidence_basis",
    "assigned_by",
    "method",
    "model_version",
    "prompt_version",
    "evidence_json",
    "source_file",
    "source_row",
    "created_at",
    "reviewed_by",
    "reviewed_at",
    "review_notes",
    "ad_creative_id",
    "external_ad_id",
    "advertiser",
    "market",
    "language",
    "asset_id",
    "storage_key",
)


def export_classifications(
    connection,
    output_path: Path,
    *,
    format: str = "csv",
    dimension: str | None = None,
    status: str | None = None,
    cutoff: str | None = None,
    scope: str = "canonical",
    taxonomy_version: str = TAXONOMY_VERSION,
) -> dict[str, Any]:
    if format not in {"csv", "jsonl"}:
        raise ValueError(f"Unsupported export format: {format!r}")
    if scope not in {"canonical", "all"}:
        raise ValueError(f"Unsupported export scope: {scope!r}")
    clauses = ["d.taxonomy_version = ?"]
    parameters: list[Any] = [taxonomy_version]
    if dimension:
        clauses.append("d.dimension = ?")
        parameters.append(dimension)
    if status:
        clauses.append("t.review_status = ?")
        parameters.append(status)
    cutoff_value = _date_bound(cutoff, end=True)
    if cutoff_value:
        clauses.append("t.created_at <= ?")
        parameters.append(cutoff_value)
    if scope == "canonical":
        clauses.append("d.dimension NOT IN (?, ?, ?, ?)")
        parameters.extend(CANONICAL_DIMENSION_EXCLUSIONS)
    rows = connection.execute(
        f"""
        SELECT t.id AS assignment_id, t.taxonomy_version, d.dimension, d.tag_key, d.label,
               t.review_status AS assignment_status, t.is_primary, t.confidence,
               t.confidence_basis, t.assigned_by, t.method, t.model_version,
               t.prompt_version, t.evidence_json, t.source_file, t.source_row,
               t.created_at, t.reviewed_by, t.reviewed_at, t.review_notes,
               t.ad_creative_id, a.external_ad_id, adv.name AS advertiser,
               adv.country AS market,
               (
                   SELECT c.language FROM ad_copy c
                   WHERE c.ad_creative_id = a.id AND c.is_canonical = 1
                   LIMIT 1
               ) AS language,
               t.asset_id,
               (
                   SELECT s.storage_key FROM asset s WHERE s.id = t.asset_id
               ) AS storage_key
        FROM ad_tag t
        JOIN tag_definition d ON d.id = t.tag_definition_id
        JOIN ad_creative a ON a.id = t.ad_creative_id
        LEFT JOIN advertiser adv ON adv.id = a.advertiser_id
        WHERE {' AND '.join(clauses)}
        ORDER BY t.id
        """,
        parameters,
    ).fetchall()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = [{key: row[key] for key in EXPORT_COLUMNS} for row in rows]
    if format == "csv":
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
            writer.writeheader()
            writer.writerows(records)
    else:
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "path": str(output_path),
        "format": format,
        "scope": scope,
        "rows": len(records),
        "cutoff": cutoff_value,
        "taxonomy_version": taxonomy_version,
    }
