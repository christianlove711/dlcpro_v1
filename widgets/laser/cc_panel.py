from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from ui_text import TEXT
from widgets.common_controls import PrecisionButtonRow, SafeComboBox, SafeDoubleSpinBox, create_toggle_button


class CcPanel(QFrame):
    EXPORTED_ATTRS = (
        "cc_label",
        "cc_enable_button",
        "precision_label",
        "precision_buttons",
        "current_set_label",
        "current_set_spin",
        "current_act_label",
        "current_act_value",
        "current_clip_label",
        "current_clip_spin",
        "current_meta_hint",
        "feedforward_label",
        "feedforward_enable_button",
        "feedforward_factor_label",
        "feedforward_factor_spin",
        "arc_label",
        "arc_enable_button",
        "arc_signal_label",
        "arc_signal_combo",
        "arc_factor_label",
        "arc_factor_spin",
        "auto_apply_hint_label",
    )

    def __init__(self, owner) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        cc_header = QHBoxLayout()
        self.cc_label = QLabel()
        self.cc_label.setObjectName("SectionTitle")
        cc_header.addWidget(self.cc_label)
        cc_header.addStretch(1)
        self.cc_enable_button = create_toggle_button(owner.laser_controller._on_cc_enable_toggled)
        cc_header.addWidget(self.cc_enable_button)
        layout.addLayout(cc_header)

        top_form = QFormLayout()
        top_form.setLabelAlignment(Qt.AlignLeft)
        top_form.setFormAlignment(Qt.AlignTop)
        top_form.setHorizontalSpacing(18)
        top_form.setVerticalSpacing(14)

        self.precision_label = QLabel()
        self.precision_row = PrecisionButtonRow(
            owner.PRECISION_OPTIONS, owner._set_cc_precision, max_columns=5
        )
        self.precision_buttons = self.precision_row.buttons

        self.current_set_label = QLabel()
        self.current_set_spin = SafeDoubleSpinBox()
        self.current_set_spin.setRange(-1000000.0, 1000000.0)
        self.current_set_spin.setDecimals(5)
        self.current_set_spin.setSingleStep(0.1)
        self.current_set_spin.setSuffix(" mA")
        self.current_set_spin.setKeyboardTracking(False)
        self.current_set_spin.valueChanged.connect(owner.laser_controller._on_current_set_changed)
        self.current_set_spin.stepApplied.connect(owner.laser_controller._on_current_set_step_applied)
        self.current_set_spin.set_button_only_mode()

        self.current_act_label = QLabel()
        self.current_act_value = QLabel()
        self.current_act_value.setObjectName("ReadValue")

        self.current_clip_label = QLabel()
        self.current_clip_spin = SafeDoubleSpinBox()
        self.current_clip_spin.setRange(-1000000.0, 1000000.0)
        self.current_clip_spin.setDecimals(5)
        self.current_clip_spin.setSuffix(" mA")
        self.current_clip_spin.setKeyboardTracking(False)
        self.current_clip_spin.connect_live_apply(owner.laser_controller._on_current_clip_finished)
        self.current_clip_spin.set_button_only_mode(False)

        top_form.addRow(self.precision_label, self.precision_row)
        top_form.addRow(self.current_set_label, owner._create_target_row("cc", self.current_set_spin))
        top_form.addRow(self.current_act_label, self.current_act_value)
        top_form.addRow(self.current_clip_label, owner._create_target_row("cc", self.current_clip_spin))
        layout.addLayout(top_form)

        self.current_meta_hint = QLabel()
        self.current_meta_hint.setObjectName("SubtleHint")
        layout.addWidget(self.current_meta_hint)

        divider_1 = QFrame()
        divider_1.setFrameShape(QFrame.HLine)
        divider_1.setObjectName("Divider")
        layout.addWidget(divider_1)

        ff_header = QHBoxLayout()
        self.feedforward_label = QLabel()
        ff_header.addWidget(self.feedforward_label)
        ff_header.addStretch(1)
        self.feedforward_enable_button = create_toggle_button(owner.laser_controller._on_feedforward_enable_toggled)
        ff_header.addWidget(self.feedforward_enable_button)
        layout.addLayout(ff_header)

        ff_form = QFormLayout()
        self.feedforward_factor_label = QLabel()
        self.feedforward_factor_spin = SafeDoubleSpinBox()
        self.feedforward_factor_spin.setRange(-1000000.0, 1000000.0)
        self.feedforward_factor_spin.setDecimals(5)
        self.feedforward_factor_spin.setSuffix(f" {TEXT[owner.language]['feedforward_factor_unit']}")
        self.feedforward_factor_spin.setKeyboardTracking(False)
        self.feedforward_factor_spin.connect_live_apply(owner.laser_controller._on_feedforward_factor_finished)
        self.feedforward_factor_spin.set_button_only_mode()
        ff_form.addRow(self.feedforward_factor_label, owner._create_target_row("cc", self.feedforward_factor_spin))
        layout.addLayout(ff_form)

        divider_2 = QFrame()
        divider_2.setFrameShape(QFrame.HLine)
        divider_2.setObjectName("Divider")
        layout.addWidget(divider_2)

        arc_header = QHBoxLayout()
        self.arc_label = QLabel()
        arc_header.addWidget(self.arc_label)
        arc_header.addStretch(1)
        self.arc_enable_button = create_toggle_button(owner.laser_controller._on_arc_enable_toggled)
        arc_header.addWidget(self.arc_enable_button)
        layout.addLayout(arc_header)

        arc_form = QFormLayout()
        self.arc_signal_label = QLabel()
        self.arc_signal_combo = SafeComboBox()
        self.arc_signal_combo.currentIndexChanged.connect(owner.laser_controller._on_arc_signal_changed)
        self.arc_factor_label = QLabel()
        self.arc_factor_spin = SafeDoubleSpinBox()
        self.arc_factor_spin.setRange(-1000000.0, 1000000.0)
        self.arc_factor_spin.setDecimals(4)
        self.arc_factor_spin.setSuffix(f" {TEXT[owner.language]['arc_factor_unit']}")
        self.arc_factor_spin.setKeyboardTracking(False)
        self.arc_factor_spin.connect_live_apply(owner.laser_controller._on_arc_factor_finished)
        self.arc_factor_spin.set_button_only_mode()
        arc_form.addRow(self.arc_signal_label, self.arc_signal_combo)
        arc_form.addRow(self.arc_factor_label, owner._create_target_row("cc", self.arc_factor_spin))
        layout.addLayout(arc_form)

        self.auto_apply_hint_label = QLabel()
        self.auto_apply_hint_label.setObjectName("SubtleHint")
        self.auto_apply_hint_label.setProperty("preserveSingleLine", True)
        self.auto_apply_hint_label.setWordWrap(False)
        self.auto_apply_hint_label.setMinimumHeight(28)
        self.auto_apply_hint_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.auto_apply_hint_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.auto_apply_hint_label)

    def bind_to(self, owner) -> None:
        # 统一把控件引用挂回主窗口，避免业务逻辑层大面积改名。
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))
