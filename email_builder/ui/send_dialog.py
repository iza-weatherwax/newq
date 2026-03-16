"""
ui/send_dialog.py — Diálogo pré-envio: assunto, destinatários opcionais e opção
de abrir rascunho no Outlook após criar.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class SendDialog(QDialog):
    def __init__(self, html: str, parent=None) -> None:
        super().__init__(parent)
        self._html = html
        self.setWindowTitle("Enviar para Outlook")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)

        # Verificação imediata de disponibilidade
        from email_builder.outlook.sender import check_available
        ok, err = check_available()
        if not ok:
            lay.addWidget(QLabel(f"Aviso: {err}"))
            lay.addWidget(QLabel("O rascunho não poderá ser criado no Outlook."))

        form = QFormLayout()

        self.edit_subject = QLineEdit()
        self.edit_subject.setPlaceholderText("Assunto do email")
        form.addRow("Assunto:", self.edit_subject)

        self.edit_recipients = QLineEdit()
        self.edit_recipients.setPlaceholderText("email1@ex.com; email2@ex.com  (opcional)")
        form.addRow("Destinatários:", self.edit_recipients)

        self.chk_open = QCheckBox("Abrir rascunho no Outlook após criar")
        self.chk_open.setChecked(True)

        lay.addLayout(form)
        lay.addWidget(self.chk_open)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_send)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_send(self) -> None:
        from email_builder.outlook.sender import create_draft

        subject = self.edit_subject.text().strip() or "(sem assunto)"
        raw_recipients = self.edit_recipients.text()
        recipients = [r.strip() for r in raw_recipients.split(";") if r.strip()]
        open_after = self.chk_open.isChecked()

        ok, err = create_draft(subject, self._html, recipients, open_after)
        if ok:
            QMessageBox.information(self, "Sucesso", "Rascunho criado na pasta Rascunhos do Outlook.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro ao criar rascunho", err)
