from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox, create_toggle_button


class PowerStabilizationPanel(QFrame):
    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("SectionTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.enable_button = create_toggle_button(owner._on_stabilization_enabled_toggled)
        header.addWidget(self.enable_button)
        layout.addLayout(header)

        self.mapping_hint_label = QLabel()
        self.mapping_hint_label.setObjectName("SubtleHint")
        self.mapping_hint_label.setWordWrap(True)
        layout.addWidget(self.mapping_hint_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.input_signal_label = QLabel()
        self.input_signal_combo = SafeComboBox()

        self.external_physical_channel_label = QLabel()
        self.external_physical_channel_combo = SafeComboBox()
        self.external_physical_channel_combo.currentIndexChanged.connect(owner._on_stabilization_pd_ext_input_channel_changed)

        self.photo_diode_value_label = QLabel()
        self.photo_diode_value_edit = QLineEdit()
        self.photo_diode_value_edit.setReadOnly(True)

        self.cal_factor_label = QLabel()
        self.cal_factor_spin = SafeDoubleSpinBox()
        self.cal_factor_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.cal_factor_spin.setDecimals(6)
        self.cal_factor_spin.setKeyboardTracking(False)
        self.cal_factor_spin.connect_live_apply(owner._on_stabilization_cal_factor_finished)
        self.cal_factor_spin.set_button_only_mode()

        self.cal_offset_label = QLabel()
        self.cal_offset_spin = SafeDoubleSpinBox()
        self.cal_offset_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.cal_offset_spin.setDecimals(6)
        self.cal_offset_spin.setKeyboardTracking(False)
        self.cal_offset_spin.connect_live_apply(owner._on_stabilization_cal_offset_finished)
        self.cal_offset_spin.set_button_only_mode()

        self.set_level_label = QLabel()
        self.set_level_spin = SafeDoubleSpinBox()
        self.set_level_spin.setRange(0.0, 1_000_000_000.0)
        self.set_level_spin.setDecimals(6)
        self.set_level_spin.setKeyboardTracking(False)
        self.set_level_spin.connect_live_apply(owner._on_stabilization_set_level_finished)
        self.set_level_spin.set_button_only_mode()

        self.actual_level_label = QLabel()
        self.actual_level_edit = QLineEdit()
        self.actual_level_edit.setReadOnly(True)

        self.output_signal_label = QLabel()
        self.output_signal_combo = SafeComboBox()

        form.addRow(self.input_signal_label, self.input_signal_combo)
        form.addRow(self.external_physical_channel_label, self.external_physical_channel_combo)
        form.addRow(self.photo_diode_value_label, self.photo_diode_value_edit)
        form.addRow(self.cal_factor_label, self.cal_factor_spin)
        form.addRow(self.cal_offset_label, self.cal_offset_spin)
        form.addRow(self.set_level_label, self.set_level_spin)
        form.addRow(self.actual_level_label, self.actual_level_edit)
        form.addRow(self.output_signal_label, self.output_signal_combo)
        layout.addLayout(form)

        gain_grid = QGridLayout()
        gain_grid.setHorizontalSpacing(12)
        gain_grid.setVerticalSpacing(10)

        self.gain_label = QLabel()
        self.gain_all_spin = self._create_gain_spin()
        self.gain_all_spin.connect_live_apply(owner._on_stabilization_gain_all_finished)
        self.p_label = QLabel("P")
        self.gain_p_spin = self._create_gain_spin()
        self.gain_p_spin.connect_live_apply(owner._on_stabilization_gain_p_finished)
        self.i_label = QLabel("I")
        self.gain_i_spin = self._create_gain_spin()
        self.gain_i_spin.connect_live_apply(owner._on_stabilization_gain_i_finished)
        self.d_label = QLabel("D")
        self.gain_d_spin = self._create_gain_spin()
        self.gain_d_spin.connect_live_apply(owner._on_stabilization_gain_d_finished)

        gain_grid.addWidget(self.gain_label, 0, 0)
        gain_grid.addWidget(self.gain_all_spin, 0, 1)
        gain_grid.addWidget(self.p_label, 0, 2)
        gain_grid.addWidget(self.gain_p_spin, 0, 3)
        gain_grid.addWidget(self.i_label, 1, 0)
        gain_grid.addWidget(self.gain_i_spin, 1, 1)
        gain_grid.addWidget(self.d_label, 1, 2)
        gain_grid.addWidget(self.gain_d_spin, 1, 3)
        gain_grid.setColumnStretch(1, 1)
        gain_grid.setColumnStretch(3, 1)
        layout.addLayout(gain_grid)

        hold_row = QHBoxLayout()
        hold_row.setContentsMargins(0, 0, 0, 0)
        hold_row.setSpacing(8)
        self.hold_output_check = QCheckBox()
        self.hold_output_check.stateChanged.connect(owner._on_stabilization_hold_output_on_unlock_changed)
        self.hold_output_label = QLabel()
        hold_row.addWidget(self.hold_output_check)
        hold_row.addWidget(self.hold_output_label)
        hold_row.addStretch(1)
        layout.addLayout(hold_row)

    @staticmethod
    def _create_gain_spin() -> SafeDoubleSpinBox:
        spin = SafeDoubleSpinBox()
        spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        spin.setDecimals(6)
        spin.setKeyboardTracking(False)
        spin.set_button_only_mode()
        return spin
