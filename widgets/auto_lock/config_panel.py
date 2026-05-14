from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from widgets.common_controls import SafeComboBox, SafeSpinBox


class AutoLockConfigPanel(QFrame):
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

        self.strategy_label = QLabel()
        self.strategy_combo = SafeComboBox()

        self.search_interval_label = QLabel()
        self.search_interval_spin = SafeSpinBox()
        self.search_interval_spin.setRange(100, 10_000)
        self.search_interval_spin.setValue(400)

        self.settle_delay_label = QLabel()
        self.settle_delay_spin = SafeSpinBox()
        self.settle_delay_spin.setRange(0, 10_000)
        self.settle_delay_spin.setValue(250)

        self.lock_timeout_label = QLabel()
        self.lock_timeout_spin = SafeSpinBox()
        self.lock_timeout_spin.setRange(500, 60_000)
        self.lock_timeout_spin.setValue(4_000)

        self.monitor_interval_label = QLabel()
        self.monitor_interval_spin = SafeSpinBox()
        self.monitor_interval_spin.setRange(100, 10_000)
        self.monitor_interval_spin.setValue(500)

        self.reacquire_delay_label = QLabel()
        self.reacquire_delay_spin = SafeSpinBox()
        self.reacquire_delay_spin.setRange(0, 30_000)
        self.reacquire_delay_spin.setValue(800)

        form.addRow(self.strategy_label, self.strategy_combo)
        form.addRow(self.search_interval_label, self.search_interval_spin)
        form.addRow(self.settle_delay_label, self.settle_delay_spin)
        form.addRow(self.lock_timeout_label, self.lock_timeout_spin)
        form.addRow(self.monitor_interval_label, self.monitor_interval_spin)
        form.addRow(self.reacquire_delay_label, self.reacquire_delay_spin)
        layout.addLayout(form)

        self.auto_enable_scan_check = QCheckBox()
        self.auto_enable_scan_check.setChecked(True)
        layout.addWidget(self.auto_enable_scan_check)

        self.watch_after_lock_check = QCheckBox()
        self.watch_after_lock_check.setChecked(True)
        layout.addWidget(self.watch_after_lock_check)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 4, 0, 0)
        button_row.setSpacing(10)

        self.start_button = QPushButton()
        self.stop_button = QPushButton()
        self.clear_log_button = QPushButton()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.clear_log_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)
