from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.auto_lock2_acquisition import AcquisitionConfig, AcquisitionFrame
from controllers.auto_lock2_settings import AutoLock2Settings
from ui_scaling import fit_window_to_screen
from ui_text import AUTO_LOCK2_STRATEGY_OPTIONS, FALC_PATH_SELECTION_OPTIONS, TEXT
from widgets.auto_lock2 import AutoLock2SignalPlot
from widgets.common_controls import PrecisionButtonRow, SafeComboBox, SafeDoubleSpinBox, SafeSpinBox
from windows.base_window import AuxiliaryWindow, set_scrollable_central_widget


class AutoLock2LogWindow(AuxiliaryWindow):
    def __init__(self, owner) -> None:
        super().__init__(owner)
        self.resize(920, 620)
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.log_edit.clear)
        layout.addWidget(self.log_edit, 1)
        layout.addWidget(self.clear_button, 0, Qt.AlignRight)
        self.setCentralWidget(central)

    def apply_texts(self, language: str) -> None:
        self._language = language
        t = TEXT[language]
        self.setWindowTitle(t["auto_lock2_log_title"])
        self.clear_button.setText(t["auto_lock2_clear_log"])

    def append_log(self, line: str) -> None:
        self.log_edit.append(line)


class AutoLock2WaveformWindow(AuxiliaryWindow):
    def __init__(self, owner) -> None:
        super().__init__(owner)
        self.resize(1120, 700)
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        self.waveform_group = QGroupBox()
        waveform_layout = QVBoxLayout(self.waveform_group)
        waveform_layout.setContentsMargins(12, 12, 12, 12)
        self.signal_plot = AutoLock2SignalPlot()
        self.signal_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        waveform_layout.addWidget(self.signal_plot, 1)
        root.addWidget(self.waveform_group, 1)

        self.setCentralWidget(central)

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['auto_lock2_title']} - {t['auto_lock2_waveform']}")
        self.waveform_group.setTitle(t["auto_lock2_waveform"])
        self.signal_plot.set_labels(
            {
                "transmission": t["auto_lock2_transmission"],
                "error": t["auto_lock2_error"],
                "empty": t["auto_lock2_waiting_frame"],
                "peak": t["auto_lock2_peak"],
                "zero": t["auto_lock2_zero"],
            }
        )

    def render_frame(self, frame: AcquisitionFrame, analysis) -> None:
        self.signal_plot.set_frame(
            frame,
            analysis.message,
            peak_fraction=analysis.peak_fraction,
            zero_fraction=analysis.zero_fraction,
        )

    def reset_state(self, language: str) -> None:
        self.signal_plot.set_frame(None, TEXT[language]["auto_lock2_waiting_frame"])


class AutoLock2ConfigDialog(QDialog):
    settingsApplied = Signal(object)
    PRESET_PATH = Path(__file__).resolve().parents[1] / "auto_lock2_algorithm_presets.json"
    COMMON_PARAMETER_KEYS = {
        "auto_lock2_config_wide_amplitude",
        "auto_lock2_config_min_amplitude",
        "auto_lock2_config_shrink_factor",
        "auto_lock2_config_offset_step",
        "auto_lock2_config_stable_frames",
        "auto_lock2_config_max_attempts",
        "auto_lock2_config_correction_gain",
    }
    TRANSMISSION_PARAMETER_KEYS = {
        "auto_lock2_config_peak_center_tolerance",
        "auto_lock2_config_transmission_peak_sigma",
        "auto_lock2_config_min_transmission_prominence",
    }
    ERROR_PARAMETER_KEYS = {
        "auto_lock2_config_zero_center_tolerance",
        "auto_lock2_config_error_slope_sigma",
        "auto_lock2_config_min_error_slope",
    }
    PROTECTION_PARAMETER_KEYS = {
        "auto_lock2_config_transmission_guard_tolerance",
    }
    PRECISION_OPTIONS = (
        ("step_100", 100.0),
        ("step_10", 10.0),
        ("step_1_int", 1.0),
        ("step_1", 0.1),
        ("step_2", 0.01),
        ("step_3", 0.001),
        ("step_4", 0.0001),
        ("step_5", 0.00001),
        ("step_6", 0.000001),
    )

    def __init__(self, settings: AutoLock2Settings, language: str, parent=None) -> None:
        super().__init__(parent)
        self._language = language
        self.setModal(False)
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
        )
        self.setSizeGripEnabled(True)
        self.setWindowTitle(TEXT[language]["auto_lock2_algorithm_config"])
        self._preset_store: dict[str, dict[str, object]] = {}
        self._selected_preset_name: str | None = None
        self._loaded_preset_name: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.preset_group = QGroupBox()
        preset_layout = QGridLayout(self.preset_group)
        preset_layout.setHorizontalSpacing(12)
        preset_layout.setVerticalSpacing(10)
        self.preset_select_label = QLabel()
        self.preset_combo = SafeComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_combo_changed)
        self.preset_loaded_label = QLabel()
        self.preset_loaded_value = QLabel()
        self.preset_loaded_value.setObjectName("ReadValue")
        self.preset_name_label = QLabel()
        self.preset_name_edit = QLineEdit()
        self.preset_new_button = QPushButton()
        self.preset_new_button.clicked.connect(self._new_preset)
        self.preset_load_button = QPushButton()
        self.preset_load_button.clicked.connect(self._load_selected_preset)
        self.preset_save_button = QPushButton()
        self.preset_save_button.clicked.connect(self._save_current_preset)
        self.preset_delete_button = QPushButton()
        self.preset_delete_button.clicked.connect(self._delete_selected_preset)
        preset_layout.addWidget(self.preset_select_label, 0, 0)
        preset_layout.addWidget(self.preset_combo, 0, 1, 1, 2)
        preset_layout.addWidget(self.preset_loaded_label, 0, 3)
        preset_layout.addWidget(self.preset_loaded_value, 0, 4)
        preset_layout.addWidget(self.preset_name_label, 1, 0)
        preset_layout.addWidget(self.preset_name_edit, 1, 1, 1, 2)
        preset_layout.addWidget(self.preset_new_button, 1, 3)
        preset_layout.addWidget(self.preset_save_button, 1, 4)
        preset_layout.addWidget(self.preset_load_button, 2, 1)
        preset_layout.addWidget(self.preset_delete_button, 2, 2)
        preset_layout.setColumnStretch(1, 1)
        preset_layout.setColumnStretch(2, 1)
        content_layout.addWidget(self.preset_group)

        precision_row = QHBoxLayout()
        precision_row.setContentsMargins(0, 0, 0, 0)
        precision_row.setSpacing(12)
        self.step_precision_label = QLabel()
        self.precision_buttons = PrecisionButtonRow(
            self.PRECISION_OPTIONS,
            self._set_precision_step,
            max_columns=5,
        )
        precision_row.addWidget(self.step_precision_label, 0, Qt.AlignTop)
        precision_row.addWidget(self.precision_buttons, 1)
        content_layout.addLayout(precision_row)

        self.strategy_group = QGroupBox()
        strategy_form = QFormLayout(self.strategy_group)
        strategy_form.setHorizontalSpacing(16)
        strategy_form.setVerticalSpacing(10)
        self.strategy_label = QLabel()
        self.strategy_combo = SafeComboBox()
        self._populate_strategy_options(language)
        self.strategy_help_button = QPushButton("!", self)
        self.strategy_help_button.setObjectName("ParameterHelpButton")
        self.strategy_help_button.setFixedWidth(28)
        self.strategy_help_button.clicked.connect(lambda checked=False: self._show_parameter_help("auto_lock2_config_strategy"))
        strategy_row = QWidget(self)
        strategy_layout = QHBoxLayout(strategy_row)
        strategy_layout.setContentsMargins(0, 0, 0, 0)
        strategy_layout.setSpacing(8)
        strategy_layout.addWidget(self.strategy_combo, 1)
        strategy_layout.addWidget(self.strategy_help_button, 0)
        strategy_form.addRow(self.strategy_label, strategy_row)
        content_layout.addWidget(self.strategy_group)

        self.wide_amplitude = self._double(settings.wide_amplitude, 0.0, 1_000_000.0, 6)
        self.min_amplitude = self._double(settings.min_amplitude, 0.0, 1_000_000.0, 6)
        self.shrink_factor = self._double(settings.shrink_factor, 0.05, 0.99, 3)
        self.offset_step = self._double(settings.offset_step, 0.000001, 1_000_000.0, 6)
        self.peak_center_tolerance = self._double(settings.peak_center_tolerance, 0.001, 0.49, 3)
        self.zero_center_tolerance = self._double(settings.zero_center_tolerance, 0.001, 0.49, 3)
        self.transmission_guard_tolerance = self._double(settings.transmission_guard_tolerance, 0.001, 0.49, 3)
        self.error_slope_sigma = self._double(settings.error_slope_sigma, 0.5, 100.0, 2)
        self.min_error_slope = self._double(settings.min_error_slope, 0.0, 1_000_000.0, 6)
        self.transmission_peak_sigma = self._double(settings.transmission_peak_sigma, 0.5, 100.0, 2)
        self.min_transmission_prominence = self._double(settings.min_transmission_prominence, 0.0, 1_000_000.0, 6)
        self.stable_frames = self._int(settings.stable_frames, 1, 100)
        self.max_attempts = self._int(settings.max_offset_attempts, 1, 10_000)
        self.correction_gain = self._double(settings.offset_correction_gain, 0.05, 2.0, 3)

        self._current_step = 0.01
        self._step_target = self.zero_center_tolerance
        self._target_buttons: list[QPushButton] = []
        self._role_labels: dict[str, QLabel] = {}
        self._group_boxes: dict[str, QGroupBox] = {}
        self._field_rows = (
            ("auto_lock2_config_wide_amplitude", self.wide_amplitude),
            ("auto_lock2_config_min_amplitude", self.min_amplitude),
            ("auto_lock2_config_shrink_factor", self.shrink_factor),
            ("auto_lock2_config_offset_step", self.offset_step),
            ("auto_lock2_config_peak_center_tolerance", self.peak_center_tolerance),
            ("auto_lock2_config_zero_center_tolerance", self.zero_center_tolerance),
            ("auto_lock2_config_transmission_guard_tolerance", self.transmission_guard_tolerance),
            ("auto_lock2_config_error_slope_sigma", self.error_slope_sigma),
            ("auto_lock2_config_min_error_slope", self.min_error_slope),
            ("auto_lock2_config_transmission_peak_sigma", self.transmission_peak_sigma),
            ("auto_lock2_config_min_transmission_prominence", self.min_transmission_prominence),
            ("auto_lock2_config_stable_frames", self.stable_frames),
            ("auto_lock2_config_max_attempts", self.max_attempts),
            ("auto_lock2_config_correction_gain", self.correction_gain),
        )
        self._field_labels: dict[str, QLabel] = {}
        self._parameter_groups = (
            (
                "auto_lock2_config_group_common",
                (
                    ("auto_lock2_config_wide_amplitude", self.wide_amplitude),
                    ("auto_lock2_config_min_amplitude", self.min_amplitude),
                    ("auto_lock2_config_shrink_factor", self.shrink_factor),
                    ("auto_lock2_config_offset_step", self.offset_step),
                    ("auto_lock2_config_stable_frames", self.stable_frames),
                    ("auto_lock2_config_max_attempts", self.max_attempts),
                    ("auto_lock2_config_correction_gain", self.correction_gain),
                ),
            ),
            (
                "auto_lock2_config_group_transmission",
                (
                    ("auto_lock2_config_peak_center_tolerance", self.peak_center_tolerance),
                    ("auto_lock2_config_transmission_peak_sigma", self.transmission_peak_sigma),
                    ("auto_lock2_config_min_transmission_prominence", self.min_transmission_prominence),
                ),
            ),
            (
                "auto_lock2_config_group_error",
                (
                    ("auto_lock2_config_zero_center_tolerance", self.zero_center_tolerance),
                    ("auto_lock2_config_error_slope_sigma", self.error_slope_sigma),
                    ("auto_lock2_config_min_error_slope", self.min_error_slope),
                ),
            ),
            (
                "auto_lock2_config_group_protection",
                (
                    ("auto_lock2_config_transmission_guard_tolerance", self.transmission_guard_tolerance),
                ),
            ),
        )
        for group_key, rows in self._parameter_groups:
            group = QGroupBox(TEXT[language][group_key])
            form = QFormLayout(group)
            form.setHorizontalSpacing(16)
            form.setVerticalSpacing(10)
            for key, widget in rows:
                label = QLabel(TEXT[language][key])
                row = self._parameter_row(widget, key)
                self._field_labels[key] = label
                form.addRow(label, row)
            self._group_boxes[group_key] = group
            content_layout.addWidget(group)
        content_layout.addStretch(1)
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._set_precision_step(self._current_step)
        self._sync_target_buttons()
        self._populate_presets()
        self.strategy_combo.currentIndexChanged.connect(self._update_parameter_roles)
        self._update_parameter_roles()

    def apply_texts(self, language: str) -> None:
        self._language = language
        t = TEXT[language]
        self.setWindowTitle(t["auto_lock2_algorithm_config"])
        self.strategy_group.setTitle(t["auto_lock2_config_strategy_group"])
        self.preset_group.setTitle(t["auto_lock2_preset_group"])
        self.preset_select_label.setText(t["auto_lock2_preset_select"])
        self.preset_loaded_label.setText(t["auto_lock2_preset_loaded"])
        self.preset_name_label.setText(t["auto_lock2_preset_name"])
        self.preset_new_button.setText(t["auto_lock2_preset_new"])
        self.preset_load_button.setText(t["auto_lock2_preset_load"])
        self.preset_save_button.setText(t["auto_lock2_preset_save"])
        self.preset_delete_button.setText(t["auto_lock2_preset_delete"])
        self._populate_presets(selected_name=self._selected_preset_name)
        self.strategy_label.setText(t["auto_lock2_config_strategy"])
        self._populate_strategy_options(language)
        self.step_precision_label.setText(t["step_precision"])
        for button in self.precision_buttons.buttons:
            button.setText(t[button._text_key])
        for button in self._target_buttons:
            button.setText(t["precision_target"])
        for group_key, group in self._group_boxes.items():
            group.setTitle(t[group_key])
        for key, widget in self._field_rows:
            label = self._field_labels.get(key)
            if label is not None:
                label.setText(t[key])
        self._update_parameter_roles()

    def _populate_strategy_options(self, language: str) -> None:
        current = self.strategy_combo.currentData() if hasattr(self, "strategy_combo") else None
        self.strategy_combo.blockSignals(True)
        self.strategy_combo.clear()
        for text_key, value in AUTO_LOCK2_STRATEGY_OPTIONS:
            self.strategy_combo.addItem(TEXT[language][text_key], value)
        target = current or "hybrid"
        index = self.strategy_combo.findData(target)
        self.strategy_combo.setCurrentIndex(index if index >= 0 else 0)
        self.strategy_combo.blockSignals(False)

    def _set_strategy(self, strategy: str) -> None:
        index = self.strategy_combo.findData(strategy)
        self.strategy_combo.blockSignals(True)
        self.strategy_combo.setCurrentIndex(index if index >= 0 else 0)
        self.strategy_combo.blockSignals(False)
        self._update_parameter_roles()

    def _role_for_parameter(self, key: str) -> str:
        strategy = str(self.strategy_combo.currentData() or "hybrid")
        if key in self.COMMON_PARAMETER_KEYS:
            return "common"
        if key in self.PROTECTION_PARAMETER_KEYS:
            return "guard"
        if strategy == "transmission_primary":
            if key in self.TRANSMISSION_PARAMETER_KEYS:
                return "primary"
            if key in self.ERROR_PARAMETER_KEYS:
                return "secondary"
        if strategy == "error_primary":
            if key in self.ERROR_PARAMETER_KEYS:
                return "primary"
            if key in {"auto_lock2_config_transmission_peak_sigma", "auto_lock2_config_min_transmission_prominence"}:
                return "guard"
            if key == "auto_lock2_config_peak_center_tolerance":
                return "unused"
        if strategy == "hybrid":
            if key in {"auto_lock2_config_transmission_peak_sigma", "auto_lock2_config_min_transmission_prominence"}:
                return "primary"
            if key in self.ERROR_PARAMETER_KEYS:
                return "primary"
            if key == "auto_lock2_config_peak_center_tolerance":
                return "secondary"
        return "secondary"

    def _update_parameter_roles(self, *_args) -> None:
        t = TEXT[self._language]
        for key, label in self._role_labels.items():
            role = self._role_for_parameter(key)
            label.setText(t[f"auto_lock2_role_{role}"])
            label.setToolTip(t[f"auto_lock2_role_{role}_hint"])
            label.setProperty("role", role)
            label.style().unpolish(label)
            label.style().polish(label)
            label.update()

    def load_settings(self, settings: AutoLock2Settings) -> None:
        self._set_strategy(settings.strategy)
        values = (
            (self.wide_amplitude, settings.wide_amplitude),
            (self.min_amplitude, settings.min_amplitude),
            (self.shrink_factor, settings.shrink_factor),
            (self.offset_step, settings.offset_step),
            (self.peak_center_tolerance, settings.peak_center_tolerance),
            (self.zero_center_tolerance, settings.zero_center_tolerance),
            (self.transmission_guard_tolerance, settings.transmission_guard_tolerance),
            (self.error_slope_sigma, settings.error_slope_sigma),
            (self.min_error_slope, settings.min_error_slope),
            (self.transmission_peak_sigma, settings.transmission_peak_sigma),
            (self.min_transmission_prominence, settings.min_transmission_prominence),
            (self.stable_frames, settings.stable_frames),
            (self.max_attempts, settings.max_offset_attempts),
            (self.correction_gain, settings.offset_correction_gain),
        )
        for spin, value in values:
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)

    def settings(self) -> AutoLock2Settings:
        return AutoLock2Settings(
            strategy=str(self.strategy_combo.currentData() or "hybrid"),
            wide_amplitude=self.wide_amplitude.value(),
            min_amplitude=self.min_amplitude.value(),
            shrink_factor=self.shrink_factor.value(),
            offset_step=self.offset_step.value(),
            peak_center_tolerance=self.peak_center_tolerance.value(),
            zero_center_tolerance=self.zero_center_tolerance.value(),
            transmission_guard_tolerance=self.transmission_guard_tolerance.value(),
            error_slope_sigma=self.error_slope_sigma.value(),
            min_error_slope=self.min_error_slope.value(),
            transmission_peak_sigma=self.transmission_peak_sigma.value(),
            min_transmission_prominence=self.min_transmission_prominence.value(),
            stable_frames=self.stable_frames.value(),
            max_offset_attempts=self.max_attempts.value(),
            offset_correction_gain=self.correction_gain.value(),
        )

    def _settings_payload(self, settings: AutoLock2Settings) -> dict[str, object]:
        return {
            "strategy": str(settings.strategy),
            "wide_amplitude": float(settings.wide_amplitude),
            "min_amplitude": float(settings.min_amplitude),
            "shrink_factor": float(settings.shrink_factor),
            "offset_step": float(settings.offset_step),
            "peak_center_tolerance": float(settings.peak_center_tolerance),
            "zero_center_tolerance": float(settings.zero_center_tolerance),
            "transmission_guard_tolerance": float(settings.transmission_guard_tolerance),
            "error_slope_sigma": float(settings.error_slope_sigma),
            "min_error_slope": float(settings.min_error_slope),
            "transmission_peak_sigma": float(settings.transmission_peak_sigma),
            "min_transmission_prominence": float(settings.min_transmission_prominence),
            "stable_frames": int(settings.stable_frames),
            "max_offset_attempts": int(settings.max_offset_attempts),
            "offset_correction_gain": float(settings.offset_correction_gain),
        }

    def _settings_from_payload(self, payload: dict[str, object]) -> AutoLock2Settings:
        defaults = AutoLock2Settings()
        return AutoLock2Settings(
            strategy=str(payload.get("strategy", defaults.strategy)),
            wide_amplitude=float(payload.get("wide_amplitude", defaults.wide_amplitude)),
            min_amplitude=float(payload.get("min_amplitude", defaults.min_amplitude)),
            shrink_factor=float(payload.get("shrink_factor", defaults.shrink_factor)),
            offset_step=float(payload.get("offset_step", defaults.offset_step)),
            peak_center_tolerance=float(payload.get("peak_center_tolerance", defaults.peak_center_tolerance)),
            zero_center_tolerance=float(payload.get("zero_center_tolerance", defaults.zero_center_tolerance)),
            transmission_guard_tolerance=float(
                payload.get("transmission_guard_tolerance", defaults.transmission_guard_tolerance)
            ),
            error_slope_sigma=float(payload.get("error_slope_sigma", defaults.error_slope_sigma)),
            min_error_slope=float(payload.get("min_error_slope", defaults.min_error_slope)),
            transmission_peak_sigma=float(payload.get("transmission_peak_sigma", defaults.transmission_peak_sigma)),
            min_transmission_prominence=float(
                payload.get("min_transmission_prominence", defaults.min_transmission_prominence)
            ),
            stable_frames=int(payload.get("stable_frames", defaults.stable_frames)),
            max_offset_attempts=int(payload.get("max_offset_attempts", defaults.max_offset_attempts)),
            offset_correction_gain=float(payload.get("offset_correction_gain", defaults.offset_correction_gain)),
        )

    def _load_preset_store(self) -> None:
        if not self.PRESET_PATH.exists():
            self._preset_store = {}
            return
        try:
            data = json.loads(self.PRESET_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._preset_store = {}
            return
        self._preset_store = data if isinstance(data, dict) else {}

    def _write_preset_store(self) -> bool:
        try:
            self.PRESET_PATH.write_text(
                json.dumps(self._preset_store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            QMessageBox.warning(self, "Warning", TEXT[self._language]["auto_lock2_preset_save_failed"])
            return False
        return True

    def _populate_presets(self, selected_name: str | None = None) -> None:
        t = TEXT[self._language]
        self._load_preset_store()
        current = selected_name if selected_name is not None else self._selected_preset_name
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem(t["auto_lock2_preset_none"], "")
        for name in sorted(self._preset_store):
            self.preset_combo.addItem(name, name)
        index = self.preset_combo.findData(current or "")
        self.preset_combo.setCurrentIndex(index if index >= 0 else 0)
        self.preset_combo.blockSignals(False)
        self._selected_preset_name = current if current in self._preset_store else None
        if self._selected_preset_name:
            self.preset_name_edit.setText(self._selected_preset_name)
        self._refresh_preset_buttons()

    def _on_preset_combo_changed(self) -> None:
        name = str(self.preset_combo.currentData() or "").strip()
        self._selected_preset_name = name or None
        if name:
            self.preset_name_edit.setText(name)
        self._refresh_preset_buttons()

    def _refresh_preset_buttons(self) -> None:
        selected = self._selected_preset_name is not None
        self.preset_load_button.setEnabled(selected)
        self.preset_delete_button.setEnabled(selected)
        self._refresh_loaded_preset_text()

    def _refresh_loaded_preset_text(self) -> None:
        t = TEXT[self._language]
        self.preset_loaded_value.setText(self._loaded_preset_name or t["auto_lock2_preset_none"])

    def _new_preset(self) -> None:
        self._load_preset_store()
        base_name = TEXT[self._language]["auto_lock2_preset_default_name"]
        index = 1
        name = f"{base_name} {index}"
        while name in self._preset_store:
            index += 1
            name = f"{base_name} {index}"
        self._selected_preset_name = None
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)
        self.preset_name_edit.setText(name)
        self._refresh_preset_buttons()

    def _save_current_preset(self) -> None:
        t = TEXT[self._language]
        self._load_preset_store()
        name = self.preset_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", t["auto_lock2_preset_name_required"])
            return
        if name in self._preset_store and name != self._selected_preset_name:
            QMessageBox.warning(self, "Warning", t["auto_lock2_preset_name_exists"].format(name=name))
            return
        self._preset_store[name] = self._settings_payload(self.settings())
        if not self._write_preset_store():
            return
        self._selected_preset_name = name
        self._populate_presets(selected_name=name)
        QMessageBox.information(self, t["auto_lock2_preset_saved_title"], t["auto_lock2_preset_saved"].format(name=name))

    def _load_selected_preset(self) -> None:
        t = TEXT[self._language]
        name = (self._selected_preset_name or "").strip()
        if not name:
            return
        self._load_preset_store()
        payload = self._preset_store.get(name)
        if not isinstance(payload, dict):
            return
        result = QMessageBox.question(
            self,
            t["auto_lock2_preset_load_confirm_title"],
            t["auto_lock2_preset_load_confirm_body"].format(name=name),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        settings = self._settings_from_payload(payload)
        self.load_settings(settings)
        self._loaded_preset_name = name
        self._refresh_loaded_preset_text()
        self.settingsApplied.emit(settings)
        QMessageBox.information(self, t["auto_lock2_preset_loaded_title"], t["auto_lock2_preset_loaded"].format(name=name))

    def _delete_selected_preset(self) -> None:
        t = TEXT[self._language]
        name = (self._selected_preset_name or "").strip()
        if not name:
            return
        result = QMessageBox.question(
            self,
            t["auto_lock2_preset_delete_confirm_title"],
            t["auto_lock2_preset_delete_confirm_body"].format(name=name),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        self._load_preset_store()
        self._preset_store.pop(name, None)
        if not self._write_preset_store():
            return
        if self._loaded_preset_name == name:
            self._loaded_preset_name = None
        self._selected_preset_name = None
        self.preset_name_edit.clear()
        self._populate_presets()
        QMessageBox.information(self, t["auto_lock2_preset_deleted_title"], t["auto_lock2_preset_deleted"].format(name=name))

    def _parameter_row(self, spinbox, key: str) -> QWidget:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(spinbox, 1)

        role_label = QLabel(self)
        role_label.setObjectName("ParameterRoleBadge")
        role_label.setAlignment(Qt.AlignCenter)
        role_label.setMinimumWidth(64)
        self._role_labels[key] = role_label
        layout.addWidget(role_label, 0)

        target_button = QPushButton(self)
        target_button.setObjectName("StepTargetButton")
        target_button.setCheckable(True)
        target_button._step_target = spinbox
        target_button.clicked.connect(lambda checked=False, s=spinbox: self._select_step_target(s))
        self._target_buttons.append(target_button)
        layout.addWidget(target_button, 0)

        help_button = QPushButton("!", self)
        help_button.setObjectName("ParameterHelpButton")
        help_button.setFixedWidth(28)
        help_button.clicked.connect(lambda checked=False, k=key: self._show_parameter_help(k))
        layout.addWidget(help_button, 0)
        return row

    def _select_step_target(self, spinbox) -> None:
        self._step_target = spinbox
        self._apply_step_to_target()
        self._sync_target_buttons()

    def _set_precision_step(self, step: float) -> None:
        self._current_step = step
        self._apply_step_to_target()
        for button in self.precision_buttons.buttons:
            button.setChecked(abs(button._precision_step - step) < 1e-12)

    def _apply_step_to_target(self) -> None:
        if isinstance(self._step_target, SafeSpinBox):
            self._step_target.setSingleStep(max(1, int(round(self._current_step))))
            return
        self._step_target.setSingleStep(self._current_step)

    def _sync_target_buttons(self) -> None:
        for button in self._target_buttons:
            button.blockSignals(True)
            button.setChecked(getattr(button, "_step_target", None) is self._step_target)
            button.blockSignals(False)

    def _show_parameter_help(self, key: str) -> None:
        t = TEXT[self._language]
        body = t.get(f"{key}_help", key)
        if key in self._role_labels:
            role = self._role_for_parameter(key)
            role_name = t.get(f"auto_lock2_role_{role}", role)
            role_hint = t.get(f"auto_lock2_role_{role}_hint", "")
            role_header = t.get("auto_lock2_help_current_role", "Current role")
            body = f"{role_header}: {role_name}\n{role_hint}\n\n{body}"
        QMessageBox.information(
            self,
            t["auto_lock2_config_help_title"],
            body,
        )

    def _double(self, value: float, minimum: float, maximum: float, decimals: int) -> SafeDoubleSpinBox:
        spin = SafeDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        return spin

    def _int(self, value: int, minimum: int, maximum: int) -> SafeSpinBox:
        spin = SafeSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin


class AutoLock2Window(AuxiliaryWindow):
    def __init__(self, owner, controller) -> None:
        super().__init__(owner)
        self.owner = owner
        self.controller = controller
        self._algorithm_settings = AutoLock2Settings()
        self.resize(1180, 620)

        self.log_window = AutoLock2LogWindow(self)
        self.waveform_window = AutoLock2WaveformWindow(self)
        self.config_window = AutoLock2ConfigDialog(self._algorithm_settings, owner.language, self)
        self.config_window.accepted.connect(self._on_algorithm_config_accepted)
        self.config_window.settingsApplied.connect(self._apply_algorithm_settings)
        self.acq_poll_timer = QTimer(self)
        self.acq_poll_timer.setInterval(50)
        self.acq_poll_timer.timeout.connect(self._poll_acquisition_future)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.algorithm_button = QPushButton()
        self.algorithm_button.clicked.connect(controller.show_algorithm_config)
        self.falc_button = QPushButton()
        self.falc_button.clicked.connect(controller.open_falc_window)
        self.waveform_button = QPushButton()
        self.waveform_button.clicked.connect(self.open_waveform_window)
        self.log_button = QPushButton()
        self.log_button.clicked.connect(controller.show_log_window)
        header.addWidget(self.algorithm_button)
        header.addWidget(self.falc_button)
        header.addWidget(self.waveform_button)
        header.addWidget(self.log_button)
        root.addLayout(header)

        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._build_status_group(), 1)
        top.addWidget(self._build_control_group(), 0)
        root.addLayout(top)

        self.acquisition_group = self._build_acquisition_group()
        root.addWidget(self.acquisition_group)

        self.scroll_area = set_scrollable_central_widget(self, central)
        self.apply_texts(owner.language)
        self.reset_state(owner.language)

    def request_shutdown(self) -> None:
        self.log_window.request_shutdown()
        self.log_window.close()
        self.waveform_window.request_shutdown()
        self.waveform_window.close()
        self.config_window.close()
        self.controller.shutdown()
        super().request_shutdown()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._shutdown_requested:
            self.log_window.request_shutdown()
            self.log_window.close()
            self.waveform_window.request_shutdown()
            self.waveform_window.close()
            self.config_window.close()
        super().closeEvent(event)

    def _build_status_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.phase_name = QLabel()
        self.phase_value = QLabel()
        self.phase_value.setObjectName("ReadValue")
        self.acq_status_name = QLabel()
        self.acq_status_value = QLabel()
        self.acq_status_value.setObjectName("ReadValue")
        self.offset_name = QLabel()
        self.offset_value = QLabel()
        self.offset_value.setObjectName("ReadValue")
        self.amplitude_name = QLabel()
        self.amplitude_value = QLabel()
        self.amplitude_value.setObjectName("ReadValue")
        self.falc_path_name = QLabel()
        self.falc_path_value = QLabel()
        self.falc_path_value.setObjectName("ReadValue")
        self.confidence_name = QLabel()
        self.confidence_value = QLabel()
        self.confidence_value.setObjectName("ReadValue")
        self.confidence_value.setWordWrap(True)

        rows = (
            (self.phase_name, self.phase_value),
            (self.acq_status_name, self.acq_status_value),
            (self.offset_name, self.offset_value),
            (self.amplitude_name, self.amplitude_value),
            (self.falc_path_name, self.falc_path_value),
            (self.confidence_name, self.confidence_value),
        )
        for row, (name, value) in enumerate(rows):
            layout.addWidget(name, row, 0)
            layout.addWidget(value, row, 1)
        return group

    def _build_control_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)
        self.one_click_button = QPushButton()
        self.one_click_button.setMinimumWidth(180)
        self.one_click_button.clicked.connect(self.controller.start)
        self.stop_button = QPushButton()
        self.stop_button.setMinimumWidth(180)
        self.stop_button.clicked.connect(self.controller.stop)
        self.start_preview_button = QPushButton()
        self.start_preview_button.clicked.connect(self.controller.start_preview)
        self.stop_preview_button = QPushButton()
        self.stop_preview_button.clicked.connect(self.controller.stop_preview)
        layout.addWidget(self.one_click_button, 0, 0, 1, 2)
        layout.addWidget(self.stop_button, 1, 0, 1, 2)
        layout.addWidget(self.start_preview_button, 2, 0)
        layout.addWidget(self.stop_preview_button, 2, 1)
        return group

    def _build_acquisition_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.source_label = QLabel()
        self.source_combo = SafeComboBox()
        self.source_combo.addItem("", "tektronix")
        self.source_combo.addItem("", "daq")
        self.resource_label = QLabel()
        self.resource_edit = QLineEdit("SOCKET::192.168.43.20::4000")
        self.transmission_label = QLabel()
        self.transmission_channel = SafeSpinBox()
        self.transmission_channel.setRange(1, 4)
        self.transmission_channel.setValue(1)
        self.error_label = QLabel()
        self.error_channel = SafeSpinBox()
        self.error_channel.setRange(1, 4)
        self.error_channel.setValue(2)
        self.points_label = QLabel()
        self.points_spin = SafeSpinBox()
        self.points_spin.setRange(100, 5_000_000)
        self.points_spin.setValue(10_000)
        self.timeout_label = QLabel()
        self.timeout_spin = SafeSpinBox()
        self.timeout_spin.setRange(500, 120_000)
        self.timeout_spin.setValue(10_000)
        self.refresh_label = QLabel()
        self.refresh_interval_spin = SafeSpinBox()
        self.refresh_interval_spin.setRange(100, 60_000)
        self.refresh_interval_spin.setValue(1000)
        self.connect_acq_button = QPushButton()
        self.connect_acq_button.clicked.connect(self.controller.connect_acquisition)
        self.disconnect_acq_button = QPushButton()
        self.disconnect_acq_button.clicked.connect(self.controller.disconnect_acquisition)

        layout.addWidget(self.source_label, 0, 0)
        layout.addWidget(self.source_combo, 0, 1)
        layout.addWidget(self.resource_label, 0, 2)
        layout.addWidget(self.resource_edit, 0, 3, 1, 3)
        layout.addWidget(self.transmission_label, 1, 0)
        layout.addWidget(self.transmission_channel, 1, 1)
        layout.addWidget(self.error_label, 1, 2)
        layout.addWidget(self.error_channel, 1, 3)
        layout.addWidget(self.points_label, 2, 0)
        layout.addWidget(self.points_spin, 2, 1)
        layout.addWidget(self.timeout_label, 2, 2)
        layout.addWidget(self.timeout_spin, 2, 3)
        layout.addWidget(self.refresh_label, 2, 4)
        layout.addWidget(self.refresh_interval_spin, 2, 5)
        layout.addWidget(self.connect_acq_button, 3, 0, 1, 3)
        layout.addWidget(self.disconnect_acq_button, 3, 3, 1, 3)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(5, 1)
        return group

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(t["auto_lock2_title"])
        self.title_label.setText(t["auto_lock2_title"])
        self.algorithm_button.setText(t["auto_lock2_algorithm_config"])
        self.falc_button.setText(t["auto_lock2_falc_settings"])
        self.waveform_button.setText(t["auto_lock2_waveform"])
        self.log_button.setText(t["auto_lock2_log"])
        self.acquisition_group.setTitle(t["auto_lock2_acquisition"])
        self.source_label.setText(t["auto_lock2_source"])
        self.source_combo.setItemText(0, t["auto_lock2_source_tektronix"])
        self.source_combo.setItemText(1, t["auto_lock2_source_daq"])
        self.resource_label.setText(t["auto_lock2_resource"])
        self.transmission_label.setText(t["auto_lock2_transmission_channel"])
        self.error_label.setText(t["auto_lock2_error_channel"])
        self.points_label.setText(t["auto_lock2_points"])
        self.timeout_label.setText(t["auto_lock2_timeout"])
        self.refresh_label.setText(t["auto_lock2_refresh_interval"])
        self.connect_acq_button.setText(t["auto_lock2_connect_acq"])
        self.disconnect_acq_button.setText(t["auto_lock2_disconnect_acq"])
        self.one_click_button.setText(t["auto_lock2_one_click"])
        self.stop_button.setText(t["auto_lock2_stop"])
        self.start_preview_button.setText(t["auto_lock2_start_preview"])
        self.stop_preview_button.setText(t["auto_lock2_stop_preview"])
        self.phase_name.setText(t["auto_lock2_phase"])
        self.acq_status_name.setText(t["auto_lock2_acq_status"])
        self.offset_name.setText(t["auto_lock2_scan_offset"])
        self.amplitude_name.setText(t["auto_lock2_scan_amplitude"])
        self.falc_path_name.setText(t["auto_lock2_falc_path"])
        self.confidence_name.setText(t["auto_lock2_confidence"])
        self.log_window.apply_texts(language)
        self.waveform_window.apply_texts(language)
        self.config_window.apply_texts(language)
        self.set_phase(getattr(self.controller, "_phase", "idle"))

    def acquisition_config(self) -> AcquisitionConfig:
        return AcquisitionConfig(
            source_type=str(self.source_combo.currentData() or "tektronix"),
            resource=self.resource_edit.text().strip(),
            transmission_channel=self.transmission_channel.value(),
            error_channel=self.error_channel.value(),
            points=self.points_spin.value(),
            timeout_ms=self.timeout_spin.value(),
        )

    def preview_interval_ms(self) -> int:
        return self.refresh_interval_spin.value()

    def current_algorithm_settings(self) -> AutoLock2Settings:
        return self._algorithm_settings

    def open_algorithm_config_window(self, settings: AutoLock2Settings) -> None:
        if self.config_window.isHidden():
            self.config_window.load_settings(settings)
            self.config_window.move(self.x() + 140, self.y() + 110)
        self.config_window.showNormal()
        self.config_window.show()
        fit_window_to_screen(self.config_window)
        self.config_window.raise_()
        self.config_window.activateWindow()

    def _on_algorithm_config_accepted(self) -> None:
        self._apply_algorithm_settings(self.config_window.settings())

    def _apply_algorithm_settings(self, settings: AutoLock2Settings) -> None:
        self._algorithm_settings = settings
        self.controller.apply_algorithm_settings(self._algorithm_settings)

    def open_log_window(self) -> None:
        if self.log_window.isHidden():
            self.log_window.move(self.x() + 80, self.y() + 80)
        self.log_window.showNormal()
        self.log_window.show()
        fit_window_to_screen(self.log_window)
        self.log_window.raise_()
        self.log_window.activateWindow()

    def open_waveform_window(self) -> None:
        if self.waveform_window.isHidden():
            self.waveform_window.move(self.x() + 110, self.y() + 90)
        self.waveform_window.showNormal()
        self.waveform_window.show()
        fit_window_to_screen(self.waveform_window)
        self.waveform_window.raise_()
        self.waveform_window.activateWindow()

    def ensure_acquisition_polling(self) -> None:
        if not self.acq_poll_timer.isActive():
            self.acq_poll_timer.start()

    def _poll_acquisition_future(self) -> None:
        self.controller.poll_acquisition_future()
        if getattr(self.controller, "_acq_future", None) is None:
            self.acq_poll_timer.stop()

    def append_log(self, line: str) -> None:
        self.log_window.append_log(line)
        self.confidence_value.setText(line)

    def set_acquisition_status(self, connected: bool, identity: str) -> None:
        t = TEXT[self.owner.language]
        text = t["auto_lock2_connected"] if connected else t["auto_lock2_disconnected"]
        if identity:
            text = f"{text}: {identity}"
        self.acq_status_value.setText(text)

    def set_acquisition_error(self, message: str) -> None:
        self.acq_status_value.setText(message)

    def set_phase(self, phase: str) -> None:
        t = TEXT[self.owner.language]
        self.phase_value.setText(t.get(f"auto_lock2_phase_{phase}", phase))

    def render_snapshot(self, snapshot) -> None:
        t = TEXT[self.owner.language]
        unit = snapshot.sc_unit or t["voltage_unit"]
        amplitude_unit = t["scan_amplitude_unit"]
        if unit != t["voltage_unit"]:
            amplitude_unit = f"{unit} pp"
        self.offset_value.setText(f"{snapshot.sc_offset:.6f} {unit}")
        self.amplitude_value.setText(f"{snapshot.sc_amplitude:.6f} {amplitude_unit}")
        path_text = t["not_available"]
        if snapshot.falc1 is not None:
            path_text = self._option_text(FALC_PATH_SELECTION_OPTIONS, snapshot.falc1.path_selection, self.owner.language)
        self.falc_path_value.setText(path_text)

    def render_frame(self, frame: AcquisitionFrame, analysis) -> None:
        self.waveform_window.render_frame(frame, analysis)
        self.confidence_value.setText(analysis.message)

    def reset_state(self, language: str) -> None:
        t = TEXT[language]
        self.set_acquisition_status(False, "")
        self.phase_value.setText(t["auto_lock2_phase_idle"])
        self.offset_value.setText(f"0.000000 {t['voltage_unit']}")
        self.amplitude_value.setText(f"0.000000 {t['scan_amplitude_unit']}")
        self.falc_path_value.setText(t["not_available"])
        self.confidence_value.setText(t["auto_lock2_waiting_frame"])
        self.waveform_window.reset_state(language)

    def set_writable(self, writable: bool, previewable: bool, running: bool) -> None:
        self.one_click_button.setEnabled(writable and self.controller.is_acquisition_connected and not running)
        self.stop_button.setEnabled(running)
        self.algorithm_button.setEnabled(previewable and not running)
        self.config_window.setEnabled(previewable and not running)
        self.falc_button.setEnabled(previewable)
        self.waveform_button.setEnabled(True)
        self.log_button.setEnabled(True)
        self.connect_acq_button.setEnabled(previewable and not running)
        self.disconnect_acq_button.setEnabled(previewable and self.controller.is_acquisition_connected and not running)
        self.start_preview_button.setEnabled(previewable and self.controller.is_acquisition_connected)
        self.stop_preview_button.setEnabled(previewable)
        for widget in (
            self.source_combo,
            self.resource_edit,
            self.transmission_channel,
            self.error_channel,
            self.points_spin,
            self.timeout_spin,
            self.refresh_interval_spin,
        ):
            widget.setEnabled(previewable and not running)

    def _option_text(self, options: list[tuple[str, object]], value: object, language: str) -> str:
        for key, item_value in options:
            if item_value == value:
                return TEXT[language].get(key, str(value))
        return str(value)
