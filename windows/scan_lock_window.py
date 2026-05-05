from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from widgets.scan_lock.lock_panel import LockSettingsPanel
from widgets.scan_lock.sc_panel import ScanControlPanel
from windows.base_window import AuxiliaryWindow


class ScanLockWindow(AuxiliaryWindow):
    def __init__(self, page: QWidget) -> None:
        super().__init__()
        self.resize(860, 620)
        self.setCentralWidget(page)


def build_scan_lock_page(owner) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(16, 16, 16, 16)
    content_layout.setSpacing(14)

    owner.scan_lock_group = QGroupBox()
    group_layout = QVBoxLayout(owner.scan_lock_group)
    group_layout.setContentsMargins(12, 12, 12, 12)
    group_layout.setSpacing(12)

    owner.scan_lock_page_title = QLabel()
    owner.scan_lock_page_title.setObjectName("PageTitle")
    group_layout.addWidget(owner.scan_lock_page_title)

    owner.scan_lock_sc_panel = ScanControlPanel(owner)
    owner.scan_lock_sc_panel.bind_to(owner)
    group_layout.addWidget(owner.scan_lock_sc_panel)

    owner.lock_settings_panel = LockSettingsPanel(owner)
    owner.lock_settings_panel.bind_to(owner)
    group_layout.addWidget(owner.lock_settings_panel)
    group_layout.addStretch(1)

    content_layout.addWidget(owner.scan_lock_group)
    scroll_area.setWidget(content)
    layout.addWidget(scroll_area)
    return page
