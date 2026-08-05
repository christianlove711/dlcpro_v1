from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QSettings, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from widgets.common_controls import (
    PrecisionButtonRow,
    SafeDoubleSpinBox,
    StepTargetSpinBoxRow,
)

from dlcpro_service import (
    ConnectionSettings,
    DlcProService,
    SnapshotRequest,
    SnapshotSection,
)


ADC_DIALOG_STYLE = """
QDialog {
    background: #f3f6fa;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QLabel, QRadioButton {
    background: transparent;
    color: #25324a;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    min-height: 34px;
    padding: 0 10px;
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 7px;
    color: #172033;
    selection-background-color: #2f6fcb;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4b82cf;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background: #f0f2f5;
    border-color: #e0e5ec;
    color: #8993a4;
}
QComboBox::drop-down {
    border: 0;
    width: 28px;
}
QPushButton {
    min-height: 34px;
    padding: 0 16px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    color: #25324a;
    font-weight: 600;
}
QPushButton:hover {
    background: #f6f8fb;
    border-color: #9eacbf;
}
QPushButton:pressed {
    background: #edf1f6;
}
QPushButton:disabled {
    background: #f0f2f5;
    border-color: #e0e5ec;
    color: #a3adbb;
}
QPushButton#PrecisionButton {
    min-width: 58px;
    padding: 0 9px;
}
QPushButton#PrecisionButton:checked {
    background: #e8f7ef;
    border-color: #75b391;
    color: #137044;
}
QPushButton#StepTargetButton {
    min-width: 94px;
}
QPushButton#StepTargetButton:checked {
    background: #fff7e8;
    border-color: #d8af68;
    color: #8a5a12;
}
QRadioButton {
    min-height: 30px;
    spacing: 8px;
}
"""


class _TaskSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object)


class _ServiceTask(QRunnable):
    def __init__(self, function: Callable[[], object]):
        super().__init__()
        self.function = function
        self.signals = _TaskSignals()

    def run(self):
        try:
            result = self.function()
        except Exception as exc:  # noqa: BLE001 - forwarded to the UI layer
            self.signals.failed.emit(exc)
        else:
            self.signals.succeeded.emit(result)


class DlcScanSession(QObject):
    """Asynchronous scan-only facade around the verified DLC pro service."""

    snapshot_changed = Signal(object)
    write_snapshot_changed = Signal(object)
    connection_changed = Signal(bool, str)
    error = Signal(str)
    busy_changed = Signal(bool)
    falc_engaged = Signal(object)

    def __init__(
        self,
        service: DlcProService | None = None,
        *,
        owns_service: bool | None = None,
        snapshot_provider: Callable[[], object | None] | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.service = service or DlcProService()
        self.owns_service = (
            service is None if owns_service is None else bool(owns_service)
        )
        self.snapshot_provider = snapshot_provider
        self.latest_snapshot = None
        self._faulted = False
        self._poll_error_notified = False
        self._busy_count = 0
        self._workers: set[_ServiceTask] = set()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(500)
        self.poll_timer.timeout.connect(self.refresh)
        self.poll_timer.start()

    @property
    def is_connected(self) -> bool:
        return bool(self.service.is_connected and not self._faulted)

    def snapshot(self):
        if self.latest_snapshot is not None:
            return self.latest_snapshot
        provider = self.snapshot_provider
        if provider is not None:
            try:
                provided = provider()
            except Exception:  # noqa: BLE001 - recorder must never call the SDK
                provided = None
            if provided is not None:
                self.latest_snapshot = provided
        return self.latest_snapshot

    def _set_busy(self, delta: int):
        was_busy = self._busy_count > 0
        self._busy_count = max(0, self._busy_count + delta)
        is_busy = self._busy_count > 0
        if was_busy != is_busy:
            self.busy_changed.emit(is_busy)

    def _submit(
        self,
        function: Callable[[], object],
        success: Callable[[object], None],
        *,
        poll: bool = False,
    ):
        task = _ServiceTask(function)
        self._workers.add(task)
        self._set_busy(1)

        def completed(result):
            self._workers.discard(task)
            self._set_busy(-1)
            success(result)

        def failed(exc):
            self._workers.discard(task)
            self._set_busy(-1)
            self._handle_error(exc, poll=poll)

        task.signals.succeeded.connect(completed)
        task.signals.failed.connect(failed)
        self.pool.start(task)

    def _accept_snapshot(self, snapshot):
        self.latest_snapshot = snapshot
        self._faulted = False
        self._poll_error_notified = False
        self.snapshot_changed.emit(snapshot)
        self.connection_changed.emit(True, "已连接")

    def _handle_error(self, exc: Exception, *, poll: bool):
        message = self.service.format_error(exc)
        if poll:
            self._faulted = True
            self.poll_timer.stop()
            self.connection_changed.emit(False, "连接中断")
            if self._poll_error_notified:
                return
            self._poll_error_notified = True
        self.error.emit(message)

    def connect_device(self, settings: ConnectionSettings):
        if not self.owns_service:
            self.error.emit("当前DLC pro连接由主程序管理，请先在主程序中连接设备。")
            return
        self._faulted = False
        self._submit(
            lambda: self.service.connect(settings),
            self._after_connected,
        )

    def _after_connected(self, snapshot):
        self.poll_timer.start()
        self._accept_snapshot(snapshot)

    def disconnect_device(self):
        if not self.owns_service:
            return

        def disconnected(_result):
            self.latest_snapshot = None
            self._faulted = False
            self.poll_timer.stop()
            self.connection_changed.emit(False, "未连接")

        self._submit(
            lambda: (self.service.disconnect(), None)[1],
            disconnected,
        )

    def refresh(self):
        if self._busy_count:
            return
        if not self.service.is_connected:
            self.connection_changed.emit(False, "未连接")
            return
        if not self.owns_service and self.snapshot_provider is not None:
            try:
                snapshot = self.snapshot_provider()
            except Exception:  # noqa: BLE001 - shared owner reports its errors
                snapshot = None
            if snapshot is not None:
                self._accept_snapshot(snapshot)
            return
        self._submit(
            lambda: self.service.read_snapshot(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            ),
            self._accept_snapshot,
            poll=True,
        )

    def set_scan_offset(self, value: float):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法写入Scan Offset。")
            return
        self._submit(
            lambda: self.service.set_sc_offset(float(value)),
            self._accept_written_snapshot,
        )

    def set_scan_enabled(self, enabled: bool):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法切换扫描启用状态。")
            return
        self._submit(
            lambda: self.service.set_sc_enabled(bool(enabled)),
            self._accept_written_snapshot,
        )

    def set_scan_amplitude(self, value: float):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法写入Scan Amplitude。")
            return
        self._submit(
            lambda: self.service.set_sc_amplitude(float(value)),
            self._accept_written_snapshot,
        )

    def set_scan_frequency(self, value: float):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法写入Scan Frequency。")
            return
        self._submit(
            lambda: self.service.set_sc_frequency(float(value)),
            self._accept_written_snapshot,
        )

    def set_scan_output_channel(self, value: int):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法写入Scan Output。")
            return
        self._submit(
            lambda: self.service.set_sc_output_channel(int(value)),
            self._accept_written_snapshot,
        )

    def set_scan_signal_type(self, value: int):
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法写入Scan Shape。")
            return
        self._submit(
            lambda: self.service.set_sc_signal_type(int(value)),
            self._accept_written_snapshot,
        )

    def engage_configured_falc(self):
        """Engage the already-configured FALC paths without changing tuning."""
        if not self.is_connected:
            self.error.emit("DLC pro未连接，无法使能FALC pro。")
            return
        self._submit(
            self.service.engage_falc1_configured_paths,
            self._accept_falc_engaged,
        )

    def _accept_written_snapshot(self, snapshot):
        self._accept_snapshot(snapshot)
        self.write_snapshot_changed.emit(snapshot)

    def _accept_falc_engaged(self, snapshot):
        self._accept_snapshot(snapshot)
        self.falc_engaged.emit(snapshot)

    def shutdown(self):
        self.poll_timer.stop()
        self.pool.waitForDone(3000)
        if self.owns_service and self.service.is_connected:
            self.service.disconnect()


class DlcProSettingsDialog(QDialog):
    """Minimal connection and Scan Offset/Amplitude editor."""

    PRECISION_OPTIONS = (
        ("100", 100.0),
        ("10", 10.0),
        ("1", 1.0),
        ("0.1", 0.1),
        ("0.01", 0.01),
        ("0.001", 0.001),
        ("0.0001", 0.0001),
        ("0.00001", 0.00001),
        ("0.000001", 0.000001),
    )
    DEFAULT_STEP = 0.01

    def __init__(
        self,
        session: DlcScanSession,
        settings: QSettings,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._scan_edit_locked = False
        self.setStyleSheet(ADC_DIALOG_STYLE)
        self.session = session
        self.settings = settings
        self.setWindowTitle("DLC pro设置")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        form = QFormLayout()
        self.mode = QComboBox()
        self.mode.addItem("网络", "network")
        self.mode.addItem("串口", "serial")
        stored_mode = str(settings.value("dlcpro/mode", "network"))
        self.mode.setCurrentIndex(max(0, self.mode.findData(stored_mode)))
        self.network_target = QLineEdit(str(settings.value(
            "dlcpro/network_target", "169.254.5.11"
        )))
        self.command_port = QSpinBox()
        self.command_port.setRange(0, 65535)
        self.command_port.setValue(int(settings.value(
            "dlcpro/command_line_port", 1998
        )))
        self.monitoring_port = QSpinBox()
        self.monitoring_port.setRange(0, 65535)
        self.monitoring_port.setValue(int(settings.value(
            "dlcpro/monitoring_line_port", 1999
        )))
        self.serial_target = QComboBox()
        self.serial_target.setEditable(True)
        self._stored_serial_target = str(settings.value(
            "dlcpro/serial_target", ""
        ))
        self.baudrate = QSpinBox()
        self.baudrate.setRange(1200, 10_000_000)
        self.baudrate.setValue(int(settings.value(
            "dlcpro/baudrate", 115200
        )))
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        self.timeout.setValue(int(settings.value("dlcpro/timeout", 5)))
        form.addRow("连接方式", self.mode)
        form.addRow("IP/系统名称", self.network_target)
        form.addRow("命令端口", self.command_port)
        form.addRow("监控端口", self.monitoring_port)
        form.addRow("串口", self.serial_target)
        form.addRow("波特率", self.baudrate)
        form.addRow("超时", self.timeout)
        root.addLayout(form)

        connection_row = QHBoxLayout()
        self.connect_button = QPushButton("连接")
        self.disconnect_button = QPushButton("断开")
        self.refresh_button = QPushButton("刷新")
        self.status = QLabel("未连接")
        connection_row.addWidget(self.connect_button)
        connection_row.addWidget(self.disconnect_button)
        connection_row.addWidget(self.refresh_button)
        connection_row.addStretch(1)
        connection_row.addWidget(self.status)
        root.addLayout(connection_row)

        scan_form = QFormLayout()
        scan_form.setHorizontalSpacing(12)
        scan_form.setVerticalSpacing(10)

        stored_step = float(settings.value(
            "dlcpro/scan_step", self.DEFAULT_STEP
        ))
        valid_steps = {step for _label, step in self.PRECISION_OPTIONS}
        self.precision_step = (
            stored_step if stored_step in valid_steps else self.DEFAULT_STEP
        )
        self.precision_row = PrecisionButtonRow(
            self.PRECISION_OPTIONS,
            self._set_precision,
            max_columns=5,
        )
        self.precision_buttons = self.precision_row.buttons
        for button, (label, _step) in zip(
            self.precision_buttons, self.PRECISION_OPTIONS
        ):
            button.setText(label)

        self.offset = SafeDoubleSpinBox()
        self.offset.setRange(-1_000_000.0, 1_000_000.0)
        self.offset.setDecimals(6)
        self.offset.setKeyboardTracking(False)
        self.offset.set_button_only_mode()
        self.amplitude = SafeDoubleSpinBox()
        self.amplitude.setRange(-1_000_000.0, 1_000_000.0)
        self.amplitude.setDecimals(6)
        self.amplitude.setKeyboardTracking(False)
        self.amplitude.set_button_only_mode()

        self.amplitude_row = StepTargetSpinBoxRow(
            "amplitude", self.amplitude, self._select_target
        )
        self.offset_row = StepTargetSpinBoxRow(
            "offset", self.offset, self._select_target
        )
        self.amplitude_target = self.amplitude_row.target_button
        self.offset_target = self.offset_row.target_button
        self.target_buttons = (self.amplitude_target, self.offset_target)
        for button in self.target_buttons:
            button.setText("当前调节")

        self.unit = QLabel("--")
        scan_form.addRow("调节步进", self.precision_row)
        scan_form.addRow("扫描幅度", self.amplitude_row)
        scan_form.addRow("扫描偏置", self.offset_row)
        scan_form.addRow("当前单位", self.unit)
        root.addLayout(scan_form)

        initial_target = str(settings.value(
            "dlcpro/scan_target", "amplitude"
        ))
        self._active_spinbox = (
            self.offset if initial_target == "offset" else self.amplitude
        )
        self._select_target(initial_target, self._active_spinbox)
        self._set_precision(self.precision_step)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.close)
        root.addWidget(close_buttons)

        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.connect_button.clicked.connect(self._connect)
        self.disconnect_button.clicked.connect(session.disconnect_device)
        self.refresh_button.clicked.connect(session.refresh)
        self.offset.connect_live_apply(self._write_offset)
        self.amplitude.connect_live_apply(self._write_amplitude)
        session.snapshot_changed.connect(self._render_snapshot)
        session.connection_changed.connect(self._connection_changed)
        session.error.connect(self._show_error)
        session.busy_changed.connect(self._busy_changed)

        self._load_serial_ports()
        self._mode_changed()
        self._connection_changed(
            session.is_connected,
            "已连接" if session.is_connected else "未连接",
        )
        if not session.owns_service:
            self.mode.setEnabled(False)
            self.network_target.setEnabled(False)
            self.command_port.setEnabled(False)
            self.monitoring_port.setEnabled(False)
            self.serial_target.setEnabled(False)
            self.baudrate.setEnabled(False)
            self.timeout.setEnabled(False)
            self.connect_button.setText("由主程序管理连接")
            self.connect_button.setEnabled(False)

    def _load_serial_ports(self):
        current = self.serial_target.currentText() or self._stored_serial_target
        self.serial_target.clear()
        for port in self.session.service.list_serial_ports():
            self.serial_target.addItem(port)
        if current:
            self.serial_target.setEditText(current)

    def _mode_changed(self):
        serial = self.mode.currentData() == "serial"
        self.network_target.setVisible(not serial)
        self.command_port.setVisible(not serial)
        self.monitoring_port.setVisible(not serial)
        self.serial_target.setVisible(serial)
        self.baudrate.setEnabled(serial and self.session.owns_service)

    def _connect(self):
        mode = str(self.mode.currentData())
        target = (
            self.network_target.text().strip()
            if mode == "network"
            else self.serial_target.currentText().strip()
        )
        if not target:
            QMessageBox.warning(self, "连接失败", "请输入DLC pro连接目标。")
            return
        self.settings.setValue("dlcpro/network_target", self.network_target.text())
        self.settings.setValue("dlcpro/mode", mode)
        self.settings.setValue("dlcpro/command_line_port", self.command_port.value())
        self.settings.setValue(
            "dlcpro/monitoring_line_port", self.monitoring_port.value()
        )
        self.settings.setValue(
            "dlcpro/serial_target", self.serial_target.currentText()
        )
        self.settings.setValue("dlcpro/baudrate", self.baudrate.value())
        self.settings.setValue("dlcpro/timeout", self.timeout.value())
        self.session.connect_device(ConnectionSettings(
            mode=mode,
            target=target,
            baudrate=self.baudrate.value(),
            timeout=self.timeout.value(),
            command_line_port=self.command_port.value(),
            monitoring_line_port=self.monitoring_port.value(),
        ))

    def _set_precision(self, step: float):
        self.precision_step = float(step)
        self._active_spinbox.setSingleStep(self.precision_step)
        self.settings.setValue("dlcpro/scan_step", self.precision_step)
        for button in self.precision_buttons:
            button.blockSignals(True)
            button.setChecked(
                abs(button._precision_step - self.precision_step) < 1e-12
            )
            button.blockSignals(False)

    def _select_target(self, target: str, spinbox: SafeDoubleSpinBox):
        self._active_spinbox = spinbox
        spinbox.setSingleStep(self.precision_step)
        self.settings.setValue("dlcpro/scan_target", target)
        for button in self.target_buttons:
            button.blockSignals(True)
            button.setChecked(button._precision_target is spinbox)
            button.blockSignals(False)

    def _write_offset(self):
        self.session.set_scan_offset(self.offset.value())

    def _write_amplitude(self):
        self.session.set_scan_amplitude(self.amplitude.value())

    def _render_snapshot(self, snapshot):
        self.offset.sync_from_device(float(snapshot.sc_offset))
        self.amplitude.sync_from_device(float(snapshot.sc_amplitude))
        unit = str(snapshot.sc_unit or "").strip()
        self.offset.setSuffix(f" {unit}" if unit else "")
        self.amplitude.setSuffix(f" {unit} pp" if unit else "")
        self.unit.setText(unit or "--")

    def _connection_changed(self, connected: bool, text: str):
        self.status.setText(text)
        self.disconnect_button.setEnabled(
            connected and self.session.owns_service
        )
        editable = connected and not self._scan_edit_locked
        self.offset.setEnabled(editable)
        self.amplitude.setEnabled(editable)

    def set_scan_edit_locked(self, locked: bool):
        """Prevent manual scan writes while an automatic controller owns them."""
        self._scan_edit_locked = bool(locked)
        editable = self.session.is_connected and not self._scan_edit_locked
        self.offset.setEnabled(editable)
        self.amplitude.setEnabled(editable)

    def _busy_changed(self, busy: bool):
        if self.session.owns_service:
            self.connect_button.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy)

    def _show_error(self, message: str):
        if self.isVisible():
            QMessageBox.critical(self, "DLC pro错误", message)

    def showEvent(self, event):
        super().showEvent(event)
        self.session.refresh()


class RecordingOptionsDialog(QDialog):
    """Choose whether one recording includes the DLC pro scan timeline."""

    WAVEFORM_ONLY = "waveform_only"
    WITH_DLCPRO = "waveform_with_dlcpro"

    def __init__(
        self,
        default_mode: str,
        summary: str,
        dlc_connected: bool,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setStyleSheet(ADC_DIALOG_STYLE)
        self.setWindowTitle("录制内容")
        root = QVBoxLayout(self)
        root.addWidget(QLabel(summary))
        self.waveform_only = QRadioButton("仅保存ADC波形")
        self.with_dlcpro = QRadioButton(
            "保存ADC波形＋DLC pro扫描参数"
        )
        if default_mode == self.WITH_DLCPRO:
            self.with_dlcpro.setChecked(True)
        else:
            self.waveform_only.setChecked(True)
        root.addWidget(self.waveform_only)
        root.addWidget(self.with_dlcpro)
        status = QLabel(
            "DLC pro：已连接"
            if dlc_connected else
            "DLC pro：未连接（组合模式需要先连接）"
        )
        root.addWidget(status)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @property
    def selected_mode(self) -> str:
        return (
            self.WITH_DLCPRO
            if self.with_dlcpro.isChecked()
            else self.WAVEFORM_ONLY
        )

    @classmethod
    def get_mode(
        cls,
        parent: QWidget,
        default_mode: str,
        summary: str,
        dlc_connected: bool,
    ) -> str | None:
        dialog = cls(default_mode, summary, dlc_connected, parent)
        return dialog.selected_mode if dialog.exec() == QDialog.Accepted else None
