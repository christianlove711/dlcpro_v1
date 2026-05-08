from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox, create_toggle_button


class LockDetectionPanel(QFrame):
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
        self.enable_button = create_toggle_button(owner._on_relock_detection_enabled_toggled)
        header.addWidget(self.enable_button)
        layout.addLayout(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.input_signal_label = QLabel()
        self.input_signal_combo = SafeComboBox()
        self.input_signal_combo.currentIndexChanged.connect(owner._on_relock_input_signal_changed)

        self.level_high_label = QLabel()
        self.level_high_spin = SafeDoubleSpinBox()
        self.level_high_spin.setRange(-1_000_000.0, 1_000_000.0)
        self.level_high_spin.setDecimals(6)
        self.level_high_spin.setKeyboardTracking(False)
        self.level_high_spin.connect_live_apply(owner._on_relock_level_high_finished)
        self.level_high_spin.set_button_only_mode(False)

        self.level_low_label = QLabel()
        self.level_low_spin = SafeDoubleSpinBox()
        self.level_low_spin.setRange(-1_000_000.0, 1_000_000.0)
        self.level_low_spin.setDecimals(6)
        self.level_low_spin.setKeyboardTracking(False)
        self.level_low_spin.connect_live_apply(owner._on_relock_level_low_finished)
        self.level_low_spin.set_button_only_mode(False)

        self.hysteresis_label = QLabel()
        self.hysteresis_spin = SafeDoubleSpinBox()
        self.hysteresis_spin.setRange(0.0, 1_000_000.0)
        self.hysteresis_spin.setDecimals(6)
        self.hysteresis_spin.setKeyboardTracking(False)
        self.hysteresis_spin.connect_live_apply(owner._on_relock_hysteresis_finished)
        self.hysteresis_spin.set_button_only_mode()

        self.delay_label = QLabel()
        self.delay_spin = SafeDoubleSpinBox()
        self.delay_spin.setRange(0.0, 1_000_000.0)
        self.delay_spin.setDecimals(2)
        self.delay_spin.setKeyboardTracking(False)
        self.delay_spin.connect_live_apply(owner._on_relock_delay_finished)
        self.delay_spin.set_button_only_mode()

        self.out_of_lock_action_label = QLabel()
        self.enable_reset_check = QCheckBox()
        self.enable_reset_check.stateChanged.connect(owner._on_relock_reset_enabled_changed)
        self.enable_reset_label = QLabel()

        reset_row = QHBoxLayout()
        reset_row.setContentsMargins(0, 0, 0, 0)
        reset_row.setSpacing(8)
        reset_row.addWidget(self.enable_reset_check)
        reset_row.addWidget(self.enable_reset_label)
        reset_row.addStretch(1)
        reset_container = QFrame()
        reset_container.setLayout(reset_row)

        form.addRow(self.input_signal_label, self.input_signal_combo)
        form.addRow(self.level_high_label, self.level_high_spin)
        form.addRow(self.level_low_label, self.level_low_spin)
        form.addRow(self.hysteresis_label, self.hysteresis_spin)
        form.addRow(self.delay_label, self.delay_spin)
        form.addRow(self.out_of_lock_action_label, reset_container)
        layout.addLayout(form)
