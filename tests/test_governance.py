from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ads_intel.db import MIGRATIONS_DIR, apply_migrations, connect
from ads_intel.governance import (
    ASSET_RIGHTS_STATUSES,
    CLAIM_REVIEW_STATUSES,
    REVIEW_EVENT_STATUSES,
    REVIEW_STATUSES,
    ApprovalError,
    assert_exportable,
    record_asset_rights_review,
    record_claim_review,
    record_source_review,
)
from ads_intel.review import record_review_decision, seed_review_queue
from ads_intel.util import utc_now

ROOT = Path(__file__).resolve().parents[1]


class GovernanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "ads_intel.db"
        self.connection = connect(self.db_path)
        apply_migrations(self.connection)
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO source (name, source_type, permission_basis, active, created_at)
            VALUES ('source', 'manual', 'pending_review', 0, ?)
            """,
            (now,),
        )
        self.source_id = int(self.connection.execute("SELECT id FROM source").fetchone()["id"])
        self.connection.execute(
            """
            INSERT INTO asset
                (asset_type, storage_key, sha256, rights_status, created_at, updated_at)
            VALUES ('image', 'image.jpg', 'a' * 64, 'unknown', ?, ?)
            """,
            (now, now),
        )
        self.asset_id = int(self.connection.execute("SELECT id FROM asset").fetchone()["id"])
        self.connection.execute(
            """
            INSERT INTO product (name, created_at, updated_at)
            VALUES ('Tinnidrop', ?, ?)
            """,
            (now, now),
        )
        self.product_id = int(self.connection.execute("SELECT id FROM product").fetchone()["id"])
        self.connection.execute(
            """
            INSERT INTO claim
                (product_id, claim_text, claim_type, evidence_refs, status, source_file, created_at)
            VALUES (?, 'HEARING PROTECTION', 'packaging_label', '["operator-provided"]',
                    'evidence_needed', 'ficha.json', ?)
            """,
            (self.product_id, now),
        )
        self.claim_id = int(self.connection.execute("SELECT id FROM claim").fetchone()["id"])
        self.connection.commit()

    def tearDown(self) -> None:
        self.connection.close()
        self.temp.cleanup()

    def test_unknown_rights_and_pending_source_are_not_exportable(self) -> None:
        with self.assertRaises(ApprovalError):
            assert_exportable(self.connection, "source", self.source_id)
        with self.assertRaises(ApprovalError):
            assert_exportable(self.connection, "asset", self.asset_id)
        with self.assertRaises(ApprovalError):
            assert_exportable(self.connection, "claim", self.claim_id)

    def test_source_approval_requires_evidence_and_permission_basis(self) -> None:
        with self.assertRaises(ApprovalError):
            record_source_review(
                self.connection,
                self.source_id,
                status="approved",
                permission_basis="written_authorization",
                reviewer="operator",
                reviewed_at="2026-10-22T00:00:00Z",
            )
        record_source_review(
            self.connection,
            self.source_id,
            status="approved",
            permission_basis="written_authorization",
            evidence_ref="evidence/source-authorization.pdf",
            reviewer="operator",
            reviewed_at="2026-10-22T00:00:00Z",
        )
        assert_exportable(self.connection, "source", self.source_id)
        row = self.connection.execute("SELECT review_status, permission_basis FROM source").fetchone()
        self.assertEqual((row["review_status"], row["permission_basis"]), ("approved", "written_authorization"))

    def test_asset_rights_approval_requires_evidence_and_preserves_unknown(self) -> None:
        with self.assertRaises(ApprovalError):
            record_asset_rights_review(
                self.connection,
                self.asset_id,
                status="approved",
                reviewer="operator",
                reviewed_at="2026-10-22T00:00:00Z",
            )
        self.assertEqual(
            self.connection.execute("SELECT rights_status FROM asset").fetchone()["rights_status"],
            "unknown",
        )
        record_asset_rights_review(
            self.connection,
            self.asset_id,
            status="approved",
            evidence_ref="evidence/asset-license.txt",
            reviewer="operator",
            reviewed_at="2026-10-22T00:00:00Z",
        )
        assert_exportable(self.connection, "asset", self.asset_id)

    def test_claim_approval_requires_new_evidence(self) -> None:
        with self.assertRaises(ApprovalError):
            record_claim_review(
                self.connection,
                self.claim_id,
                status="approved",
                reviewer="operator",
                reviewed_at="2026-10-22T00:00:00Z",
            )
        with self.assertRaises(ApprovalError):
            record_claim_review(
                self.connection,
                self.claim_id,
                status="approved",
                evidence_refs=[],
                reviewer="operator",
                reviewed_at="2026-10-22T00:00:00Z",
            )
        record_claim_review(
            self.connection,
            self.claim_id,
            status="approved",
            evidence_refs=["evidence/claim-review.pdf"],
            reviewer="operator",
            reviewed_at="2026-10-22T00:00:00Z",
        )
        assert_exportable(self.connection, "claim", self.claim_id)
        row = self.connection.execute("SELECT status, approved_by, evidence_refs FROM claim").fetchone()
        self.assertEqual(row["status"], "approved")
        self.assertEqual(row["approved_by"], "operator")
        self.assertIn("evidence/claim-review.pdf", row["evidence_refs"])

    def test_review_decision_is_explicit_and_audited(self) -> None:
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO review_item
                (item_key, category, object_type, object_id, title, description,
                 evidence_json, status, created_at, updated_at)
            VALUES ('test:item', 'test', 'claim', ?, 'title', 'description',
                    '{}', 'pending', ?, ?)
            """,
            (self.claim_id, now, now),
        )
        item_id = int(cursor.lastrowid)
        self.connection.commit()
        record_review_decision(
            self.connection,
            item_id,
            status="resolved",
            decision="Evidence reviewed and accepted",
            reviewer="operator",
            notes="recorded manually",
        )
        item = self.connection.execute("SELECT * FROM review_item WHERE id = ?", (item_id,)).fetchone()
        self.assertEqual(item["status"], "resolved")
        self.assertEqual(item["reviewer"], "operator")
        self.assertIsNotNone(item["reviewed_at"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM review_event WHERE object_type = 'review_item' AND object_id = ?",
                (item_id,),
            ).fetchone()["n"],
            1,
        )
        seed_review_queue(self.connection, ROOT)
        preserved = self.connection.execute("SELECT status, decision FROM review_item WHERE id = ?", (item_id,)).fetchone()
        self.assertEqual((preserved["status"], preserved["decision"]), ("resolved", "Evidence reviewed and accepted"))

    def test_review_event_check_accepts_declared_statuses_and_rejects_unknown(self) -> None:
        now = utc_now()
        for status in sorted(REVIEW_EVENT_STATUSES):
            self.connection.execute(
                """
                INSERT INTO review_event (object_type, object_id, review_type, status, created_at)
                VALUES ('test', 1, 'contract', ?, ?)
                """,
                (status, now),
            )
        self.connection.commit()
        stored = {
            row["status"]
            for row in self.connection.execute("SELECT DISTINCT status FROM review_event")
        }
        self.assertEqual(stored, REVIEW_EVENT_STATUSES)
        before = self.connection.execute("SELECT COUNT(*) AS n FROM review_event").fetchone()["n"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO review_event (object_type, object_id, review_type, status, created_at)
                VALUES ('test', 1, 'contract', 'not_a_status', ?)
                """,
                (now,),
            )
        self.connection.rollback()
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) AS n FROM review_event").fetchone()["n"],
            before,
        )

    def test_public_review_paths_record_every_object_status(self) -> None:
        reviewed_at = "2026-10-22T00:00:00Z"
        for status in sorted(REVIEW_STATUSES):
            reviewer = "operator" if status in {"approved", "restricted", "rejected"} else None
            permission_basis = "written_authorization" if status == "approved" else None
            evidence_ref = "evidence/source.pdf" if status == "approved" else None
            record_source_review(
                self.connection,
                self.source_id,
                status=status,
                permission_basis=permission_basis,
                evidence_ref=evidence_ref,
                reviewer=reviewer,
                reviewed_at=reviewed_at if status == "approved" else None,
            )
        for status in sorted(ASSET_RIGHTS_STATUSES):
            reviewer = "operator" if status in {"approved", "restricted", "rejected"} else None
            record_asset_rights_review(
                self.connection,
                self.asset_id,
                status=status,
                evidence_ref="evidence/asset.txt" if status == "approved" else None,
                reviewer=reviewer,
                reviewed_at=reviewed_at if status == "approved" else None,
            )
        for status in sorted(CLAIM_REVIEW_STATUSES):
            reviewer = "operator" if status in {"approved", "restricted", "rejected"} else None
            record_claim_review(
                self.connection,
                self.claim_id,
                status=status,
                evidence_refs=["evidence/claim.pdf"] if status == "approved" else None,
                reviewer=reviewer,
                reviewed_at=reviewed_at if status == "approved" else None,
            )
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO review_item
                (item_key, category, object_type, object_id, title, description,
                 evidence_json, status, created_at, updated_at)
            VALUES ('test:all-statuses', 'test', 'claim', ?, 'title', 'description',
                    '{}', 'pending', ?, ?)
            """,
            (self.claim_id, now, now),
        )
        item_id = int(cursor.lastrowid)
        self.connection.commit()
        for status in ("in_review", "needs_evidence", "resolved", "rejected"):
            record_review_decision(
                self.connection,
                item_id,
                status=status,
                decision=f"decision for {status}",
                reviewer="operator",
            )
        stored = {
            row["status"]
            for row in self.connection.execute("SELECT DISTINCT status FROM review_event")
        }
        self.assertTrue(REVIEW_EVENT_STATUSES.issubset(stored), REVIEW_EVENT_STATUSES - stored)

    def test_invalid_review_status_does_not_modify_state(self) -> None:
        before_asset = tuple(
            self.connection.execute(
                "SELECT rights_status, rights_evidence_ref, rights_reviewer, rights_reviewed_at FROM asset"
            ).fetchone()
        )
        before_events = self.connection.execute("SELECT COUNT(*) AS n FROM review_event").fetchone()["n"]
        with self.assertRaises(ValueError):
            record_asset_rights_review(self.connection, self.asset_id, status="not_a_status")
        with self.assertRaises(ValueError):
            record_source_review(self.connection, self.source_id, status="unknown")
        with self.assertRaises(ValueError):
            record_claim_review(self.connection, self.claim_id, status="unknown")
        self.assertEqual(
            tuple(
                self.connection.execute(
                    "SELECT rights_status, rights_evidence_ref, rights_reviewer, rights_reviewed_at FROM asset"
                ).fetchone()
            ),
            before_asset,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) AS n FROM review_event").fetchone()["n"],
            before_events,
        )

    def test_review_event_upgrade_preserves_existing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old_migrations = Path(directory)
            for name in ("0001_init.sql", "0002_advertiser_ranking.sql", "0002_asset_intelligence.sql"):
                shutil.copy2(MIGRATIONS_DIR / name, old_migrations / name)
            db_path = Path(directory) / "upgrade.db"
            connection = connect(db_path)
            try:
                apply_migrations(connection, old_migrations)
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO review_event
                        (object_type, object_id, review_type, status, notes, payload_json, created_at)
                    VALUES ('asset', 7, 'rights', 'approved', 'kept', '{"a":1}', ?)
                    """,
                    (now,),
                )
                connection.execute(
                    """
                    INSERT INTO review_event
                        (object_type, object_id, review_type, status, created_at)
                    VALUES ('review_item', 3, 'human_decision', 'resolved', ?)
                    """,
                    (now,),
                )
                connection.commit()
                before = [
                    tuple(row)
                    for row in connection.execute(
                        "SELECT id, object_type, object_id, status, notes, payload_json FROM review_event ORDER BY id"
                    )
                ]
                apply_migrations(connection, MIGRATIONS_DIR)
                after = [
                    tuple(row)
                    for row in connection.execute(
                        "SELECT id, object_type, object_id, status, notes, payload_json FROM review_event ORDER BY id"
                    )
                ]
                self.assertEqual(before, after)
                connection.execute(
                    """
                    INSERT INTO review_event (object_type, object_id, review_type, status, created_at)
                    VALUES ('asset', 8, 'rights', 'unknown', ?)
                    """,
                    (now,),
                )
                connection.execute(
                    """
                    INSERT INTO review_event (object_type, object_id, review_type, status, created_at)
                    VALUES ('claim', 1, 'claim', 'evidence_needed', ?)
                    """,
                    (now,),
                )
                connection.commit()
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
