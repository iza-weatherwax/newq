"""
ui/palette_panel.py — Painel esquerdo com lista de tipos de bloco (drag source).
MIME: application/x-email-block → {"block_type": "<tipo>"}
"""
from __future__ import annotations

import json

from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


BLOCK_DEFINITIONS = [
    ("KPI", "kpi", "#4285f4"),
    ("Tabela", "table", "#34a853"),
    ("Barras Verticais", "chart_bar", "#ea4335"),
    ("Barras Horizontais", "chart_barh", "#ea4335"),
    ("Linha", "chart_line", "#fbbc04"),
    ("Pizza", "chart_pie", "#ff6d00"),
    ("Texto", "text", "#9e9e9e"),
    ("Divisor", "divider", "#757575"),
    ("Espaço", "spacer", "#bdbdbd"),
]

MIME_TYPE = "application/x-email-block"


class _DraggableList(QListWidget):
    def startDrag(self, supported_actions) -> None:
        item = self.currentItem()
        if not item:
            return
        block_type = item.data(Qt.ItemDataRole.UserRole)
        payload = json.dumps({"block_type": block_type}).encode()

        mime = QMimeData()
        mime.setData(MIME_TYPE, payload)

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class PalettePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(160)
        self.setMaximumWidth(220)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Blocos")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        title.setFont(font)
        layout.addWidget(title)

        hint = QLabel("Arraste para o canvas →")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.list_widget = _DraggableList()
        self.list_widget.setDragEnabled(True)
        self.list_widget.setDefaultDropAction(Qt.DropAction.CopyAction)

        for label, block_type, color in BLOCK_DEFINITIONS:
            item = QListWidgetItem(f"  {label}")
            item.setData(Qt.ItemDataRole.UserRole, block_type)
            item.setForeground(Qt.GlobalColor.black)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)
        layout.addStretch()
