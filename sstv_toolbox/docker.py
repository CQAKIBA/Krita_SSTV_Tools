"""Dockable Krita SSTV Toolbox prototype (Krita 5 / 6).
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""

import json
import os
import sys
import tempfile
from krita import Krita, DockWidget, DockWidgetFactory, DockWidgetFactoryBase, InfoObject
from .qt_compat import (
    Qt, QT6, QColor, QFont, QFontMetrics, QImage, QImageReader,
    QPainter, QSettings, QByteArray, QSize, QPoint, QRect, QRectF, QThread, pyqtSignal,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QSlider, QScrollArea,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QCheckBox, QComboBox,
    QApplication, QMenu, QGuiApplication, QDesktopServices, QUrl, QSizeGrip, QDockWidget, QRadioButton,
    CUSTOM_CONTEXT_MENU,
    ALIGN_CENTER, KEEP_ASPECT, SMOOTH, HORIZONTAL, FORMAT_ARGB32,
    QUESTION_YES, QUESTION_NO,
)
from .presets import defaults, resolve_text
from .geometry import fit_dimensions, cover_source_rect
from .preset_dialog import PresetDialog
from .ipp_client import send_png, IPPError
from .png_export import export_png_for_ipp
from .layer_policy import choose_background_placement, is_blank_bgra
from .docker_lookup import history_docker
from .window_position import floating_window_position

REPOSITORY_URL = "https://github.com/CQAKIBA/Krita_SSTV_Tools"


class PrintWorker(QThread):
    result = pyqtSignal(bool, str)

    def __init__(self, url, data, parent=None):
        super().__init__(parent)
        self.url, self.data = url, data

    def run(self):
        try:
            result = send_png(self.url, self.data)
            self.result.emit(True, result)
        except Exception as exc:
            self.result.emit(False, str(exc))


class PrinterSettings(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IPP仮想プリンタ設定")
        self.resize(460, 160)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("送信先IPPプリンタURL:"))
        self.url = QLineEdit(url)
        self.url.setPlaceholderText("ipp://127.0.0.1:631/printers/sstv")
        layout.addWidget(self.url)
        caption = QLabel("PNG (image/png) を受信できるIPPサーバが必要です。\n"
                         "実在する送信先を入力してから送信してください。")
        caption.setWordWrap(True)
        layout.addWidget(caption)
        row = QHBoxLayout()
        cancel = QPushButton("キャンセル")
        ok = QPushButton("保存")
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)


class SSTVToolbox(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSTVツールボックス")
        self.settings = QSettings("SSTVToolbox", "KritaSSTVToolbox")
        self._print_worker = None
        self._help_fallback_menu = None
        self._last_node = None
        self._last_doc = None
        self.presets = self._load_presets()

        # Keep the resize grip OUTSIDE the scroll area, so it remains visible
        # even when the toolbox has many controls and its content is scrolled.
        panel = QWidget(self)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        scroller = QScrollArea(panel)
        scroller.setWidgetResizable(True)
        scroller.setFrameStyle(0)
        body = QWidget(scroller)
        self.layout_root = QVBoxLayout(body)
        self.layout_root.setContentsMargins(8, 8, 8, 8)
        self.layout_root.setSpacing(8)
        scroller.setWidget(body)
        panel_layout.addWidget(scroller, 1)
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(4, 0, 4, 2)
        grip_row.addStretch(1)
        self.resize_grip = QSizeGrip(panel)
        self.resize_grip.setFixedSize(28, 28)
        self.resize_grip.setToolTip("ドラッグしてSSTVツールボックスのサイズを変更")
        grip_row.addWidget(self.resize_grip)
        panel_layout.addLayout(grip_row)
        self.setWidget(panel)
        # Update only our own grip. No global Qt stylesheet or Krita UI changes.
        self.topLevelChanged.connect(self._floating_changed)
        self._floating_changed(self.isFloating())
        self.setMinimumWidth(225)

        self._make_canvas_buttons()
        self._make_image_buttons()
        self._make_wipe_buttons()
        self._make_text_buttons()
        self._make_operation_buttons()
        self._make_print_buttons()
        self._make_help_buttons()
        self.status = QLabel("準備OK。新規キャンバスを作るか画像を開いてください。")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: palette(mid);")
        self.layout_root.addWidget(self.status)
        self.layout_root.addStretch(1)

    def _floating_changed(self, floating):
        self.resize_grip.setVisible(bool(floating))

    def canvasChanged(self, canvas):
        if canvas is not None and Krita.instance().activeDocument() is not None:
            doc = Krita.instance().activeDocument()
            if hasattr(self, "status"):
                self.status.setText("キャンバス: {} × {}".format(doc.width(), doc.height()))

    def _load_presets(self):
        try:
            data = json.loads(self.settings.value("presets", "null"))
            if isinstance(data, list) and all(isinstance(v, dict) for v in data):
                return data[:40]
        except (ValueError, TypeError):
            pass
        return defaults()

    def _group(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setSpacing(5)
        self.layout_root.addWidget(group)
        return layout

    def _row_buttons(self, layout, pairs):
        row = QHBoxLayout()
        for label, handler in pairs:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            row.addWidget(btn)
        layout.addLayout(row)

    def _make_canvas_buttons(self):
        layout = self._group("新規キャンバス")
        self._row_buttons(layout, [("640 × 480", lambda: self._guard(lambda: self.new_canvas(640, 480))),
                                   ("640 × 512", lambda: self._guard(lambda: self.new_canvas(640, 512)))])

    def _make_image_buttons(self):
        layout = self._group("背景に貼り付け")
        self.full_size = QCheckBox("フルサイズ（余白なし・中央をトリミング）")
        self.full_size.setChecked(str(self.settings.value("background_full_size", "false")).lower() == "true")
        self.full_size.toggled.connect(lambda value: self.settings.setValue("background_full_size", value))
        layout.addWidget(self.full_size)
        self._row_buttons(layout, [("ファイルから", lambda: self._guard(lambda: self.paste_file(False))),
                                   ("クリップボードから", lambda: self._guard(lambda: self.paste_clipboard(False)))])
        hint = QLabel("OFF: 全体を表示（余白あり） / ON: 画面を埋める")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def _make_wipe_buttons(self):
        layout = self._group("ワイプとして貼り付け")
        row = QHBoxLayout()
        row.addWidget(QLabel("大きさ"))
        self.wipe = QSlider(HORIZONTAL)
        self.wipe.setMinimum(10)
        self.wipe.setMaximum(100)
        self.wipe.setSingleStep(5)
        self.wipe.setPageStep(10)
        self.wipe.setValue(int(self.settings.value("wipe_percent", 30)))
        self.wipe_label = QLabel("{}%".format(self.wipe.value()))
        row.addWidget(self.wipe, 1)
        row.addWidget(self.wipe_label)
        layout.addLayout(row)
        self.wipe.valueChanged.connect(self._wipe_changed)
        self._row_buttons(layout, [("ファイルから", lambda: self._guard(lambda: self.paste_file(True))),
                                   ("クリップボードから", lambda: self._guard(lambda: self.paste_clipboard(True)))])
        hint = QLabel("100%=キャンバス内に収まる最大サイズ（縦横比維持）")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def _wipe_changed(self, value):
        self.wipe_label.setText("{}%".format(value))
        self.settings.setValue("wipe_percent", value)

    def _make_text_buttons(self):
        layout = self._group("テキストを貼り付け")
        callrow = QHBoxLayout()
        callrow.addWidget(QLabel("コールサイン"))
        self.call = QLineEdit(str(self.settings.value("callsign", "JA1ABC")))
        self.call.setPlaceholderText("JA1ABC")
        self.call.setMinimumWidth(70)
        self.call.editingFinished.connect(lambda: self.settings.setValue("callsign", self.call.text()))
        callrow.addWidget(self.call, 1)
        layout.addLayout(callrow)
        effect_row = QHBoxLayout()
        effect_row.addWidget(QLabel("文字装飾"))
        self.text_effect = QComboBox()
        for label, value in (("装飾なし", "none"), ("白フチ", "white-outline"),
                             ("黒フチ", "black-outline"), ("白影", "white-shadow"),
                             ("黒影", "black-shadow")):
            self.text_effect.addItem(label, value)
        old_effect = str(self.settings.value("text_effect", "black-outline"))
        index = self.text_effect.findData(old_effect)
        self.text_effect.setCurrentIndex(max(0, index))
        self.text_effect.currentIndexChanged.connect(
            lambda _: self.settings.setValue("text_effect", self.text_effect.currentData()))
        effect_row.addWidget(self.text_effect, 1)
        layout.addLayout(effect_row)
        edit = QPushButton("＋ 登録・書式編集…")
        edit.clicked.connect(lambda: self._guard(self.edit_presets))
        layout.addWidget(edit)
        self.text_grid_holder = QWidget()
        self.text_grid = QGridLayout(self.text_grid_holder)
        self.text_grid.setContentsMargins(0, 0, 0, 0)
        self.text_grid.setSpacing(5)
        layout.addWidget(self.text_grid_holder)
        self.rebuild_presets()

    def rebuild_presets(self):
        while self.text_grid.count():
            item = self.text_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, preset in enumerate(self.presets):
            btn = QPushButton(str(preset.get("label", "文字")))
            btn.clicked.connect(lambda checked=False, index=i: self._guard(lambda: self.insert_text(index)))
            self.text_grid.addWidget(btn, i // 3, i % 3)

    def _make_operation_buttons(self):
        layout = self._group("操作")
        first = QHBoxLayout()
        undo = QPushButton("元に戻す")
        undo.clicked.connect(lambda: self._guard(lambda: self.do_action("edit_undo")))
        first.addWidget(undo, 1)
        redo = QPushButton("やり直す")
        redo.clicked.connect(lambda: self._guard(lambda: self.do_action("edit_redo")))
        first.addWidget(redo, 1)
        self.history_button = QPushButton("編集履歴")
        self.history_button.setToolTip("左クリック: 表示/非表示、右クリック: フローティング表示")
        self.history_button.clicked.connect(lambda: self._guard(self.toggle_history))
        self.history_button.setContextMenuPolicy(CUSTOM_CONTEXT_MENU)
        self.history_button.customContextMenuRequested.connect(self._history_context_menu)
        self._history_popup = QMenu(self.history_button)
        float_action = self._history_popup.addAction("フローティングで表示")
        float_action.triggered.connect(lambda: self._guard(self.float_history))
        first.addWidget(self.history_button, 1)
        layout.addLayout(first)

        second = QHBoxLayout()
        for label, tip, callback in (
            ("選択解除", "Kritaの選択範囲を解除", lambda: self.do_action("deselect")),
            ("選択レイヤを中央", "今選択しているレイヤーの画像をキャンバス中央へ移動", self.recenter_layer),
            ("全体表示", "Kritaの「ビューに合わせる」", lambda: self.do_action("zoom_to_fit")),
        ):
            button = QPushButton(label)
            button.setToolTip(tip)
            button.clicked.connect(lambda checked=False, fn=callback: self._guard(fn))
            second.addWidget(button, 1)
        layout.addLayout(second)

    def _make_print_buttons(self):
        layout = self._group("SSTV送信")
        send = QPushButton("▶ バーチャルプリンタへ送信")
        send.clicked.connect(lambda: self._guard(self.print_to_ipp))
        layout.addWidget(send)
        self.send_button = send
        setup = QPushButton("IPP送信先の設定…")
        setup.clicked.connect(lambda: self._guard(self.printer_settings))
        layout.addWidget(setup)

    def _make_help_buttons(self):
        layout = self._group("困ったとき")
        row = QHBoxLayout()
        help_btn = QPushButton("Kritaのヘルプメニュー ▼")
        help_btn.clicked.connect(lambda: self._guard(lambda: self.open_help(help_btn)))
        row.addWidget(help_btn, 2)
        github_btn = QPushButton("GitHub")
        github_btn.setToolTip("SSTV ToolboxのソースコードとライセンスをGitHubで開く")
        github_btn.clicked.connect(lambda: self._guard(self.open_repository))
        row.addWidget(github_btn, 1)
        layout.addLayout(row)
        layout.addWidget(QLabel("KritaのAbout・開発者情報はヘルプメニューから確認できます。"))

    def open_repository(self):
        if not QDesktopServices.openUrl(QUrl(REPOSITORY_URL)):
            QMessageBox.warning(self, "GitHub", "ブラウザを開けませんでした。\n" + REPOSITORY_URL)

    def _guard(self, callback):
        try:
            callback()
        except Exception as exc:
            QMessageBox.critical(self, "SSTV Toolbox", "操作に失敗しました:\n{}".format(exc))
            if hasattr(self, "status"):
                self.status.setText("エラー: {}".format(exc))

    def _document(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            QMessageBox.information(self, "キャンバスがありません", "まず新規キャンバスを作ってください。")
            return None
        if doc.colorModel() != "RGBA" or doc.colorDepth() != "U8":
            QMessageBox.warning(self, "画像形式", "試作版の貼り付けはRGBA・8bitキャンバス専用です。\n"
                               "SSTVツールボックスの新規キャンバスを使ってください。")
            return None
        if sys.byteorder != "little":
            QMessageBox.warning(self, "未対応", "この試作版はリトルエンディアン環境専用です。")
            return None
        return doc

    def new_canvas(self, width, height):
        app = Krita.instance()
        window = app.activeWindow()
        if window is None:
            raise RuntimeError("Kritaのウィンドウが見つかりません。")
        doc = app.createDocument(width, height, "SSTV {}x{}".format(width, height),
                                 "RGBA", "U8", "", 72.0)
        if doc is None:
            raise RuntimeError("キャンバスを作成できませんでした。")
        window.addView(doc)
        # Background from our own new-document button is predictable; do not
        # prompt during creation even if a Krita release creates extra nodes.
        white = QImage(width, height, FORMAT_ARGB32)
        white.fill(QColor("white"))
        self._replace_background(doc, white, interactive=False)
        doc.refreshProjection()
        self.status.setText("{}×{} のSSTVキャンバスを作成しました".format(width, height))

    def _add_layer(self, doc, image, x, y, name, above="top", select=True):
        # setPixelData expects BGRA for U8 RGBA Krita layers. Qt ARGB32 on
        # little-endian Windows/Linux provides exactly B,G,R,A bytes.
        image = image.convertToFormat(FORMAT_ARGB32)
        raw = image.bits().asstring(image.sizeInBytes())
        node = doc.createNode(name, "paintlayer")
        if node is None:
            raise RuntimeError("画像レイヤーを作成できません。")
        if not node.setPixelData(QByteArray(raw), x, y, image.width(), image.height()):
            raise RuntimeError("レイヤーに画像を書き込めませんでした。")
        root = doc.rootNode()
        siblings = root.childNodes()
        above_node = siblings[-1] if above == "top" and siblings else None
        if not root.addChildNode(node, above_node):
            raise RuntimeError("レイヤーの追加に失敗しました。")
        if select:
            doc.setActiveNode(node)
            self._last_node, self._last_doc = node, doc
        doc.refreshProjection()
        return node

    def paste_file(self, wipe):
        if self._document() is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "写真を選択", "", "画像ファイル (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff);;すべて (*)"
        )
        if not path:
            return
        reader = QImageReader(path)
        reader.setAutoTransform(True)  # apply EXIF orientation
        image = reader.read()
        if image.isNull():
            raise RuntimeError("画像を開けません: {}".format(reader.errorString()))
        self._place_image(image, wipe, os.path.basename(path))

    def paste_clipboard(self, wipe):
        if self._document() is None:
            return
        image = QApplication.clipboard().image()
        if image.isNull():
            QMessageBox.information(self, "クリップボード", "画像が見つかりません。\n画像をコピーしてから試してください。")
            return
        self._place_image(image, wipe, "クリップボード")

    def _layer_is_blank(self, doc, node):
        """Conservative white/transparent BGRA test; None means unknown.

        A visually white layer may have been edited before; never use the test
        to overwrite or remove it. It only picks a layer insertion position.
        """
        if node.type() != "paintlayer":
            return None
        if node.bounds().isEmpty():
            return True
        width, height = doc.width(), doc.height()
        if width * height > 4_000_000:
            return None  # refuse a potentially huge pixelData allocation
        try:
            pixels = bytes(node.pixelData(0, 0, width, height))
            return is_blank_bgra(pixels, width, height)
        except (RuntimeError, ValueError, TypeError):
            return None

    def _ask_background_placement(self, reason):
        """Ask BEFORE creating or replacing any background layer."""
        dialog = QDialog(self)
        dialog.setWindowTitle("背景レイヤーの配置を確認")
        dialog.resize(420, 240)
        layout = QVBoxLayout(dialog)
        if reason == "complex":
            message = "この文書にはグループや特殊レイヤーがあります。\n背景の位置を自動判定できませんでした。"
        else:
            message = "最下層のレイヤーに描画内容があるか、白紙かどうか判断できません。\n背景の配置先を選んでください。"
        info = QLabel(message + "\n既存レイヤーの中身は変更しません。")
        info.setWordWrap(True)
        layout.addWidget(info)
        options = [
            ("bottom", "一番下に配置（上の絵を隠しにくい）"),
            ("above_bottom", "最下層の直上に配置（2層目）"),
            ("top", "一番上に配置（他の絵を隠す場合あり）"),
        ]
        radios = []
        for key, label in options:
            radio = QRadioButton(label, dialog)
            radio.setProperty("placement", key)
            layout.addWidget(radio)
            radios.append(radio)
        if reason == "complex":
            # The native move-layer-down action can enter groups. In complex
            # stacks do not attempt to move a layer all the way to the bottom.
            radios[0].setEnabled(False)
            radios[0].setText("一番下に配置（複雑な構造のため自動操作しません）")
            radios[2].setChecked(True)
        else:
            radios[1].setChecked(True)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("キャンセル")
        accept = QPushButton("この位置に配置")
        cancel.clicked.connect(dialog.reject)
        accept.clicked.connect(dialog.accept)
        row.addWidget(cancel)
        row.addWidget(accept)
        layout.addLayout(row)
        exec_dialog = dialog.exec if QT6 else dialog.exec_
        accepted = QDialog.DialogCode.Accepted if QT6 else QDialog.Accepted
        if exec_dialog() != accepted:
            return None
        return next(str(r.property("placement")) for r in radios if r.isChecked())

    def _replace_background(self, doc, image, interactive=True):
        """Replace only our own named layer, and place it safely near bottom.

        Never guess a translated Krita default layer name, and never alter its
        pixels. The new layer is inserted before the old one is removed.
        """
        root = doc.rootNode()
        siblings = list(root.childNodes())  # documented bottom -> top
        managed = [n for n in siblings if n.type() == "paintlayer" and n.name() == "SSTV 背景"]
        if len(managed) > 1:
            QMessageBox.warning(self, "背景が複数あります", "SSTV 背景が複数あります。\nレイヤーを整理してから再度お試しください。")
            return False
        old = managed[0] if managed else None
        others = [n for n in siblings if n is not old]
        infos = [{"type": n.type(), "blank": self._layer_is_blank(doc, n) if i == 0 else None,
                  "nested": bool(n.childNodes())} for i, n in enumerate(others)]
        position, reason = choose_background_placement(infos)
        if position == "ask":
            if not interactive:
                # Our fresh blank document is under our control: safest fallback.
                position = "bottom"
            else:
                position = self._ask_background_placement(reason)
                if position is None:
                    self.status.setText("背景の配置をキャンセルしました")
                    return False
        anchor = None
        if position == "above_bottom" and others:
            anchor = others[0]
        elif position == "top" and others:
            anchor = others[-1]
        # Krita's addChildNode(..., None) appends to the TOP (or is the only
        # layer if empty). For a true bottom insertion, use its native Move
        # Layer Down action below, never setChildNodes on arbitrary user art.
        new_node = doc.createNode("SSTV 背景", "paintlayer")
        if new_node is None:
            raise RuntimeError("背景レイヤーを作成できません")
        image = image.convertToFormat(FORMAT_ARGB32)
        raw = image.bits().asstring(image.sizeInBytes())
        if not new_node.setPixelData(QByteArray(raw), 0, 0, doc.width(), doc.height()):
            raise RuntimeError("背景の画像データを書き込めませんでした")
        previous = doc.activeNode()
        if not root.addChildNode(new_node, anchor):
            raise RuntimeError("背景レイヤーを追加できませんでした")
        if position == "bottom" and others:
            # Only supported for a simple flat paint-layer stack. Always
            # verify each move, preserving the original background until all
            # moves succeed. A complex stack was handled in the dialog above.
            if any(n.type() != "paintlayer" or bool(n.childNodes()) for n in siblings):
                root.removeChildNode(new_node)
                raise RuntimeError("複雑なレイヤー構造では最下層への自動移動はできません")
            move_action = Krita.instance().action("move_layer_down")
            if move_action is None:
                root.removeChildNode(new_node)
                raise RuntimeError("このKritaにはレイヤーを下げる操作が見つかりません")
            doc.setActiveNode(new_node)
            for _ in range(len(siblings)):
                before = [str(n.uniqueId()) for n in root.childNodes()]
                index = before.index(str(new_node.uniqueId()))
                if index == 0:
                    break
                move_action.trigger()
                doc.waitForDone()
                after = [str(n.uniqueId()) for n in root.childNodes()]
                if str(new_node.uniqueId()) not in after or after.index(str(new_node.uniqueId())) >= index:
                    root.removeChildNode(new_node)
                    raise RuntimeError("最下層への移動を確定できなかったため、元の背景を維持しました")
            if [str(n.uniqueId()) for n in root.childNodes()][0] != str(new_node.uniqueId()):
                root.removeChildNode(new_node)
                raise RuntimeError("最下層への移動に失敗しました。元の背景を維持しました")
        if old is not None and not root.removeChildNode(old):
            root.removeChildNode(new_node)
            raise RuntimeError("既存のSSTV背景を置き換えられませんでした")
        new_node.setLocked(True)
        # Keep the original paintable layer selected where possible; a locked
        # background should never become the user-visible drag target.
        remaining = list(root.childNodes())
        if previous is not None and previous is not old and previous.parentNode() is not None:
            doc.setActiveNode(previous)
        else:
            candidates = [n for n in remaining if n is not new_node and n.type() == "paintlayer" and not n.locked()]
            doc.setActiveNode(candidates[-1] if candidates else new_node)
        doc.refreshProjection()
        return True

    def _place_image(self, image, wipe, name):
        doc = self._document()
        if doc is None:
            return
        if wipe:
            # 100% = maximum contained image size, regardless of aspect ratio.
            width, height = fit_dimensions(image.width(), image.height(),
                                           doc.width(), doc.height(), self.wipe.value())
            # The computed dimensions already respect the source aspect ratio.
            scaled = image.scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio
                                  if QT6 else Qt.IgnoreAspectRatio, SMOOTH)
            x = (doc.width() - scaled.width()) // 2
            y = (doc.height() - scaled.height()) // 2
            self._add_layer(doc, scaled, x, y, "ワイプ: " + name)
            self._select_move_tool()
            self.status.setText("ワイプを追加 ({}×{}, {}%)。移動ツールで位置を調整できます。".format(
                scaled.width(), scaled.height(), self.wipe.value()))
        else:
            # A background is always a full-canvas layer. In contain mode,
            # uncovered space is white; in cover mode, crop the centre.
            frame = QImage(doc.width(), doc.height(), FORMAT_ARGB32)
            frame.fill(QColor("white"))
            painter = QPainter(frame)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform
                                  if QT6 else QPainter.SmoothPixmapTransform, True)
            if self.full_size.isChecked():
                sx, sy, sw, sh = cover_source_rect(image.width(), image.height(),
                                                   doc.width(), doc.height())
                painter.drawImage(QRectF(0, 0, doc.width(), doc.height()), image,
                                  QRectF(sx, sy, sw, sh))
                mode = "フルサイズ（中央トリミング）"
            else:
                width, height = fit_dimensions(image.width(), image.height(),
                                               doc.width(), doc.height())
                painter.drawImage((doc.width() - width) // 2, (doc.height() - height) // 2,
                                  image.scaled(width, height,
                                               Qt.AspectRatioMode.IgnoreAspectRatio if QT6
                                               else Qt.IgnoreAspectRatio, SMOOTH))
                mode = "全体を表示"
            painter.end()
            if self._replace_background(doc, frame):
                self._select_move_tool()
                self.status.setText("背景を更新しました: {}（{}）".format(name, mode))

    def _select_move_tool(self):
        """Use Krita's native Move Tool so the new object can be dragged."""
        action = Krita.instance().action("KritaTransform/KisToolMove")
        if action is not None:
            action.trigger()

    def _foreground_color(self, default_color):
        """Use Krita's foreground swatch; preset color is fallback only."""
        try:
            window = Krita.instance().activeWindow()
            view = window.activeView() if window is not None else None
            if view is not None:
                current = view.foregroundColor().colorForCanvas(view.canvas())
                if current.isValid():
                    return current
        except (AttributeError, RuntimeError, TypeError):
            pass
        fallback = QColor(default_color)
        return fallback if fallback.isValid() else QColor("white")

    def edit_presets(self):
        dialog = PresetDialog(self.presets, self)
        exec_dialog = dialog.exec if QT6 else dialog.exec_
        if exec_dialog() == (QDialog.DialogCode.Accepted if QT6 else QDialog.Accepted):
            self.presets = dialog.presets
            self.settings.setValue("presets", json.dumps(self.presets, ensure_ascii=False))
            self.rebuild_presets()
            self.status.setText("文字プリセットを保存しました")

    def insert_text(self, index):
        doc = self._document()
        if doc is None or index >= len(self.presets):
            return
        preset = self.presets[index]
        value = resolve_text(preset.get("text", ""), self.call.text().strip())
        if not value:
            QMessageBox.information(self, "テキスト", "挿入する文字列が空です。")
            return
        font = QFont(preset.get("font", "Sans Serif"))
        font.setPixelSize(int(preset.get("size", 40)))
        fm = QFontMetrics(font)
        lines = value.splitlines() or [value]
        pad = 12  # room for 2px outline and 3px shadow
        for _ in range(160):
            text_width = max(fm.horizontalAdvance(line) for line in lines) + pad * 2
            text_height = fm.height() * len(lines) + pad * 2
            if text_width <= doc.width() and text_height <= doc.height():
                break
            font.setPixelSize(max(8, font.pixelSize() - 1))
            fm = QFontMetrics(font)
        width = min(doc.width(), max(16, max(fm.horizontalAdvance(v) for v in lines) + pad * 2))
        height = min(doc.height(), max(16, fm.height() * len(lines) + pad * 2))
        image = QImage(width, height, FORMAT_ARGB32)
        image.fill(QColor(0, 0, 0, 0))
        painter = QPainter(image)
        painter.setFont(font)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing
                              if QT6 else QPainter.TextAntialiasing, True)
        color = self._foreground_color(preset.get("color", "#ffffff"))
        effect = self.text_effect.currentData()
        effect_color = QColor("white" if effect.startswith("white") else "black")
        for j, line in enumerate(lines):
            rect = QRect(0, pad + j * fm.height(), width, fm.height())
            if effect in ("white-outline", "black-outline"):
                painter.setPen(effect_color)
                # A circular-ish two-pixel outline, including diagonal offsets.
                for dx in (-2, -1, 0, 1, 2):
                    for dy in (-2, -1, 0, 1, 2):
                        if (dx or dy) and dx * dx + dy * dy <= 5:
                            painter.drawText(rect.translated(dx, dy), ALIGN_CENTER, line)
            elif effect in ("white-shadow", "black-shadow"):
                painter.setPen(effect_color)
                painter.drawText(rect.translated(3, 3), ALIGN_CENTER, line)
            painter.setPen(color)
            painter.drawText(rect, ALIGN_CENTER, line)
        painter.end()
        x = (doc.width() - width) // 2
        position = preset.get("position", "bottom")
        if position == "top":
            y = 8
        elif position == "center":
            y = (doc.height() - height) // 2
        else:
            y = doc.height() - height - 8
        self._add_layer(doc, image, x, y, "文字: " + preset.get("label", value))
        self._select_move_tool()
        self.status.setText("文字「{}」を追加しました".format(value))

    def do_action(self, action_id):
        action = Krita.instance().action(action_id)
        if action is None:
            QMessageBox.information(self, "Krita", "この環境では操作が見つかりません: " + action_id)
            return
        action.trigger()

    def _window_dockers(self):
        window = Krita.instance().activeWindow()
        if window is None:
            return []
        if hasattr(window, "dockers"):
            return list(window.dockers())
        qwin = window.qwindow()
        return list(qwin.findChildren(QDockWidget)) if qwin is not None else []

    def _history_docker(self):
        result = history_docker(self._window_dockers())
        if result is None:
            QMessageBox.information(
                self, "編集履歴", "Kritaの編集履歴ドッカーが見つかりませんでした。\n"
                "設定 → ドッキングパネル → 編集履歴 から表示できます。")
        return result

    def toggle_history(self):
        docker = self._history_docker()
        if docker is None:
            return
        if docker.isVisible():
            docker.hide()
            self.status.setText("編集履歴を非表示にしました")
        else:
            docker.show()
            docker.raise_()  # activate a tabbed docker, if possible
            self.status.setText("編集履歴を表示しました")

    def _history_context_menu(self, position):
        self._history_popup.popup(self.history_button.mapToGlobal(position))

    def float_history(self):
        docker = self._history_docker()
        if docker is None:
            return
        window = Krita.instance().activeWindow()
        main = window.qwindow() if window is not None else None
        docker.setFloating(True)
        docker.show()  # Qt may reparent the dock when transitioning to floating.
        if main is not None:
            # Pick a point in Krita's main window, never the mouse or toolbox
            # position (which can be hidden amongst right-side dock tabs).
            anchor = main.mapToGlobal(QPoint(int(main.width() * 0.30),
                                             int(main.height() * 0.30)))
            screen = QGuiApplication.screenAt(anchor) if hasattr(QGuiApplication, "screenAt") else None
            if screen is None and hasattr(main, "screen"):
                screen = main.screen()
        else:
            screen = None
            anchor = QPoint(0, 0)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            width = min(380, max(160, area.width() - 32))
            height = min(480, max(160, area.height() - 32))
            x, y = floating_window_position(anchor.x(), anchor.y(), width, height,
                                            area.left(), area.top(),
                                            area.width(), area.height())
            docker.resize(width, height)
            docker.move(x, y)
        docker.raise_()
        docker.activateWindow()
        self.status.setText("編集履歴をフローティング表示しました")

    def recenter_layer(self):
        doc = self._document()
        if doc is None:
            return
        node = doc.activeNode()
        if node is None:
            QMessageBox.information(self, "レイヤーの中央配置", "レイヤーパネルで画像レイヤーを選択してください。")
            return
        if node.type() not in ("paintlayer", "vectorlayer") or node.locked():
            QMessageBox.information(self, "レイヤーの中央配置", "移動できるペイント/ベクターレイヤーを選択してください。\n"
                                    "ロックされた背景やグループは対象外です。")
            return
        bounds = node.bounds()
        if bounds.isEmpty():
            QMessageBox.information(self, "レイヤーの中央配置", "選択レイヤーに移動できる画像がありません。")
            return
        dx = (doc.width() - bounds.width()) // 2 - bounds.x()
        dy = (doc.height() - bounds.height()) // 2 - bounds.y()
        current = node.position()
        node.move(current.x() + dx, current.y() + dy)
        doc.refreshProjection()
        self.status.setText("選択中の「{}」を中央へ移動しました".format(node.name()))

    def printer_settings(self):
        dialog = PrinterSettings(str(self.settings.value("ipp_uri", "")), self)
        exec_dialog = dialog.exec if QT6 else dialog.exec_
        if exec_dialog() == (QDialog.DialogCode.Accepted if QT6 else QDialog.Accepted):
            # Validate URI before storing.
            from .ipp_client import normalize_printer_uri
            url = dialog.url.text().strip()
            if url:
                normalize_printer_uri(url)
            self.settings.setValue("ipp_uri", url)
            self.status.setText("IPP送信先を保存しました" if url else "IPP送信先を未設定にしました")

    def print_to_ipp(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            QMessageBox.information(self, "IPP送信", "キャンバスを作成してください。")
            return
        if self._print_worker is not None:
            QMessageBox.information(self, "IPP送信", "現在送信中です。")
            return
        url = str(self.settings.value("ipp_uri", "")).strip()
        if not url:
            self.printer_settings()
            url = str(self.settings.value("ipp_uri", "")).strip()
            if not url:
                return
        from .ipp_client import normalize_printer_uri
        normalize_printer_uri(url)
        result = QMessageBox.question(
            self, "IPP送信を確認",
            "現在のキャンバスをPNGで\n{}\nへ送信します。\n\n"
            "※サーバ側が受け付けた場合、SSTV送信が始まる可能性があります。\n送信しますか？".format(url),
            QUESTION_YES | QUESTION_NO, QUESTION_NO
        )
        if result != QUESTION_YES:
            return
        doc.waitForDone()
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="krita_sstv_")
            os.close(fd)
            if not export_png_for_ipp(doc, tmp_path, InfoObject):
                raise RuntimeError("PNG画像を書き出せませんでした。未確定の変形がある場合は確定してください。")
            with open(tmp_path, "rb") as fh:
                data = fh.read()
            if len(data) > 64 * 1024 * 1024:
                raise RuntimeError("PNGが64MiBを超えています。")
        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        self.send_button.setEnabled(False)
        self.status.setText("IPPサーバへ送信中…")
        self._print_worker = PrintWorker(url, data, self)
        self._print_worker.result.connect(self._on_print_result)
        self._print_worker.finished.connect(self._worker_finished)
        self._print_worker.start()

    def _on_print_result(self, ok, message):
        if ok:
            self.status.setText(message)
            QMessageBox.information(self, "IPP送信", message + "\n\n無線送信の完了を意味するものではありません。")
        else:
            self.status.setText("IPPエラー: " + message)
            QMessageBox.warning(self, "IPP送信失敗", message)

    def _worker_finished(self):
        self.send_button.setEnabled(True)
        worker = self._print_worker
        self._print_worker = None
        if worker is not None:
            worker.deleteLater()

    def open_help(self, button):
        window = Krita.instance().activeWindow()
        qwin = window.qwindow() if window is not None else None
        if qwin is not None:
            for entry in qwin.menuBar().actions():
                label = entry.text().replace("&", "").strip().lower()
                # objectName is often language-independent; label may be translated.
                object_name = entry.objectName().lower()
                if ("help" in object_name or label in ("help", "ヘルプ", "hilfe", "aide")
                        or label.startswith("ヘルプ")):
                    menu = entry.menu()
                    if menu is not None:
                        menu.popup(button.mapToGlobal(QPoint(0, button.height())))
                        return
        # If Krita's menu bar implementation changes, keep both handbook and
        # About Krita available. Do not silently skip the About dialog.
        menu = QMenu(button)
        for action_id, label in (("help_contents", "Krita Handbook"),
                                 ("help_about_app", "Kritaについて"),
                                 ("help_about_kde", "KDEについて")):
            action = Krita.instance().action(action_id)
            if action is not None:
                menu.addAction(action)
        if not menu.actions():
            menu.addAction("Kritaのヘルプメニューは見つかりませんでした")
        self._help_fallback_menu = menu
        menu.popup(button.mapToGlobal(QPoint(0, button.height())))


def register_docker():
    Krita.instance().addDockWidgetFactory(
        DockWidgetFactory("sstv_toolbox_docker", DockWidgetFactoryBase.DockRight, SSTVToolbox)
    )
