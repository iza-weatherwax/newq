"""
ui/canvas_commands.py — Comandos para QUndoStack (padrão Command).
Cada classe implementa redo() e undo() operando sobre o CanvasSurface.
"""
from __future__ import annotations

from PyQt6.QtGui import QUndoCommand

from email_builder.models import BlockConfig


class AddBlockCommand(QUndoCommand):
    def __init__(self, canvas, config: BlockConfig) -> None:
        super().__init__(f"Adicionar {config.block_type.upper()}")
        self._canvas = canvas
        self._config = config
        self._item = None

    def redo(self) -> None:
        self._item = self._canvas._add_block(self._config)

    def undo(self) -> None:
        if self._item:
            self._canvas._remove_block(self._item)
            self._item = None


class DeleteBlockCommand(QUndoCommand):
    def __init__(self, canvas, config: BlockConfig) -> None:
        super().__init__(f"Deletar {config.block_type.upper()}")
        self._canvas = canvas
        self._config = config
        self._item = None

    def redo(self) -> None:
        # Encontra o item pelo block_id e remove
        for item in self._canvas._blocks:
            if item.config.block_id == self._config.block_id:
                self._item = item
                break
        if self._item:
            self._canvas._remove_block(self._item)

    def undo(self) -> None:
        self._item = self._canvas._add_block(self._config)


class MoveBlockCommand(QUndoCommand):
    def __init__(self, canvas, block_id: str, old_pos: dict, new_pos: dict) -> None:
        super().__init__("Mover bloco")
        self._canvas = canvas
        self._block_id = block_id
        self._old_pos = old_pos
        self._new_pos = new_pos

    def redo(self) -> None:
        self._apply(self._new_pos)

    def undo(self) -> None:
        self._apply(self._old_pos)

    def _apply(self, pos: dict) -> None:
        for item in self._canvas._blocks:
            if item.config.block_id == self._block_id:
                item.config.pos = pos
                item.move(pos["x"], pos["y"])
                break


class ResizeBlockCommand(QUndoCommand):
    def __init__(self, canvas, block_id: str, old_size: dict, new_size: dict) -> None:
        super().__init__("Redimensionar bloco")
        self._canvas = canvas
        self._block_id = block_id
        self._old_size = old_size
        self._new_size = new_size

    def redo(self) -> None:
        self._apply(self._new_size)

    def undo(self) -> None:
        self._apply(self._old_size)

    def _apply(self, size: dict) -> None:
        for item in self._canvas._blocks:
            if item.config.block_id == self._block_id:
                item.config.size = size
                item.setFixedSize(size["w"], size["h"])
                break


class UpdateConfigCommand(QUndoCommand):
    def __init__(self, canvas, old_config: BlockConfig, new_config: BlockConfig) -> None:
        super().__init__(f"Editar {new_config.block_type.upper()}")
        self._canvas = canvas
        self._old = old_config
        self._new = new_config

    def redo(self) -> None:
        self._canvas.update_block_config(self._new)

    def undo(self) -> None:
        self._canvas.update_block_config(self._old)
