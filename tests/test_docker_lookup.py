# Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless undo-history docker identification tests."""
import importlib.util
import unittest
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "sstv_toolbox" / "docker_lookup.py"
spec = importlib.util.spec_from_file_location("sstv_docker_lookup_test", src)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeDocker:
    def __init__(self, name, title):
        self.name, self.title = name, title
    def objectName(self):
        return self.name
    def windowTitle(self):
        return self.title


class HistoryDockerTests(unittest.TestCase):
    def test_english_and_japanese_titles(self):
        for title in ("Undo History", "編集履歴", "元に戻す履歴"):
            candidate = FakeDocker("", title)
            self.assertIs(module.history_docker([candidate]), candidate)

    def test_stable_id_ignores_translation(self):
        candidate = FakeDocker("HistoryDock", "Historique")
        self.assertIs(module.history_docker([candidate]), candidate)

    def test_does_not_confuse_brush_history(self):
        brush = FakeDocker("BrushPresetHistory", "Brush Preset History")
        real = FakeDocker("History", "編集履歴")
        self.assertIs(module.history_docker([brush, real]), real)
        self.assertIsNone(module.history_docker([brush]))

    def test_no_unrelated_docker(self):
        self.assertIsNone(module.history_docker([FakeDocker("Layer", "レイヤー")]))


if __name__ == "__main__":
    unittest.main()
