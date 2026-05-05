from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui_text import TEXT
from widgets.common_controls import PrecisionButtonRow, create_toggle_button


class PcPanel(QFrame):
    EXPORTED_ATTRS = (
        "pc_label",
        "pc_enable_button",
        "pc_precision_label",
        "pc_precision_buttons",
        "pc_voltage_set_label",
        "pc_voltage_set_spin",
        "pc_voltage_act_label",
        "pc_voltage_act_value",
        "pc_slew_rate_enable_label",
        "pc_slew_rate_enable_button",
        "pc_slew_rate_label",
        "pc_slew_rate_spin",
        "pc_arc_label",
        "pc_arc_enable_button",
        "pc_arc_signal_label",
        "pc_arc_signal_combo",
        "pc_arc_factor_label",
        "pc_arc_factor_spin",
        "pressure_comp_label",
        "pressure_comp_enable_label",
        "pressure_comp_enable_button",
        "pressure_comp_air_pressure_label",
        "pressure_comp_air_pressure_value",
        "pressure_comp_factor_label",
        "pressure_comp_factor_spin",
        "pressure_comp_voltage_label",
        "pressure_comp_voltage_value",
    )

    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.pc_label = QLabel()
        self.pc_label.setObjectName("SectionTitle")
        header.addWidget(self.pc_label)
        header.addStretch(1)
        self.pc_enable_button = create_toggle_button(owner._on_pc_enable_toggled)
        header.addWidget(self.pc_enable_button)
        layout.addLayout(header)

        pc_form = QFormLayout()
        pc_form.setLabelAlignment(Qt.AlignLeft)
        pc_form.setFormAlignment(Qt.AlignTop)
        pc_form.setHorizontalSpacing(18)
        pc_form.setVerticalSpacing(14)

        self.pc_voltage_set_label = QLabel()
        self.pc_voltage_set_spin = QDoubleSpinBox()
        self.pc_voltage_set_spin.setRange(-1000000.0, 1000000.0)
        self.pc_voltage_set_spin.setDecimals(6)
        self.pc_voltage_set_spin.setSuffix(f" {TEXT[owner.language]['voltage_unit']}")
        self.pc_voltage_set_spin.setKeyboardTracking(False)
        self.pc_voltage_set_spin.editingFinished.connect(owner._on_pc_voltage_set_finished)

        self.pc_voltage_act_label = QLabel()
        self.pc_voltage_act_value = QLabel()
        self.pc_voltage_act_value.setObjectName("ReadValue")

        self.pc_precision_label = QLabel()
        self.pc_precision_row = PrecisionButtonRow(owner.PRECISION_OPTIONS, owner._set_pc_precision)
        self.pc_precision_buttons = self.pc_precision_row.buttons

        pc_form.addRow(self.pc_precision_label, self.pc_precision_row)
        pc_form.addRow(self.pc_voltage_set_label, owner._create_target_row("pc", self.pc_voltage_set_spin))
        pc_form.addRow(self.pc_voltage_act_label, self.pc_voltage_act_value)
        layout.addLayout(pc_form)

        divider_4 = QFrame()
        divider_4.setFrameShape(QFrame.HLine)
        divider_4.setObjectName("Divider")
        layout.addWidget(divider_4)

        pc_slew_form = QFormLayout()
        pc_slew_form.setLabelAlignment(Qt.AlignLeft)
        pc_slew_form.setFormAlignment(Qt.AlignTop)
        pc_slew_form.setHorizontalSpacing(18)
        pc_slew_form.setVerticalSpacing(14)

        self.pc_slew_rate_enable_label = QLabel()
        self.pc_slew_rate_enable_button = create_toggle_button(owner._on_pc_slew_rate_enable_toggled)
        self.pc_slew_rate_label = QLabel()
        self.pc_slew_rate_spin = QDoubleSpinBox()
        self.pc_slew_rate_spin.setRange(-1000000.0, 1000000.0)
        self.pc_slew_rate_spin.setDecimals(5)
        self.pc_slew_rate_spin.setSuffix(f" {TEXT[owner.language]['slew_rate_unit']}")
        self.pc_slew_rate_spin.setKeyboardTracking(False)
        self.pc_slew_rate_spin.editingFinished.connect(owner._on_pc_slew_rate_finished)
        pc_slew_form.addRow(self.pc_slew_rate_enable_label, self.pc_slew_rate_enable_button)
        pc_slew_form.addRow(self.pc_slew_rate_label, owner._create_target_row("pc", self.pc_slew_rate_spin))
        layout.addLayout(pc_slew_form)

        divider_5 = QFrame()
        divider_5.setFrameShape(QFrame.HLine)
        divider_5.setObjectName("Divider")
        layout.addWidget(divider_5)

        pc_arc_header = QHBoxLayout()
        self.pc_arc_label = QLabel()
        pc_arc_header.addWidget(self.pc_arc_label)
        pc_arc_header.addStretch(1)
        self.pc_arc_enable_button = create_toggle_button(owner._on_pc_arc_enable_toggled)
        pc_arc_header.addWidget(self.pc_arc_enable_button)
        layout.addLayout(pc_arc_header)

        pc_arc_form = QFormLayout()
        self.pc_arc_signal_label = QLabel()
        self.pc_arc_signal_combo = QComboBox()
        self.pc_arc_signal_combo.currentIndexChanged.connect(owner._on_pc_arc_signal_changed)
        self.pc_arc_factor_label = QLabel()
        self.pc_arc_factor_spin = QDoubleSpinBox()
        self.pc_arc_factor_spin.setRange(-1000000.0, 1000000.0)
        self.pc_arc_factor_spin.setDecimals(4)
        self.pc_arc_factor_spin.setSuffix(f" {TEXT[owner.language]['pc_arc_factor_unit']}")
        self.pc_arc_factor_spin.setKeyboardTracking(False)
        self.pc_arc_factor_spin.editingFinished.connect(owner._on_pc_arc_factor_finished)
        pc_arc_form.addRow(self.pc_arc_signal_label, self.pc_arc_signal_combo)
        pc_arc_form.addRow(self.pc_arc_factor_label, owner._create_target_row("pc", self.pc_arc_factor_spin))
        layout.addLayout(pc_arc_form)

        divider_6 = QFrame()
        divider_6.setFrameShape(QFrame.HLine)
        divider_6.setObjectName("Divider")
        layout.addWidget(divider_6)

        self.pressure_comp_label = QLabel()
        self.pressure_comp_label.setObjectName("SectionTitle")
        layout.addWidget(self.pressure_comp_label)

        pressure_comp_form = QFormLayout()
        pressure_comp_form.setLabelAlignment(Qt.AlignLeft)
        pressure_comp_form.setFormAlignment(Qt.AlignTop)
        pressure_comp_form.setHorizontalSpacing(18)
        pressure_comp_form.setVerticalSpacing(14)

        self.pressure_comp_enable_label = QLabel()
        self.pressure_comp_enable_button = create_toggle_button(owner._on_pressure_comp_enable_toggled)
        self.pressure_comp_air_pressure_label = QLabel()
        self.pressure_comp_air_pressure_value = QLabel()
        self.pressure_comp_air_pressure_value.setObjectName("ReadValue")
        self.pressure_comp_factor_label = QLabel()
        self.pressure_comp_factor_spin = QDoubleSpinBox()
        self.pressure_comp_factor_spin.setRange(-1000000.0, 1000000.0)
        self.pressure_comp_factor_spin.setDecimals(3)
        self.pressure_comp_factor_spin.setSuffix(f" {TEXT[owner.language]['pressure_comp_factor_unit']}")
        self.pressure_comp_factor_spin.setKeyboardTracking(False)
        self.pressure_comp_factor_spin.editingFinished.connect(owner._on_pressure_comp_factor_finished)
        self.pressure_comp_voltage_label = QLabel()
        self.pressure_comp_voltage_value = QLabel()
        self.pressure_comp_voltage_value.setObjectName("ReadValue")

        pressure_comp_form.addRow(self.pressure_comp_enable_label, self.pressure_comp_enable_button)
        pressure_comp_form.addRow(self.pressure_comp_air_pressure_label, self.pressure_comp_air_pressure_value)
        pressure_comp_form.addRow(self.pressure_comp_factor_label, owner._create_target_row("pc", self.pressure_comp_factor_spin))
        pressure_comp_form.addRow(self.pressure_comp_voltage_label, self.pressure_comp_voltage_value)
        layout.addLayout(pressure_comp_form)

    def bind_to(self, owner) -> None:
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
