from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

from ads_intel.db import apply_migrations, connect
from ads_intel.util import sha256_file, sha256_text, utc_now
from ads_intel.visuals import (
    dhash64,
    hamming_distance,
    list_visual_candidates,
    list_visual_scan_runs,
    scan_visual_similarity,
)

ROOT = Path(__file__).resolve().parents[1]


def _draw_base() -> Image.Image:
    image = Image.new("RGB", (160, 160), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 90, 80), fill="black")
    draw.ellipse((70, 80, 140, 150), fill="blue")
    draw.line((10, 150, 150, 10), fill="red", width=8)
    return image


class VisualSimilarityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name) / "repo"
        cls.root.mkdir()
        image_dir = cls.root / "images"
        image_dir.mkdir()
        base = _draw_base()
        base_path = image_dir / "base.jpg"
        base.save(base_path, quality=90)
        minor_path = image_dir / "minor.jpg"
        ImageEnhance.Brightness(base).enhance(0.9).save(minor_path, quality=90)
        crop_path = image_dir / "crop.jpg"
        base.crop((4, 4, 156, 156)).resize((160, 160), Image.Resampling.LANCZOS).save(
            crop_path, quality=90
        )
        solid_white = image_dir / "solid-white.jpg"
        Image.new("RGB", (160, 160), "white").save(solid_white)
        solid_gray = image_dir / "solid-gray.jpg"
        Image.new("RGB", (160, 160), (180, 180, 180)).save(solid_gray)
        duplicate = image_dir / "duplicate.jpg"
        duplicate.write_bytes(base_path.read_bytes())
        cls.duplicate_hash = dhash64(duplicate)[0]

        cls.db_path = Path(cls.temp.name) / "ads_intel.db"
        cls.connection = connect(cls.db_path)
        apply_migrations(cls.connection)
        now = utc_now()
        paths = [base_path, minor_path, crop_path, solid_white, solid_gray]
        cls.asset_ids: dict[str, int] = {}
        for path in paths:
            relative = path.relative_to(cls.root).as_posix()
            cursor = cls.connection.execute(
                """
                INSERT INTO asset
                    (asset_type, storage_key, mime_type, sha256, width, height, bytes,
                     rights_status, created_at, updated_at)
                VALUES ('image', ?, 'image/jpeg', ?, 160, 160, ?, 'unknown', ?, ?)
                """,
                (relative, sha256_file(path), path.stat().st_size, now, now),
            )
            cls.asset_ids[path.stem] = int(cursor.lastrowid)
        cls.connection.execute(
            """
            INSERT INTO asset
                (asset_type, storage_key, mime_type, sha256, width, height, bytes,
                 rights_status, created_at, updated_at)
            VALUES ('image', 'images/missing.jpg', 'image/jpeg', ?, 1, 1, 0, 'unknown', ?, ?)
            """,
            (sha256_text("missing"), now, now),
        )
        cls.missing_asset_id = int(
            cls.connection.execute(
                "SELECT id FROM asset WHERE storage_key = 'images/missing.jpg'"
            ).fetchone()["id"]
        )
        cls.connection.commit()
        cls.before_hashes = {
            path.relative_to(cls.root).as_posix(): sha256_file(path) for path in paths
        }
        cls.thumbnail_root = cls.root / "data" / "thumbs"
        cls.result = scan_visual_similarity(
            cls.connection,
            cls.root,
            threshold=8,
            thumbnail_root=cls.thumbnail_root,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()
        cls.temp.cleanup()

    def _candidate(self, left: int, right: int):
        return self.connection.execute(
            """
            SELECT * FROM visual_similarity_candidate
            WHERE left_asset_id = ? AND right_asset_id = ? AND scan_run_id = ?
            """,
            (min(left, right), max(left, right), self.result["run_id"]),
        ).fetchone()

    def test_scan_processes_canonical_images_and_reports_failure(self) -> None:
        self.assertEqual(self.result["assets"], 6)
        self.assertEqual(self.result["processed"], 5)
        self.assertEqual(self.result["failed"], 1)
        self.assertEqual(self.result["signatures"], 5)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM asset_visual_signature"
            ).fetchone()["n"],
            5,
        )
        self.assertIsNone(
            self.connection.execute(
                "SELECT id FROM asset_visual_signature WHERE asset_id = ?",
                (self.missing_asset_id,),
            ).fetchone()
        )
        item = self.connection.execute(
            "SELECT status FROM review_item WHERE item_key = ?",
            (f"visual:failed:{self.missing_asset_id}",),
        ).fetchone()
        self.assertIsNotNone(item)
        self.assertEqual(item["status"], "pending")

    def test_exact_duplicate_hash_matches(self) -> None:
        base_hash = dhash64(self.root / "images" / "base.jpg")[0]
        self.assertEqual(base_hash, self.duplicate_hash)
        self.assertEqual(hamming_distance(base_hash, self.duplicate_hash), 0)

    def test_minor_variant_and_crop_are_candidates_not_duplicates(self) -> None:
        minor = self._candidate(self.asset_ids["base"], self.asset_ids["minor"])
        crop = self._candidate(self.asset_ids["base"], self.asset_ids["crop"])
        self.assertIsNotNone(minor)
        self.assertIsNotNone(crop)
        self.assertEqual(minor["review_status"], "pending")
        self.assertEqual(crop["review_status"], "pending")
        self.assertLessEqual(crop["distance"], 8)
        evidence = json.loads(minor["evidence_json"])
        self.assertFalse(evidence["duplicate_claim"])
        self.assertFalse(evidence["exact_sha256_match"])

    def test_false_positive_is_kept_pending(self) -> None:
        candidate = self._candidate(self.asset_ids["solid-white"], self.asset_ids["solid-gray"])
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["review_status"], "pending")
        evidence = json.loads(candidate["evidence_json"])
        self.assertEqual(evidence["distance"], 0)
        self.assertFalse(evidence["exact_sha256_match"])
        self.assertFalse(evidence["duplicate_claim"])

    def test_thumbnails_are_written_only_under_data(self) -> None:
        thumbnails = list(self.thumbnail_root.rglob("*.jpg"))
        self.assertEqual(len(thumbnails), 5)
        for path in thumbnails:
            self.assertTrue(path.is_file())
            self.assertTrue(path.relative_to(self.root).as_posix().startswith("data/"))

    def test_original_images_and_rights_are_unchanged(self) -> None:
        after_hashes = {
            path.relative_to(self.root).as_posix(): sha256_file(path)
            for path in [
                self.root / "images" / "base.jpg",
                self.root / "images" / "minor.jpg",
                self.root / "images" / "crop.jpg",
                self.root / "images" / "solid-white.jpg",
                self.root / "images" / "solid-gray.jpg",
            ]
        }
        self.assertEqual(self.before_hashes, after_hashes)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM asset WHERE rights_status = 'unknown'"
            ).fetchone()["n"],
            6,
        )

    def test_scan_is_idempotent_and_keeps_pending_candidates(self) -> None:
        second = scan_visual_similarity(
            self.connection,
            self.root,
            threshold=8,
            thumbnail_root=self.thumbnail_root,
        )
        self.assertEqual(second["signatures"], 5)
        self.assertEqual(second["candidates"], self.result["candidates"])
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM visual_scan_run"
            ).fetchone()["n"],
            2,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM visual_similarity_candidate WHERE review_status != 'pending'"
            ).fetchone()["n"],
            0,
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) AS n FROM visual_similarity_candidate"
            ).fetchone()["n"],
            self.result["candidates"] * 2,
        )
        self.assertEqual(len(list_visual_candidates(self.connection)), self.result["candidates"])
        self.assertEqual(
            len(list_visual_candidates(self.connection, run_id=self.result["run_id"])),
            self.result["candidates"],
        )


class VisualThresholdHistoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        image_dir = self.root / "images"
        image_dir.mkdir()
        base = _draw_base()
        self.base_path = image_dir / "base.jpg"
        self.minor_path = image_dir / "minor.jpg"
        self.solid_path = image_dir / "solid.jpg"
        self.solid_gray_path = image_dir / "solid-gray.jpg"
        base.save(self.base_path, quality=90)
        ImageEnhance.Brightness(base).enhance(0.9).save(self.minor_path, quality=90)
        Image.new("RGB", (160, 160), "white").save(self.solid_path)
        Image.new("RGB", (160, 160), (180, 180, 180)).save(self.solid_gray_path)

        self.connection = connect(Path(self.temp.name) / "ads_intel.db")
        apply_migrations(self.connection)
        now = utc_now()
        self.ids: dict[str, int] = {}
        for path in (self.base_path, self.minor_path, self.solid_path, self.solid_gray_path):
            cursor = self.connection.execute(
                """
                INSERT INTO asset
                    (asset_type, storage_key, mime_type, sha256, width, height, bytes,
                     rights_status, created_at, updated_at)
                VALUES ('image', ?, 'image/jpeg', ?, 160, 160, ?, 'unknown', ?, ?)
                """,
                (
                    path.relative_to(self.root).as_posix(),
                    sha256_file(path),
                    path.stat().st_size,
                    now,
                    now,
                ),
            )
            self.ids[path.stem] = int(cursor.lastrowid)
        self.connection.commit()
        self.thumbs = self.root / "data" / "thumbs"

    def tearDown(self) -> None:
        self.connection.close()
        self.temp.cleanup()

    def test_threshold_change_hides_stale_candidates_from_current_view(self) -> None:
        first = scan_visual_similarity(
            self.connection, self.root, threshold=8, thumbnail_root=self.thumbs
        )
        second = scan_visual_similarity(
            self.connection, self.root, threshold=0, thumbnail_root=self.thumbs
        )
        current = list_visual_candidates(self.connection)
        self.assertTrue(current)
        self.assertTrue(all(row["scan_run_id"] == second["run_id"] for row in current))
        self.assertTrue(all(row["distance"] <= 0 for row in current))
        self.assertEqual(second["candidates"], len(current))
        self.assertFalse(any(
            {row["left_asset_id"], row["right_asset_id"]} == {self.ids["base"], self.ids["minor"]}
            for row in current
        ))
        historical = list_visual_candidates(self.connection, run_id=first["run_id"])
        self.assertTrue(historical)
        self.assertTrue(any(
            {row["left_asset_id"], row["right_asset_id"]} == {self.ids["base"], self.ids["minor"]}
            for row in historical
        ))
        self.assertTrue(all(row["scan_run_id"] == first["run_id"] for row in historical))
        runs = list_visual_scan_runs(self.connection)
        self.assertEqual([row["id"] for row in runs], [second["run_id"], first["run_id"]])
        self.assertEqual(runs[0]["candidate_count"], second["candidates"])
        self.assertEqual(runs[1]["candidate_count"], first["candidates"])

    def test_current_view_uses_latest_run_even_when_threshold_keeps_pairs(self) -> None:
        first = scan_visual_similarity(
            self.connection, self.root, threshold=1, thumbnail_root=self.thumbs
        )
        second = scan_visual_similarity(
            self.connection, self.root, threshold=8, thumbnail_root=self.thumbs
        )
        current = list_visual_candidates(self.connection)
        self.assertTrue(current)
        self.assertTrue(all(row["scan_run_id"] == second["run_id"] for row in current))
        self.assertTrue(all(row["threshold"] == 8 for row in current))
        self.assertGreaterEqual(second["candidates"], first["candidates"])
        self.assertEqual(
            len(list_visual_candidates(self.connection, run_id=first["run_id"])),
            first["candidates"],
        )


if __name__ == "__main__":
    unittest.main()
