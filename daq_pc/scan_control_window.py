"""ADC-side DLC pro scan control popup backed by the shared SDK session."""
from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui_text import SCAN_OUTPUT_OPTIONS, SCAN_SHAPE_OPTIONS, TEXT
from widgets.common_controls import (
    PrecisionButtonRow,
    SafeComboBox,
    SafeDoubleSpinBox,
    StepTargetSpinBoxRow,
)


SCAN_CONTROL_STYLE = """
QMainWindow, QWidget#scanControlRoot {
    background: #f3f6fa;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QLabel { background: transparent; color: #25324a; }
QLabel#title { color: #102f57; font-size: 22px; font-weight: 700; }
QLabel#muted { color: #69758a; }
QLabel#state {
    background: #edf4ff; border: 1px solid #bfd5f6; border-radius: 7px;
    color: #195ca8; font-weight: 700; padding: 8px 12px;
}
QFrame#card {
    background: #ffffff; border: 1px solid #dce3ed; border-radius: 10px;
}
QLabel#sectionTitle { color: #25324a; font-size: 15px; font-weight: 700; }
QDoubleSpinBox, QComboBox {
    min-height: 36px; padding: 0 10px; background: #ffffff;
    border: 1px solid #cfd8e6; border-radius: 7px; color: #172033;
    selection-background-color: #2f6fcb;
}
QDoubleSpinBox:disabled, QComboBox:disabled {
    background: #f0f2f5; color: #8993a4; border-color: #e0e5ec;
}
QComboBox::drop-down { border: 0; width: 28px; }
QPushButton {
    min-height: 36px; padding: 0 16px; background: #ffffff;
    border: 1px solid #cbd5e1; border-radius: 7px;
    color: #25324a; font-weight: 600;
}
QPushButton:hover { background: #f6f8fb; border-color: #9eacbf; }
QPushButton:disabled { background: #f0f2f5; color: #a3adbb; }
QPushButton#PrecisionButton { min-width: 58px; padding: 0 8px; }
QPushButton#PrecisionButton:checked {
    background: #e8f7ef; border-color: #75b391; color: #137044;
}
QPushButton#StepTargetButton { min-width: 94px; }
QPushButton#StepTargetButton:checked {
    background: #fff7e8; border-color: #d8af68; color: #8a5a12;
}
QPushButton#scanEnable:checked {
    background: #178455; border-color: #178455; color: #ffffff;
}
QMessageBox { background: #ffffff; color: #172033; }
QMessageBox QLabel { background: transparent; color: #172033; min-width: 420px; }
"""


class DlcScanControlWindow(QMainWindow):
    """Manual scan controls sharing the ADC window's single DLC pro session."""

    PRECISION_OPTIONS = (
        ("100", 100.0), ("10", 10.0), ("1", 1.0),
        ("0.1", 0.1), ("0.01", 0.01), ("0.001", 0.001),
        ("0.0001", 0.0001), ("0.00001", 0.00001),
        ("0.000001", 0.000001),
    )

    def __init__(self, session, settings: QSettings, parent=None):
        super().__init__(parent)
        self.session = session
        self.settings = settings
        self._scan_edit_locked = False
        self._write_pending = False
        self._connected = bool(session.is_connected)
        self._step = float(settings.value("dlcpro/scan_step", 0.01))
        valid_steps = {value for _label, value in self.PRECISION_OPTIONS}
        if self._step not in valid_steps:
            self._step = 0.01

        self.setWindowTitle("扫频控制")
        self.resize(920, 650)
        self.setMinimumSize(780, 560)
        self.setStyleSheet(SCAN_CONTROL_STYLE)

        root = QWidget()
        root.setObjectName("scanControlRoot")
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(22, 20, 22, 22)
        page.setSpacing(14)

        title = QLabel("DLC pro 扫频控制")
        title.setObjectName("title")
        note = QLabel(
            "与自动锁频共用同一连接。仅观察模式下可按算法建议手动调整；"
            "自动控制模式运行时禁止人工写入。"
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        page.addWidget(title)
        page.addWidget(note)
        self.status = QLabel("已连接" if self._connected else "DLC pro 未连接")
        self.status.setObjectName("state")
        page.addWidget(self.status)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 18)
        card_layout.setSpacing(14)

        header = QHBoxLayout()
        section = QLabel("SC · 扫描控制")
        section.setObjectName("sectionTitle")
        self.enable_button = QPushButton("启用扫描")
        self.enable_button.setObjectName("scanEnable")
        self.enable_button.setCheckable(True)
        header.addWidget(section)
        header.addStretch(1)
        header.addWidget(self.enable_button)
        card_layout.addLayout(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(13)

        self.precision_row = PrecisionButtonRow(
            self.PRECISION_OPTIONS, self._set_precision, max_columns=5
        )
        self.precision_buttons = self.precision_row.buttons
        for button, (label, _value) in zip(
            self.precision_buttons, self.PRECISION_OPTIONS
        ):
            button.setText(label)

        self.amplitude = self._numeric_spin(decimals=6)
        self.offset = self._numeric_spin(decimals=6)
        self.frequency = self._numeric_spin(decimals=3, minimum=0.0)
        self.frequency.setSuffix(" Hz")

        self.amplitude_row = StepTargetSpinBoxRow(
            "amplitude", self.amplitude, self._select_target
        )
        self.offset_row = StepTargetSpinBoxRow(
            "offset", self.offset, self._select_target
        )
        self.frequency_row = StepTargetSpinBoxRow(
            "frequency", self.frequency, self._select_target
        )
        self.target_buttons = (
            self.amplitude_row.target_button,
            self.offset_row.target_button,
            self.frequency_row.target_button,
        )
        for button in self.target_buttons:
            button.setText("当前调节")

        self.output = SafeComboBox()
        for text_key, value in SCAN_OUTPUT_OPTIONS:
            self.output.addItem(TEXT["zh"][text_key], value)
        self.shape = SafeComboBox()
        for text_key, value in SCAN_SHAPE_OPTIONS:
            self.shape.addItem(TEXT["zh"][text_key], value)

        form.addRow("调节步进", self.precision_row)
        form.addRow("扫描幅度", self.amplitude_row)
        form.addRow("扫描偏置", self.offset_row)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        form.addRow(divider)
        form.addRow("扫描输出", self.output)
        form.addRow("扫描频率", self.frequency_row)
        form.addRow("扫描波形", self.shape)
        card_layout.addLayout(form)
        page.addWidget(card)

        footer = QHBoxLayout()
        self.refresh_button = QPushButton("刷新设备读回")
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        footer.addWidget(self.refresh_button)
        footer.addStretch(1)
        footer.addWidget(close_button)
        page.addLayout(footer)
        page.addStretch(1)

        initial_target = str(settings.value(
            "dlcpro/scan_target", "amplitude"
        ))
        targets = {
            "amplitude": self.amplitude,
            "offset": self.offset,
            "frequency": self.frequency,
        }
        self._active_spinbox = targets.get(initial_target, self.amplitude)
        self._select_target(initial_target, self._active_spinbox)
        self._set_precision(self._step)

        self.enable_button.clicked.connect(self._write_enabled)
        self.amplitude.connect_live_apply(
            lambda: self._write(self.session.set_scan_amplitude, self.amplitude.value())
        )
        self.offset.connect_live_apply(
            lambda: self._write(self.session.set_scan_offset, self.offset.value())
        )
        self.frequency.connect_live_apply(
            lambda: self._write(self.session.set_scan_frequency, self.frequency.value())
        )
        self.output.currentIndexChanged.connect(self._write_output)
        self.shape.currentIndexChanged.connect(self._write_shape)
        self.refresh_button.clicked.connect(self.session.refresh)
        self.session.snapshot_changed.connect(self._render_snapshot)
        self.session.write_snapshot_changed.connect(self._write_completed)
        self.session.connection_changed.connect(self._connection_changed)
        self.session.error.connect(self._show_error)
        self._update_editable()

    @staticmethod
    def _numeric_spin(*, decimals: int, minimum: float = -1_000_000.0):
        spin = SafeDoubleSpinBox()
        spin.setRange(minimum, 1_000_000.0)
        spin.setDecimals(decimals)
        spin.setKeyboardTracking(False)
        spin.set_button_only_mode()
        return spin

    def _set_precision(self, step: float):
        self._step = float(step)
        self._active_spinbox.setSingleStep(self._step)
        self.settings.setValue("dlcpro/scan_step", self._step)
        for button in self.precision_buttons:
            button.blockSignals(True)
            button.setChecked(abs(button._precision_step - self._step) < 1e-12)
            button.blockSignals(False)

    def _select_target(self, target: str, spinbox: SafeDoubleSpinBox):
        self._active_spinbox = spinbox
        spinbox.setSingleStep(self._step)
        self.settings.setValue("dlcpro/scan_target", target)
        for button in self.target_buttons:
            button.blockSignals(True)
            button.setChecked(button._precision_target is spinbox)
            button.blockSignals(False)

    def _write(self, setter, value):
        if not self._can_write():
            return
        self._write_pending = True
        self._update_editable()
        setter(value)

    def _write_enabled(self, checked: bool):
        self._write(self.session.set_scan_enabled, bool(checked))

    def _write_output(self):
        if self.output.signalsBlocked() or self.output.currentData() is None:
            return
        self._write(self.session.set_scan_output_channel, int(self.output.currentData()))

    def _write_shape(self):
        if self.shape.signalsBlocked() or self.shape.currentData() is None:
            return
        self._write(self.session.set_scan_signal_type, int(self.shape.currentData()))

    def _can_write(self) -> bool:
        return self._connected and not self._scan_edit_locked and not self._write_pending

    def _write_completed(self, _snapshot):
        self._write_pending = False
        self._update_editable()

    def _render_snapshot(self, snapshot):
        self.amplitude.sync_from_device(float(snapshot.sc_amplitude))
        self.offset.sync_from_device(float(snapshot.sc_offset))
        self.frequency.sync_from_device(float(snapshot.sc_frequency))
        unit = str(snapshot.sc_unit or "").strip()
        self.offset.setSuffix(f" {unit}" if unit else "")
        self.amplitude.setSuffix(f" {unit} pp" if unit else "")
        self._sync_combo(self.output, int(snapshot.sc_output_channel), "设备值")
        self._sync_combo(self.shape, int(snapshot.sc_signal_type), "设备值")
        self.enable_button.blockSignals(True)
        self.enable_button.setChecked(bool(snapshot.sc_enabled))
        self.enable_button.setText("扫描已启用" if snapshot.sc_enabled else "启用扫描")
        self.enable_button.blockSignals(False)

    @staticmethod
    def _sync_combo(combo: QComboBox, value: int, fallback: str):
        index = combo.findData(value)
        if index < 0:
            combo.addItem(f"{fallback} {value}", value)
            index = combo.count() - 1
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def set_scan_edit_locked(self, locked: bool):
        self._scan_edit_locked = bool(locked)
        self._update_editable()

    def _connection_changed(self, connected: bool, text: str):
        self._connected = bool(connected)
        self._write_pending = False
        self.status.setText("已连接 DLC pro" if connected else text)
        self._update_editable()

    def _update_editable(self):
        editable = self._can_write()
        for widget in (
            self.enable_button, self.amplitude, self.offset, self.frequency,
            self.output, self.shape,
        ):
            widget.setEnabled(editable)
        self.precision_row.setEnabled(not self._scan_edit_locked)
        self.refresh_button.setEnabled(self._connected and not self._write_pending)
        if self._scan_edit_locked:
            self.status.setText("自动锁频正在控制扫频参数，人工调节已锁定")

    def _show_error(self, message: str):
        self._write_pending = False
        self._update_editable()
        if self._connected:
            self.session.refresh()
        if self.isVisible():
            QMessageBox.critical(self, "DLC pro 扫频控制错误", message)

    def showEvent(self, event):
        super().showEvent(event)
        self.session.refresh()
