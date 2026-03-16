"""
ui/canvas.py — Área central: drop zone que hospeda BlockItems.
Snap de grid (20px), linha guia de 600px, gestão de seleção.
"""
from __future__ import annotations

import json
from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QUndoStack
from PyQt6.QtWidgets import QScrollArea, QWidget

from email_builder.config.settings import AppSettings
from email_builder.models import BlockConfig
from email_builder.ui.palette_panel import MIME_TYPE
from email_builder.ui.block_item import BlockItem, _snap, GRID

CANVAS_W = 800
CANVAS_H = 2400
GUIDE_X = 600   # largura máxima do email


class CanvasSurface(QScrollArea):
    block_selected = pyqtSignal(object)    # emite BlockConfig
    selection_cleared = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._blocks: list[BlockItem] = []
        self._selected: Optional[BlockItem] = None

        self._surface = _Surface(self)
        self.setWidget(self._surface)
        self.setWidgetResizable(False)
        self.setAcceptDrops(True)
        self.setStyleSheet("background: #e8e8e8;")

        # QUndoStack (conectado à MainWindow depois)
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(settings.undo_limit)

        # Notificar main window
        if parent and hasattr(parent, "set_undo_stack"):
            parent.set_undo_stack(self.undo_stack)

    # ------------------------------------------------------------------ #
    # Drag-and-drop
    # ------------------------------------------------------------------ #

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasFormat(MIME_TYPE):
            event.ignore()
            return
        raw = bytes(event.mimeData().data(MIME_TYPE)).decode()
        payload = json.loads(raw)
        block_type = payload.get("block_type", "text")

        pos = self._surface.mapFrom(self, event.position().toPoint())
        x = max(0, _snap(pos.x(), GRID))
        y = max(0, _snap(pos.y(), GRID))

        config = BlockConfig(
            block_id=BlockConfig.new_id(),
            block_type=block_type,
            title=block_type.upper(),
            pos={"x": x, "y": y},
            size={"w": 200, "h": 120},
        )
        from email_builder.ui.canvas_commands import AddBlockCommand
        cmd = AddBlockCommand(self, config)
        self.undo_stack.push(cmd)
        event.acceptProposedAction()

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def _add_block(self, config: BlockConfig) -> BlockItem:
        item = BlockItem(config, self._surface)
        item.clicked.connect(self._select)
        item.delete_requested.connect(self._on_delete_requested)
        item.moved.connect(self._on_moved)
        item.resized.connect(self._on_resized)
        self._blocks.append(item)
        item.show()
        self._surface.update()
        return item

    def _remove_block(self, item: BlockItem) -> None:
        if item in self._blocks:
            self._blocks.remove(item)
        if self._selected is item:
            self._selected = None
            self.selection_cleared.emit()
        item.hide()
        item.setParent(None)
        self._surface.update()

    def add_block_from_config(self, config: BlockConfig) -> BlockItem:
        return self._add_block(config)

    def update_block_config(self, config: BlockConfig) -> None:
        for item in self._blocks:
            if item.config.block_id == config.block_id:
                item.update_from_config(config)
                break

    def clear_all(self) -> None:
        for item in list(self._blocks):
            item.hide()
            item.setParent(None)
        self._blocks.clear()
        self._selected = None
        self.undo_stack.clear()
        self._surface.update()

    def has_blocks(self) -> bool:
        return bool(self._blocks)

    def get_all_configs(self) -> list[BlockConfig]:
        return [item.config for item in self._blocks]

    # ------------------------------------------------------------------ #
    # Seleção
    # ------------------------------------------------------------------ #

    def _select(self, item: BlockItem) -> None:
        if self._selected and self._selected is not item:
            self._selected.set_selected(False)
        self._selected = item
        item.set_selected(True)
        self.block_selected.emit(item.config)

    def _deselect_all(self) -> None:
        if self._selected:
            self._selected.set_selected(False)
            self._selected = None
        self.selection_cleared.emit()

    # ------------------------------------------------------------------ #
    # Slots de bloco
    # ------------------------------------------------------------------ #

    def _on_delete_requested(self, item: BlockItem) -> None:
        from email_builder.ui.canvas_commands import DeleteBlockCommand
        cmd = DeleteBlockCommand(self, item.config)
        self.undo_stack.push(cmd)

    def _on_moved(self, item: BlockItem) -> None:
        pass  # config já atualizado no mouseMoveEvent

    def _on_resized(self, item: BlockItem) -> None:
        pass  # config já atualizado no resizeEvent

    def mousePressEvent(self, event) -> None:
        # Clique no fundo do canvas → desseleciona
        hit = self._surface.childAt(self._surface.mapFrom(self, event.pos()))
        if hit is None or hit is self._surface:
            self._deselect_all()
        super().mousePressEvent(event)


class _Surface(QWidget):
    """Widget filho do QScrollArea — faz o desenho de fundo e guias."""

    def __init__(self, parent: CanvasSurface) -> None:
        super().__init__(parent)
        self.setFixedSize(CANVAS_W, CANVAS_H)
        self.setAcceptDrops(False)
        self.setStyleSheet("background: white;")

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)

        # Grid de pontos
        dot_color = QColor("#e0e0e0")
        for x in range(0, CANVAS_W, GRID):
            for y in range(0, CANVAS_H, GRID):
                p.fillRect(x, y, 1, 1, dot_color)

        # Linha guia de 600px (limite de email)
        pen = QPen(QColor("#4285f4"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(GUIDE_X, 0, GUIDE_X, CANVAS_H)

        p.end()
