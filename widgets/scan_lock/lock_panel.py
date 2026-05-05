from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from widgets.common_controls import create_toggle_button


class LockSettingsPanel(QFrame):
    EXPORTED_ATTRS = (
        "lock_settings_label",
        "lock_enable_button",
        "lock_hold_button",
        "lock_input_signal_label",
        "lock_input_signal_combo",
        "lock_type_label",
        "lock_type_combo",
        "lock_pid_selection_label",
        "lock_pid_selection_combo",
        "lock_without_lockpoint_label",
        "lock_without_lockpoint_check",
    )

    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.lock_settings_label = QLabel()
        self.lock_settings_label.setObjectName("SectionTitle")
        header.addWidget(self.lock_settings_label)
        header.addStretch(1)
        self.lock_enable_button = create_toggle_button(owner._on_lock_enabled_toggled)
        header.addWidget(self.lock_enable_button)
        self.lock_hold_button = create_toggle_button(owner._on_lock_hold_toggled)
        header.addWidget(self.lock_hold_button)
        layout.addLayout(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.lock_input_signal_label = QLabel()
        self.lock_input_signal_combo = QComboBox()
        self.lock_input_signal_combo.currentIndexChanged.connect(owner._on_lock_input_signal_changed)

        self.lock_type_label = QLabel()
        self.lock_type_combo = QComboBox()
        self.lock_type_combo.currentIndexChanged.connect(owner._on_lock_type_changed)

        self.lock_pid_selection_label = QLabel()
        self.lock_pid_selection_combo = QComboBox()
        self.lock_pid_selection_combo.currentIndexChanged.connect(owner._on_lock_pid_selection_changed)

        self.lock_without_lockpoint_label = QLabel()
        self.lock_without_lockpoint_check = QCheckBox()
        self.lock_without_lockpoint_check.stateChanged.connect(owner._on_lock_without_lockpoint_changed)

        form.addRow(self.lock_input_signal_label, self.lock_input_signal_combo)
        form.addRow(self.lock_type_label, self.lock_type_combo)
        form.addRow(self.lock_pid_selection_label, self.lock_pid_selection_combo)
        form.addRow(self.lock_without_lockpoint_label, self.lock_without_lockpoint_check)
        layout.addLayout(form)

    def bind_to(self, owner) -> None:
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
