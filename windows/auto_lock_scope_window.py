from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import AutoLockTelemetry, LockPointSnapshot
from ui_text import AUTO_LOCK_SCOPE_SIGNAL_OPTIONS, AUTO_LOCK_SCOPE_UPDATE_RATE_OPTIONS, TEXT
from widgets.auto_lock import ScopePlotWidget
from widgets.common_controls import SafeComboBox
from windows.base_window import AuxiliaryWindow


class AutoLockScopeWindow(AuxiliaryWindow):
    def __init__(self, owner, controller) -> None:
        super().__init__()
        self.owner = owner
        self.controller = controller
        self._last_scope = None
        self._last_scope_error: str | None = None
        self._last_candidates: tuple[LockPointSnapshot, ...] = ()
        self._last_selected: LockPointSnapshot | None = None
        self._last_tracking: LockPointSnapshot | None = None
        self._target: LockPointSnapshot | None = None

        self.resize(1120, 760)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.scope_group = QGroupBox()
        scope_layout = QVBoxLayout(self.scope_group)
        scope_layout.setContentsMargins(12, 12, 12, 12)
        scope_layout.setSpacing(10)

        self.scope_hint_label = QLabel()
        self.scope_hint_label.setObjectName("SubtleHint")
        self.scope_hint_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_hint_label)

        toolbar = QGridLayout()
        toolbar.setHorizontalSpacing(10)
        toolbar.setVerticalSpacing(8)

        self.scope_channel1_label = QLabel()
        self.scope_channel1_combo = SafeComboBox()
        self.scope_channel2_label = QLabel()
        self.scope_channel2_combo = SafeComboBox()
        self.scope_update_rate_label = QLabel()
        self.scope_update_rate_combo = SafeComboBox()
        self.scope_mode_label = QLabel()
        self.scope_mode_value = QLabel()
        self.scope_mode_value.setObjectName("ReadValue")

        self.scope_xy_button = QPushButton()
        self.scope_xy_button.setObjectName("ScopeModeButton")
        self.scope_xy_button.setCheckable(True)
        self.scope_time_button = QPushButton()
        self.scope_time_button.setObjectName("ScopeModeButton")
        self.scope_time_button.setCheckable(True)
        self.scope_frequency_button = QPushButton()
        self.scope_frequency_button.setObjectName("ScopeModeButton")
        self.scope_frequency_button.setCheckable(True)
        self.scope_refresh_button = QPushButton()

        toolbar.addWidget(self.scope_channel1_label, 0, 0)
        toolbar.addWidget(self.scope_channel1_combo, 0, 1)
        toolbar.addWidget(self.scope_channel2_label, 0, 2)
        toolbar.addWidget(self.scope_channel2_combo, 0, 3)
        toolbar.addWidget(self.scope_xy_button, 0, 4)
        toolbar.addWidget(self.scope_time_button, 0, 5)
        toolbar.addWidget(self.scope_frequency_button, 0, 6)
        toolbar.addWidget(self.scope_update_rate_label, 1, 0)
        toolbar.addWidget(self.scope_update_rate_combo, 1, 1)
        toolbar.addWidget(self.scope_mode_label, 1, 2)
        toolbar.addWidget(self.scope_mode_value, 1, 3)
        toolbar.addWidget(self.scope_refresh_button, 1, 6)
        scope_layout.addLayout(toolbar)

        self.scope_status_label = QLabel()
        self.scope_status_label.setObjectName("SubtleHint")
        self.scope_status_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_status_label)

        self.scope_plot = ScopePlotWidget()
        scope_layout.addWidget(self.scope_plot, 1)
        root.addWidget(self.scope_group, 1)

        self.setCentralWidget(central)

        self.scope_channel1_combo.currentIndexChanged.connect(controller.on_scope_channel1_changed)
        self.scope_channel2_combo.currentIndexChanged.connect(controller.on_scope_channel2_changed)
        self.scope_update_rate_combo.currentIndexChanged.connect(controller.on_scope_update_rate_changed)
        self.scope_xy_button.clicked.connect(lambda: controller.on_scope_variant_requested(0))
        self.scope_time_button.clicked.connect(lambda: controller.on_scope_variant_requested(1))
        self.scope_frequency_button.clicked.connect(lambda: controller.on_scope_variant_requested(2))
        self.scope_refresh_button.clicked.connect(controller.request_scope_refresh)
        self.scope_plot.candidateClicked.connect(controller.on_scope_candidate_clicked)

        self.reset_state(owner.language)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.controller.on_scope_window_visibility_changed(True)

    def hideEvent(self, event) -> None:  # noqa: N802
        self.controller.on_scope_window_visibility_changed(False)
        super().hideEvent(event)

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['auto_lock_scope_window_title']}")
        self.scope_group.setTitle(t["auto_lock_scope"])
        self.scope_hint_label.setText(t["auto_lock_scope_status_hint"])
        self.scope_channel1_label.setText(t["auto_lock_scope_channel1"])
        self.scope_channel2_label.setText(t["auto_lock_scope_channel2"])
        self.scope_update_rate_label.setText(t["auto_lock_scope_update_rate"])
        self.scope_mode_label.setText(t["auto_lock_scope_mode"])
        self.scope_xy_button.setText(t["auto_lock_scope_mode_xy"])
        self.scope_time_button.setText(t["auto_lock_scope_mode_time"])
        self.scope_frequency_button.setText(t["auto_lock_scope_mode_frequency"])
        self.scope_refresh_button.setText(t["auto_lock_scope_refresh"])
        self._populate_scope_signal_options(language)
        self._populate_scope_update_rate_options()

    def reset_state(self, language: str) -> None:
        self._last_scope = None
        self._last_scope_error = None
        self._last_candidates = ()
        self._last_selected = None
        self._last_tracking = None
        self._target = None
        self.apply_texts(language)
        t = TEXT[language]
        self.scope_mode_value.setText(t["auto_lock_value_waiting"])
        self.scope_status_label.setText(t["auto_lock_scope_click_hint"])
        self._sync_variant_buttons(None)
        self.scope_plot.set_plot_data(
            None,
            (),
            None,
            None,
            None,
            t,
            empty_text=t["auto_lock_scope_empty"],
        )

    def render_telemetry(
        self,
        telemetry: AutoLockTelemetry,
        language: str,
        target: LockPointSnapshot | None,
    ) -> None:
        self._last_scope = telemetry.scope
        self._last_scope_error = telemetry.scope_error
        self._last_candidates = telemetry.candidates
        self._last_selected = telemetry.selected
        self._last_tracking = telemetry.tracking
        self._target = target
        t = TEXT[language]

        if telemetry.scope is not None:
            self.scope_mode_value.setText(self._scope_mode_text(t, telemetry.scope.variant))
            self._sync_scope_combo(self.scope_channel1_combo, telemetry.scope.channel1_signal)
            self._sync_scope_combo(self.scope_channel2_combo, telemetry.scope.channel2_signal)
            self._sync_scope_combo(self.scope_update_rate_combo, telemetry.scope.update_rate)
            self._sync_variant_buttons(telemetry.scope.variant)
            status_text = t["auto_lock_scope_click_hint"]
            if telemetry.scope_error:
                status_text = f"{t['auto_lock_scope_error_prefix']}{telemetry.scope_error}"
            self.scope_status_label.setText(status_text)
            self.scope_plot.set_plot_data(
                telemetry.scope,
                telemetry.candidates,
                telemetry.selected,
                telemetry.tracking,
                target,
                t,
                empty_text=t["auto_lock_scope_empty"],
                error_text=telemetry.scope_error,
            )
            return

        self.scope_mode_value.setText(t["auto_lock_value_waiting"])
        self._sync_variant_buttons(None)
        error_text = None
        if telemetry.scope_error:
            error_text = f"{t['auto_lock_scope_error_prefix']}{telemetry.scope_error}"
        self.scope_status_label.setText(error_text or t["auto_lock_scope_click_hint"])
        self.scope_plot.set_plot_data(
            None,
            telemetry.candidates,
            telemetry.selected,
            telemetry.tracking,
            target,
            t,
            empty_text=t["auto_lock_scope_empty"],
            error_text=error_text,
        )

    def set_target_point(self, point: LockPointSnapshot | None, language: str) -> None:
        self._target = point
        t = TEXT[language]
        self.scope_plot.set_plot_data(
            self._last_scope,
            self._last_candidates,
            self._last_selected,
            self._last_tracking,
            point,
            t,
            empty_text=t["auto_lock_scope_empty"],
            error_text=self._last_scope_error,
        )

    def set_scope_status_message(self, text: str) -> None:
        self.scope_status_label.setText(text)

    def set_writable(self, writable: bool, running: bool) -> None:
        editable = writable and not running
        for widget in (
            self.scope_channel1_combo,
            self.scope_channel2_combo,
            self.scope_update_rate_combo,
            self.scope_xy_button,
            self.scope_time_button,
            self.scope_frequency_button,
            self.scope_refresh_button,
        ):
            widget.setEnabled(editable)

    def _populate_scope_signal_options(self, language: str) -> None:
        for combo in (self.scope_channel1_combo, self.scope_channel2_combo):
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for text_key, value in AUTO_LOCK_SCOPE_SIGNAL_OPTIONS:
                combo.addItem(TEXT[language][text_key], value)
            combo.blockSignals(False)
            target = current
            if target is None:
                target = 100 if combo is self.scope_channel1_combo else 30
            index = combo.findData(target)
            if index >= 0:
                combo.blockSignals(True)
                combo.setCurrentIndex(index)
                combo.blockSignals(False)

    def _populate_scope_update_rate_options(self) -> None:
        combo = self.scope_update_rate_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for value in AUTO_LOCK_SCOPE_UPDATE_RATE_OPTIONS:
            combo.addItem(f"{value} Hz", value)
        combo.blockSignals(False)
        target = 5 if current is None else current
        index = combo.findData(target)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    @staticmethod
    def _scope_mode_text(text_map: dict[str, str], variant: int) -> str:
        if variant == 0:
            return text_map["auto_lock_scope_mode_xy"]
        if variant == 1:
            return text_map["auto_lock_scope_mode_time"]
        if variant == 2:
            return text_map["auto_lock_scope_mode_frequency"]
        return str(variant)

    @staticmethod
    def _sync_scope_combo(combo: QComboBox, value: int) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _sync_variant_buttons(self, variant: int | None) -> None:
        for button, candidate in (
            (self.scope_xy_button, 0),
            (self.scope_time_button, 1),
            (self.scope_frequency_button, 2),
        ):
            button.blockSignals(True)
            button.setChecked(variant == candidate)
            button.blockSignals(False)
