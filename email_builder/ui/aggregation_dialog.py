"""
ui/aggregation_dialog.py — Diálogo para criar DataBlocks a partir de um DataFrame.
Emite blocks_updated(list[DataBlock]) ao confirmar.
"""
from __future__ import annotations

import pandas as pd
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from email_builder.data_engine.aggregator import AggOp, DataAggregator
from email_builder.models import DataBlock


_BLOCK_TYPES = [
    ("KPI — Valor único", "kpi"),
    ("Tabela", "table"),
    ("Gráfico de Barras", "chart_bar"),
    ("Gráfico de Barras Horizontais", "chart_barh"),
    ("Gráfico de Linha", "chart_line"),
    ("Gráfico de Pizza", "chart_pie"),
]

_AGG_OPS = [(op.value, op) for op in AggOp if op != AggOp.NONE]


class AggregationDialog(QDialog):
    blocks_updated = pyqtSignal(list)

    def __init__(
        self,
        sheets: dict[str, pd.DataFrame],
        source_file: str,
        source_hash: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.sheets = sheets
        self.source_file = source_file
        self.source_hash = source_hash
        self._created_blocks: list[DataBlock] = []
        self._aggregator = DataAggregator()

        self.setWindowTitle("Criar Agregações")
        self.resize(900, 600)
        self._build_ui()
        self._populate_sheets()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        main = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main.addWidget(splitter)

        # Painel esquerdo — configuração
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(8, 8, 8, 8)

        # Sheet + tipo de bloco
        form = QFormLayout()
        self.combo_sheet = QComboBox()
        self.combo_sheet.currentTextChanged.connect(self._on_sheet_changed)
        form.addRow("Aba (sheet):", self.combo_sheet)

        self.combo_block_type = QComboBox()
        for label, val in _BLOCK_TYPES:
            self.combo_block_type.addItem(label, val)
        self.combo_block_type.currentIndexChanged.connect(self._on_block_type_changed)
        form.addRow("Tipo de bloco:", self.combo_block_type)

        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Título do bloco")
        form.addRow("Título:", self.edit_title)

        left_lay.addLayout(form)

        # Configuração específica por tipo
        self.grp_kpi = self._build_kpi_group()
        self.grp_table = self._build_table_group()
        self.grp_chart = self._build_chart_group()

        left_lay.addWidget(self.grp_kpi)
        left_lay.addWidget(self.grp_table)
        left_lay.addWidget(self.grp_chart)
        left_lay.addStretch()

        btn_add = QPushButton("Adicionar bloco →")
        btn_add.clicked.connect(self._on_add_block)
        left_lay.addWidget(btn_add)

        # Painel direito — blocos criados + preview
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 8, 8, 8)

        right_lay.addWidget(QLabel("Blocos criados:"))
        self.list_blocks = QListWidget()
        self.list_blocks.setMaximumHeight(160)
        btn_remove = QPushButton("Remover selecionado")
        btn_remove.clicked.connect(self._on_remove_block)
        right_lay.addWidget(self.list_blocks)
        right_lay.addWidget(btn_remove)

        right_lay.addWidget(QLabel("Preview dos dados:"))
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_lay.addWidget(self.preview_table)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([420, 480])

        # Botões OK / Cancelar
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

        # Ajuste de layout
        wrapper = QVBoxLayout()
        wrapper.addWidget(splitter)
        wrapper.addWidget(btns)
        # Remontar layout corretamente
        container = QWidget()
        container.setLayout(wrapper)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)

        self._on_block_type_changed(0)

    def _build_kpi_group(self) -> QGroupBox:
        grp = QGroupBox("Configuração KPI")
        f = QFormLayout(grp)
        self.combo_kpi_column = QComboBox()
        f.addRow("Coluna:", self.combo_kpi_column)
        self.combo_kpi_op = QComboBox()
        for label, val in _AGG_OPS:
            self.combo_kpi_op.addItem(label, val)
        f.addRow("Operação:", self.combo_kpi_op)
        self.edit_kpi_format = QLineEdit("{:,.0f}")
        f.addRow("Formato:", self.edit_kpi_format)
        return grp

    def _build_table_group(self) -> QGroupBox:
        grp = QGroupBox("Configuração Tabela")
        f = QFormLayout(grp)
        self.combo_table_groupby = QComboBox()
        self.combo_table_groupby.addItem("(sem agrupamento)", None)
        f.addRow("Agrupar por:", self.combo_table_groupby)
        self.combo_table_op = QComboBox()
        self.combo_table_op.addItem("(sem agregação)", AggOp.NONE)
        for label, val in _AGG_OPS:
            self.combo_table_op.addItem(label, val)
        f.addRow("Operação:", self.combo_table_op)
        return grp

    def _build_chart_group(self) -> QGroupBox:
        grp = QGroupBox("Configuração Gráfico")
        f = QFormLayout(grp)
        self.combo_chart_x = QComboBox()
        f.addRow("Eixo X:", self.combo_chart_x)
        self.combo_chart_y = QComboBox()
        f.addRow("Eixo Y:", self.combo_chart_y)
        self.combo_chart_op = QComboBox()
        self.combo_chart_op.addItem("(sem agregação)", AggOp.NONE)
        for label, val in _AGG_OPS:
            self.combo_chart_op.addItem(label, val)
        f.addRow("Operação:", self.combo_chart_op)
        return grp

    # ------------------------------------------------------------------ #
    # Slots internos
    # ------------------------------------------------------------------ #

    def _populate_sheets(self) -> None:
        for name in self.sheets:
            self.combo_sheet.addItem(name)
        if self.sheets:
            self._on_sheet_changed(self.combo_sheet.currentText())

    def _on_sheet_changed(self, sheet_name: str) -> None:
        df = self.sheets.get(sheet_name, pd.DataFrame())
        cols = list(df.columns)

        for combo in (
            self.combo_kpi_column,
            self.combo_table_groupby,
            self.combo_chart_x,
            self.combo_chart_y,
        ):
            combo.blockSignals(True)
            combo.clear()

        self.combo_kpi_column.addItems(cols)
        self.combo_table_groupby.addItem("(sem agrupamento)", None)
        self.combo_table_groupby.addItems(cols)
        self.combo_chart_x.addItems(cols)
        self.combo_chart_y.addItems(cols)

        for combo in (
            self.combo_kpi_column,
            self.combo_table_groupby,
            self.combo_chart_x,
            self.combo_chart_y,
        ):
            combo.blockSignals(False)

        self._update_preview(df)

    def _on_block_type_changed(self, _idx: int) -> None:
        block_type = self.combo_block_type.currentData()
        self.grp_kpi.setVisible(block_type == "kpi")
        self.grp_table.setVisible(block_type == "table")
        self.grp_chart.setVisible(block_type in {"chart_bar", "chart_barh", "chart_line", "chart_pie"})

    def _on_add_block(self) -> None:
        sheet_name = self.combo_sheet.currentText()
        df = self.sheets.get(sheet_name, pd.DataFrame())
        block_type = self.combo_block_type.currentData()
        title = self.edit_title.text().strip() or block_type.upper()

        config = self._build_config(block_type, title)
        try:
            block = self._aggregator.create_block(
                block_type, df, config,
                source_file=self.source_file,
                source_hash=self.source_hash,
            )
            self._created_blocks.append(block)
            item = QListWidgetItem(f"[{block_type}] {title}")
            item.setData(Qt.ItemDataRole.UserRole, block.block_id)
            self.list_blocks.addItem(item)

            # Preview do resultado
            if isinstance(block.data, pd.DataFrame):
                self._update_preview(block.data)
            elif isinstance(block.data, dict) and "df" in block.data:
                self._update_preview(block.data["df"])
            else:
                val = block.data.get("formatted", str(block.data.get("value", "")))
                self._show_kpi_preview(title, val)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao criar bloco", str(exc))

    def _on_remove_block(self) -> None:
        row = self.list_blocks.currentRow()
        if row < 0:
            return
        item = self.list_blocks.takeItem(row)
        block_id = item.data(Qt.ItemDataRole.UserRole)
        self._created_blocks = [b for b in self._created_blocks if b.block_id != block_id]

    def _on_accept(self) -> None:
        if not self._created_blocks:
            QMessageBox.warning(self, "Nenhum bloco", "Adicione ao menos um bloco antes de confirmar.")
            return
        self.blocks_updated.emit(self._created_blocks)
        self.accept()

    def _build_config(self, block_type: str, title: str) -> dict:
        if block_type == "kpi":
            return {
                "title": title,
                "label": title,
                "column": self.combo_kpi_column.currentText(),
                "operation": self.combo_kpi_op.currentData().value,
                "format": self.edit_kpi_format.text() or "{:,.0f}",
            }
        if block_type == "table":
            gb = self.combo_table_groupby.currentData()
            return {
                "title": title,
                "group_by": gb,
                "operation": self.combo_table_op.currentData().value,
                "max_rows": 50,
            }
        # chart_*
        return {
            "title": title,
            "chart_type": block_type.replace("chart_", ""),
            "x": self.combo_chart_x.currentText(),
            "y": self.combo_chart_y.currentText(),
            "operation": self.combo_chart_op.currentData().value,
        }

    def _update_preview(self, df: pd.DataFrame) -> None:
        df = df.head(20)
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r, row in enumerate(df.itertuples(index=False)):
            for c, val in enumerate(row):
                self.preview_table.setItem(r, c, QTableWidgetItem(str(val)))
        self.preview_table.resizeColumnsToContents()

    def _show_kpi_preview(self, label: str, value: str) -> None:
        self.preview_table.setRowCount(1)
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Label", "Valor"])
        self.preview_table.setItem(0, 0, QTableWidgetItem(label))
        self.preview_table.setItem(0, 1, QTableWidgetItem(value))
