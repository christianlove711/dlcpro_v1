from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout

from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox, SafeSpinBox, create_toggle_button


class LockSettingsPanel(QFrame):
    EXPORTED_ATTRS = (
        "lock_settings_label",
        "lock_enable_button",
        "lock_hold_button",
        "lock_input_signal_label",
        "lock_input_signal_combo",
        "lock_error_signal_label",
        "lock_error_signal_combo",
        "lock_type_label",
        "lock_type_combo",
        "lock_pid_selection_label",
        "lock_pid_selection_combo",
        "lock_falc_selection_label",
        "lock_falc_selection_combo",
        "lock_without_lockpoint_label",
        "lock_without_lockpoint_check",
        "lock_status_label",
        "lock_status_value",
        "lock_candidate_filter_group",
        "lock_candidate_top_check",
        "lock_candidate_bottom_check",
        "lock_candidate_positive_edge_check",
        "lock_candidate_negative_edge_check",
        "lock_candidate_edge_level_label",
        "lock_candidate_edge_level_spin",
        "lock_candidate_peak_noise_tolerance_label",
        "lock_candidate_peak_noise_tolerance_spin",
        "lock_candidate_edge_min_distance_label",
        "lock_candidate_edge_min_distance_spin",
        "lock_candidate_top_of_fringe_low_pass_label",
        "lock_candidate_top_of_fringe_low_pass_check",
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
        self.lock_input_signal_combo = SafeComboBox()
        self.lock_input_signal_combo.currentIndexChanged.connect(owner._on_lock_input_signal_changed)

        self.lock_error_signal_label = QLabel()
        self.lock_error_signal_combo = SafeComboBox()
        self.lock_error_signal_combo.currentIndexChanged.connect(owner._on_lock_error_signal_changed)

        self.lock_type_label = QLabel()
        self.lock_type_combo = SafeComboBox()
        self.lock_type_combo.currentIndexChanged.connect(owner._on_lock_type_changed)

        self.lock_pid_selection_label = QLabel()
        self.lock_pid_selection_combo = SafeComboBox()
        self.lock_pid_selection_combo.currentIndexChanged.connect(owner._on_lock_pid_selection_changed)

        self.lock_falc_selection_label = QLabel()
        self.lock_falc_selection_combo = SafeComboBox()
        self.lock_falc_selection_combo.currentIndexChanged.connect(owner._on_lock_falc_selection_changed)

        self.lock_without_lockpoint_label = QLabel()
        self.lock_without_lockpoint_check = QCheckBox()
        self.lock_without_lockpoint_check.stateChanged.connect(owner._on_lock_without_lockpoint_changed)

        self.lock_status_label = QLabel()
        self.lock_status_value = QLabel("--")
        self.lock_status_value.setObjectName("SubtleHint")

        form.addRow(self.lock_input_signal_label, self.lock_input_signal_combo)
        form.addRow(self.lock_error_signal_label, self.lock_error_signal_combo)
        form.addRow(self.lock_type_label, self.lock_type_combo)
        form.addRow(self.lock_pid_selection_label, self.lock_pid_selection_combo)
        form.addRow(self.lock_falc_selection_label, self.lock_falc_selection_combo)
        form.addRow(self.lock_without_lockpoint_label, self.lock_without_lockpoint_check)
        form.addRow(self.lock_status_label, self.lock_status_value)
        layout.addLayout(form)

        self.lock_candidate_filter_group = QGroupBox()
        candidate_form = QFormLayout(self.lock_candidate_filter_group)
        candidate_form.setLabelAlignment(Qt.AlignLeft)
        candidate_form.setFormAlignment(Qt.AlignTop)
        candidate_form.setHorizontalSpacing(18)
        candidate_form.setVerticalSpacing(12)

        self.lock_candidate_top_check = QCheckBox()
        self.lock_candidate_top_check.toggled.connect(owner._on_lock_candidate_top_changed)
        candidate_form.addRow(QLabel(), self._labeled_checkbox(self.lock_candidate_top_check))

        self.lock_candidate_bottom_check = QCheckBox()
        self.lock_candidate_bottom_check.toggled.connect(owner._on_lock_candidate_bottom_changed)
        candidate_form.addRow(QLabel(), self._labeled_checkbox(self.lock_candidate_bottom_check))

        self.lock_candidate_positive_edge_check = QCheckBox()
        self.lock_candidate_positive_edge_check.toggled.connect(owner._on_lock_candidate_positive_edge_changed)
        candidate_form.addRow(QLabel(), self._labeled_checkbox(self.lock_candidate_positive_edge_check))

        self.lock_candidate_negative_edge_check = QCheckBox()
        self.lock_candidate_negative_edge_check.toggled.connect(owner._on_lock_candidate_negative_edge_changed)
        candidate_form.addRow(QLabel(), self._labeled_checkbox(self.lock_candidate_negative_edge_check))

        self.lock_candidate_edge_level_label = QLabel()
        self.lock_candidate_edge_level_spin = SafeDoubleSpinBox()
        self.lock_candidate_edge_level_spin.setDecimals(5)
        self.lock_candidate_edge_level_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.lock_candidate_edge_level_spin.setSingleStep(0.001)
        self.lock_candidate_edge_level_spin.connect_live_apply(owner._on_lock_candidate_edge_level_finished)
        candidate_form.addRow(self.lock_candidate_edge_level_label, self.lock_candidate_edge_level_spin)

        self.lock_candidate_peak_noise_tolerance_label = QLabel()
        self.lock_candidate_peak_noise_tolerance_spin = SafeDoubleSpinBox()
        self.lock_candidate_peak_noise_tolerance_spin.setDecimals(5)
        self.lock_candidate_peak_noise_tolerance_spin.setRange(0.0, 1_000_000_000.0)
        self.lock_candidate_peak_noise_tolerance_spin.setSingleStep(0.001)
        self.lock_candidate_peak_noise_tolerance_spin.connect_live_apply(
            owner._on_lock_candidate_peak_noise_tolerance_finished
        )
        candidate_form.addRow(
            self.lock_candidate_peak_noise_tolerance_label,
            self.lock_candidate_peak_noise_tolerance_spin,
        )

        self.lock_candidate_edge_min_distance_label = QLabel()
        self.lock_candidate_edge_min_distance_spin = SafeSpinBox()
        self.lock_candidate_edge_min_distance_spin.setRange(0, 1_000_000_000)
        self.lock_candidate_edge_min_distance_spin.setSingleStep(1)
        self.lock_candidate_edge_min_distance_spin.connect_live_apply(owner._on_lock_candidate_edge_min_distance_finished)
        candidate_form.addRow(self.lock_candidate_edge_min_distance_label, self.lock_candidate_edge_min_distance_spin)

        self.lock_candidate_top_of_fringe_low_pass_label = QLabel()
        self.lock_candidate_top_of_fringe_low_pass_check = QCheckBox()
        self.lock_candidate_top_of_fringe_low_pass_check.toggled.connect(
            owner._on_lock_candidate_top_of_fringe_low_pass_changed
        )
        candidate_form.addRow(
            self.lock_candidate_top_of_fringe_low_pass_label,
            self.lock_candidate_top_of_fringe_low_pass_check,
        )
        layout.addWidget(self.lock_candidate_filter_group)

    def bind_to(self, owner) -> None:
        for name in self.EXPORTED_ATTRS:
            setattr(owner, name, getattr(self, name))

    @staticmethod
    def _labeled_checkbox(checkbox: QCheckBox):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        row.addWidget(checkbox)
        container = QFrame()
        container.setLayout(row)
        return container
