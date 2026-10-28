# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
# SPDX-License-Identifier: GPL-3.0-or-later
"""SSTV image-placement math, independent of Krita/PyQt."""
import unittest
import importlib.util
from pathlib import Path
src = Path(__file__).resolve().parents[1] / "sstv_toolbox" / "geometry.py"
spec = importlib.util.spec_from_file_location("sstv_test_geometry", src)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)
fit_dimensions = geometry.fit_dimensions
cover_source_rect = geometry.cover_source_rect


class GeometryTests(unittest.TestCase):
    def test_full_fit_same_aspect(self):
        self.assertEqual(fit_dimensions(4000, 3000, 640, 480), (640, 480))

    def test_full_fit_landscape_16_9(self):
        self.assertEqual(fit_dimensions(1920, 1080, 640, 480), (640, 360))

    def test_full_fit_portrait(self):
        self.assertEqual(fit_dimensions(1080, 1920, 640, 480), (270, 480))

    def test_30_percent_max_fit(self):
        self.assertEqual(fit_dimensions(1920, 1080, 640, 480, 30), (192, 108))
        self.assertEqual(fit_dimensions(1080, 1920, 640, 480, 30), (81, 144))

    def test_640x512(self):
        self.assertEqual(fit_dimensions(640, 480, 640, 512, 100), (640, 480))
        self.assertEqual(fit_dimensions(640, 480, 640, 512, 30), (192, 144))

    def test_cover_source_crop_landscape(self):
        x, y, w, h = cover_source_rect(1920, 1080, 640, 480)
        self.assertAlmostEqual(w / h, 640 / 480)
        self.assertAlmostEqual(y, 0)
        self.assertGreater(x, 0)

    def test_cover_source_crop_portrait(self):
        x, y, w, h = cover_source_rect(1080, 1920, 640, 480)
        self.assertAlmostEqual(w / h, 640 / 480)
        self.assertAlmostEqual(x, 0)
        self.assertGreater(y, 0)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            fit_dimensions(0, 100, 640, 480)
        with self.assertRaises(ValueError):
            fit_dimensions(100, 100, 640, 480, 0)


if __name__ == "__main__":
    unittest.main()
