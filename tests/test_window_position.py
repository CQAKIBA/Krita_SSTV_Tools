# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
# SPDX-License-Identifier: GPL-3.0-or-later
"""No-Qt tests for editing-history floating dock placement."""
import importlib.util
import unittest
from pathlib import Path

file = Path(__file__).resolve().parents[1] / "sstv_toolbox" / "window_position.py"
spec = importlib.util.spec_from_file_location("sstv_window_position_test", file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class WindowPositionTests(unittest.TestCase):
    def test_krita_30_percent_anchor(self):
        self.assertEqual(module.floating_window_position(500, 300, 380, 480,
                                                          0, 0, 1920, 1080), (500, 300))

    def test_clamp_to_visible_screen(self):
        self.assertEqual(module.floating_window_position(2500, 1600, 380, 480,
                                                          1920, 0, 1280, 900), (2500, 420))

    def test_clamp_to_screen_origin(self):
        self.assertEqual(module.floating_window_position(-3000, -40, 380, 480,
                                                          -1920, 0, 1920, 1080), (-1920, 0))
