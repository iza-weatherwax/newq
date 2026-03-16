"""
main.py — Entry point do Email Builder.
"""
import sys

from PyQt6.QtWidgets import QApplication

from email_builder.config.settings import AppSettings
from email_builder.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Email Builder")
    app.setOrganizationName("EmailBuilder")

    # Estilo global
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow { background: #f5f5f5; }
        QSplitter::handle { background: #ddd; width: 2px; }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; }
        QPushButton {
            padding: 4px 12px;
            border: 1px solid #bbb;
            border-radius: 3px;
            background: #fff;
        }
        QPushButton:hover { background: #e8f0fe; border-color: #4285f4; }
        QPushButton:pressed { background: #c8d8fc; }
    """)

    settings = AppSettings.load()
    window = MainWindow(settings)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
