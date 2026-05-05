from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui_text import TEXT
from widgets.common_controls import create_toggle_button


class ScanControlPanel(QFrame):
    EXPORTED_ATTRS = (
        "sc_label",
        "sc_enable_button",
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
        "sc_precision_buttons",
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

        top_form = QFormLayout()
        top_form.setLabelAlignment(Qt.AlignLeft)
        top_form.setFormAlignment(Qt.AlignTop)
        top_form.setHorizontalSpacing(18)
        top_form.setVerticalSpacing(14)

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

        top_form.addRow(self.scan_amplitude_label, self.scan_amplitude_spin)
        top_form.addRow(self.scan_offset_label, self.scan_offset_spin)
        layout.addLayout(top_form)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("Divider")
        layout.addWidget(divider)

        bottom_form = QFormLayout()
        bottom_form.setLabelAlignment(Qt.AlignLeft)
        bottom_form.setFormAlignment(Qt.AlignTop)
        bottom_form.setHorizontalSpacing(18)
        bottom_form.setVerticalSpacing(14)

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

        bottom_form.addRow(self.scan_output_label, self.scan_output_combo)
        bottom_form.addRow(self.scan_frequency_label, self.scan_frequency_spin)
        bottom_form.addRow(self.scan_shape_label, self.scan_shape_combo)
        layout.addLayout(bottom_form)

        # Scan&Lock 的 SC 页面按官方界面单独布局，不复用 Laser 页面的步进按钮区。
        self.sc_precision_buttons: list = []

    def bind_to(self, owner) -> None:
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
