from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui_text import TEXT
from widgets.common_controls import PrecisionButtonRow, SafeComboBox, SafeDoubleSpinBox, create_toggle_button


class TcPanel(QFrame):
    EXPORTED_ATTRS = (
        "tc_label",
        "tc_enable_button",
        "tc_precision_label",
        "tc_precision_buttons",
        "temp_set_label",
        "temp_set_spin",
        "temp_act_label",
        "temp_act_value",
        "tc_arc_label",
        "tc_arc_enable_button",
        "tc_arc_signal_label",
        "tc_arc_signal_combo",
        "tc_arc_factor_label",
        "tc_arc_factor_spin",
    )

    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.tc_label = QLabel()
        self.tc_label.setObjectName("SectionTitle")
        header.addWidget(self.tc_label)
        header.addStretch(1)
        self.tc_enable_button = create_toggle_button(owner.laser_controller._on_tc_enable_toggled)
        header.addWidget(self.tc_enable_button)
        layout.addLayout(header)

        tc_form = QFormLayout()
        tc_form.setLabelAlignment(Qt.AlignLeft)
        tc_form.setFormAlignment(Qt.AlignTop)
        tc_form.setHorizontalSpacing(18)
        tc_form.setVerticalSpacing(14)

        self.temp_set_label = QLabel()
        self.temp_set_spin = SafeDoubleSpinBox()
        self.temp_set_spin.setRange(-1000000.0, 1000000.0)
        self.temp_set_spin.setDecimals(3)
        self.temp_set_spin.setSuffix(f" {TEXT[owner.language]['temperature_unit']}")
        self.temp_set_spin.setKeyboardTracking(False)
        self.temp_set_spin.connect_live_apply(owner.laser_controller._on_temp_set_finished)
        self.temp_set_spin.set_button_only_mode()

        self.temp_act_label = QLabel()
        self.temp_act_value = QLabel()
        self.temp_act_value.setObjectName("ReadValue")

        self.tc_precision_label = QLabel()
        self.tc_precision_row = PrecisionButtonRow(
            owner.PRECISION_OPTIONS, owner._set_tc_precision, max_columns=5
        )
        self.tc_precision_buttons = self.tc_precision_row.buttons

        tc_form.addRow(self.tc_precision_label, self.tc_precision_row)
        tc_form.addRow(self.temp_set_label, owner._create_target_row("tc", self.temp_set_spin))
        tc_form.addRow(self.temp_act_label, self.temp_act_value)
        layout.addLayout(tc_form)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("Divider")
        layout.addWidget(divider)

        arc_header = QHBoxLayout()
        self.tc_arc_label = QLabel()
        arc_header.addWidget(self.tc_arc_label)
        arc_header.addStretch(1)
        self.tc_arc_enable_button = create_toggle_button(owner.laser_controller._on_tc_arc_enable_toggled)
        arc_header.addWidget(self.tc_arc_enable_button)
        layout.addLayout(arc_header)

        arc_form = QFormLayout()
        self.tc_arc_signal_label = QLabel()
        self.tc_arc_signal_combo = SafeComboBox()
        self.tc_arc_signal_combo.currentIndexChanged.connect(owner.laser_controller._on_tc_arc_signal_changed)
        self.tc_arc_factor_label = QLabel()
        self.tc_arc_factor_spin = SafeDoubleSpinBox()
        self.tc_arc_factor_spin.setRange(-1000000.0, 1000000.0)
        self.tc_arc_factor_spin.setDecimals(4)
        self.tc_arc_factor_spin.setSuffix(f" {TEXT[owner.language]['tc_arc_factor_unit']}")
        self.tc_arc_factor_spin.setKeyboardTracking(False)
        self.tc_arc_factor_spin.connect_live_apply(owner.laser_controller._on_tc_arc_factor_finished)
        self.tc_arc_factor_spin.set_button_only_mode()
        arc_form.addRow(self.tc_arc_signal_label, self.tc_arc_signal_combo)
        arc_form.addRow(self.tc_arc_factor_label, owner._create_target_row("tc", self.tc_arc_factor_spin))
        layout.addLayout(arc_form)

    def bind_to(self, owner) -> None:
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
