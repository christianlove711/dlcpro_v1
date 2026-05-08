from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from widgets.scan_lock.lock_panel import LockSettingsPanel
from widgets.scan_lock.pid_panel import PidPanel
from widgets.scan_lock.sc_panel import ScanControlPanel
from windows.base_window import AuxiliaryWindow


class ScanLockWindow(AuxiliaryWindow):
    def __init__(self, page: QWidget) -> None:
        super().__init__()
        self.resize(980, 1180)
        self.setCentralWidget(page)


def build_scan_lock_page(owner) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    scroll_area = QScrollArea()
    owner.scan_lock_scroll_area = scroll_area
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

    owner.pid1_panel = PidPanel(owner, "pid1", "pid1_section")
    owner.pid1_panel.bind_to(owner)
    group_layout.addWidget(owner.pid1_panel)

    owner.pid2_panel = PidPanel(owner, "pid2", "pid2_section")
    owner.pid2_panel.bind_to(owner)
    group_layout.addWidget(owner.pid2_panel)
    owner._register_module_precision_targets(
        "sc",
        owner.scan_amplitude_spin,
        owner.scan_amplitude_spin,
        owner.scan_offset_spin,
        owner.scan_frequency_spin,
    )
    owner._register_module_precision_targets(
        "pid",
        owner.pid1_gain_spin,
        owner.pid1_gain_spin,
        owner.pid1_p_spin,
        owner.pid1_i_spin,
        owner.pid1_d_spin,
        owner.pid1_i_cutoff_spin,
        owner.pid1_limit_spin,
        owner.pid2_gain_spin,
        owner.pid2_p_spin,
        owner.pid2_i_spin,
        owner.pid2_d_spin,
        owner.pid2_limit_spin,
    )
    group_layout.addStretch(1)

    content_layout.addWidget(owner.scan_lock_group)
    scroll_area.setWidget(content)
    layout.addWidget(scroll_area)
    return page
