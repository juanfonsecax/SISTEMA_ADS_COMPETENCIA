from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ads_intel.classification import (
    classification_context,
    classify_legacy,
    list_classifications,
    list_mappings,
    record_classification_review,
    record_mapping_decision,
)
from ads_intel.db import connect
from ads_intel.enrichment import (
    ENRICHMENT_CONTRACT_VERSION,
    enrichment_contract_schema,
    ingest_enrichment,
    validate_enrichment_payload,
)
from ads_intel.explorer import creative_detail, export_classifications, search_creatives
from ads_intel.importers import import_all
from ads_intel.reconcile import build_report
from ads_intel.taxonomy import TAXONOMY_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TaxonomyClassificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp.name) / "base.db"
        import_all(ROOT, cls.db_path)
        cls.connection = connect(cls.db_path)
        with cls.connection:
            cls.classification = classify_legacy(cls.connection, root=ROOT)
        cls.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        cls.report = build_report(cls.connection, root=ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()
        cls.temp.cleanup()

    def _copy_connection(self):
        case_dir = Path(tempfile.mkdtemp(dir=self.temp.name))
        db_path = case_dir / "case.db"
        shutil.copy2(self.db_path, db_path)
        connection = connect(db_path)
        self.addCleanup(connection.close)
        return connection

    def test_taxonomy_is_versioned_and_c6_is_not_canonical(self) -> None:
        version = self.connection.execute(
            "SELECT version, status FROM taxonomy_version"
        ).fetchone()
        self.assertEqual((version["version"], version["status"]), (TAXONOMY_VERSION, "active"))
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) AS n FROM taxonomy_dimension").fetchone()["n"],
            21,
        )
        concept_keys = {
            row["tag_key"]
            for row in self.connection.execute(
                "SELECT tag_key FROM tag_definition WHERE dimension = 'concepto'"
            )
        }
        self.assertEqual(
            concept_keys,
            {"C1_OFERTA", "C2_BENEFICIOS", "C3_SINTOMA", "C4_TRANSFORMACION",
             "C5_PRUEBA", "C7_DESEO", "C8_PROGRESION", "C9_COMPARACION", "SIN_CLASIFICAR"},
        )
        self.assertFalse(any(key.startswith("C6") for key in concept_keys))
        null_definitions = self.connection.execute(
            """
            SELECT COUNT(*) AS n FROM tag_definition
            WHERE taxonomy_version = ?
              AND dimension NOT IN ('legacy_concepto_crudo', 'legacy_gallery_auto',
                                    'legacy_preclasificacion', 'curaduria')
              AND (definition IS NULL OR TRIM(definition) = '')
            """,
            (TAXONOMY_VERSION,),
        ).fetchone()["n"]
        self.assertEqual(null_definitions, 0)

    def test_legacy_mapping_preserves_source_and_marks_pending(self) -> None:
        self.assertEqual(self.classification["run_id"], 1)
        self.assertEqual(self.classification["source_labels"], 29)
        self.assertEqual(self.classification["mapped_labels"], 19)
        self.assertEqual(self.classification["needs_review_labels"], 10)
        self.assertEqual(self.classification["errors"], [])
        c6 = self.connection.execute(
            """
            SELECT id, target_dimension, target_tag_key, mapping_status, rationale
            FROM taxonomy_mapping
            WHERE source_dimension = 'legacy_concepto_crudo' AND source_tag_key = 'C6_UNBOXING'
            """
        ).fetchone()
        self.assertIsNotNone(c6)
        self.assertEqual((c6["target_dimension"], c6["target_tag_key"]), ("concepto", "C5_PRUEBA"))
        self.assertEqual(c6["mapping_status"], "mapped")
        self.assertIn("retirado", c6["rationale"])
        legacy_c6 = self.connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE d.dimension = 'legacy_concepto_crudo' AND d.tag_key = 'C6_UNBOXING'
            """
        ).fetchone()["n"]
        self.assertEqual(legacy_c6, 2)
        assignment = self.connection.execute(
            """
            SELECT t.id, t.confidence, t.confidence_basis, t.review_status,
                   t.legacy_review_status, t.evidence_json, t.method
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.method = 'legacy_mapping_v1'
              AND d.dimension = 'concepto'
            ORDER BY t.id
            LIMIT 1
            """
        ).fetchone()
        self.assertIsNotNone(assignment)
        self.assertIsNone(assignment["confidence"])
        self.assertEqual(assignment["confidence_basis"], "legacy_mapping_without_numeric_confidence")
        self.assertEqual(assignment["review_status"], "pending_review")
        self.assertIsNotNone(assignment["legacy_review_status"])
        evidence = json.loads(assignment["evidence_json"])
        self.assertIn("source_ad_tag_id", evidence)
        self.assertIn("mapping_id", evidence)
        self.assertIn("source_dimension", evidence)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM taxonomy_mapping WHERE mapping_status = 'needs_review'"
            ).fetchone()["n"],
            10,
        )

    def test_classification_list_defaults_to_canonical_scope(self) -> None:
        pending = list_classifications(self.connection, status="pending_review")
        self.assertEqual(len(pending), 88)
        self.assertTrue(all(item["dimension"] == "concepto" for item in pending))
        all_pending = list_classifications(
            self.connection, status="pending_review", include_legacy=True
        )
        self.assertGreater(len(all_pending), len(pending))

    def test_reconciliation_remains_green_after_classification(self) -> None:
        self.assertTrue(self.report["ok"], [c for c in self.report["checks"] if not c["ok"]])
        self.assertEqual(self.report["counts"]["ad_tag"], 1041)
        self.assertEqual(self.report["counts"]["tag_definition"], 48)
        self.assertEqual(self.report["phase3"]["taxonomy_dimensions"], 21)
        self.assertEqual(self.report["phase3"]["taxonomy_tags"], 97)
        self.assertEqual(self.report["phase3"]["classification_pending"], 88)

    def test_approved_tag_is_not_overwritten_by_automatic_run(self) -> None:
        connection = self._copy_connection()
        assignment = connection.execute(
            """
            SELECT t.id, t.ad_creative_id, t.tag_definition_id
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.method = 'legacy_mapping_v1' AND d.dimension = 'concepto'
            ORDER BY t.id
            LIMIT 1
            """
        ).fetchone()
        record_classification_review(
            connection,
            assignment["id"],
            action="approve",
            reviewer="human@example.test",
            reason="Evidence checked.",
        )
        connection.commit()
        before = connection.execute(
            "SELECT COUNT(*) AS n FROM ad_tag WHERE method = 'legacy_mapping_v1'"
        ).fetchone()["n"]
        classify_legacy(connection, root=ROOT)
        connection.commit()
        after = connection.execute(
            "SELECT COUNT(*) AS n FROM ad_tag WHERE method = 'legacy_mapping_v1'"
        ).fetchone()["n"]
        self.assertEqual(after, before)
        approved = connection.execute(
            "SELECT review_status, reviewed_by, is_primary FROM ad_tag WHERE id = ?",
            (assignment["id"],),
        ).fetchone()
        self.assertEqual(approved["review_status"], "approved")
        self.assertEqual(approved["reviewed_by"], "human@example.test")
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) AS n FROM ad_tag_event WHERE ad_tag_id = ? AND event_type = 'approved'",
                (assignment["id"],),
            ).fetchone()["n"],
            1,
        )

    def test_correction_supersedes_without_deleting_history(self) -> None:
        connection = self._copy_connection()
        assignment = connection.execute(
            """
            SELECT t.id, t.ad_creative_id, d.tag_key
            FROM ad_tag t
            JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.method = 'legacy_mapping_v1' AND d.dimension = 'concepto'
              AND d.tag_key != 'C9_COMPARACION'
            ORDER BY t.id
            LIMIT 1
            """
        ).fetchone()
        result = record_classification_review(
            connection,
            assignment["id"],
            action="correct",
            reviewer="human@example.test",
            reason="Human corrected the concept.",
            target_dimension="concepto",
            target_tag_key="C9_COMPARACION",
            approve_correction=True,
            primary=True,
        )
        connection.commit()
        old = connection.execute(
            "SELECT review_status, superseded_by_id, is_primary FROM ad_tag WHERE id = ?",
            (assignment["id"],),
        ).fetchone()
        self.assertEqual(old["review_status"], "superseded")
        self.assertEqual(old["superseded_by_id"], result["new_tag_id"])
        self.assertEqual(old["is_primary"], 0)
        new = connection.execute(
            "SELECT review_status, assigned_by, method, is_primary, confidence_basis FROM ad_tag WHERE id = ?",
            (result["new_tag_id"],),
        ).fetchone()
        self.assertEqual(new["review_status"], "approved")
        self.assertEqual(new["assigned_by"], "human@example.test")
        self.assertEqual(new["method"], "human_correction")
        self.assertEqual(new["is_primary"], 1)
        self.assertEqual(new["confidence_basis"], "human_correction")
        history = classification_context(connection, assignment["id"])["history"]
        self.assertEqual([event["event_type"] for event in history], ["created_from_legacy_mapping", "superseded"])
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) AS n FROM review_event WHERE object_type = 'ad_tag' AND object_id = ?",
                (assignment["id"],),
            ).fetchone()["n"],
            1,
        )
        report = build_report(connection, root=ROOT)
        self.assertTrue(report["ok"], [check for check in report["checks"] if not check["ok"]])
        self.assertEqual(report["counts"]["ad_tag"], 1041)

    def test_reject_and_defer_are_audited(self) -> None:
        connection = self._copy_connection()
        rows = connection.execute(
            """
            SELECT t.id FROM ad_tag t JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.method = 'legacy_mapping_v1' AND d.dimension = 'concepto'
            ORDER BY t.id LIMIT 2
            """
        ).fetchall()
        record_classification_review(
            connection, rows[0]["id"], action="reject", reviewer="human@example.test", reason="Not the concept."
        )
        record_classification_review(
            connection, rows[1]["id"], action="defer", reviewer="human@example.test", reason="Need more context."
        )
        connection.commit()
        statuses = [
            connection.execute("SELECT review_status FROM ad_tag WHERE id = ?", (row["id"],)).fetchone()[
                "review_status"
            ]
            for row in rows
        ]
        self.assertEqual(statuses, ["rejected", "pending_review"])
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) AS n FROM ad_tag_event WHERE event_type = 'rejected'"
            ).fetchone()["n"],
            1,
        )
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) AS n FROM ad_tag_event WHERE event_type = 'deferred'"
            ).fetchone()["n"],
            1,
        )

    def test_mapping_decision_and_apply(self) -> None:
        connection = self._copy_connection()
        decision = record_mapping_decision(
            connection,
            source_dimension="legacy_preclasificacion",
            source_tag_key="CATALOGO_DINAMICO",
            target_dimension="concepto",
            target_tag_key="C1_OFERTA",
            reviewer="human@example.test",
            reason="Human confirmed the mapping.",
        )
        connection.commit()
        row = connection.execute(
            "SELECT mapping_status, reviewed_by FROM taxonomy_mapping WHERE id = ?",
            (decision["mapping_id"],),
        ).fetchone()
        self.assertEqual(row["mapping_status"], "mapped")
        self.assertEqual(row["reviewed_by"], "human@example.test")
        classify_legacy(connection, root=ROOT)
        connection.commit()
        self.assertGreater(
            connection.execute(
                """
                SELECT COUNT(*) AS n FROM ad_tag t
                JOIN tag_definition d ON d.id = t.tag_definition_id
                WHERE t.method = 'legacy_mapping_v1' AND d.tag_key = 'C1_OFERTA'
                """
            ).fetchone()["n"],
            0,
        )

    def test_explorer_filters_and_detail(self) -> None:
        rows = search_creatives(self.connection, market="GT", language="es", limit=10)
        self.assertTrue(rows)
        self.assertTrue(all(row["market"] == "GT" for row in rows))
        self.assertTrue(all(row["language"] == "es" for row in rows))
        concept_rows = search_creatives(
            self.connection, tag_filters=[("concepto", "C2_BENEFICIOS")], limit=10
        )
        self.assertTrue(concept_rows)
        self.assertTrue(any(tag["tag_key"] == "C2_BENEFICIOS" for tag in concept_rows[0]["tags"]))
        unclassified = search_creatives(self.connection, unclassified=True, limit=1000)
        self.assertTrue(unclassified)
        self.assertTrue(all(not any(tag["dimension"] == "concepto" for tag in row["tags"]) for row in unclassified))
        low = search_creatives(self.connection, low_evidence=True, limit=1000)
        self.assertTrue(low)
        detail = creative_detail(self.connection, rows[0]["id"])
        self.assertEqual(detail["creative"]["id"], rows[0]["id"])
        self.assertTrue(detail["assets"])
        self.assertTrue(detail["copies"])
        self.assertTrue(detail["tags"])

    def test_export_has_provenance_and_cutoff(self) -> None:
        output = Path(tempfile.mkdtemp(dir=self.temp.name)) / "classifications.csv"
        result = export_classifications(self.connection, output, cutoff="2099-12-31")
        self.assertEqual(result["rows"], 199)
        with output.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 199)
        self.assertIn("assignment_id", rows[0])
        self.assertIn("evidence_json", rows[0])
        self.assertIn("taxonomy_version", rows[0])
        self.assertIn("reviewed_by", rows[0])
        empty = export_classifications(
            self.connection,
            Path(tempfile.mkdtemp(dir=self.temp.name)) / "past.csv",
            cutoff="2000-01-01",
        )
        self.assertEqual(empty["rows"], 0)

    def test_enrichment_contract_protects_approved_and_tracks_cost(self) -> None:
        connection = self._copy_connection()
        approved = connection.execute(
            """
            SELECT t.id, t.ad_creative_id, d.dimension, d.tag_key
            FROM ad_tag t JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.review_status = 'reviewed' AND d.dimension = 'concepto'
            ORDER BY t.id LIMIT 1
            """
        ).fetchone()
        payload = {
            "contract_version": ENRICHMENT_CONTRACT_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "ad_creative_id": approved["ad_creative_id"],
            "model": {"provider": "test", "model_version": "v1", "prompt_version": "p1"},
            "outputs": [
                {
                    "dimension": approved["dimension"],
                    "tag_key": approved["tag_key"],
                    "confidence": 0.91,
                    "confidence_basis": "model score",
                    "evidence": {"text": "visible"},
                    "rationale": "Same concept already reviewed.",
                },
                {
                    "dimension": "formato",
                    "tag_key": "editorial",
                    "confidence": 0.72,
                    "confidence_basis": "model score",
                    "evidence": {"text": "layout"},
                    "rationale": "Editorial layout.",
                },
            ],
            "claims": [{"text": "Test claim", "claim_type": "health"}],
            "cost": {"currency": "USD", "amount": 0.04, "unit": "request"},
        }
        result = ingest_enrichment(connection, payload)
        connection.commit()
        self.assertEqual(result["assignments_skipped_protected"], 1)
        self.assertEqual(result["assignments_inserted"], 1)
        self.assertEqual(result["claims_pending_human_review"], 1)
        run = connection.execute(
            "SELECT cost_json, counts_json, contract_version FROM classification_run WHERE id = ?",
            (result["run_id"],),
        ).fetchone()
        self.assertEqual(json.loads(run["cost_json"])["amount"], 0.04)
        self.assertEqual(run["contract_version"], ENRICHMENT_CONTRACT_VERSION)
        self.assertEqual(
            connection.execute("SELECT COUNT(*) AS n FROM claim").fetchone()["n"],
            7,
        )
        suggested = connection.execute(
            """
            SELECT t.confidence, t.confidence_basis, t.review_status, t.model_version, t.prompt_version
            FROM ad_tag t JOIN tag_definition d ON d.id = t.tag_definition_id
            WHERE t.ad_creative_id = ? AND d.dimension = 'formato' AND d.tag_key = 'editorial'
            """,
            (approved["ad_creative_id"],),
        ).fetchone()
        self.assertEqual(suggested["confidence"], 0.72)
        self.assertEqual(suggested["review_status"], "suggested")
        self.assertEqual((suggested["model_version"], suggested["prompt_version"]), ("v1", "p1"))

    def test_enrichment_rejects_unknown_tags_and_claim_approval(self) -> None:
        payload = {
            "contract_version": ENRICHMENT_CONTRACT_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "ad_creative_id": 1,
            "model": {"provider": "test", "model_version": "v1"},
            "outputs": [{"dimension": "concepto", "tag_key": "C6_UNBOXING"}],
        }
        with self.assertRaises(ValueError):
            validate_enrichment_payload(self.connection, payload)
        payload["outputs"] = [{"dimension": "formato", "tag_key": "editorial"}]
        payload["claims"] = [{"text": "Approved claim", "approved": True}]
        with self.assertRaises(ValueError):
            validate_enrichment_payload(self.connection, payload)
        payload["claims"] = []
        payload["outputs"] = [{"dimension": "legacy_preclasificacion", "tag_key": "OFERTA_PRECIO"}]
        with self.assertRaises(ValueError):
            validate_enrichment_payload(self.connection, payload)

    def test_enrichment_schema_hash_is_stable(self) -> None:
        first = enrichment_contract_schema()
        second = enrichment_contract_schema()
        self.assertEqual(first["schema_hash"], second["schema_hash"])
        self.assertEqual(len(first["schema_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
