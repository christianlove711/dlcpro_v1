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
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import DeviceSnapshot, FalcSnapshot
from ui_text import FALC_MON_CONFIG_OPTIONS, FALC_PATH_SELECTION_OPTIONS, TEXT
from widgets.common_controls import SafeComboBox, SafeDoubleSpinBox
from windows.base_window import AuxiliaryWindow


class FalcProWindow(AuxiliaryWindow):
    FILTER_NAMES = ("i1", "i2", "i3", "d1", "d2")
    # Inference:
    # The SDK exposes integer values for FALC corner presets, while the Manual only
    # confirms these are preset corner frequencies without listing the full table.
    # We format larger raw values as deci-Hz-derived engineering labels to better
    # match the official GUI, but we always keep the original raw integer as data.
    DISPLAY_SCALE_HZ = 10.0

    def __init__(self, owner) -> None:
        super().__init__()
        self.owner = owner
        self.resize(760, 760)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        root.addWidget(self.title_label)

        self.status_hint = QLabel()
        self.status_hint.setObjectName("SubtleHint")
        self.status_hint.setWordWrap(True)
        root.addWidget(self.status_hint)

        self.link_group = QGroupBox()
        link_layout = QFormLayout(self.link_group)
        link_layout.setContentsMargins(14, 14, 14, 14)
        link_layout.setSpacing(10)

        self.path_selection_label = QLabel()
        self.path_selection_combo = SafeComboBox()
        self.path_selection_combo.currentIndexChanged.connect(owner._on_falc_path_selection_changed)
        self._configure_combo(self.path_selection_combo, minimum=170, maximum=220)
        link_layout.addRow(self.path_selection_label, self.path_selection_combo)

        self.mon_config_label = QLabel()
        self.mon_config_combo = SafeComboBox()
        self.mon_config_combo.currentIndexChanged.connect(owner._on_falc_mon_config_changed)
        self._configure_combo(self.mon_config_combo, minimum=170, maximum=220)
        link_layout.addRow(self.mon_config_label, self.mon_config_combo)

        self.hold_state_label = QLabel()
        self.hold_state_value = QLabel("--")
        self.hold_state_value.setObjectName("ReadValue")
        link_layout.addRow(self.hold_state_label, self.hold_state_value)
        root.addWidget(self.link_group)

        self.input_group = QGroupBox()
        input_layout = QFormLayout(self.input_group)
        input_layout.setContentsMargins(14, 14, 14, 14)
        input_layout.setSpacing(10)

        self.input_gain_label = QLabel()
        self.input_gain_combo = SafeComboBox()
        self.input_gain_combo.addItem("x1", 1)
        self.input_gain_combo.addItem("x5", 5)
        self.input_gain_combo.currentIndexChanged.connect(owner._on_falc_input_gain_changed)
        self._configure_combo(self.input_gain_combo, minimum=150, maximum=190)
        input_layout.addRow(self.input_gain_label, self.input_gain_combo)

        self.input_offset_label = QLabel()
        self.input_offset_spin = SafeDoubleSpinBox()
        self.input_offset_spin.setDecimals(5)
        self.input_offset_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.input_offset_spin.setSingleStep(0.0001)
        self.input_offset_spin.connect_live_apply(owner._on_falc_input_offset_finished)
        self.input_offset_spin.set_button_only_mode()
        input_layout.addRow(self.input_offset_label, self.input_offset_spin)
        root.addWidget(self.input_group)

        self.main_group = QGroupBox()
        main_layout = QVBoxLayout(self.main_group)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        main_header = QHBoxLayout()
        self.main_enable_label = QLabel()
        self.main_enable_button = QPushButton()
        self.main_enable_button.setCheckable(True)
        self.main_enable_button.clicked.connect(owner._on_falc_main_enabled_toggled)
        self.main_indicator = QFrame()
        self.main_indicator.setFixedSize(16, 16)
        self.main_indicator.setStyleSheet("border-radius: 8px; background: #4d4d4d; border: 1px solid #6a6a6a;")
        main_header.addWidget(self.main_enable_label)
        main_header.addStretch(1)
        main_header.addWidget(self.main_enable_button)
        main_header.addWidget(self.main_indicator)
        main_layout.addLayout(main_header)

        self.filter_grid = QGridLayout()
        self.filter_grid.setHorizontalSpacing(12)
        self.filter_grid.setVerticalSpacing(10)

        self.filter_labels: dict[str, QLabel] = {}
        self.filter_combos: dict[str, SafeComboBox] = {}
        self.filter_checks: dict[str, QCheckBox] = {}
        for row, name in enumerate(self.FILTER_NAMES):
            label = QLabel(name.upper())
            combo = self._create_preset_combo(name)
            check = QCheckBox()
            check.toggled.connect(lambda checked, filter_name=name: owner._on_falc_filter_enabled_toggled(filter_name, checked))
            self.filter_labels[name] = label
            self.filter_combos[name] = combo
            self.filter_checks[name] = check
            self.filter_grid.addWidget(label, row, 0)
            self.filter_grid.addWidget(combo, row, 1)
            self.filter_grid.addWidget(check, row, 2)
        main_layout.addLayout(self.filter_grid)

        gain_row = QHBoxLayout()
        self.main_gain_label = QLabel()
        self.main_gain_spin = SafeDoubleSpinBox()
        self.main_gain_spin.setDecimals(2)
        self.main_gain_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.main_gain_spin.setSingleStep(0.1)
        self.main_gain_spin.connect_live_apply(owner._on_falc_main_gain_finished)
        self.main_gain_spin.set_button_only_mode()
        gain_row.addWidget(self.main_gain_label)
        gain_row.addStretch(1)
        gain_row.addWidget(self.main_gain_spin)
        main_layout.addLayout(gain_row)

        self.main_use_external_input_label = QLabel()
        self.main_use_external_input_check = QCheckBox()
        self.main_use_external_input_check.toggled.connect(owner._on_falc_main_use_external_input_toggled)
        main_layout.addLayout(self._create_toggle_row(self.main_use_external_input_label, self.main_use_external_input_check))

        self.main_lock_state_label = QLabel()
        self.main_lock_state_value = QLabel("--")
        self.main_lock_state_value.setObjectName("ReadValue")
        main_layout.addLayout(self._create_value_row(self.main_lock_state_label, self.main_lock_state_value))
        root.addWidget(self.main_group)

        self.unlim_group = QGroupBox()
        unlim_layout = QVBoxLayout(self.unlim_group)
        unlim_layout.setContentsMargins(14, 14, 14, 14)
        unlim_layout.setSpacing(12)

        unlim_header = QHBoxLayout()
        self.unlim_enable_label = QLabel()
        self.unlim_enable_button = QPushButton()
        self.unlim_enable_button.setCheckable(True)
        self.unlim_enable_button.clicked.connect(owner._on_falc_unlim_enabled_toggled)
        self.unlim_enable_indicator = QFrame()
        self.unlim_enable_indicator.setFixedSize(16, 16)
        self.unlim_enable_indicator.setStyleSheet(
            "border-radius: 8px; background: #4d4d4d; border: 1px solid #6a6a6a;"
        )
        self.unlim_hold_button = QPushButton()
        self.unlim_hold_button.setCheckable(True)
        self.unlim_hold_button.clicked.connect(owner._on_falc_unlim_hold_toggled)
        self.unlim_hold_indicator = QFrame()
        self.unlim_hold_indicator.setFixedSize(16, 16)
        self.unlim_hold_indicator.setStyleSheet(
            "border-radius: 8px; background: #4d4d4d; border: 1px solid #6a6a6a;"
        )
        unlim_header.addWidget(self.unlim_enable_label)
        unlim_header.addStretch(1)
        unlim_header.addWidget(self.unlim_enable_button)
        unlim_header.addWidget(self.unlim_enable_indicator)
        unlim_header.addSpacing(12)
        unlim_header.addWidget(self.unlim_hold_button)
        unlim_header.addWidget(self.unlim_hold_indicator)
        unlim_layout.addLayout(unlim_header)

        unlim_form = QFormLayout()
        unlim_form.setHorizontalSpacing(16)
        unlim_form.setVerticalSpacing(10)

        self.unlim_input_offset_label = QLabel()
        self.unlim_input_offset_spin = SafeDoubleSpinBox()
        self.unlim_input_offset_spin.setDecimals(2)
        self.unlim_input_offset_spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
        self.unlim_input_offset_spin.setSingleStep(0.01)
        self.unlim_input_offset_spin.connect_live_apply(owner._on_falc_unlim_input_offset_finished)
        self.unlim_input_offset_spin.set_button_only_mode()
        unlim_form.addRow(self.unlim_input_offset_label, self.unlim_input_offset_spin)

        self.unlim_output_range_label = QLabel()
        self.unlim_output_range_spin = SafeDoubleSpinBox()
        self.unlim_output_range_spin.setDecimals(2)
        self.unlim_output_range_spin.setRange(0.0, 1_000_000_000.0)
        self.unlim_output_range_spin.setSingleStep(0.01)
        self.unlim_output_range_spin.connect_live_apply(owner._on_falc_unlim_output_range_finished)
        unlim_form.addRow(self.unlim_output_range_label, self.unlim_output_range_spin)

        self.unlim_slew_rate_label = QLabel()
        self.unlim_slew_rate_spin = SafeDoubleSpinBox()
        self.unlim_slew_rate_spin.setDecimals(0)
        self.unlim_slew_rate_spin.setRange(1.0, 12.0)
        self.unlim_slew_rate_spin.setSingleStep(1.0)
        self.unlim_slew_rate_spin.connect_live_apply(owner._on_falc_unlim_slew_rate_finished)
        self.unlim_slew_rate_spin.set_button_only_mode()
        unlim_form.addRow(self.unlim_slew_rate_label, self.unlim_slew_rate_spin)

        self.unlim_gain_label = QLabel()
        self.unlim_gain_value = QLabel()
        self.unlim_gain_value.setObjectName("ReadValue")
        unlim_form.addRow(self.unlim_gain_label, self.unlim_gain_value)

        self.unlim_sign_positive_label = QLabel()
        self.unlim_sign_positive_check = QCheckBox()
        self.unlim_sign_positive_check.toggled.connect(owner._on_falc_unlim_sign_toggled)
        sign_row = QHBoxLayout()
        sign_row.setContentsMargins(0, 0, 0, 0)
        sign_row.addWidget(self.unlim_sign_positive_label)
        sign_row.addStretch(1)
        sign_row.addWidget(self.unlim_sign_positive_check)
        sign_container = QWidget()
        sign_container.setLayout(sign_row)
        unlim_form.addRow(QLabel(""), sign_container)

        unlim_layout.addLayout(unlim_form)
        self.unlim_lock_state_label = QLabel()
        self.unlim_lock_state_value = QLabel("--")
        self.unlim_lock_state_value.setObjectName("ReadValue")
        unlim_layout.addLayout(self._create_value_row(self.unlim_lock_state_label, self.unlim_lock_state_value))

        self.unlim_regulating_state_label = QLabel()
        self.unlim_regulating_state_value = QLabel("--")
        self.unlim_regulating_state_value.setObjectName("ReadValue")
        unlim_layout.addLayout(self._create_value_row(self.unlim_regulating_state_label, self.unlim_regulating_state_value))
        root.addWidget(self.unlim_group)

        root.addStretch(1)
        self.setCentralWidget(central)
        self._set_main_indicator(False)
        self._set_unlim_enable_indicator(False)
        self._set_unlim_hold_indicator(False)

    def _create_preset_combo(self, filter_name: str) -> SafeComboBox:
        combo = SafeComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.lineEdit().setAlignment(Qt.AlignLeft)
        self._configure_combo(combo, minimum=170, maximum=220)
        combo.lineEdit().editingFinished.connect(
            lambda filter_key=filter_name: self.owner._on_falc_filter_value_changed(filter_key)
        )
        combo.activated.connect(lambda _index, filter_key=filter_name: self.owner._on_falc_filter_value_changed(filter_key))
        return combo

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['falc']}")
        self.link_group.setTitle(t["falc_link"])
        self.input_group.setTitle(t["falc_input"])
        self.main_group.setTitle(t["falc_main"])
        self.unlim_group.setTitle(t["falc_unlim"])
        self.path_selection_label.setText(t["falc_path_selection"])
        self.mon_config_label.setText(t["falc_mon_config"])
        self.hold_state_label.setText(t["falc_hold_state"])
        self.input_gain_label.setText(t["falc_input_gain"])
        self.input_offset_label.setText(t["falc_offset"])
        self.main_enable_label.setText(t["falc_main"])
        self.main_enable_button.setText(t["enable"])
        self.main_gain_label.setText(t["falc_main_gain"])
        self.main_use_external_input_label.setText(t["falc_main_use_external_input"])
        self.main_lock_state_label.setText(t["falc_main_lock_state"])
        self.unlim_enable_label.setText(t["falc_unlim"])
        self.unlim_enable_button.setText(t["enable"])
        self.unlim_hold_button.setText(t["falc_unlim_hold"])
        self.unlim_input_offset_label.setText(t["falc_unlim_input_offset"])
        self.unlim_output_range_label.setText(t["falc_unlim_output_range"])
        self.unlim_slew_rate_label.setText(t["falc_unlim_slew_rate"])
        self.unlim_gain_label.setText(t["falc_unlim_gain"])
        self.unlim_lock_state_label.setText(t["falc_unlim_lock_state"])
        self.unlim_regulating_state_label.setText(t["falc_unlim_regulating_state"])
        self.unlim_sign_positive_label.setText(t["falc_unlim_sign_positive"])
        self._populate_combo_options(self.path_selection_combo, FALC_PATH_SELECTION_OPTIONS, language)
        self._populate_combo_options(self.mon_config_combo, FALC_MON_CONFIG_OPTIONS, language)
        for name, check in self.filter_checks.items():
            check.setText(f"{t['enable']} {name.upper()}")
        self.input_offset_spin.setSuffix(f" {t['voltage_unit']}")
        self.main_gain_spin.setSuffix(f" {t['falc_gain_unit']}")
        self.unlim_input_offset_spin.setSuffix(f" {t['falc_unlim_input_offset_unit']}")
        self.unlim_output_range_spin.setSuffix(f" {t['voltage_unit']}")
        self.unlim_gain_value.setText(self._format_value_with_unit(0.0, 2, t["falc_unlim_gain_unit"]))
        if self.owner.snapshot is None:
            self.reset_state(language)

    def render_snapshot(self, snapshot: DeviceSnapshot | None) -> None:
        language = self.owner.language
        t = TEXT[language]
        if snapshot is None or snapshot.falc1 is None:
            self.reset_state(language)
            return

        falc = snapshot.falc1
        serial = falc.serial_number or t["not_available"]
        self.title_label.setText(f"FALC 1 (S/N: {serial})")
        self.status_hint.setText(f"{t['latest_message']}: {falc.status_txt or t['not_available']}")

        self._sync_combo_data(self.input_gain_combo, falc.input_gain, f"x{falc.input_gain}")
        self._sync_combo_data(
            self.path_selection_combo,
            falc.path_selection,
            self._localized_option_label(FALC_PATH_SELECTION_OPTIONS, falc.path_selection, language),
        )
        self._sync_combo_data(
            self.mon_config_combo,
            falc.mon_config,
            self._localized_option_label(FALC_MON_CONFIG_OPTIONS, falc.mon_config, language),
        )
        self.hold_state_value.setText(self._state_text(falc.hold_state, language, "active"))
        self._set_spin_if_idle(self.input_offset_spin, falc.input_offset)

        self._update_main_enabled(falc.main.enabled)
        self._set_spin_if_idle(self.main_gain_spin, falc.main.gain_all)
        self.main_use_external_input_check.blockSignals(True)
        self.main_use_external_input_check.setChecked(falc.main.use_external_input)
        self.main_use_external_input_check.blockSignals(False)
        self.main_lock_state_value.setText(self._state_text(falc.main.lock_state, language, "locked"))

        for name in self.FILTER_NAMES:
            combo = self.filter_combos[name]
            check = self.filter_checks[name]
            value = getattr(falc.main, name)
            enabled = getattr(falc.main, f"{name}_enabled")
            self._sync_combo_data(combo, value, self._format_filter_value(value))
            check.blockSignals(True)
            check.setChecked(enabled)
            check.blockSignals(False)

        self._update_unlim_enabled(falc.unlim.enabled)
        self._update_unlim_hold(falc.unlim.hold)
        self._set_spin_if_idle(self.unlim_input_offset_spin, falc.unlim.input_offset)
        self._set_spin_if_idle(self.unlim_output_range_spin, falc.unlim.output_range)
        self._set_spin_if_idle(self.unlim_slew_rate_spin, float(falc.unlim.slew_rate))
        self.unlim_gain_value.setText(self._format_value_with_unit(falc.unlim.gain, 2, t["falc_unlim_gain_unit"]))
        self.unlim_lock_state_value.setText(self._state_text(falc.unlim.lock_state, language, "locked"))
        self.unlim_regulating_state_value.setText(self._state_text(falc.unlim.regulating_state, language, "active"))
        self.unlim_sign_positive_check.blockSignals(True)
        self.unlim_sign_positive_check.setChecked(falc.unlim.sign)
        self.unlim_sign_positive_check.blockSignals(False)

    def reset_state(self, language: str) -> None:
        t = TEXT[language]
        self.title_label.setText(t["falc"])
        self.status_hint.setText(t["falc_unavailable"])
        self._sync_combo_data(self.input_gain_combo, 1, "x1")
        self._sync_combo_data(self.path_selection_combo, 0, t["falc_path_none"])
        self._sync_combo_data(self.mon_config_combo, 0, t["falc_mon_error"])
        self.hold_state_value.setText(t["not_available"])
        self.input_offset_spin.blockSignals(True)
        self.input_offset_spin.setValue(0.0)
        self.input_offset_spin.blockSignals(False)
        self._update_main_enabled(False)
        self.main_gain_spin.blockSignals(True)
        self.main_gain_spin.setValue(0.0)
        self.main_gain_spin.blockSignals(False)
        self.main_use_external_input_check.blockSignals(True)
        self.main_use_external_input_check.setChecked(False)
        self.main_use_external_input_check.blockSignals(False)
        self.main_lock_state_value.setText(t["not_available"])
        for name in self.FILTER_NAMES:
            self._sync_combo_data(self.filter_combos[name], 0, self._format_filter_value(0))
            check = self.filter_checks[name]
            check.blockSignals(True)
            check.setChecked(False)
            check.blockSignals(False)
        self._update_unlim_enabled(False)
        self._update_unlim_hold(False)
        self.unlim_input_offset_spin.blockSignals(True)
        self.unlim_input_offset_spin.setValue(0.0)
        self.unlim_input_offset_spin.blockSignals(False)
        self.unlim_output_range_spin.blockSignals(True)
        self.unlim_output_range_spin.setValue(0.0)
        self.unlim_output_range_spin.blockSignals(False)
        self.unlim_slew_rate_spin.blockSignals(True)
        self.unlim_slew_rate_spin.setValue(1.0)
        self.unlim_slew_rate_spin.blockSignals(False)
        self.unlim_gain_value.setText(self._format_value_with_unit(0.0, 2, t["falc_unlim_gain_unit"]))
        self.unlim_lock_state_value.setText(t["not_available"])
        self.unlim_regulating_state_value.setText(t["not_available"])
        self.unlim_sign_positive_check.blockSignals(True)
        self.unlim_sign_positive_check.setChecked(False)
        self.unlim_sign_positive_check.blockSignals(False)

    def set_writable(self, writable: bool, previewable: bool) -> None:
        self.input_gain_combo.setEnabled(previewable)
        self.path_selection_combo.setEnabled(previewable)
        self.mon_config_combo.setEnabled(previewable)
        for combo in self.filter_combos.values():
            combo.setEnabled(previewable)
        for widget in (
            self.input_offset_spin,
            self.main_enable_button,
            self.main_gain_spin,
            self.main_use_external_input_check,
            self.unlim_enable_button,
            self.unlim_hold_button,
            self.unlim_input_offset_spin,
            self.unlim_output_range_spin,
            self.unlim_slew_rate_spin,
            self.unlim_sign_positive_check,
            *self.filter_checks.values(),
        ):
            widget.setEnabled(writable)

    @staticmethod
    def _set_spin_if_idle(spinbox, value: float) -> None:
        sync_from_device = getattr(spinbox, "sync_from_device", None)
        if callable(sync_from_device):
            sync_from_device(value)
            return
        if spinbox.hasFocus():
            return
        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)

    def _populate_combo_options(self, combo: SafeComboBox, options, language: str) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in options:
            combo.addItem(TEXT[language][text_key], value)
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    @staticmethod
    def _localized_option_label(options, value: int, language: str) -> str:
        for text_key, option_value in options:
            if option_value == value:
                return TEXT[language][text_key]
        return str(value)

    @staticmethod
    def _state_text(value: bool, language: str, style: str) -> str:
        if style == "locked":
            return TEXT[language]["locked_state"] if value else TEXT[language]["unlocked_state"]
        return TEXT[language]["active_state"] if value else TEXT[language]["inactive_state"]

    def current_filter_value(self, filter_name: str) -> int | None:
        combo = self.filter_combos[filter_name]
        data = combo.currentData()
        if isinstance(data, int):
            return data
        text = combo.currentText().strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    def _update_main_enabled(self, enabled: bool) -> None:
        self.main_enable_button.blockSignals(True)
        self.main_enable_button.setChecked(enabled)
        self.main_enable_button.blockSignals(False)
        self._set_main_indicator(enabled)

    def _set_main_indicator(self, enabled: bool) -> None:
        color = "#1ad11a" if enabled else "#4d4d4d"
        border = "#76f176" if enabled else "#6a6a6a"
        self.main_indicator.setStyleSheet(
            f"border-radius: 8px; background: {color}; border: 1px solid {border};"
        )

    def _update_unlim_enabled(self, enabled: bool) -> None:
        self.unlim_enable_button.blockSignals(True)
        self.unlim_enable_button.setChecked(enabled)
        self.unlim_enable_button.blockSignals(False)
        self._set_unlim_enable_indicator(enabled)

    def _update_unlim_hold(self, enabled: bool) -> None:
        self.unlim_hold_button.blockSignals(True)
        self.unlim_hold_button.setChecked(enabled)
        self.unlim_hold_button.blockSignals(False)
        self._set_unlim_hold_indicator(enabled)

    def _set_unlim_enable_indicator(self, enabled: bool) -> None:
        color = "#1ad11a" if enabled else "#4d4d4d"
        border = "#76f176" if enabled else "#6a6a6a"
        self.unlim_enable_indicator.setStyleSheet(
            f"border-radius: 8px; background: {color}; border: 1px solid {border};"
        )

    def _set_unlim_hold_indicator(self, enabled: bool) -> None:
        color = "#1f7a1f" if enabled else "#4d4d4d"
        border = "#5db35d" if enabled else "#6a6a6a"
        self.unlim_hold_indicator.setStyleSheet(
            f"border-radius: 8px; background: {color}; border: 1px solid {border};"
        )

    def _sync_combo_data(self, combo: SafeComboBox, value: int, label: str) -> None:
        index = combo.findData(value)
        if index < 0:
            combo.addItem(label, value)
            index = combo.count() - 1
        else:
            combo.setItemText(index, label)
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.setEditText(label)
        combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    def _configure_combo(self, combo: SafeComboBox, minimum: int, maximum: int) -> None:
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setMinimumWidth(minimum)
        combo.setMaximumWidth(maximum)
        self._fit_combo_popup_width(combo)

    def _fit_combo_popup_width(self, combo: SafeComboBox) -> None:
        metrics = combo.fontMetrics()
        widths = [metrics.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())]
        current_width = metrics.horizontalAdvance(combo.currentText()) if combo.currentText() else 0
        content_width = max(widths + [current_width, combo.minimumWidth()])
        target_width = content_width + 52
        combo.view().setMinimumWidth(target_width)
        combo.setMinimumWidth(min(target_width, combo.maximumWidth()))

    def _format_filter_value(self, raw_value: int) -> str:
        if raw_value <= 0:
            return str(raw_value)
        if raw_value < 10:
            return f"Preset {raw_value}"
        frequency_hz = raw_value / self.DISPLAY_SCALE_HZ
        return self._format_frequency_label(frequency_hz)

    @staticmethod
    def _format_frequency_label(frequency_hz: float) -> str:
        if frequency_hz >= 1_000_000:
            value = frequency_hz / 1_000_000
            unit = "MHz"
        elif frequency_hz >= 1_000:
            value = frequency_hz / 1_000
            unit = "kHz"
        else:
            value = frequency_hz
            unit = "Hz"

        if value >= 100:
            text = f"{value:.0f}"
        elif value >= 10:
            text = f"{value:.1f}".rstrip("0").rstrip(".")
        else:
            text = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"{text} {unit}"

    @staticmethod
    def _format_value_with_unit(value: float, decimals: int, unit: str) -> str:
        return f"{value:.{decimals}f} {unit}"

    @staticmethod
    def _create_toggle_row(label: QLabel, checkbox: QCheckBox) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(checkbox)
        return row

    @staticmethod
    def _create_value_row(label: QLabel, value_widget: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(value_widget)
        return row
