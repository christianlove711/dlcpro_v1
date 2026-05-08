from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox, create_toggle_button


class RelockPanel(QFrame):
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
        self.enable_button = create_toggle_button(owner._on_relock_enabled_toggled)
        header.addWidget(self.enable_button)
        layout.addLayout(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.amplitude_label = QLabel()
        self.amplitude_spin = SafeDoubleSpinBox()
        self.amplitude_spin.setRange(0.0, 1_000_000.0)
        self.amplitude_spin.setDecimals(6)
        self.amplitude_spin.setKeyboardTracking(False)
        self.amplitude_spin.connect_live_apply(owner._on_relock_amplitude_finished)
        self.amplitude_spin.set_button_only_mode()

        self.frequency_label = QLabel()
        self.frequency_spin = SafeDoubleSpinBox()
        self.frequency_spin.setRange(0.0, 1_000_000.0)
        self.frequency_spin.setDecimals(2)
        self.frequency_spin.setKeyboardTracking(False)
        self.frequency_spin.connect_live_apply(owner._on_relock_frequency_finished)
        self.frequency_spin.set_button_only_mode()

        self.output_channel_label = QLabel()
        self.output_channel_combo = SafeComboBox()
        self.output_channel_combo.currentIndexChanged.connect(owner._on_relock_output_channel_changed)

        form.addRow(self.amplitude_label, self.amplitude_spin)
        form.addRow(self.frequency_label, self.frequency_spin)
        form.addRow(self.output_channel_label, self.output_channel_combo)
        layout.addLayout(form)
