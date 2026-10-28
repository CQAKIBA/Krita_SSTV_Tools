"""Custom text-style presets dialog for SSTV Toolbox.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""
from .qt_compat import (
    Qt, QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QListWidget,
    QPushButton, QLineEdit, QFontComboBox, QSpinBox,
    QComboBox, QLabel, QFont,
)
from .presets import defaults


class PresetDialog(QDialog):
    def __init__(self, presets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文字プリセットの登録・編集")
        self.resize(620, 420)
        self.presets = [dict(item) for item in presets]
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        self.items = QListWidget()
        self.items.addItems([p.get("label", "") for p in self.presets])
        left.addWidget(QLabel("登録済みのボタン"))
        left.addWidget(self.items)
        add_btn = QPushButton("＋ 新規登録")
        delete_btn = QPushButton("選択した項目を削除")
        reset_btn = QPushButton("初期値に戻す")
        left.addWidget(add_btn)
        left.addWidget(delete_btn)
        left.addWidget(reset_btn)
        layout.addLayout(left, 2)

        right = QVBoxLayout()
        form = QFormLayout()
        self.label_edit = QLineEdit()
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("{CALLSIGN}, {DATE}, {TIME}, {DATETIME} が利用可能")
        self.font_edit = QFontComboBox()
        self.size_edit = QSpinBox()
        self.size_edit.setRange(8, 200)
        self.size_edit.setValue(40)
        self.position_edit = QComboBox()
        self.position_edit.addItem("上", "top")
        self.position_edit.addItem("中央", "center")
        self.position_edit.addItem("下", "bottom")
        self.color_value = "#ffffff"  # kept as a fallback for old presets
        form.addRow("ボタン名", self.label_edit)
        form.addRow("文字列", self.text_edit)
        form.addRow("フォント", self.font_edit)
        form.addRow("文字サイズ(px)", self.size_edit)
        form.addRow("初期配置", self.position_edit)
        right.addLayout(form)
        right.addWidget(QLabel("文字色はKritaの現在の前景色（カラーピッカー）を使います。"))
        right.addWidget(QLabel("装飾（フチ・影）はツールボックス上で切り替えます。"))
        right.addWidget(QLabel("差し込み記号: {CALLSIGN} / {DATE} / {TIME} / {DATETIME}"))
        save_item = QPushButton("この項目に変更を反映")
        right.addWidget(save_item)
        right.addStretch()
        ok = QPushButton("設定を保存して閉じる")
        cancel = QPushButton("キャンセル")
        buttons = QHBoxLayout()
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        right.addLayout(buttons)
        layout.addLayout(right, 3)

        self.items.currentRowChanged.connect(self.load_item)
        add_btn.clicked.connect(self.add_item)
        delete_btn.clicked.connect(self.delete_item)
        reset_btn.clicked.connect(self.reset_items)
        save_item.clicked.connect(self.apply_item)
        ok.clicked.connect(self.save_and_accept)
        cancel.clicked.connect(self.reject)
        if self.presets:
            self.items.setCurrentRow(0)

    def load_item(self, index):
        if index < 0 or index >= len(self.presets):
            return
        item = self.presets[index]
        self.label_edit.setText(item.get("label", ""))
        self.text_edit.setText(item.get("text", ""))
        self.font_edit.setCurrentFont(QFont(item.get("font", "Sans Serif")))
        self.size_edit.setValue(int(item.get("size", 40)))
        pos = self.position_edit.findData(item.get("position", "bottom"))
        self.position_edit.setCurrentIndex(max(0, pos))
        self.color_value = item.get("color", "#ffffff")

    def apply_item(self):
        index = self.items.currentRow()
        if index < 0:
            return
        label = self.label_edit.text().strip()
        value = self.text_edit.text()
        if not label or not value:
            from .qt_compat import QMessageBox
            QMessageBox.warning(self, "文字プリセット", "ボタン名と文字列を入力してください。")
            return False
        self.presets[index] = dict(
            label=label, text=value, font=self.font_edit.currentFont().family(),
            size=self.size_edit.value(), color=self.color_value,
            position=self.position_edit.currentData(),
        )
        self.items.item(index).setText(label)
        return True

    def add_item(self):
        self.presets.append(dict(label="新しい文字", text="HELLO", font="Sans Serif",
                                 size=40, color="#ffffff", position="bottom"))
        self.items.addItem("新しい文字")
        self.items.setCurrentRow(len(self.presets) - 1)

    def delete_item(self):
        index = self.items.currentRow()
        if index >= 0:
            self.presets.pop(index)
            self.items.takeItem(index)
            if self.presets:
                self.items.setCurrentRow(min(index, len(self.presets) - 1))

    def reset_items(self):
        self.presets = defaults()
        self.items.clear()
        self.items.addItems([p["label"] for p in self.presets])
        self.items.setCurrentRow(0)

    def save_and_accept(self):
        if self.items.currentRow() >= 0:
            if not self.apply_item():
                return
        self.accept()
