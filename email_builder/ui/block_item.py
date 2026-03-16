"""
ui/block_item.py — Widget arrastável e redimensionável que representa um bloco no canvas.
Comportamentos divididos em mixins para manutenibilidade.
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QCursor
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from email_builder.models import BlockConfig

MIN_W = 120
MIN_H = 60
GRID = 20          # snap de posição
COL_SNAPS = [0, 200, 300, 400, 600]   # snap de largura (frações de 600px)


def _nearest_col_snap(w: int) -> int:
    """Encontra a largura mais próxima nos col snaps (distância mínima)."""
    candidates = []
    for i in range(len(COL_SNAPS) - 1):
        candidates.append(COL_SNAPS[i + 1] - COL_SNAPS[i])
    # larguras válidas: diferenças entre breakpoints
    valid_widths = [200, 300, 400, 600, 100]  # 1/3, 1/2, 2/3, full, min
    return min(valid_widths, key=lambda v: abs(v - w))


def _snap(value: int, step: int) -> int:
    return round(value / step) * step


class BlockItem(QFrame):
    clicked = pyqtSignal(object)          # emite self
    delete_requested = pyqtSignal(object) # emite self
    moved = pyqtSignal(object)            # emite self após move
    resized = pyqtSignal(object)          # emite self após resize

    def __init__(self, config: BlockConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._selected = False
        self._drag_offset = QPoint()
        self._dragging = False

        self.setFixedSize(config.size["w"], config.size["h"])
        self.move(config.pos["x"], config.pos["y"])
        self.setFrameShape(QFrame.Shape.Box)
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setAcceptDrops(False)

        self._build_ui()
        self._apply_style()

    # ------------------------------------------------------------------ #
    # Construção interna
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setFixedHeight(28)
        hdr_lay = QHBoxLayout(self._header)
        hdr_lay.setContentsMargins(6, 2, 2, 2)

        self._title_label = QLabel(self.config.title or self.config.block_type.upper())
        self._title_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        hdr_lay.addWidget(self._title_label, 1)

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(20, 20)
        btn_del.setStyleSheet(
            "QPushButton { background: transparent; color: white; border: none; font-size: 11px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.3); border-radius: 3px; }"
        )
        btn_del.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        hdr_lay.addWidget(btn_del)
        outer.addWidget(self._header)

        # Body
        self._body = QWidget()
        self._body_label = QLabel(self._body_text())
        self._body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body_label.setWordWrap(True)
        self._body_label.setStyleSheet(f"color: {self.config.text_color}; font-size: {self.config.font_size}px;")
        body_lay = QVBoxLayout(self._body)
        body_lay.addWidget(self._body_label)
        outer.addWidget(self._body, 1)

        # Resize grip
        grip_row = QWidget()
        grip_lay = QHBoxLayout(grip_row)
        grip_lay.setContentsMargins(0, 0, 0, 0)
        grip_lay.addStretch()
        self._grip = QSizeGrip(self)
        grip_lay.addWidget(self._grip)
        outer.addWidget(grip_row)

    def _body_text(self) -> str:
        bt = self.config.block_type
        if bt == "text":
            return self.config.text_body or "(texto)"
        if bt == "kpi":
            return "[ KPI ]"
        if bt == "table":
            return "[ TABELA ]"
        if bt.startswith("chart"):
            return f"[ {bt.replace('chart_', '').upper()} ]"
        if bt == "divider":
            return "─────────"
        if bt == "spacer":
            return ""
        return f"[ {bt.upper()} ]"

    def _apply_style(self) -> None:
        self._header.setStyleSheet(f"background: {self.config.header_color}; border-radius: 3px 3px 0 0;")
        self._body.setStyleSheet(f"background: {self.config.bg_color};")
        if self._selected:
            self.setStyleSheet("QFrame { border: 2px solid #4285f4; border-radius: 4px; }")
        else:
            self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; }")

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def update_from_config(self, config: BlockConfig) -> None:
        self.config = config
        self._title_label.setText(config.title or config.block_type.upper())
        self._body_label.setText(self._body_text())
        self._body_label.setStyleSheet(
            f"color: {config.text_color}; font-size: {config.font_size}px;"
        )
        self._apply_style()

    # ------------------------------------------------------------------ #
    # Mouse — drag dentro do canvas
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.pos()
            self._dragging = True
            self.clicked.emit(self)
            self.raise_()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = self.mapToParent(event.pos() - self._drag_offset)
            x = max(0, _snap(new_pos.x(), GRID))
            y = max(0, _snap(new_pos.y(), GRID))
            self.move(x, y)
            self.config.pos = {"x": x, "y": y}
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging:
            self._dragging = False
            self.moved.emit(self)
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------ #
    # Resize — intercept QSizeGrip para aplicar snap
    # ------------------------------------------------------------------ #

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = max(MIN_W, self.width())
        h = max(MIN_H, self.height())
        if w != self.width() or h != self.height():
            self.setFixedSize(w, h)
        self.config.size = {"w": self.width(), "h": self.height()}
        self.resized.emit(self)
