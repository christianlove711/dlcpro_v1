from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


def _value_label() -> QLabel:
    label = QLabel()
    label.setObjectName("ReadValue")
    label.setWordWrap(False)
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

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        self.phase_label = QLabel()
        self.phase_value = _value_label()
        self.lock_state_label = QLabel()
        self.lock_state_value = _value_label()
        self.lock_enabled_label = QLabel()
        self.lock_enabled_value = _value_label()
        self.template_progress_label = QLabel()
        self.template_progress_value = _value_label()
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
        self.message_value.setMinimumWidth(220)
        self.message_value.setWordWrap(True)

        row.addWidget(self._metric_block(self.phase_label, self.phase_value))
        row.addWidget(self._metric_block(self.lock_state_label, self.lock_state_value))
        row.addWidget(self._metric_block(self.lock_enabled_label, self.lock_enabled_value))
        row.addWidget(self._metric_block(self.template_progress_label, self.template_progress_value))
        row.addWidget(self._metric_block(self.candidate_count_label, self.candidate_count_value))
        row.addWidget(self._metric_block(self.scan_offset_label, self.scan_offset_value))
        row.addWidget(self._metric_block(self.target_label, self.target_value))
        row.addWidget(self._metric_block(self.tracking_label, self.tracking_value))
        row.addWidget(self._metric_block(self.message_label, self.message_value, stretch=1))
        layout.addLayout(row)

    @staticmethod
    def _metric_block(label: QLabel, value: QLabel, stretch: int = 0) -> QWidget:
        container = QWidget()
        block = QHBoxLayout(container)
        block.setContentsMargins(0, 0, 0, 0)
        block.setSpacing(6)
        container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setWordWrap(False)
        block.addWidget(label)
        block.addWidget(value)
        if stretch:
            container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            block.addStretch(stretch)
        return container
