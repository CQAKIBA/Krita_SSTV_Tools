# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
import importlib.util
import os
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "sstv_toolbox", "png_export.py")
spec = importlib.util.spec_from_file_location("png_export", SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeInfoObject:
    def __init__(self):
        self.properties = {}

    def setProperty(self, name, value):
        self.properties[name] = value


class FakeDocument:
    def __init__(self, initial=False, should_succeed=True, raise_error=False):
        self.state = initial
        self.events = []
        self.options = None
        self.should_succeed = should_succeed
        self.raise_error = raise_error

    def batchmode(self):
        return self.state

    def setBatchmode(self, value):
        self.events.append(("batchmode", value))
        self.state = value

    def exportImage(self, name, options):
        self.events.append(("export", self.state))
        self.options = options
        if self.raise_error:
            raise RuntimeError("export failed")
        return self.should_succeed


class Tests(unittest.TestCase):
    def test_silent_export_with_fixed_sstv_options(self):
        doc = FakeDocument()
        ok = module.export_png_for_ipp(doc, "test.png", FakeInfoObject)
        self.assertTrue(ok)
        self.assertEqual(doc.events, [("batchmode", True), ("export", True), ("batchmode", False)])
        self.assertEqual(doc.options.properties, {
            "compression": 3, "indexed": False, "interlaced": False,
            "alpha": False, "transparencyFillcolor": [255, 255, 255],
            "forceSRGB": True, "saveSRGBProfile": True,
        })

    def test_existing_batchmode_preserved(self):
        doc = FakeDocument(initial=True)
        self.assertTrue(module.export_png_for_ipp(doc, "test.png", FakeInfoObject))
        self.assertTrue(doc.state)

    def test_restores_batchmode_when_export_rejected(self):
        doc = FakeDocument(should_succeed=False)
        self.assertFalse(module.export_png_for_ipp(doc, "test.png", FakeInfoObject))
        self.assertFalse(doc.state)

    def test_restores_batchmode_when_export_raises(self):
        doc = FakeDocument(raise_error=True)
        with self.assertRaisesRegex(RuntimeError, "export failed"):
            module.export_png_for_ipp(doc, "test.png", FakeInfoObject)
        self.assertFalse(doc.state)


if __name__ == "__main__":
    unittest.main()
