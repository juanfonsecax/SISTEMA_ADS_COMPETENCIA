from __future__ import annotations

import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from ads_intel.inventory import (
    build_code_inventory,
    build_data_inventory,
    build_recovery_manifest,
    create_recovery_backup,
    restore_recovery_backup,
)


class InventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        files = {
            "ads_intel/__init__.py": "",
            "ads_intel/inventory.py": "x = 1\n",
            "tests/test_inventory.py": "x = 1\n",
            "scripts/full_snapshot.py": "x = 1\n",
            "odd/tasks/task.md": "# task\n",
            "README.md": "# readme\n",
            "requirements.txt": "Pillow>=11\n",
            ".gitignore": "data/\n",
            "_ADS.csv": "ad_archive_id\n1\n",
            "_CATALOGO_CONCEPTOS.md": "# catalog\n",
            "_IMG/a.jpg": "image\n",
            "_BANCO_CREATIVOS/_INDICE.csv": "archivo\n",
            "_BLUEPRINTS/_LEEME.md": "# blueprint\n",
            "ANALISIS/notes.md": "# research\n",
            "bajar.py": "print('legacy')\n",
            "_GALERIA.html": "<html></html>\n",
            "data/thumb.jpg": "thumb\n",
            "data/backups/old.zip": "old\n",
            ".env": "SECRET=1\n",
            "venv/lib.py": "x = 1\n",
            "__pycache__/x.pyc": "cache\n",
            "data/ads_intel.db-wal": "wal\n",
        }
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        db_path = self.root / "data" / "ads_intel.db"
        connection = sqlite3.connect(db_path)
        try:
            connection.execute("CREATE TABLE marker (id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute("INSERT INTO marker (value) VALUES ('ok')")
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_code_inventory_covers_active_code_only(self) -> None:
        inventory = build_code_inventory(self.root)
        paths = {item["path"] for item in inventory["files"]}
        self.assertIn("ads_intel/inventory.py", paths)
        self.assertIn("tests/test_inventory.py", paths)
        self.assertIn("scripts/full_snapshot.py", paths)
        self.assertIn("requirements.txt", paths)
        self.assertNotIn("bajar.py", paths)
        self.assertNotIn("_IMG/a.jpg", paths)
        self.assertNotIn("_ADS.csv", paths)
        self.assertNotIn(".env", paths)
        self.assertNotIn("venv/lib.py", paths)

    def test_data_inventory_covers_operational_data_and_excludes_backups(self) -> None:
        inventory = build_data_inventory(self.root)
        paths = {item["path"] for item in inventory["files"]}
        self.assertIn("_IMG/a.jpg", paths)
        self.assertIn("_ADS.csv", paths)
        self.assertIn("ANALISIS/notes.md", paths)
        self.assertIn("data/thumb.jpg", paths)
        self.assertNotIn("data/backups/old.zip", paths)
        self.assertNotIn("data/ads_intel.db", paths)
        self.assertNotIn(".env", paths)
        self.assertIsNotNone(inventory["database_source"])
        self.assertEqual(inventory["database_source"]["path"], "data/ads_intel.db")

    def test_recovery_manifest_includes_legacy_evidence_and_excludes_secrets(self) -> None:
        manifest = build_recovery_manifest(self.root)
        paths = {item["path"] for item in manifest["files"]}
        self.assertIn("ads_intel/inventory.py", paths)
        self.assertIn("_IMG/a.jpg", paths)
        self.assertIn("bajar.py", paths)
        self.assertIn("_GALERIA.html", paths)
        self.assertNotIn(".env", paths)
        self.assertNotIn("venv/lib.py", paths)
        self.assertNotIn("__pycache__/x.pyc", paths)
        self.assertNotIn("data/backups/old.zip", paths)
        self.assertNotIn("data/ads_intel.db", paths)

    def test_recovery_backup_round_trip_verifies_hashes_and_database(self) -> None:
        report = create_recovery_backup(
            self.root,
            self.root / "data" / "backups",
            manifest_dir=self.root / "data" / "manifests",
            db_path=self.root / "data" / "ads_intel.db",
        )
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["mismatch"], [])
        self.assertEqual(report["extra"], [])
        self.assertEqual(report["integrity"], "ok")
        self.assertEqual(report["foreign_keys"], [])
        self.assertEqual(report["counts"]["restored_tables"]["marker"], 1)
        archive = self.root / report["archive"]
        with zipfile.ZipFile(archive) as handle:
            names = set(handle.namelist())
        self.assertIn("ads_intel/inventory.py", names)
        self.assertIn("data/ads_intel.db", names)
        self.assertIn("_IMG/a.jpg", names)
        self.assertIn("bajar.py", names)
        restored = self.root / "restored"
        result = restore_recovery_backup(archive, restored)
        self.assertIn("ads_intel/inventory.py", result["files"])
        connection = sqlite3.connect(restored / "data" / "ads_intel.db")
        try:
            self.assertEqual(connection.execute("SELECT value FROM marker").fetchone()[0], "ok")
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
