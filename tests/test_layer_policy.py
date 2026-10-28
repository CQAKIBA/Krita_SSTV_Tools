# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless tests for background placement safeguards."""
import importlib.util
import unittest
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "sstv_toolbox" / "layer_policy.py"
spec = importlib.util.spec_from_file_location("sstv_layer_policy_test", src)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BackgroundPolicyTests(unittest.TestCase):
    def test_empty_canvas_adds_at_bottom(self):
        self.assertEqual(module.choose_background_placement([]), ("bottom", "empty"))

    def test_blank_base_inserts_second_even_with_overlays(self):
        self.assertEqual(module.choose_background_placement([
            {"type": "paintlayer", "blank": True, "nested": False},
            {"type": "paintlayer", "blank": False, "nested": False},
        ]), ("above_bottom", "blank"))

    def test_modified_base_requests_confirmation(self):
        self.assertEqual(module.choose_background_placement([
            {"type": "paintlayer", "blank": False, "nested": False},
        ]), ("ask", "content_or_unknown"))

    def test_unknown_pixels_requests_confirmation(self):
        self.assertEqual(module.choose_background_placement([
            {"type": "paintlayer", "blank": None, "nested": False},
        ]), ("ask", "content_or_unknown"))

    def test_complex_stack_requests_confirmation(self):
        self.assertEqual(module.choose_background_placement([
            {"type": "grouplayer", "blank": None, "nested": True},
            {"type": "paintlayer", "blank": False, "nested": False},
        ]), ("ask", "complex"))

    def test_blank_exact_white_opaque_and_transparent(self):
        self.assertTrue(module.is_blank_bgra(b"\xff" * 16, 2, 2))
        self.assertTrue(module.is_blank_bgra(b"\x02\x01\x03\x00" * 4, 2, 2))
        self.assertTrue(module.is_blank_bgra(b"\x00" * 16, 2, 2))

    def test_white_and_transparent_mixed_are_blank(self):
        pixels = b"\xff\xff\xff\xff" + b"\x15\x14\x13\x00"
        self.assertTrue(module.is_blank_bgra(pixels, 2, 1))

    def test_semialpha_is_not_blank(self):
        self.assertFalse(module.is_blank_bgra(b"\xff\xff\xff\x80", 1, 1))

    def test_non_blank_pixels_or_bad_size(self):
        self.assertFalse(module.is_blank_bgra(b"\xff" * 12 + b"\x00\x00\xff\xff", 2, 2))
        self.assertFalse(module.is_blank_bgra(b"\xff" * 12, 2, 2))


if __name__ == "__main__":
    unittest.main()
