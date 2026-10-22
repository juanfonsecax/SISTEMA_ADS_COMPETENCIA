from __future__ import annotations

import unittest
from pathlib import Path

from ads_intel.jpeg import is_jpeg, jpeg_dimensions

ROOT = Path(__file__).resolve().parents[1]


class JpegParserTest(unittest.TestCase):
    def test_real_image_dimensions(self) -> None:
        path = next((ROOT / "_IMG").rglob("*.jpg"))
        data = path.read_bytes()
        self.assertTrue(is_jpeg(data))
        dimensions = jpeg_dimensions(data)
        self.assertIsNotNone(dimensions)
        width, height = dimensions
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_invalid_data(self) -> None:
        self.assertFalse(is_jpeg(b"not a jpeg"))
        self.assertIsNone(jpeg_dimensions(b"not a jpeg"))


if __name__ == "__main__":
    unittest.main()
