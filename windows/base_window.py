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

        self.title_label = QLabel(title, central)
        self.title_label.setObjectName("PageTitle")
        self.body_label = QLabel("Reserved for future development.", central)
        self.body_label.setObjectName("PlaceholderBody")
        self.body_label.setAlignment(Qt.AlignCenter)
        self.body_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addStretch(1)
        layout.addWidget(self.body_label)
        layout.addStretch(1)

        self.setCentralWidget(central)
