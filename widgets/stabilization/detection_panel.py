from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from widgets.common_controls import SafeDoubleSpinBox, create_toggle_button


class StabilizationDetectionPanel(QFrame):
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
        self.enable_button = create_toggle_button(owner._on_stabilization_window_enabled_toggled)
        header.addWidget(self.enable_button)
        layout.addLayout(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.level_label = QLabel()
        self.level_spin = SafeDoubleSpinBox()
        self.level_spin.setRange(0.0, 1_000_000_000.0)
        self.level_spin.setDecimals(6)
        self.level_spin.setKeyboardTracking(False)
        self.level_spin.connect_live_apply(owner._on_stabilization_window_level_finished)
        self.level_spin.set_button_only_mode()

        self.hysteresis_label = QLabel()
        self.hysteresis_spin = SafeDoubleSpinBox()
        self.hysteresis_spin.setRange(0.0, 1_000_000_000.0)
        self.hysteresis_spin.setDecimals(6)
        self.hysteresis_spin.setKeyboardTracking(False)
        self.hysteresis_spin.connect_live_apply(owner._on_stabilization_window_hysteresis_finished)
        self.hysteresis_spin.set_button_only_mode()

        form.addRow(self.level_label, self.level_spin)
        form.addRow(self.hysteresis_label, self.hysteresis_spin)
        layout.addLayout(form)
