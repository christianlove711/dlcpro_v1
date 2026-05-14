from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QLabel, QVBoxLayout


def _value_label() -> QLabel:
    label = QLabel()
    label.setObjectName("ReadValue")
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return label


class AutoLockStatusPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        self.title_label = QLabel()
        self.title_label.setObjectName("SectionTitle")
        layout.addWidget(self.title_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        self.phase_label = QLabel()
        self.phase_value = _value_label()
        self.lock_state_label = QLabel()
        self.lock_state_value = _value_label()
        self.lock_enabled_label = QLabel()
        self.lock_enabled_value = _value_label()
        self.candidate_count_label = QLabel()
        self.candidate_count_value = _value_label()
        self.scan_offset_label = QLabel()
        self.scan_offset_value = _value_label()
        self.target_label = QLabel()
        self.target_value = _value_label()
        self.tracking_label = QLabel()
        self.tracking_value = _value_label()
        self.message_label = QLabel()
        self.message_value = _value_label()

        form.addRow(self.phase_label, self.phase_value)
        form.addRow(self.lock_state_label, self.lock_state_value)
        form.addRow(self.lock_enabled_label, self.lock_enabled_value)
        form.addRow(self.candidate_count_label, self.candidate_count_value)
        form.addRow(self.scan_offset_label, self.scan_offset_value)
        form.addRow(self.target_label, self.target_value)
        form.addRow(self.tracking_label, self.tracking_value)
        form.addRow(self.message_label, self.message_value)
        layout.addLayout(form)
