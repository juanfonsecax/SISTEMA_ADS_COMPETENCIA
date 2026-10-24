from __future__ import annotations

from pathlib import Path
from typing import Any

from .taxonomy import CANONICAL_CONCEPT_KEYS, CANONICAL_DIMENSIONS, DIMENSIONS, TAXONOMY_VERSION
from .util import canonical_json

LEGACY_TAG_DIMENSIONS = (
    "concepto",
    "legacy_concepto_crudo",
    "legacy_gallery_auto",
    "legacy_preclasificacion",
    "curaduria",
)

LEGACY_TAG_METHODS = (
    "manual_final",
    "manual_curation",
    "manual_raw",
    "rule_text_gallery",
    "rule_text",
)

TABLES = (
    "source",
    "capture_batch",
    "source_payload",
    "advertiser",
    "advertiser_alias",
    "ad_creative",
    "ad_observation",
    "asset",
    "ad_asset",
    "ad_copy",
    "ad_relation",
    "tag_definition",
    "ad_tag",
    "legacy_score_snapshot",
    "legacy_element_observation",
    "reference_document",
    "product",
    "product_fact",
    "claim",
    "import_issue",
    "job_run",
    "audit_event",
    "review_event",
    "review_item",
    "asset_visual_signature",
    "visual_similarity_candidate",
    "visual_scan_run",
    "taxonomy_version",
    "taxonomy_dimension",
    "taxonomy_mapping",
    "classification_run",
    "ad_tag_event",
)

EXPECTED = {
    "source": 1,
    "capture_batch": 2,
    "advertiser": 89,
    "advertiser_alias": 10,
    "ad_creative": 597,
    "ad_observation": 597,
    "asset": 597,
    "ad_asset": 597,
    "ad_copy": 629,
    "legacy_score_snapshot": 36,
    "legacy_element_observation": 36,
    "reference_document": 190,
    "product": 1,
    "product_fact": 17,
    "claim": 7,
    "ad_tag": 1041,
    "tag_definition": 48,
    "import_issue": 10,
    "source_payload": 1742,
}


def db_counts(connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        row = connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        counts[table] = int(row["n"])
    counts["tag_definition_total"] = counts["tag_definition"]
    counts["ad_tag_total"] = counts["ad_tag"]
    placeholders = ",".join("?" for _ in LEGACY_TAG_DIMENSIONS)
    method_placeholders = ",".join("?" for _ in LEGACY_TAG_METHODS)
    counts["tag_definition"] = int(
        connection.execute(
            f"SELECT COUNT(*) AS n FROM tag_definition WHERE dimension IN ({placeholders})",
            LEGACY_TAG_DIMENSIONS,
        ).fetchone()["n"]
    )
    counts["ad_tag"] = int(
        connection.execute(
            f"""
            SELECT COUNT(*) AS n
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension IN ({placeholders})
              AND t.method IN ({method_placeholders})
            """,
            (*LEGACY_TAG_DIMENSIONS, *LEGACY_TAG_METHODS),
        ).fetchone()["n"]
    )
    counts["names_total"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM (
                SELECT name FROM advertiser WHERE name IS NOT NULL
                UNION
                SELECT name FROM advertiser_alias WHERE name IS NOT NULL
            )
            """
        ).fetchone()["n"]
    )
    counts["ads_with_asset"] = int(
        connection.execute(
            """
            SELECT COUNT(DISTINCT a.id) AS n
            FROM ad_creative a
            JOIN ad_asset aa ON aa.ad_creative_id = a.id
            JOIN asset s ON s.id = aa.asset_id
            """
        ).fetchone()["n"]
    )
    counts["ads_with_observation"] = int(
        connection.execute("SELECT COUNT(DISTINCT ad_creative_id) AS n FROM ad_observation").fetchone()["n"]
    )
    counts["claims_approved"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM claim WHERE status = 'approved'").fetchone()["n"]
    )
    counts["tags_final_concept"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'concepto' AND t.method = 'manual_final'
            """
        ).fetchone()["n"]
    )
    counts["tags_raw_concept"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'legacy_concepto_crudo'
            """
        ).fetchone()["n"]
    )
    counts["tags_preclassification"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'legacy_preclasificacion'
            """
        ).fetchone()["n"]
    )
    counts["tags_gallery"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'legacy_gallery_auto'
            """
        ).fetchone()["n"]
    )
    counts["tags_favorite"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'curaduria' AND d.tag_key = 'FAVORITO'
            """
        ).fetchone()["n"]
    )
    counts["reference_banco"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'banco_creativo'").fetchone()["n"]
    )
    counts["reference_ficha"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'ficha'").fetchone()["n"]
    )
    counts["reference_canonico"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'canonico'").fetchone()["n"]
    )
    counts["reference_blueprint"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'blueprint'").fetchone()["n"]
    )
    counts["reference_blueprint_t01"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'blueprint_filled_t01'"
        ).fetchone()["n"]
    )
    counts["assets_unknown_rights"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM asset WHERE rights_status = 'unknown'").fetchone()["n"]
    )
    counts["review_items_pending"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM review_item WHERE status = 'pending'").fetchone()["n"]
    )
    counts["visual_signatures"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM asset_visual_signature").fetchone()["n"]
    )
    counts["visual_candidates_pending"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM visual_similarity_candidate WHERE review_status = 'pending'"
        ).fetchone()["n"]
    )
    counts["catalog_versions"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'catalog'"
        ).fetchone()["n"]
    )
    canonical_placeholders = ",".join("?" for _ in CANONICAL_DIMENSIONS)
    counts["taxonomy_tags"] = int(
        connection.execute(
            f"""
            SELECT COUNT(*) AS n
            FROM tag_definition
            WHERE taxonomy_version = ? AND dimension IN ({canonical_placeholders})
            """,
            (TAXONOMY_VERSION, *CANONICAL_DIMENSIONS),
        ).fetchone()["n"]
    )
    counts["taxonomy_tags_total"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM tag_definition WHERE taxonomy_version = ?",
            (TAXONOMY_VERSION,),
        ).fetchone()["n"]
    )
    counts["taxonomy_canonical_concepts"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM tag_definition
            WHERE dimension = 'concepto'
              AND taxonomy_version = ?
              AND tag_key != 'SIN_CLASIFICAR'
            """,
            (TAXONOMY_VERSION,),
        ).fetchone()["n"]
    )
    counts["taxonomy_c6_canonical"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM tag_definition
            WHERE dimension = 'concepto'
              AND taxonomy_version = ?
              AND tag_key LIKE 'C6%'
            """,
            (TAXONOMY_VERSION,),
        ).fetchone()["n"]
    )
    counts["taxonomy_mappings_needing_review"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM taxonomy_mapping WHERE mapping_status = 'needs_review'"
        ).fetchone()["n"]
    )
    counts["classification_assignments"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.taxonomy_version = ?
              AND d.dimension NOT IN ('legacy_concepto_crudo', 'legacy_gallery_auto',
                                      'legacy_preclasificacion', 'curaduria')
            """,
            (TAXONOMY_VERSION,),
        ).fetchone()["n"]
    )
    counts["classification_pending"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.review_status IN ('suggested', 'pending_review')
              AND d.dimension NOT IN ('legacy_concepto_crudo', 'legacy_gallery_auto',
                                      'legacy_preclasificacion', 'curaduria')
            """
        ).fetchone()["n"]
    )
    counts["classification_approved"] = int(
        connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.review_status = 'approved'
              AND d.dimension NOT IN ('legacy_concepto_crudo', 'legacy_gallery_auto',
                                      'legacy_preclasificacion', 'curaduria')
            """
        ).fetchone()["n"]
    )
    counts["classification_runs"] = int(
        connection.execute("SELECT COUNT(*) AS n FROM classification_run").fetchone()["n"]
    )
    return counts


def build_report(connection, root: Path | None = None) -> dict[str, Any]:
    counts = db_counts(connection)
    checks = []
    for key, expected in EXPECTED.items():
        if key == "reference_document":
            expected += max(0, counts["catalog_versions"] - 1)
        actual = counts.get(key, 0)
        checks.append({"name": key, "expected": expected, "actual": actual, "ok": actual == expected})
    extra_checks = [
        {"name": "names_total", "expected": 95, "actual": counts["names_total"]},
        {"name": "ads_with_asset", "expected": 597, "actual": counts["ads_with_asset"]},
        {"name": "ads_with_observation", "expected": 597, "actual": counts["ads_with_observation"]},
        {"name": "claims_approved", "expected": 0, "actual": counts["claims_approved"]},
        {"name": "tags_final_concept", "expected": 111, "actual": counts["tags_final_concept"]},
        {"name": "tags_raw_concept", "expected": 111, "actual": counts["tags_raw_concept"]},
        {"name": "tags_preclassification", "expected": 597, "actual": counts["tags_preclassification"]},
        {"name": "tags_gallery", "expected": 111, "actual": counts["tags_gallery"]},
        {"name": "tags_favorite", "expected": 111, "actual": counts["tags_favorite"]},
        {"name": "reference_banco", "expected": 48, "actual": counts["reference_banco"]},
        {"name": "reference_ficha", "expected": 111, "actual": counts["reference_ficha"]},
        {"name": "reference_canonico", "expected": 22, "actual": counts["reference_canonico"]},
        {"name": "reference_blueprint", "expected": 4, "actual": counts["reference_blueprint"]},
        {"name": "reference_blueprint_t01", "expected": 4, "actual": counts["reference_blueprint_t01"]},
        {"name": "taxonomy_dimensions", "expected": len(DIMENSIONS), "actual": counts["taxonomy_dimension"]},
        {
            "name": "taxonomy_canonical_concepts",
            "expected": len(CANONICAL_CONCEPT_KEYS),
            "actual": counts["taxonomy_canonical_concepts"],
        },
        {"name": "taxonomy_c6_canonical", "expected": 0, "actual": counts["taxonomy_c6_canonical"]},
    ]
    for check in extra_checks:
        check["ok"] = check["actual"] == check["expected"]
        checks.append(check)
    if root is not None:
        missing_paths = [
            row["storage_key"]
            for row in connection.execute("SELECT storage_key FROM asset ORDER BY id")
            if not (root / row["storage_key"]).is_file()
        ]
        checks.append(
            {
                "name": "asset_paths_missing",
                "expected": 0,
                "actual": len(missing_paths),
                "ok": not missing_paths,
                "paths": missing_paths,
            }
        )
    issues = [
        dict(row)
        for row in connection.execute(
            "SELECT severity, issue_type, source_file, source_row, external_id, message FROM import_issue ORDER BY id"
        )
    ]
    return {
        "counts": counts,
        "checks": checks,
        "issues": issues,
        "phase2": {
            "assets_unknown_rights": counts["assets_unknown_rights"],
            "review_items_pending": counts["review_items_pending"],
            "visual_signatures": counts["visual_signatures"],
            "visual_candidates_pending": counts["visual_candidates_pending"],
        },
        "phase3": {
            "taxonomy_versions": counts["taxonomy_version"],
            "taxonomy_dimensions": counts["taxonomy_dimension"],
            "taxonomy_tags": counts["taxonomy_tags"],
            "taxonomy_mappings_needing_review": counts["taxonomy_mappings_needing_review"],
            "classification_assignments": counts["classification_assignments"],
            "classification_pending": counts["classification_pending"],
            "classification_approved": counts["classification_approved"],
            "classification_runs": counts["classification_runs"],
        },
        "ok": all(check["ok"] for check in checks),
    }


def print_report(report: dict[str, Any]) -> None:
    print(canonical_json(report))
