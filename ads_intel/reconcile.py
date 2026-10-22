from __future__ import annotations

from typing import Any

from .util import canonical_json

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
            WHERE d.dimension = 'concepto'
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
    return counts


def build_report(connection) -> dict[str, Any]:
    counts = db_counts(connection)
    checks = []
    for key, expected in EXPECTED.items():
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
    ]
    for check in extra_checks:
        check["ok"] = check["actual"] == check["expected"]
        checks.append(check)
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
        "ok": all(check["ok"] for check in checks),
    }


def print_report(report: dict[str, Any]) -> None:
    print(canonical_json(report))
