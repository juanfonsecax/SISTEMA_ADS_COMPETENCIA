from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ads_intel.manifest import build_manifest, freeze
from ads_intel.util import git_tracked_files, git_untracked_files

ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    def test_manifest_counts_and_dimensions(self) -> None:
        manifest = build_manifest(ROOT, include_images=True)
        self.assertEqual(manifest["schema"], "legacy-manifest-v2")
        self.assertEqual(manifest["counts"]["ads_unique"], 597)
        self.assertEqual(manifest["counts"]["images"], 597)
        self.assertEqual(manifest["counts"]["reference_assets"], 48)
        tracked_total = sum(1 for path in git_tracked_files(ROOT) if path.exists())
        untracked_total = len(git_untracked_files(ROOT))
        self.assertEqual(manifest["counts"]["tracked_total"], tracked_total)
        self.assertEqual(manifest["counts"]["untracked"], untracked_total)
        self.assertEqual(manifest["counts"]["total"], tracked_total + untracked_total)
        self.assertEqual(manifest["counts"]["images_with_dimensions"], 597)
        self.assertEqual(manifest["counts"]["pages_unique"], 89)
        self.assertIsNotNone(manifest["repo_head"])
        self.assertEqual(len(manifest["repo_head"]), 40)
        self.assertTrue(all(item["width"] and item["height"] for item in manifest["images"]))
        all_items = manifest["files"] + manifest["images"] + manifest["reference_assets"]
        paths = [item["path"] for item in all_items]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), tracked_total + untracked_total)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in all_items))
        file_paths = {item["path"] for item in manifest["files"]}
        self.assertIn("_ADS.csv", file_paths)
        self.assertIn("_BANCO.csv", file_paths)
        self.assertIn("_CATALOGO_CONCEPTOS.md", file_paths)
        self.assertIn("_BLUEPRINTS/_datos/tanda01.py", file_paths)
        self.assertIn("ANALISIS/CATALOGO_CONCEPTOS_EVIDENCIA.md", file_paths)
        self.assertIn("_BANCO_CREATIVOS/_INDICE.csv", file_paths)
        self.assertIn("ads_intel/governance.py", file_paths)
        self.assertIn("ads_intel/inventory.py", file_paths)

    def test_freeze_creates_full_manifest_and_zip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            manifest_path = base / "manifest.json"
            backup_dir = base / "backups"
            result = freeze(ROOT, manifest_path, backup_dir, include_images=True, do_backup=True)
            self.assertTrue(manifest_path.exists())
            backup_path = Path(result["backup_path"])
            self.assertTrue(backup_path.exists())
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["counts"]["images"], 597)
            self.assertEqual(
                payload["counts"]["tracked_total"],
                sum(1 for path in git_tracked_files(ROOT) if path.exists()),
            )
            with zipfile.ZipFile(backup_path) as archive:
                names = set(archive.namelist())
            self.assertIn("legacy_manifest.json", names)
            self.assertIn("_ADS.csv", names)
            self.assertIn("_BLUEPRINTS/_datos/tanda01.py", names)
            self.assertIn("_BANCO_CREATIVOS/_INDICE.csv", names)
            self.assertIn("ads_intel/governance.py", names)
            self.assertTrue(any(name.startswith("_IMG/") for name in names))
            self.assertTrue(any(name.startswith("_BANCO_CREATIVOS/") and name.endswith(".jpg") for name in names))
            self.assertFalse(any(name.startswith("data/") for name in names))


if __name__ == "__main__":
    unittest.main()
