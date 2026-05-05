from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox, QFrame, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from widgets.laser.cc_panel import CcPanel
from widgets.laser.pc_panel import PcPanel
from widgets.laser.tc_panel import TcPanel
from widgets.common_controls import StepTargetSpinBoxRow
from windows.base_window import AuxiliaryWindow


class LaserWindow(AuxiliaryWindow):
    def __init__(self, page: QWidget) -> None:
        super().__init__()
        self.resize(860, 900)
        self.setCentralWidget(page)


def _create_target_row(owner, module: str, spinbox: QDoubleSpinBox) -> StepTargetSpinBoxRow:
    row = StepTargetSpinBoxRow(module, spinbox, owner._select_precision_target)
    owner.module_precision_target_buttons[module].append(row.target_button)
    return row


def build_laser_page(owner) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setObjectName("LaserScrollArea")

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(16, 16, 16, 16)
    content_layout.setSpacing(14)

    owner.laser_group = QGroupBox()
    group_layout = QVBoxLayout(owner.laser_group)
    group_layout.setContentsMargins(12, 12, 12, 12)
    group_layout.setSpacing(12)

    owner.laser_page_title = QLabel()
    owner.laser_page_title.setObjectName("PageTitle")
    group_layout.addWidget(owner.laser_page_title)

    owner.cc_panel = CcPanel(owner)
    owner.cc_panel.bind_to(owner)
    owner.tc_panel = TcPanel(owner)
    owner.tc_panel.bind_to(owner)
    owner.pc_panel = PcPanel(owner)
    owner.pc_panel.bind_to(owner)
    owner._register_module_precision_targets(
        "cc",
        owner.current_set_spin,
        owner.current_set_spin,
        owner.current_clip_spin,
        owner.feedforward_factor_spin,
        owner.arc_factor_spin,
    )
    owner._register_module_precision_targets(
        "tc",
        owner.temp_set_spin,
        owner.temp_set_spin,
        owner.tc_arc_factor_spin,
    )
    owner._register_module_precision_targets(
        "pc",
        owner.pc_voltage_set_spin,
        owner.pc_voltage_set_spin,
        owner.pc_slew_rate_spin,
        owner.pc_arc_factor_spin,
        owner.pressure_comp_factor_spin,
    )
    group_layout.addWidget(owner.cc_panel)
    group_layout.addWidget(owner.tc_panel)
    group_layout.addWidget(owner.pc_panel)
    group_layout.addStretch(1)
    content_layout.addWidget(owner.laser_group)
    scroll_area.setWidget(content)
    layout.addWidget(scroll_area)
    return page
