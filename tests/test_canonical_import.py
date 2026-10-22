from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ads_intel.config import LEGACY_INPUT_FILES, LEGACY_JSON_GLOBS
from ads_intel.db import connect
from ads_intel.importers import import_all
from ads_intel.reconcile import build_report
from ads_intel.util import iter_glob_files, sha256_file

ROOT = Path(__file__).resolve().parents[1]


class CanonicalImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp.name) / "ads_intel.db"
        cls.legacy_paths = iter_glob_files(ROOT, LEGACY_INPUT_FILES + LEGACY_JSON_GLOBS)
        cls.legacy_before = {path: sha256_file(path) for path in cls.legacy_paths}
        cls.first_counts = import_all(ROOT, cls.db_path)
        cls.second_counts = import_all(ROOT, cls.db_path)
        cls.legacy_after = {path: sha256_file(path) for path in cls.legacy_paths}
        cls.connection = connect(cls.db_path)
        cls.report = build_report(cls.connection)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()
        cls.temp.cleanup()

    def test_reconciliation_is_green(self) -> None:
        failures = [check for check in self.report["checks"] if not check["ok"]]
        self.assertTrue(self.report["ok"], failures)

    def test_reimport_is_idempotent_for_domain_tables(self) -> None:
        ignored = {"job_run", "audit_event"}
        first = {key: value for key, value in self.first_counts.items() if key not in ignored}
        second = {key: value for key, value in self.second_counts.items() if key not in ignored}
        self.assertEqual(first, second)
        self.assertEqual(self.report["counts"]["ad_creative"], 597)
        self.assertEqual(self.report["counts"]["ad_observation"], 597)

    def test_advertiser_aliases_resolve_to_page_ids(self) -> None:
        counts = self.report["counts"]
        self.assertEqual(counts["advertiser"], 89)
        self.assertEqual(counts["advertiser_alias"], 10)
        self.assertEqual(counts["names_total"], 95)
        advertiser = self.connection.execute(
            "SELECT id, name FROM advertiser WHERE external_page_id = '1148274688362148'"
        ).fetchone()
        self.assertIsNotNone(advertiser)
        names = {advertiser["name"]}
        names.update(
            row["name"]
            for row in self.connection.execute(
                "SELECT name FROM advertiser_alias WHERE advertiser_id = ?", (advertiser["id"],)
            )
        )
        self.assertIn("Flor Expres GT", names)
        self.assertIn("Flor Exprs GT", names)

    def test_ranking_snapshot_is_imported(self) -> None:
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM advertiser WHERE reported_real_active_ads IS NOT NULL"
            ).fetchone()["n"],
            60,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM source_payload WHERE legacy_file = '_RANKING_CUENTAS.csv'"
            ).fetchone()["n"],
            60,
        )

    def test_observations_keep_both_batches(self) -> None:
        rows = self.connection.execute(
            "SELECT observed_on, COUNT(*) AS n FROM ad_observation GROUP BY observed_on ORDER BY observed_on"
        ).fetchall()
        self.assertEqual([(row["observed_on"], row["n"]) for row in rows], [("2026-08-17", 225), ("2026-08-18", 372)])

    def test_assets_and_copies(self) -> None:
        counts = self.report["counts"]
        self.assertEqual(counts["asset"], 597)
        self.assertEqual(counts["ads_with_asset"], 597)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM asset WHERE width IS NULL OR height IS NULL"
            ).fetchone()["n"],
            0,
        )
        self.assertEqual(counts["ad_copy"], 629)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM ad_copy WHERE source_file = '_COPIES.csv'"
            ).fetchone()["n"],
            32,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM ad_copy WHERE is_canonical = 1"
            ).fetchone()["n"],
            597,
        )

    def test_orphan_copies_are_preserved(self) -> None:
        issues = self.connection.execute(
            "SELECT external_id FROM import_issue WHERE issue_type = 'orphan_copy' ORDER BY external_id"
        ).fetchall()
        self.assertEqual(
            [row["external_id"] for row in issues],
            ["1443039764315605", "2521595411673768", "3009333172743578"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM source_payload WHERE legacy_file = '_COPIES.csv'"
            ).fetchone()["n"],
            35,
        )

    def test_tags_and_references(self) -> None:
        counts = self.report["counts"]
        self.assertEqual(counts["tags_final_concept"], 111)
        self.assertEqual(counts["tags_raw_concept"], 111)
        self.assertEqual(counts["tags_preclassification"], 597)
        self.assertEqual(counts["tags_gallery"], 111)
        self.assertEqual(counts["tags_favorite"], 111)
        self.assertEqual(counts["reference_banco"], 48)
        self.assertEqual(counts["reference_ficha"], 111)
        self.assertEqual(counts["reference_canonico"], 22)
        self.assertEqual(counts["reference_blueprint"], 4)
        self.assertEqual(counts["reference_blueprint_t01"], 4)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'banco_creativo' AND ad_creative_id IS NULL"
            ).fetchone()["n"],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM reference_document WHERE kind = 'ficha' AND ad_creative_id IS NULL"
            ).fetchone()["n"],
            0,
        )

    def test_element_matrix_links_to_selection(self) -> None:
        self.assertEqual(self.report["counts"]["legacy_element_observation"], 36)
        self.assertEqual(self.report["counts"]["legacy_score_snapshot"], 36)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM legacy_element_observation WHERE ad_creative_id IS NULL"
            ).fetchone()["n"],
            0,
        )
        bounds = self.connection.execute(
            "SELECT MIN(selection_n) AS low, MAX(selection_n) AS high FROM legacy_element_observation"
        ).fetchone()
        self.assertEqual((bounds["low"], bounds["high"]), (1, 36))

    def test_product_claims_are_not_approved(self) -> None:
        self.assertEqual(self.report["counts"]["product"], 1)
        self.assertEqual(self.report["counts"]["claim"], 7)
        self.assertEqual(self.report["counts"]["claims_approved"], 0)
        statuses = {
            row["status"]
            for row in self.connection.execute("SELECT status FROM claim")
        }
        self.assertEqual(statuses, {"evidence_needed"})
        cost = self.connection.execute(
            "SELECT value, currency FROM product_fact WHERE fact_key = 'supplier_cost'"
        ).fetchone()
        self.assertIsNotNone(cost)
        self.assertEqual((cost["value"], cost["currency"]), ("41", "Q"))

    def test_legacy_files_are_byte_identical(self) -> None:
        self.assertEqual(self.legacy_before, self.legacy_after)

    def test_issues_are_visible(self) -> None:
        self.assertEqual(self.report["counts"]["import_issue"], 10)
        self.assertEqual(len(self.report["issues"]), 10)


if __name__ == "__main__":
    unittest.main()
