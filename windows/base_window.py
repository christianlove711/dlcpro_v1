from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class AuxiliaryWindow(QMainWindow):
    def closeEvent(self, event) -> None:  # noqa: N802
        self.hide()
        event.ignore()


class PlaceholderWindow(AuxiliaryWindow):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.resize(860, 700)
        self.setWindowTitle(title)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)

        label = QLabel(title, central)
        label.setObjectName("PageTitle")
        body = QLabel("Reserved for future development.", central)
        body.setObjectName("PlaceholderBody")
        body.setAlignment(Qt.AlignCenter)
        body.setWordWrap(True)

        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(body)
        layout.addStretch(1)

        self.setCentralWidget(central)
