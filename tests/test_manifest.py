from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ads_intel.manifest import build_manifest, freeze

ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    def test_manifest_counts_and_dimensions(self) -> None:
        manifest = build_manifest(ROOT, include_images=True)
        self.assertEqual(manifest["schema"], "legacy-manifest-v1")
        self.assertEqual(manifest["counts"]["ads_unique"], 597)
        self.assertEqual(manifest["counts"]["images"], 597)
        self.assertEqual(manifest["counts"]["images_with_dimensions"], 597)
        self.assertEqual(manifest["counts"]["pages_unique"], 89)
        self.assertTrue(all(item["width"] and item["height"] for item in manifest["images"]))
        paths = {item["path"] for item in manifest["files"]}
        self.assertIn("_ADS.csv", paths)
        self.assertIn("_BANCO.csv", paths)
        self.assertIn("_CATALOGO_CONCEPTOS.md", paths)

    def test_freeze_creates_manifest_and_zip_without_images(self) -> None:
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
            with zipfile.ZipFile(backup_path) as archive:
                names = set(archive.namelist())
            self.assertIn("legacy_manifest.json", names)
            self.assertIn("_ADS.csv", names)
            self.assertFalse(any(name.startswith("_IMG/") for name in names))


if __name__ == "__main__":
    unittest.main()
