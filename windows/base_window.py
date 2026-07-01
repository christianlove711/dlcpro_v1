from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QScrollArea, QVBoxLayout, QWidget


class AuxiliaryWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shutdown_requested = False

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._shutdown_requested:
            event.accept()
            return
        self.hide()
        event.ignore()

    def request_shutdown(self) -> None:
        self._shutdown_requested = True


def set_scrollable_central_widget(window: QMainWindow, content: QWidget) -> QScrollArea:
    scroll = QScrollArea(window)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setWidget(content)
    window.setCentralWidget(scroll)
    return scroll


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
