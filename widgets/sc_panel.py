from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui_text import TEXT
from widgets.common_controls import PrecisionButtonRow, create_toggle_button


class ScPanel(QFrame):
    EXPORTED_ATTRS = (
        "sc_label",
        "sc_enable_button",
        "sc_precision_label",
        "sc_precision_buttons",
        "scan_amplitude_label",
        "scan_amplitude_spin",
        "scan_offset_label",
        "scan_offset_spin",
        "scan_output_label",
        "scan_output_combo",
        "scan_frequency_label",
        "scan_frequency_spin",
        "scan_shape_label",
        "scan_shape_combo",
    )

    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QHBoxLayout()
        self.sc_label = QLabel()
        self.sc_label.setObjectName("SectionTitle")
        header.addWidget(self.sc_label)
        header.addStretch(1)
        self.sc_enable_button = create_toggle_button(owner._on_sc_enable_toggled)
        header.addWidget(self.sc_enable_button)
        layout.addLayout(header)

        sc_form = QFormLayout()
        sc_form.setLabelAlignment(Qt.AlignLeft)
        sc_form.setFormAlignment(Qt.AlignTop)
        sc_form.setHorizontalSpacing(18)
        sc_form.setVerticalSpacing(14)

        self.sc_precision_label = QLabel()
        self.sc_precision_row = PrecisionButtonRow(owner.PRECISION_OPTIONS, owner._set_sc_precision)
        self.sc_precision_buttons = self.sc_precision_row.buttons

        self.scan_amplitude_label = QLabel()
        self.scan_amplitude_spin = QDoubleSpinBox()
        self.scan_amplitude_spin.setRange(-1000000.0, 1000000.0)
        self.scan_amplitude_spin.setDecimals(6)
        self.scan_amplitude_spin.setSuffix(f" {TEXT[owner.language]['scan_amplitude_unit']}")
        self.scan_amplitude_spin.setKeyboardTracking(False)
        self.scan_amplitude_spin.editingFinished.connect(owner._on_sc_amplitude_finished)

        self.scan_offset_label = QLabel()
        self.scan_offset_spin = QDoubleSpinBox()
        self.scan_offset_spin.setRange(-1000000.0, 1000000.0)
        self.scan_offset_spin.setDecimals(6)
        self.scan_offset_spin.setSuffix(f" {TEXT[owner.language]['voltage_unit']}")
        self.scan_offset_spin.setKeyboardTracking(False)
        self.scan_offset_spin.editingFinished.connect(owner._on_sc_offset_finished)

        sc_form.addRow(self.sc_precision_label, self.sc_precision_row)
        sc_form.addRow(self.scan_amplitude_label, owner._create_target_row("sc", self.scan_amplitude_spin))
        sc_form.addRow(self.scan_offset_label, owner._create_target_row("sc", self.scan_offset_spin))
        layout.addLayout(sc_form)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("Divider")
        layout.addWidget(divider)

        scan_config_form = QFormLayout()
        scan_config_form.setLabelAlignment(Qt.AlignLeft)
        scan_config_form.setFormAlignment(Qt.AlignTop)
        scan_config_form.setHorizontalSpacing(18)
        scan_config_form.setVerticalSpacing(14)

        self.scan_output_label = QLabel()
        self.scan_output_combo = QComboBox()
        self.scan_output_combo.currentIndexChanged.connect(owner._on_sc_output_changed)

        self.scan_frequency_label = QLabel()
        self.scan_frequency_spin = QDoubleSpinBox()
        self.scan_frequency_spin.setRange(0.0, 1000000.0)
        self.scan_frequency_spin.setDecimals(2)
        self.scan_frequency_spin.setSuffix(" Hz")
        self.scan_frequency_spin.setKeyboardTracking(False)
        self.scan_frequency_spin.editingFinished.connect(owner._on_sc_frequency_finished)

        self.scan_shape_label = QLabel()
        self.scan_shape_combo = QComboBox()
        self.scan_shape_combo.currentIndexChanged.connect(owner._on_sc_shape_changed)

        scan_config_form.addRow(self.scan_output_label, self.scan_output_combo)
        scan_config_form.addRow(self.scan_frequency_label, owner._create_target_row("sc", self.scan_frequency_spin))
        scan_config_form.addRow(self.scan_shape_label, self.scan_shape_combo)
        layout.addLayout(scan_config_form)

    def bind_to(self, owner) -> None:
        # SC 面板沿用和 CC/TC/PC 相同的引用导出方式，保证主窗口事件层保持稳定。
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
