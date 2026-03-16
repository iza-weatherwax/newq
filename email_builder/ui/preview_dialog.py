"""
ui/preview_dialog.py — Exibe o HTML gerado.
Tenta usar QWebEngineView; fallback: abre no navegador do sistema.
"""
from __future__ import annotations

import tempfile
import webbrowser
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class PreviewDialog(QDialog):
    send_requested = pyqtSignal()

    def __init__(self, html: str, parent=None) -> None:
        super().__init__(parent)
        self._html = html
        self.setWindowTitle("Preview HTML")
        self.resize(700, 600)
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)

        # Tenta QWebEngineView
        web_view = self._try_webengine()
        if web_view is not None:
            lay.addWidget(web_view, 1)
        else:
            info = QLabel("QWebEngineView não disponível. Use 'Abrir no navegador' para visualizar.")
            info.setStyleSheet("color: #888; font-size: 11px;")
            lay.addWidget(info)

            # Fallback: mostra HTML bruto editável
            txt = QTextEdit()
            txt.setPlainText(self._html)
            txt.setReadOnly(True)
            lay.addWidget(txt, 1)

        # Botões
        btn_browser = QPushButton("Abrir no navegador")
        btn_browser.clicked.connect(self._open_browser)

        btn_send = QPushButton("Enviar para Outlook…")
        btn_send.clicked.connect(self._on_send)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_browser)
        btn_row.addStretch()
        btn_row.addWidget(btn_send)
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

    def _try_webengine(self):
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            view = QWebEngineView()
            view.setHtml(self._html)
            return view
        except ImportError:
            return None

    def _open_browser(self) -> None:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        )
        tmp.write(self._html)
        tmp.close()
        webbrowser.open(f"file://{tmp.name}")

    def _on_send(self) -> None:
        self.send_requested.emit()
        self.accept()
