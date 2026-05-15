from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox, SafeSpinBox


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

        self.overview_hint_label = QLabel()
        self.overview_hint_label.setObjectName("SubtleHint")
        self.overview_hint_label.setWordWrap(True)
        layout.addWidget(self.overview_hint_label)

        self._basic_section_title = ""
        self._advanced_section_title = ""
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        layout.addLayout(grid)

        self.quick_link_group = QGroupBox()
        quick_link_form = QFormLayout(self.quick_link_group)
        quick_link_form.setLabelAlignment(Qt.AlignLeft)
        quick_link_form.setFormAlignment(Qt.AlignTop)
        quick_link_form.setHorizontalSpacing(18)
        quick_link_form.setVerticalSpacing(12)

        self.error_signal_label = QLabel()
        self.error_signal_combo = SafeComboBox()
        self._configure_combo(self.error_signal_combo)
        quick_link_form.addRow(self.error_signal_label, self.error_signal_combo)

        self.falc_selection_label = QLabel()
        self.falc_selection_combo = SafeComboBox()
        self._configure_combo(self.falc_selection_combo)
        quick_link_form.addRow(self.falc_selection_label, self.falc_selection_combo)

        self.falc_path_label = QLabel()
        self.falc_path_combo = SafeComboBox()
        self._configure_combo(self.falc_path_combo)
        quick_link_form.addRow(self.falc_path_label, self.falc_path_combo)
        grid.addWidget(self.quick_link_group, 0, 0, 1, 2)

        self.preset_group = QGroupBox()
        preset_layout = QVBoxLayout(self.preset_group)
        preset_layout.setContentsMargins(14, 14, 14, 14)
        preset_layout.setSpacing(12)

        self.preset_scope_hint_label = QLabel()
        self.preset_scope_hint_label.setObjectName("SubtleHint")
        self.preset_scope_hint_label.setWordWrap(True)
        preset_layout.addWidget(self.preset_scope_hint_label)

        preset_form = QFormLayout()
        preset_form.setLabelAlignment(Qt.AlignLeft)
        preset_form.setFormAlignment(Qt.AlignTop)
        preset_form.setHorizontalSpacing(18)
        preset_form.setVerticalSpacing(12)
        preset_layout.addLayout(preset_form)

        self.preset_button_list_label = QLabel()
        self.preset_button_grid = QGridLayout()
        self.preset_button_grid.setContentsMargins(0, 0, 0, 0)
        self.preset_button_grid.setHorizontalSpacing(8)
        self.preset_button_grid.setVerticalSpacing(8)
        self.preset_button_container = QFrame()
        self.preset_button_container.setLayout(self.preset_button_grid)
        self.preset_button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        preset_form.addRow(self.preset_button_list_label, self.preset_button_container)

        self.preset_name_label = QLabel()
        self.preset_name_edit = QLineEdit()
        preset_form.addRow(self.preset_name_label, self.preset_name_edit)

        self.preset_button_row = QHBoxLayout()
        self.preset_button_row.setContentsMargins(0, 0, 0, 0)
        self.preset_button_row.setSpacing(10)
        self.preset_new_button = QPushButton()
        self.preset_save_button = QPushButton()
        self.preset_delete_button = QPushButton()
        self.preset_button_row.addWidget(self.preset_new_button)
        self.preset_button_row.addWidget(self.preset_save_button)
        self.preset_button_row.addWidget(self.preset_delete_button)
        self.preset_button_row.addStretch(1)
        preset_buttons_container = QFrame()
        preset_buttons_container.setLayout(self.preset_button_row)
        preset_form.addRow(QLabel(""), preset_buttons_container)

        self.preset_details_label = QLabel()
        self.preset_details_container = QFrame()
        self.preset_details_container.setObjectName("PresetDetailsPanel")
        self.preset_details_layout = QGridLayout(self.preset_details_container)
        self.preset_details_layout.setContentsMargins(0, 0, 0, 0)
        self.preset_details_layout.setHorizontalSpacing(10)
        self.preset_details_layout.setVerticalSpacing(10)
        preset_form.addRow(self.preset_details_label, self.preset_details_container)
        grid.addWidget(self.preset_group, 1, 0, 1, 2)

        self.basic_form_group = QGroupBox()
        basic_layout = QVBoxLayout(self.basic_form_group)
        basic_layout.setContentsMargins(14, 14, 14, 14)
        basic_layout.setSpacing(12)

        self.pre_scan_usage_hint_label = QLabel()
        self.pre_scan_usage_hint_label.setObjectName("SubtleHint")
        self.pre_scan_usage_hint_label.setWordWrap(True)
        basic_layout.addWidget(self.pre_scan_usage_hint_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        basic_layout.addLayout(form)

        self.strategy_label = QLabel()
        self.strategy_combo = SafeComboBox()
        self._configure_combo(self.strategy_combo)

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

        self.pre_scan_duration_label = QLabel()
        self.pre_scan_duration_spin = SafeSpinBox()
        self.pre_scan_duration_spin.setRange(1_000, 60_000)
        self.pre_scan_duration_spin.setValue(10_000)

        self.pre_scan_shrink_percent_label = QLabel()
        self.pre_scan_shrink_percent_spin = SafeSpinBox()
        self.pre_scan_shrink_percent_spin.setRange(5, 95)
        self.pre_scan_shrink_percent_spin.setValue(20)

        form.addRow(self.strategy_label, self.strategy_combo)
        form.addRow(self.pre_scan_duration_label, self.pre_scan_duration_spin)
        form.addRow(self.pre_scan_shrink_percent_label, self.pre_scan_shrink_percent_spin)
        form.addRow(self.search_interval_label, self.search_interval_spin)
        form.addRow(self.settle_delay_label, self.settle_delay_spin)
        form.addRow(self.lock_timeout_label, self.lock_timeout_spin)
        form.addRow(self.monitor_interval_label, self.monitor_interval_spin)
        form.addRow(self.reacquire_delay_label, self.reacquire_delay_spin)
        grid.addWidget(self.basic_form_group, 2, 0)

        self.candidate_filter_group = QGroupBox()
        candidate_form = QFormLayout(self.candidate_filter_group)
        candidate_form.setLabelAlignment(Qt.AlignLeft)
        candidate_form.setFormAlignment(Qt.AlignTop)
        candidate_form.setHorizontalSpacing(18)
        candidate_form.setVerticalSpacing(12)

        self.candidate_top_check = QCheckBox()
        candidate_form.addRow(QLabel(), self._aligned_checkbox(self.candidate_top_check))

        self.candidate_bottom_check = QCheckBox()
        candidate_form.addRow(QLabel(), self._aligned_checkbox(self.candidate_bottom_check))

        self.candidate_positive_edge_check = QCheckBox()
        candidate_form.addRow(QLabel(), self._aligned_checkbox(self.candidate_positive_edge_check))

        self.candidate_negative_edge_check = QCheckBox()
        candidate_form.addRow(QLabel(), self._aligned_checkbox(self.candidate_negative_edge_check))

        self.candidate_edge_level_label = QLabel()
        self.candidate_edge_level_spin = SafeDoubleSpinBox()
        self.candidate_edge_level_spin.setDecimals(5)
        self.candidate_edge_level_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.candidate_edge_level_spin.setSingleStep(0.001)
        candidate_form.addRow(self.candidate_edge_level_label, self.candidate_edge_level_spin)

        self.candidate_peak_noise_tolerance_label = QLabel()
        self.candidate_peak_noise_tolerance_spin = SafeDoubleSpinBox()
        self.candidate_peak_noise_tolerance_spin.setDecimals(5)
        self.candidate_peak_noise_tolerance_spin.setRange(0.0, 1_000_000_000.0)
        self.candidate_peak_noise_tolerance_spin.setSingleStep(0.001)
        candidate_form.addRow(
            self.candidate_peak_noise_tolerance_label,
            self.candidate_peak_noise_tolerance_spin,
        )

        self.candidate_edge_min_distance_label = QLabel()
        self.candidate_edge_min_distance_spin = SafeSpinBox()
        self.candidate_edge_min_distance_spin.setRange(0, 1_000_000_000)
        candidate_form.addRow(self.candidate_edge_min_distance_label, self.candidate_edge_min_distance_spin)

        self.candidate_top_of_fringe_low_pass_label = QLabel()
        self.candidate_top_of_fringe_low_pass_check = QCheckBox()
        candidate_form.addRow(
            self.candidate_top_of_fringe_low_pass_label,
            self.candidate_top_of_fringe_low_pass_check,
        )
        grid.addWidget(self.candidate_filter_group, 2, 1)

        self.runtime_options_group = QGroupBox()
        runtime_layout = QVBoxLayout(self.runtime_options_group)
        runtime_layout.setContentsMargins(14, 14, 14, 14)
        runtime_layout.setSpacing(12)

        self.runtime_hint_label = QLabel()
        self.runtime_hint_label.setObjectName("SubtleHint")
        self.runtime_hint_label.setWordWrap(True)
        runtime_layout.addWidget(self.runtime_hint_label)

        self.auto_enable_scan_check = QCheckBox()
        self.auto_enable_scan_check.setChecked(True)
        runtime_layout.addWidget(self.auto_enable_scan_check)

        self.watch_after_lock_check = QCheckBox()
        self.watch_after_lock_check.setChecked(True)
        runtime_layout.addWidget(self.watch_after_lock_check)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 8, 0, 0)
        button_row.setSpacing(10)
        self.pre_scan_button = QPushButton()
        self.start_button = QPushButton()
        self.stop_button = QPushButton()
        self.clear_log_button = QPushButton()
        button_row.addWidget(self.pre_scan_button)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.clear_log_button)
        button_row.addStretch(1)
        runtime_layout.addLayout(button_row)
        grid.addWidget(self.runtime_options_group, 3, 0, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addStretch(1)

    @staticmethod
    def _aligned_checkbox(checkbox: QCheckBox):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        row.addWidget(checkbox)
        container = QFrame()
        container.setLayout(row)
        return container

    def set_section_titles(self, basic_title: str, advanced_title: str) -> None:
        self._basic_section_title = basic_title
        self._advanced_section_title = advanced_title

    @staticmethod
    def _configure_combo(combo: SafeComboBox) -> None:
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setMinimumWidth(220)
        combo.setMaximumWidth(360)
