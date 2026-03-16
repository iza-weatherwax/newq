"""
ui/properties_panel.py — Painel direito: edita o bloco selecionado no canvas.
Emite block_changed(BlockConfig) ao modificar qualquer campo.
"""
from __future__ import annotations

import copy

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from email_builder.models import BlockConfig, DataBlock

_CHART_TYPES = {"chart_bar", "chart_barh", "chart_line", "chart_pie"}
_DATA_TYPES = {"kpi", "table"} | _CHART_TYPES


class PropertiesPanel(QScrollArea):
    block_changed = pyqtSignal(object)  # emite BlockConfig

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._config: BlockConfig | None = None
        self._data_blocks: list[DataBlock] = []
        self._updating = False  # guard contra loops de sinal

        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._lay = QVBoxLayout(container)
        self._lay.setContentsMargins(8, 8, 8, 8)
        self._lay.setSpacing(8)
        self.setWidget(container)

        self._placeholder = QLabel("Selecione um bloco\npara editar suas propriedades.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #999;")
        self._lay.addWidget(self._placeholder)
        self._lay.addStretch()

        self._form_widget: QWidget | None = None

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def load_block(self, config: BlockConfig) -> None:
        self._config = copy.deepcopy(config)
        self._rebuild_form()

    def clear(self) -> None:
        self._config = None
        self._rebuild_form()

    def set_available_data_blocks(self, blocks: list[DataBlock]) -> None:
        self._data_blocks = blocks
        if self._config:
            self._rebuild_form()

    # ------------------------------------------------------------------ #
    # Construção do formulário
    # ------------------------------------------------------------------ #

    def _rebuild_form(self) -> None:
        # Remove formulário anterior
        if self._form_widget:
            self._lay.removeWidget(self._form_widget)
            self._form_widget.deleteLater()
            self._form_widget = None

        self._placeholder.setVisible(self._config is None)

        if self._config is None:
            return

        cfg = self._config
        self._form_widget = QWidget()
        form = QFormLayout(self._form_widget)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Título
        self._edit_title = QLineEdit(cfg.title)
        self._edit_title.textChanged.connect(self._on_title_changed)
        form.addRow("Título:", self._edit_title)

        # Tamanho da fonte
        self._spin_font = QSpinBox()
        self._spin_font.setRange(8, 48)
        self._spin_font.setValue(cfg.font_size)
        self._spin_font.valueChanged.connect(self._on_font_size_changed)
        form.addRow("Fonte (px):", self._spin_font)

        # Cor de fundo
        self._btn_bg = _ColorButton(cfg.bg_color)
        self._btn_bg.color_changed.connect(self._on_bg_changed)
        form.addRow("Fundo:", self._btn_bg)

        # Cor do cabeçalho
        self._btn_hdr = _ColorButton(cfg.header_color)
        self._btn_hdr.color_changed.connect(self._on_hdr_changed)
        form.addRow("Cabeçalho:", self._btn_hdr)

        # Cor do texto
        self._btn_txt = _ColorButton(cfg.text_color)
        self._btn_txt.color_changed.connect(self._on_txt_changed)
        form.addRow("Texto:", self._btn_txt)

        # DataBlock vinculado (apenas para tipos de dados)
        if cfg.block_type in _DATA_TYPES:
            self._combo_data = QComboBox()
            self._combo_data.addItem("(nenhum)", None)
            for db in self._data_blocks:
                if self._is_compatible(cfg.block_type, db.block_type):
                    self._combo_data.addItem(f"[{db.block_type}] {db.title}", db.block_id)
            # Selecionar atual
            idx = self._combo_data.findData(cfg.data_block_id)
            if idx >= 0:
                self._combo_data.setCurrentIndex(idx)
            self._combo_data.currentIndexChanged.connect(self._on_data_block_changed)
            form.addRow("DataBlock:", self._combo_data)

        # Texto livre (somente para bloco text)
        if cfg.block_type == "text":
            self._edit_body = QTextEdit(cfg.text_body)
            self._edit_body.setMaximumHeight(100)
            self._edit_body.textChanged.connect(self._on_body_changed)
            form.addRow("Conteúdo:", self._edit_body)

        self._lay.insertWidget(1, self._form_widget)

    @staticmethod
    def _is_compatible(block_type: str, data_type: str) -> bool:
        if block_type == "kpi" and data_type == "kpi":
            return True
        if block_type == "table" and data_type == "table":
            return True
        if block_type in _CHART_TYPES and data_type in _CHART_TYPES:
            return True
        return False

    # ------------------------------------------------------------------ #
    # Slots de mudança de campo
    # ------------------------------------------------------------------ #

    def _emit(self) -> None:
        if not self._updating and self._config:
            self.block_changed.emit(self._config)

    def _on_title_changed(self, val: str) -> None:
        if self._config:
            self._config.title = val
            self._emit()

    def _on_font_size_changed(self, val: int) -> None:
        if self._config:
            self._config.font_size = val
            self._emit()

    def _on_bg_changed(self, color: str) -> None:
        if self._config:
            self._config.bg_color = color
            self._emit()

    def _on_hdr_changed(self, color: str) -> None:
        if self._config:
            self._config.header_color = color
            self._emit()

    def _on_txt_changed(self, color: str) -> None:
        if self._config:
            self._config.text_color = color
            self._emit()

    def _on_data_block_changed(self, _idx: int) -> None:
        if self._config:
            self._config.data_block_id = self._combo_data.currentData()
            self._emit()

    def _on_body_changed(self) -> None:
        if self._config:
            self._config.text_body = self._edit_body.toPlainText()
            self._emit()


class _ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedHeight(28)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ background: {self._color}; border: 1px solid #999; border-radius: 3px; }}"
        )
        self.setText(self._color)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(QColor(self._color), self, "Escolher cor")
        if c.isValid():
            self._color = c.name()
            self._update_style()
            self.color_changed.emit(self._color)
