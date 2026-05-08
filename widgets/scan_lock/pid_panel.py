from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QGridLayout, QLabel, QVBoxLayout

from widgets.common_controls import PrecisionButtonRow, SafeComboBox, SafeDoubleSpinBox


class PidPanel(QFrame):
    def __init__(self, owner, pid_name: str, title_key: str) -> None:
        super().__init__()
        self.setObjectName("LaserPanel")
        self.pid_name = pid_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title = QLabel()
        title.setObjectName("SectionTitle")
        setattr(self, f"{pid_name}_title_label", title)
        layout.addWidget(title)

        if pid_name == "pid1":
            precision_form = QFormLayout()
            precision_form.setLabelAlignment(Qt.AlignLeft)
            precision_form.setFormAlignment(Qt.AlignTop)
            precision_form.setHorizontalSpacing(18)
            self.pid_precision_label = QLabel()
            self.pid_precision_row = PrecisionButtonRow(owner.PRECISION_OPTIONS, owner._set_pid_precision)
            self.pid_precision_buttons = self.pid_precision_row.buttons
            precision_form.addRow(self.pid_precision_label, self.pid_precision_row)
            layout.addLayout(precision_form)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)

        gain_label = QLabel()
        gain_spin = SafeDoubleSpinBox()
        gain_spin.setRange(-1000000.0, 1000000.0)
        gain_spin.setDecimals(2)
        gain_spin.setKeyboardTracking(False)
        gain_spin.connect_live_apply(getattr(owner, f"_on_{pid_name}_gain_finished"))
        gain_spin.set_button_only_mode()

        p_label = QLabel()
        p_spin = SafeDoubleSpinBox()
        p_spin.setRange(-1000000.0, 1000000.0)
        p_spin.setDecimals(4)
        p_spin.setKeyboardTracking(False)
        p_spin.connect_live_apply(getattr(owner, f"_on_{pid_name}_p_finished"))
        p_spin.set_button_only_mode()

        i_label = QLabel()
        i_spin = SafeDoubleSpinBox()
        i_spin.setRange(-1000000.0, 1000000.0)
        i_spin.setDecimals(4)
        i_spin.setKeyboardTracking(False)
        i_spin.connect_live_apply(getattr(owner, f"_on_{pid_name}_i_finished"))
        i_spin.set_button_only_mode()

        d_label = QLabel()
        d_spin = SafeDoubleSpinBox()
        d_spin.setRange(-1000000.0, 1000000.0)
        d_spin.setDecimals(4)
        d_spin.setKeyboardTracking(False)
        d_spin.connect_live_apply(getattr(owner, f"_on_{pid_name}_d_finished"))
        d_spin.set_button_only_mode()

        grid.addWidget(gain_label, 0, 0)
        grid.addWidget(owner._create_target_row("pid", gain_spin), 0, 1)
        grid.addWidget(p_label, 0, 2)
        grid.addWidget(owner._create_target_row("pid", p_spin), 0, 3)
        grid.addWidget(i_label, 1, 0)
        grid.addWidget(owner._create_target_row("pid", i_spin), 1, 1)
        grid.addWidget(d_label, 1, 2)
        grid.addWidget(owner._create_target_row("pid", d_spin), 1, 3)
        layout.addLayout(grid)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)

        output_label = QLabel()
        output_combo = SafeComboBox()
        output_combo.currentIndexChanged.connect(getattr(owner, f"_on_{pid_name}_output_channel_changed"))

        sign_check = QCheckBox()
        sign_check.stateChanged.connect(getattr(owner, f"_on_{pid_name}_sign_changed"))
        sign_label = QLabel()

        use_i_cutoff_label = QLabel()
        use_i_cutoff_check = QCheckBox()
        if pid_name == "pid1":
            use_i_cutoff_check.stateChanged.connect(owner._on_pid1_i_cutoff_enabled_changed)
        else:
            use_i_cutoff_check.setEnabled(False)
            use_i_cutoff_label.setEnabled(False)

        i_cutoff_spin = SafeDoubleSpinBox()
        i_cutoff_spin.setRange(0.0, 1000000.0)
        i_cutoff_spin.setDecimals(2)
        i_cutoff_spin.setKeyboardTracking(False)
        i_cutoff_spin.set_button_only_mode()
        if pid_name == "pid1":
            i_cutoff_spin.connect_live_apply(owner._on_pid1_i_cutoff_finished)
        else:
            i_cutoff_spin.setEnabled(False)

        use_limit_label = QLabel()
        use_limit_check = QCheckBox()
        use_limit_check.stateChanged.connect(getattr(owner, f"_on_{pid_name}_limit_enabled_changed"))

        limit_spin = SafeDoubleSpinBox()
        limit_spin.setRange(0.0, 1000000.0)
        limit_spin.setDecimals(2)
        limit_spin.setKeyboardTracking(False)
        limit_spin.connect_live_apply(getattr(owner, f"_on_{pid_name}_limit_finished"))
        limit_spin.set_button_only_mode(False)

        enable_label = QLabel()
        enable_check = QCheckBox()
        enable_check.stateChanged.connect(getattr(owner, f"_on_{pid_name}_enabled_changed"))

        form.addRow(output_label, output_combo)
        form.addRow(sign_label, sign_check)
        form.addRow(use_i_cutoff_label, use_i_cutoff_check)
        form.addRow(QLabel(), owner._create_target_row("pid", i_cutoff_spin))
        form.addRow(use_limit_label, use_limit_check)
        form.addRow(QLabel(), owner._create_target_row("pid", limit_spin))
        form.addRow(enable_label, enable_check)
        layout.addLayout(form)

        for name, widget in (
            ("title_label", title),
            ("gain_label", gain_label),
            ("gain_spin", gain_spin),
            ("p_label", p_label),
            ("p_spin", p_spin),
            ("i_label", i_label),
            ("i_spin", i_spin),
            ("d_label", d_label),
            ("d_spin", d_spin),
            ("output_channel_label", output_label),
            ("output_channel_combo", output_combo),
            ("sign_label", sign_label),
            ("sign_check", sign_check),
            ("use_i_cutoff_label", use_i_cutoff_label),
            ("use_i_cutoff_check", use_i_cutoff_check),
            ("i_cutoff_spin", i_cutoff_spin),
            ("use_limit_label", use_limit_label),
            ("use_limit_check", use_limit_check),
            ("limit_spin", limit_spin),
            ("enable_label", enable_label),
            ("enable_check", enable_check),
        ):
            setattr(self, f"{pid_name}_{name}", widget)

    def bind_to(self, owner) -> None:
        for name, value in self.__dict__.items():
            if name.startswith(f"{self.pid_name}_"):
                setattr(owner, name, value)
        if self.pid_name == "pid1":
            owner.pid_precision_label = self.pid_precision_label
            owner.pid_precision_buttons = self.pid_precision_buttons
