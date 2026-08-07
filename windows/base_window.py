from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QScrollArea, QWidget


class AuxiliaryWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shutdown_requested = False

    def closeEvent(self, event) -> None:  # noqa: N802
        manager = getattr(self, "_window_layout_manager", None)
        if manager is not None:
            manager.save_window(self)
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
