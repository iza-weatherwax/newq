"""
ui/main_window.py — Janela principal do Email Builder.
Layout: QSplitter horizontal com palette | canvas | properties.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QUndoStack
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QWidget,
)

from email_builder.config.settings import AppSettings
from email_builder.layout_manager.manager import (
    empty_layout,
    load_layout,
    save_layout,
)
from email_builder.models import DataBlock, Layout


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.layout_data: Layout = empty_layout()
        self.data_blocks: dict[str, DataBlock] = {}  # data_block_id → DataBlock
        self._current_file: Path | None = None

        self.setWindowTitle("Email Builder")
        self.resize(1280, 800)

        self._build_ui()
        self._build_menu()
        self._build_status_bar()

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        # Importações tardias para evitar ciclos
        from email_builder.ui.palette_panel import PalettePanel
        from email_builder.ui.canvas import CanvasSurface
        from email_builder.ui.properties_panel import PropertiesPanel

        self.palette = PalettePanel(self)
        self.canvas = CanvasSurface(self.settings, self)
        self.properties = PropertiesPanel(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.palette)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.properties)
        splitter.setSizes([200, 780, 300])
        splitter.setStretchFactor(1, 1)  # canvas expande

        self.setCentralWidget(splitter)

        # Conectar sinais
        self.canvas.block_selected.connect(self.properties.load_block)
        self.properties.block_changed.connect(self.canvas.update_block_config)
        self.canvas.selection_cleared.connect(self.properties.clear)

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # --- File ---
        file_menu = mb.addMenu("&Arquivo")

        act_new = QAction("&Novo", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self._on_new)
        file_menu.addAction(act_new)

        act_open_data = QAction("Abrir &Dados…", self)
        act_open_data.setShortcut("Ctrl+O")
        act_open_data.triggered.connect(self._on_open_data)
        file_menu.addAction(act_open_data)

        file_menu.addSeparator()

        act_save = QAction("&Salvar Layout…", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._on_save)
        file_menu.addAction(act_save)

        act_load = QAction("&Carregar Layout…", self)
        act_load.setShortcut("Ctrl+L")
        act_load.triggered.connect(self._on_load)
        file_menu.addAction(act_load)

        file_menu.addSeparator()

        act_exit = QAction("Sai&r", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # --- Edit ---
        edit_menu = mb.addMenu("&Editar")

        self.act_undo = QAction("&Desfazer", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.setEnabled(False)
        edit_menu.addAction(self.act_undo)

        self.act_redo = QAction("&Refazer", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.setEnabled(False)
        edit_menu.addAction(self.act_redo)

        # --- Build ---
        build_menu = mb.addMenu("&Construir")

        act_agg = QAction("Criar Agre&gações…", self)
        act_agg.setShortcut("Ctrl+G")
        act_agg.triggered.connect(self._on_open_aggregation)
        build_menu.addAction(act_agg)

        build_menu.addSeparator()

        act_preview = QAction("&Preview HTML…", self)
        act_preview.setShortcut("Ctrl+P")
        act_preview.triggered.connect(self._on_preview)
        build_menu.addAction(act_preview)

        act_send = QAction("Abrir no &Outlook…", self)
        act_send.setShortcut("Ctrl+Shift+O")
        act_send.triggered.connect(self._on_send)
        build_menu.addAction(act_send)

    def _build_status_bar(self) -> None:
        self.status_label = QLabel("Pronto")
        sb = QStatusBar()
        sb.addWidget(self.status_label)
        self.setStatusBar(sb)

    # ------------------------------------------------------------------ #
    # Integração com QUndoStack (chamado pelo canvas após criação)
    # ------------------------------------------------------------------ #

    def set_undo_stack(self, stack: QUndoStack) -> None:
        self.act_undo.triggered.disconnect() if self.act_undo.receivers(self.act_undo.triggered) else None
        self.act_redo.triggered.disconnect() if self.act_redo.receivers(self.act_redo.triggered) else None
        self.act_undo.triggered.connect(stack.undo)
        self.act_redo.triggered.connect(stack.redo)
        stack.canUndoChanged.connect(self.act_undo.setEnabled)
        stack.canRedoChanged.connect(self.act_redo.setEnabled)
        stack.undoTextChanged.connect(lambda t: self.act_undo.setText(f"Desfazer: {t}" if t else "Desfazer"))
        stack.redoTextChanged.connect(lambda t: self.act_redo.setText(f"Refazer: {t}" if t else "Refazer"))

    # ------------------------------------------------------------------ #
    # Slots de menu
    # ------------------------------------------------------------------ #

    def _on_new(self) -> None:
        if not self._confirm_discard():
            return
        self.canvas.clear_all()
        self.layout_data = empty_layout()
        self.data_blocks.clear()
        self.properties.set_available_data_blocks([])
        self._current_file = None
        self.setWindowTitle("Email Builder")
        self.status_label.setText("Novo layout criado.")

    def _on_open_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir arquivo de dados",
            self.settings.last_open_dir,
            "Planilhas (*.xlsx *.xls *.csv *.tsv);;Todos os arquivos (*)",
        )
        if not path:
            return
        self.settings.last_open_dir = str(Path(path).parent)
        self.settings.save()
        self._load_data_file(path)

    def _load_data_file(self, path: str) -> None:
        from email_builder.data_engine.loader import DataLoader
        from email_builder.ui.aggregation_dialog import AggregationDialog
        try:
            loader = DataLoader(path)
            sheets = loader.load()
            dlg = AggregationDialog(sheets, loader.source_path, loader.source_hash, self)
            dlg.blocks_updated.connect(self._on_blocks_updated)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao carregar dados", str(exc))

    def _on_blocks_updated(self, blocks: list[DataBlock]) -> None:
        for block in blocks:
            self.data_blocks[block.block_id] = block
        self.properties.set_available_data_blocks(list(self.data_blocks.values()))
        self.status_label.setText(f"{len(self.data_blocks)} DataBlock(s) disponíveis.")

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar layout",
            self.settings.last_open_dir,
            "Layout JSON (*.json);;Todos os arquivos (*)",
        )
        if not path:
            return
        try:
            self.layout_data.blocks = self.canvas.get_all_configs()
            save_layout(path, self.layout_data)
            self._current_file = Path(path)
            self.setWindowTitle(f"Email Builder — {self._current_file.name}")
            self.status_label.setText(f"Layout salvo em {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar layout",
            self.settings.last_open_dir,
            "Layout JSON (*.json);;Todos os arquivos (*)",
        )
        if not path:
            return
        try:
            layout = load_layout(path)
            self.canvas.clear_all()
            for block_config in layout.blocks:
                self.canvas.add_block_from_config(block_config)
            self.layout_data = layout
            self._current_file = Path(path)
            self.setWindowTitle(f"Email Builder — {self._current_file.name}")
            self.status_label.setText(f"Layout carregado: {len(layout.blocks)} bloco(s).")
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao carregar layout", str(exc))

    def _on_open_aggregation(self) -> None:
        if not self.data_blocks:
            self._on_open_data()
        else:
            # Reabre com último arquivo carregado, se disponível
            source = self.layout_data.meta.source_file
            if source and Path(source).exists():
                self._load_data_file(source)
            else:
                self._on_open_data()

    def _on_preview(self) -> None:
        from email_builder.html_compiler.compiler import compile_canvas
        from email_builder.html_compiler.validator import validate_layout
        from email_builder.ui.preview_dialog import PreviewDialog

        configs = self.canvas.get_all_configs()
        errors = validate_layout([c.to_dict() for c in configs])
        if errors:
            msgs = "\n".join(f"• {e}" for e in errors)
            QMessageBox.warning(self, "Avisos de validação", msgs)

        try:
            html = compile_canvas([c.to_dict() for c in configs], self.data_blocks)
            dlg = PreviewDialog(html, self)
            dlg.send_requested.connect(self._on_send)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao compilar HTML", str(exc))

    def _on_send(self) -> None:
        from email_builder.html_compiler.compiler import compile_canvas
        from email_builder.html_compiler.validator import validate_layout
        from email_builder.ui.send_dialog import SendDialog

        configs = self.canvas.get_all_configs()
        errors = validate_layout([c.to_dict() for c in configs])
        if errors:
            msgs = "\n".join(f"• {e}" for e in errors)
            if QMessageBox.question(
                self, "Avisos", f"Há avisos:\n{msgs}\n\nContinuar mesmo assim?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            ) == QMessageBox.StandardButton.No:
                return

        try:
            html = compile_canvas([c.to_dict() for c in configs], self.data_blocks)
            dlg = SendDialog(html, self)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao compilar HTML", str(exc))

    # ------------------------------------------------------------------ #
    # Utilitários
    # ------------------------------------------------------------------ #

    def _confirm_discard(self) -> bool:
        if not self.canvas.has_blocks():
            return True
        reply = QMessageBox.question(
            self,
            "Descartar alterações?",
            "O canvas tem blocos. Deseja descartar as alterações?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def closeEvent(self, event) -> None:
        self.settings.save()
        super().closeEvent(event)
