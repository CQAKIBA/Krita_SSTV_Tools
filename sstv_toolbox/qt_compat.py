"""Shared PyQt 5 / 6 imports and small enum shims.
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO
"""
try:
    from PyQt6.QtCore import Qt, QSettings, QByteArray, QSize, QPoint, QRect, QRectF, QThread, pyqtSignal, QUrl
    from PyQt6.QtGui import QColor, QFont, QFontMetrics, QImage, QImageReader, QPainter, QPen, QGuiApplication, QDesktopServices
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
        QLabel, QPushButton, QLineEdit, QSlider, QScrollArea,
        QFileDialog, QMessageBox, QDialog, QFormLayout, QListWidget,
        QFontComboBox, QSpinBox, QColorDialog, QComboBox, QDialogButtonBox,
        QToolButton, QMenu, QApplication, QCheckBox, QSizeGrip, QDockWidget, QRadioButton,
    )
    QT6 = True
except ImportError:
    from PyQt5.QtCore import Qt, QSettings, QByteArray, QSize, QPoint, QRect, QRectF, QThread, pyqtSignal, QUrl
    from PyQt5.QtGui import QColor, QFont, QFontMetrics, QImage, QImageReader, QPainter, QPen, QGuiApplication, QDesktopServices
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
        QLabel, QPushButton, QLineEdit, QSlider, QScrollArea,
        QFileDialog, QMessageBox, QDialog, QFormLayout, QListWidget,
        QFontComboBox, QSpinBox, QColorDialog, QComboBox, QDialogButtonBox,
        QToolButton, QMenu, QApplication, QCheckBox, QSizeGrip, QDockWidget, QRadioButton,
    )
    QT6 = False

ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter if QT6 else Qt.AlignCenter
ALIGN_HCENTER = Qt.AlignmentFlag.AlignHCenter if QT6 else Qt.AlignHCenter
ALIGN_VCENTER = Qt.AlignmentFlag.AlignVCenter if QT6 else Qt.AlignVCenter
KEEP_ASPECT = Qt.AspectRatioMode.KeepAspectRatio if QT6 else Qt.KeepAspectRatio
SMOOTH = Qt.TransformationMode.SmoothTransformation if QT6 else Qt.SmoothTransformation
HORIZONTAL = Qt.Orientation.Horizontal if QT6 else Qt.Horizontal
FORMAT_ARGB32 = QImage.Format.Format_ARGB32 if QT6 else QImage.Format_ARGB32
COLOR_DIALOG = QColorDialog.ColorDialogOption.ShowAlphaChannel if QT6 else QColorDialog.ShowAlphaChannel
DIALOG_OK = QDialog.DialogCode.Accepted if QT6 else QDialog.Accepted
QUESTION_YES = QMessageBox.StandardButton.Yes if QT6 else QMessageBox.Yes
QUESTION_NO = QMessageBox.StandardButton.No if QT6 else QMessageBox.No

CUSTOM_CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu if QT6 else Qt.CustomContextMenu
