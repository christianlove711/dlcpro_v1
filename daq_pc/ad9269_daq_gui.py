from __future__ import annotations

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from widgets.common_controls import VisibleCheckBox

from daq_pc.daq_protocol_v2 import (
    CONFIG_CHANNEL_SWAP,
    CONFIG_TEST_SHIFT,
    CONFIG_TRIGGER_B,
    DATA_FORMAT_DUAL_S16,
    DATA_PORT,
    FLAG_DCO_ALIVE,
    FLAG_DMA_ERROR,
    FLAG_FIFO_OVERFLOW,
    FLAG_LINK_UP,
    FLAG_OTR_A,
    FLAG_OTR_B,
    FLAG_RUNNING,
    FLAG_SPI_ERROR,
    Command,
)
from daq_pc.daq_qt_dual import UdpDualReceiver
from daq_pc.daq_udp_dual import ControlClient, DualSampleRingBuffer


TIMEBASES = [
    ("100 us", 100e-6),
    ("200 us", 200e-6),
    ("1 ms", 1e-3),
    ("10 ms", 10e-3),
    ("100 ms", 100e-3),
    ("1 s", 1.0),
]

RATES = [3_000_000, 5_000_000, 10_000_000, 20_000_000]

DISPLAY_REFRESH_RATES = [
    ("2 FPS（慢）", 2),
    ("5 FPS", 5),
    ("10 FPS", 10),
    ("20 FPS", 20),
    ("30 FPS", 30),
]

VERTICAL_SCALES = [
    ("自动量程", None),
    ("2 V/div", 2.0),
    ("1 V/div", 1.0),
    ("500 mV/div", 0.5),
    ("200 mV/div", 0.2),
    ("100 mV/div", 0.1),
    ("50 mV/div", 0.05),
    ("20 mV/div", 0.02),
    ("10 mV/div", 0.01),
]

RECORD_INTERVAL_SECONDS = 0.1
RECORD_MAX_ANALYSIS_SAMPLES = 50_000


def codes_to_voltage(values, full_scale_volts: float):
    """Convert signed AD9269 codes to the module SMA input voltage."""
    return np.asarray(values, dtype=np.float32) * (float(full_scale_volts) / 32768.0)


def voltage_statistics(values: np.ndarray, valid: np.ndarray, full_scale_volts: float):
    """Return compact voltage statistics without retaining a raw capture."""
    if values.size == 0 or valid.size != values.size or not valid.any():
        return None
    voltage = values[valid].astype(np.float64) * (float(full_scale_volts) / 32768.0)
    low, high = np.percentile(voltage, (0.5, 99.5))
    mean = float(np.mean(voltage))
    return {
        "min_v": float(np.min(voltage)),
        "max_v": float(np.max(voltage)),
        "vpp_v": float(np.ptp(voltage)),
        "vpp99_v": float(high - low),
        "mean_v": mean,
        "ac_rms_v": float(np.sqrt(np.mean(np.square(voltage - mean)))),
    }


def _smooth_bins(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    if values.size < 5:
        return values
    weights = np.array([1.0, 2.0, 3.0, 2.0, 1.0], dtype=np.float32)
    source = np.where(valid, values, 0.0)
    numerator = np.convolve(source, weights, mode="same")
    denominator = np.convolve(valid.astype(np.float32), weights, mode="same")
    return np.divide(
        numerator,
        denominator,
        out=values.astype(np.float32, copy=True),
        where=denominator > 0.0,
    )


def make_dual_envelope(
    a: np.ndarray,
    b: np.ndarray,
    valid: np.ndarray,
    pixels: int,
    *,
    smooth: bool,
):
    """Reduce a raw window to a smooth trace plus a lossless peak envelope."""
    count = int(a.size)
    if count == 0:
        return None
    bins = min(max(1, int(pixels)), count)
    boundaries = np.linspace(0, count, bins + 1, dtype=np.int64)
    starts = boundaries[:-1]
    widths = np.diff(boundaries)
    a_min = np.minimum.reduceat(a, starts).astype(np.float32)
    a_max = np.maximum.reduceat(a, starts).astype(np.float32)
    b_min = np.minimum.reduceat(b, starts).astype(np.float32)
    b_max = np.maximum.reduceat(b, starts).astype(np.float32)
    a_mean = np.add.reduceat(a, starts, dtype=np.int64) / widths
    b_mean = np.add.reduceat(b, starts, dtype=np.int64) / widths
    valid_count = np.add.reduceat(valid.astype(np.uint8), starts)
    bin_valid = valid_count == widths
    a_mean = a_mean.astype(np.float32)
    b_mean = b_mean.astype(np.float32)
    if smooth:
        a_mean = _smooth_bins(a_mean, bin_valid)
        b_mean = _smooth_bins(b_mean, bin_valid)
    return a_min, a_max, a_mean, b_min, b_max, b_mean, bin_valid


def select_scope_window(
    a: np.ndarray,
    b: np.ndarray,
    valid: np.ndarray,
    samples: int,
    trigger_channel: int,
    trigger_mode: int,
    threshold: int,
):
    """Align a display window to the latest usable trigger crossing."""
    samples = min(max(1, int(samples)), int(a.size))
    if samples <= 1:
        return a[-samples:], b[-samples:], valid[-samples:], None, None

    trace = b if trigger_channel else a
    sample_step = max(1, trace.size // 200_000)
    sampled_valid = valid[::sample_step]
    valid_values = trace[::sample_step][sampled_valid]
    if valid_values.size < 8:
        return a[-samples:], b[-samples:], valid[-samples:], None, None

    if trigger_mode in (1, 2):
        level = float(threshold)
    else:
        low, high = np.percentile(valid_values, (10.0, 90.0))
        level = float(low + high) * 0.5

    pretrigger = max(1, samples // 5)
    posttrigger = samples - pretrigger
    search_end = max(pretrigger + 1, a.size - posttrigger + 1)
    search_start = max(pretrigger, search_end - max(samples // 2, 2048))
    trace_window = trace[search_start - 1 : search_end]
    valid_window = valid[search_start - 1 : search_end]
    pair_valid = valid_window[:-1] & valid_window[1:]
    if trigger_mode == 2:
        crossing_mask = (trace_window[:-1] >= level) & (trace_window[1:] < level)
    else:
        crossing_mask = (trace_window[:-1] <= level) & (trace_window[1:] > level)
    crossings = np.flatnonzero(pair_valid & crossing_mask) + search_start

    usable = crossings[(crossings >= pretrigger) & (crossings + posttrigger <= a.size)]
    if usable.size == 0:
        return a[-samples:], b[-samples:], valid[-samples:], None, level

    trigger_index = int(usable[-1])
    start = trigger_index - pretrigger
    end = start + samples
    return (
        a[start:end],
        b[start:end],
        valid[start:end],
        pretrigger / max(1, samples - 1),
        level,
    )


def estimate_frequency(values: np.ndarray, valid: np.ndarray, rate_hz: float) -> float:
    """Estimate frequency from robust rising crossings for scope measurements."""
    if values.size < 16 or rate_hz <= 0.0:
        return 0.0
    step = max(1, values.size // 200_000)
    trace = values[::step].astype(np.float32)
    mask = valid[::step]
    if np.count_nonzero(mask) < 16:
        return 0.0
    trace = _smooth_bins(trace, mask)
    low, high = np.percentile(trace[mask], (10.0, 90.0))
    level = float(low + high) * 0.5
    crossings = np.flatnonzero(
        mask[:-1] & mask[1:] & (trace[:-1] <= level) & (trace[1:] > level)
    )
    if crossings.size < 3:
        return 0.0
    periods = np.diff(crossings)
    median_period = float(np.median(periods))
    if median_period <= 0.0:
        return 0.0
    return (float(rate_hz) / step) / median_period


class StatusPoller(QThread):
    received = Signal(object)
    failed = Signal(str)

    def __init__(self, control: ControlClient):
        super().__init__()
        self.control = control
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        while not self._stop_requested:
            try:
                self.received.emit(self.control.request(Command.STATUS))
            except Exception as exc:
                if not self._stop_requested:
                    self.failed.emit(str(exc))
            for _ in range(20):
                if self._stop_requested:
                    return
                self.msleep(50)


class DualWaveformWidget(QWidget):
    def __init__(self, single_channel: int | None = None):
        super().__init__()
        self._single_channel = single_channel
        self.setMinimumSize(720, 420 if single_channel is not None else 520)
        self._envelope = None
        self._duration = 1e-3
        self._unit_modes = ["voltage", "voltage"]
        self._full_scale_volts = [5.0, 5.0]
        self._volts_per_div = [None, None]
        self._vertical_offset = [0.0, 0.0]
        self._trigger_position = None
        self._trigger_level_code = None
        self._trigger_channel = 0

    def clear(self):
        self._envelope = None
        self.update()

    def set_display_options(
        self,
        unit_modes,
        full_scale_volts,
        volts_per_div,
        vertical_offset,
    ):
        self._unit_modes = [str(unit_modes[0]), str(unit_modes[1])]
        self._full_scale_volts = [
            float(full_scale_volts[0]),
            float(full_scale_volts[1]),
        ]
        self._volts_per_div = [volts_per_div[0], volts_per_div[1]]
        self._vertical_offset = [
            float(vertical_offset[0]),
            float(vertical_offset[1]),
        ]
        self.update()

    def set_envelope(
        self,
        envelope,
        duration: float,
        *,
        trigger_position=None,
        trigger_level_code=None,
        trigger_channel: int = 0,
    ):
        self._envelope = envelope
        self._duration = float(duration)
        self._trigger_position = trigger_position
        self._trigger_level_code = trigger_level_code
        self._trigger_channel = int(trigger_channel)
        self.update()

    @staticmethod
    def _time_text(seconds: float) -> str:
        if seconds < 1e-3:
            return f"{seconds * 1e6:.0f} us"
        if seconds < 1.0:
            return f"{seconds * 1e3:.1f} ms"
        return f"{seconds:.2f} s"

    @staticmethod
    def _nice_division(required: float) -> float:
        required = max(float(required), 1e-12)
        exponent = np.floor(np.log10(required))
        base = required / (10.0 ** exponent)
        if base <= 1.0:
            nice = 1.0
        elif base <= 2.0:
            nice = 2.0
        elif base <= 5.0:
            nice = 5.0
        else:
            nice = 10.0
        return nice * (10.0 ** exponent)

    def _convert(self, values: np.ndarray, channel: int) -> np.ndarray:
        if self._unit_modes[channel] == "voltage":
            return codes_to_voltage(values, self._full_scale_volts[channel])
        return np.asarray(values, dtype=np.float32)

    def _axis_text(self, value: float, channel: int) -> str:
        if self._unit_modes[channel] != "voltage":
            return f"{value:.0f}"
        if abs(value) >= 1.0:
            return f"{value:.3g} V"
        if abs(value) >= 1e-3:
            return f"{value * 1e3:.3g} mV"
        return f"{value * 1e6:.3g} uV"

    def _channel_range(self, mean: np.ndarray, valid: np.ndarray, channel: int):
        volts_per_div = self._volts_per_div[channel]
        center = self._vertical_offset[channel]
        if self._unit_modes[channel] == "voltage" and volts_per_div is not None:
            division = float(volts_per_div)
            return center - 4.0 * division, center + 4.0 * division, division
        if self._unit_modes[channel] != "voltage" and volts_per_div is not None:
            return -32768.0, 32768.0, 8192.0

        finite = valid & np.isfinite(mean)
        if not finite.any():
            fallback = (
                self._full_scale_volts[channel]
                if self._unit_modes[channel] == "voltage"
                else 32768.0
            )
            return -fallback, fallback, fallback / 4.0
        values = mean[finite]
        low, high = np.percentile(values, (1.0, 99.0))
        center = float(low + high) * 0.5
        minimum_span = 0.01 if self._unit_modes[channel] == "voltage" else 64.0
        half_span = max(float(high - low) * 0.60, minimum_span * 0.5)
        division = self._nice_division(half_span / 3.5)
        return center - 4.0 * division, center + 4.0 * division, division

    def _draw_channel(
        self,
        painter: QPainter,
        area,
        minimum: np.ndarray,
        maximum: np.ndarray,
        mean: np.ndarray,
        valid: np.ndarray,
        color: QColor,
        label: str,
        channel: int,
    ):
        painter.fillRect(area, QColor("#09111f"))
        painter.setPen(QPen(QColor("#526174"), 1))
        painter.drawRect(area)
        painter.setPen(QPen(QColor("#233247"), 1))
        for index in range(1, 8):
            y = area.top() + area.height() * index / 8
            painter.drawLine(area.left(), int(y), area.right(), int(y))
        for index in range(1, 10):
            x = area.left() + area.width() * index / 10
            painter.drawLine(int(x), area.top(), int(x), area.bottom())

        minimum = self._convert(minimum, channel)
        maximum = self._convert(maximum, channel)
        mean = self._convert(mean, channel)
        ymin, ymax, division = self._channel_range(mean, valid, channel)
        span = max(1e-12, ymax - ymin)

        if ymin < 0.0 < ymax:
            zero_y = area.bottom() - (0.0 - ymin) * area.height() / span
            painter.setPen(QPen(QColor("#53657a"), 1))
            painter.drawLine(area.left(), int(zero_y), area.right(), int(zero_y))

        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.drawText(area.adjusted(8, 6, 0, 0), Qt.AlignTop | Qt.AlignLeft, label)
        scale_text = (
            f"{self._axis_text(division, channel)}/div"
            if self._unit_modes[channel] == "voltage"
            else f"{division:.0f} code/div"
        )
        painter.drawText(area.adjusted(0, 6, -8, 0), Qt.AlignTop | Qt.AlignRight, scale_text)
        painter.drawText(4, area.top() + 5, self._axis_text(ymax, channel))
        painter.drawText(4, area.center().y() + 5, self._axis_text((ymin + ymax) * 0.5, channel))
        painter.drawText(4, area.bottom(), self._axis_text(ymin, channel))

        if minimum.size == 0:
            painter.setPen(QPen(QColor("#718096"), 1))
            painter.drawText(area, Qt.AlignCenter, "等待数据")
            return

        if (
            self._trigger_position is not None
            and channel == self._trigger_channel
            and self._trigger_level_code is not None
        ):
            trigger_level = float(
                self._convert(np.array([self._trigger_level_code]), channel)[0]
            )
            if ymin <= trigger_level <= ymax:
                trigger_y = area.bottom() - (trigger_level - ymin) * area.height() / span
                trigger_color = QColor("#facc15")
                trigger_color.setAlpha(125)
                painter.setPen(QPen(trigger_color, 1, Qt.DashLine))
                painter.drawLine(area.left(), int(trigger_y), area.right(), int(trigger_y))

        x_scale = area.width() / max(1, minimum.size - 1)
        envelope_color = QColor(color)
        envelope_color.setAlpha(78)
        painter.save()
        painter.setClipRect(area)
        painter.setPen(QPen(envelope_color, 0.8))
        for index, is_valid in enumerate(valid):
            if not is_valid:
                continue
            x = area.left() + index * x_scale
            y_min = area.bottom() - (float(minimum[index]) - ymin) * area.height() / span
            y_max = area.bottom() - (float(maximum[index]) - ymin) * area.height() / span
            if abs(y_min - y_max) >= 1.0:
                painter.drawLine(QPointF(x, y_max), QPointF(x, y_min))

        painter.setPen(QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QPainterPath()
        path_started = False
        for index, is_valid in enumerate(valid):
            if not is_valid:
                path_started = False
                continue
            x = area.left() + index * x_scale
            y_mid = area.bottom() - (float(mean[index]) - ymin) * area.height() / span
            if not path_started:
                path.moveTo(x, y_mid)
                path_started = True
            else:
                path.lineTo(x, y_mid)
        painter.drawPath(path)
        painter.restore()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#f8fafc"))
        outer = self.rect().adjusted(82, 20, -20, -48)

        if self._envelope is None:
            empty = np.empty(0)
            valid = np.empty(0, dtype=np.bool_)
            a_min = a_max = a_mean = b_min = b_max = b_mean = empty
        else:
            a_min, a_max, a_mean, b_min, b_max, b_mean, valid = self._envelope

        if self._single_channel is None:
            gap = 36
            panel_height = (outer.height() - gap) // 2
            area_a = outer.adjusted(0, 0, 0, -(outer.height() - panel_height))
            area_b = outer.adjusted(0, panel_height + gap, 0, 0)
            self._draw_channel(
                painter, area_a, a_min, a_max, a_mean, valid, QColor("#38bdf8"),
                f"通道 A  透射信号 / {'V' if self._unit_modes[0] == 'voltage' else 'ADC code'}",
                0,
            )
            self._draw_channel(
                painter, area_b, b_min, b_max, b_mean, valid, QColor("#f59e0b"),
                f"通道 B  误差信号 / {'V' if self._unit_modes[1] == 'voltage' else 'ADC code'}",
                1,
            )
            time_area = area_b
            trigger_top = area_a.top()
            trigger_bottom = area_b.bottom()
        else:
            channel = self._single_channel
            if channel == 0:
                minimum, maximum, mean = a_min, a_max, a_mean
                color = QColor("#38bdf8")
                name = "通道 A  透射信号"
            else:
                minimum, maximum, mean = b_min, b_max, b_mean
                color = QColor("#f59e0b")
                name = "通道 B  误差信号"
            self._draw_channel(
                painter,
                outer,
                minimum,
                maximum,
                mean,
                valid,
                color,
                f"{name} / {'V' if self._unit_modes[channel] == 'voltage' else 'ADC code'}",
                channel,
            )
            time_area = outer
            trigger_top = outer.top()
            trigger_bottom = outer.bottom()

        if (
            self._trigger_position is not None
            and (
                self._single_channel is None
                or self._single_channel == self._trigger_channel
            )
        ):
            trigger_x = time_area.left() + time_area.width() * float(self._trigger_position)
            painter.setPen(QPen(QColor("#facc15"), 1, Qt.DashLine))
            painter.drawLine(int(trigger_x), trigger_top, int(trigger_x), trigger_bottom)
            painter.drawText(int(trigger_x) + 5, trigger_top + 17, "T")

        painter.setPen(QPen(QColor("#475569"), 1))
        if self._trigger_position is None:
            left_text = f"-{self._time_text(self._duration)}"
            right_text = "现在"
        else:
            left_text = f"-{self._time_text(self._duration * self._trigger_position)}"
            right_text = f"+{self._time_text(self._duration * (1.0 - self._trigger_position))}"
        painter.drawText(
            time_area.adjusted(0, time_area.height() + 8, 0, time_area.height() + 30),
            Qt.AlignLeft,
            left_text,
        )
        painter.drawText(
            time_area.adjusted(0, time_area.height() + 8, 0, time_area.height() + 30),
            Qt.AlignRight,
            right_text,
        )
        painter.end()


class ChannelScopeWindow(QWidget):
    def __init__(
        self,
        channel: int,
        unit: QComboBox,
        full_scale: QDoubleSpinBox,
        vertical_scale: QComboBox,
        offset: QDoubleSpinBox,
        parent=None,
    ):
        super().__init__(parent, Qt.Window)
        self.channel = int(channel)
        channel_name = "通道 A - 透射信号" if channel == 0 else "通道 B - 误差信号"
        self.setWindowTitle(f"AD9269 {channel_name}")
        self.resize(1120, 680)
        self.setMinimumSize(760, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(channel_name)
        title.setObjectName("scopeTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        settings = QFrame()
        settings.setObjectName("scopeSettings")
        settings_layout = QHBoxLayout(settings)
        settings_layout.setContentsMargins(12, 8, 12, 8)
        settings_layout.setSpacing(16)

        def add_setting(label_text: str, widget: QWidget):
            group = QVBoxLayout()
            label = QLabel(label_text)
            label.setObjectName("scopeSettingLabel")
            widget.setMinimumWidth(150)
            group.addWidget(label)
            group.addWidget(widget)
            settings_layout.addLayout(group)

        add_setting("单位", unit)
        add_setting("满量程峰值", full_scale)
        add_setting("垂直档位", vertical_scale)
        add_setting("垂直偏移", offset)
        settings_layout.addStretch()
        layout.addWidget(settings)

        self.measurement_label = QLabel("等待数据")
        self.measurement_label.setObjectName("scopeMeasurement")
        layout.addWidget(self.measurement_label)

        self.waveform = DualWaveformWidget(single_channel=channel)
        layout.addWidget(self.waveform, 1)

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def set_measurement(self, text: str):
        self.measurement_label.setText(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AD9269 双通道连续采集")
        self.resize(1040, 760)
        self.control: ControlClient | None = None
        self.receiver: UdpDualReceiver | None = None
        self.poller: StatusPoller | None = None
        self.ring = DualSampleRingBuffer()
        self.latest_metrics: dict = {}
        self.latest_status = None
        self.measured_pair_rate_hz = 0.0
        self._status_pair_count: int | None = None
        self._status_timestamp: float | None = None
        self._transitioning = False
        self._expected_stream_id: int | None = None
        self.frozen = False
        self._last_display_window = None
        self._frozen_snapshot = None
        self._latest_analysis: dict = {}
        self._recording = False
        self._record_rows: list[dict] = []
        self._record_started_monotonic = 0.0
        self._record_started_wall = None
        self._last_record_monotonic = 0.0

        root = QWidget()
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(24, 18, 24, 22)
        page.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("AD9269 双通道连续采集")
        title.setObjectName("title")
        self.run_badge = QLabel("未连接")
        self.run_badge.setObjectName("badge")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.run_badge)
        page.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        controls = QFrame()
        controls.setObjectName("panel")
        controls.setFixedWidth(420)
        control_layout = QVBoxLayout(controls)
        control_layout.setContentsMargins(20, 20, 20, 20)

        settings_scroll = QScrollArea()
        settings_scroll.setObjectName("settingsScroll")
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        settings_widget = QWidget()
        settings_widget.setObjectName("settingsContent")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 8, 0)
        settings_layout.setSpacing(10)
        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self.board_ip = QLineEdit("192.168.20.2")
        self.rate = QComboBox()
        for rate in RATES:
            self.rate.addItem(f"{rate // 1_000_000} MSPS", rate)
        self.rate.setCurrentText("5 MSPS")
        self.timebase = QComboBox()
        for label, seconds in TIMEBASES:
            self.timebase.addItem(label, seconds)
        self.timebase.setCurrentText("1 ms")
        self.display_mode = QComboBox()
        self.display_mode.addItem("示波器触发（稳定）", "scope")
        self.display_mode.addItem("慢速滚动", "roll")
        self.display_refresh = QComboBox()
        for label, fps in DISPLAY_REFRESH_RATES:
            self.display_refresh.addItem(label, fps)
        self.display_refresh.setCurrentText("5 FPS")
        self.display_unit_a = QComboBox()
        self.display_unit_b = QComboBox()
        for combo in (self.display_unit_a, self.display_unit_b):
            combo.addItem("电压 / V", "voltage")
            combo.addItem("ADC 原码", "code")
        self.full_scale_a = QDoubleSpinBox()
        self.full_scale_b = QDoubleSpinBox()
        for spin in (self.full_scale_a, self.full_scale_b):
            spin.setRange(0.1, 20.0)
            spin.setDecimals(2)
            spin.setSingleStep(0.1)
            spin.setValue(5.0)
            spin.setSuffix(" V")
        self.vertical_scale_a = QComboBox()
        self.vertical_scale_b = QComboBox()
        for combo in (self.vertical_scale_a, self.vertical_scale_b):
            for label, volts_per_div in VERTICAL_SCALES:
                combo.addItem(label, volts_per_div)
            combo.setCurrentText("自动量程")
        self.vertical_offset_a = QDoubleSpinBox()
        self.vertical_offset_b = QDoubleSpinBox()
        for spin in (self.vertical_offset_a, self.vertical_offset_b):
            spin.setRange(-20.0, 20.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setSuffix(" V")
        self.smooth_display = VisibleCheckBox("平滑主曲线（原始毛刺仍保留）")
        self.smooth_display.setChecked(True)
        self.trigger_mode = QComboBox()
        self.trigger_mode.addItem("仅记录，不触发", 0)
        self.trigger_mode.addItem("高于阈值", 1)
        self.trigger_mode.addItem("低于阈值", 2)
        self.trigger_mode.addItem("立即标记", 3)
        self.trigger_mode.addItem("外部触发", 4)
        self.trigger_channel = QComboBox()
        self.trigger_channel.addItem("A：透射", 0)
        self.trigger_channel.addItem("B：误差", 1)
        self.threshold = QSpinBox()
        self.threshold.setRange(-32768, 32767)
        self.threshold.setValue(0)
        self.test_mode = QComboBox()
        self.test_mode.addItem("关闭", 0)
        for mode in range(1, 8):
            self.test_mode.addItem(f"AD9269 测试码 {mode}", mode)
        self.channel_swap = VisibleCheckBox("交换 A/B 边沿映射")

        self.scope_a = ChannelScopeWindow(
            0,
            self.display_unit_a,
            self.full_scale_a,
            self.vertical_scale_a,
            self.vertical_offset_a,
            self,
        )
        self.scope_b = ChannelScopeWindow(
            1,
            self.display_unit_b,
            self.full_scale_b,
            self.vertical_scale_b,
            self.vertical_offset_b,
            self,
        )

        form.addRow("板卡 IP", self.board_ip)
        form.addRow("采样率", self.rate)
        form.addRow("显示时间基", self.timebase)
        form.addRow("显示模式", self.display_mode)
        form.addRow("刷新速度", self.display_refresh)
        form.addRow("轨迹显示", self.smooth_display)
        form.addRow("触发标记", self.trigger_mode)
        form.addRow("触发通道", self.trigger_channel)
        form.addRow("触发阈值 (ADC码)", self.threshold)
        form.addRow("ADC 测试", self.test_mode)
        form.addRow("通道校正", self.channel_swap)
        settings_layout.addLayout(form)

        info = QLabel(
            "DDR 始终保存双通道完整数据。PC 网络模式支持 3/5/10/20 MSPS；"
            "40/80 MSPS 保留给 DDR 与 ARM 本地处理。冻结窗口不会停止板卡采集。"
        )
        info.setWordWrap(True)
        info.setObjectName("hint")
        settings_layout.addWidget(info)
        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)
        control_layout.addWidget(settings_scroll, 1)

        row = QHBoxLayout()
        self.connect_button = QPushButton("连接板卡")
        self.start_button = QPushButton("开始")
        self.stop_button = QPushButton("停止")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        row.addWidget(self.connect_button)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        control_layout.addLayout(row)

        row2 = QHBoxLayout()
        self.freeze_button = QPushButton("冻结窗口")
        self.freeze_button.setEnabled(False)
        row2.addWidget(self.freeze_button)
        control_layout.addLayout(row2)

        self.record_button = QPushButton("开始实验记录")
        self.record_button.setEnabled(False)
        self.record_button.setToolTip(
            "连续记录两路电压幅值、RMS、频率和采集状态；结束时导出 CSV"
        )
        self.record_status = QLabel("实验记录未开始")
        self.record_status.setObjectName("recordStatus")
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.record_status)

        plot_panel = QFrame()
        plot_panel.setObjectName("panel")
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(18, 14, 18, 14)
        self.metrics_label = QLabel("等待连接")
        self.metrics_label.setObjectName("metrics")
        self.measurements_label = QLabel("A: --    B: --")
        self.measurements_label.setObjectName("measurements")
        plot_layout.addWidget(self.metrics_label)
        plot_layout.addWidget(self.measurements_label)

        scope_actions = QHBoxLayout()
        scope_actions.setSpacing(12)
        self.open_scope_a_button = QPushButton("打开通道 A 波形")
        self.open_scope_b_button = QPushButton("打开通道 B 波形")
        self.open_scope_a_button.setObjectName("scopeButtonA")
        self.open_scope_b_button.setObjectName("scopeButtonB")
        scope_actions.addWidget(self.open_scope_a_button)
        scope_actions.addWidget(self.open_scope_b_button)
        plot_layout.addLayout(scope_actions)

        channel_status = QHBoxLayout()
        self.channel_a_status = QLabel("通道 A  透射信号")
        self.channel_b_status = QLabel("通道 B  误差信号")
        self.channel_a_status.setObjectName("channelStatusA")
        self.channel_b_status.setObjectName("channelStatusB")
        channel_status.addWidget(self.channel_a_status)
        channel_status.addWidget(self.channel_b_status)
        plot_layout.addLayout(channel_status)
        plot_layout.addStretch(1)

        body.addWidget(controls)
        body.addWidget(plot_panel, 1)
        page.addLayout(body, 1)

        self.connect_button.clicked.connect(self.connect_board)
        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        self.freeze_button.clicked.connect(self.toggle_freeze)
        self.record_button.clicked.connect(self.toggle_recording)
        self.open_scope_a_button.clicked.connect(self.scope_a.show_window)
        self.open_scope_b_button.clicked.connect(self.scope_b.show_window)
        self.display_refresh.currentIndexChanged.connect(self._update_plot_interval)
        for combo in (
            self.display_unit_a,
            self.display_unit_b,
            self.vertical_scale_a,
            self.vertical_scale_b,
        ):
            combo.currentIndexChanged.connect(self._update_display_options)
        for spin in (
            self.full_scale_a,
            self.full_scale_b,
            self.vertical_offset_a,
            self.vertical_offset_b,
        ):
            spin.valueChanged.connect(self._update_display_options)
        self.display_mode.currentIndexChanged.connect(self.refresh_plot)
        self.timebase.currentIndexChanged.connect(self.refresh_plot)
        self.smooth_display.toggled.connect(self.refresh_plot)

        self.plot_timer = QTimer(self)
        self.plot_timer.setTimerType(Qt.PreciseTimer)
        self._update_plot_interval()
        self.plot_timer.timeout.connect(self.refresh_plot)
        self.plot_timer.start()

        self.record_timer = QTimer(self)
        self.record_timer.setInterval(round(RECORD_INTERVAL_SECONDS * 1000))
        self.record_timer.timeout.connect(self._append_record_point)
        self.record_timer.start()
        self._update_display_options()

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #eef2f7; color: #172033; font-size: 14px; }
            QLabel#title { font-size: 28px; font-weight: 700; }
            QLabel#badge { font-size: 15px; font-weight: 600; padding: 8px 12px; color: #334155; }
            QFrame#panel { background: white; border: 1px solid #d7dee8; border-radius: 7px; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { min-height: 34px; background: white; border: 1px solid #b9c4d3; border-radius: 5px; padding: 0 10px; }
            QPushButton { min-height: 38px; border: 1px solid #aeb9c8; border-radius: 5px; background: white; font-weight: 600; }
            QPushButton:hover { border-color: #2563eb; color: #1d4ed8; }
            QPushButton:disabled { background: #f1f5f9; color: #94a3b8; }
            QPushButton#primary { background: #2563eb; color: white; border-color: #2563eb; }
            QLabel#metrics { font-size: 14px; color: #334155; padding: 2px 4px; }
            QLabel#measurements { font-family: Consolas; font-size: 13px; color: #475569; padding: 0 4px 4px 4px; }
            QLabel#hint { color: #64748b; line-height: 1.4; }
            QLabel#recordStatus { color: #64748b; font-size: 12px; padding: 2px 4px; }
            QLabel#scopeTitle { color: #172033; font-size: 22px; font-weight: 700; }
            QLabel#scopeSettingLabel { color: #64748b; font-size: 12px; }
            QLabel#scopeMeasurement { color: #475569; font-family: Consolas; padding: 2px 4px; }
            QFrame#scopeSettings { background: #f8fafc; border: 1px solid #d7dee8; border-radius: 5px; }
            QLabel#channelStatusA, QLabel#channelStatusB { min-height: 180px; padding: 20px; font-size: 18px; font-weight: 600; border: 1px solid #d7dee8; border-radius: 5px; }
            QLabel#channelStatusA { color: #0369a1; background: #f0f9ff; }
            QLabel#channelStatusB { color: #b45309; background: #fffbeb; }
            QPushButton#scopeButtonA { color: #0369a1; border-color: #7dd3fc; }
            QPushButton#scopeButtonB { color: #b45309; border-color: #fcd34d; }
            QScrollArea#settingsScroll, QWidget#settingsContent { background: transparent; border: none; }
            QPushButton#recording { background: #dc2626; color: white; border-color: #dc2626; }
            """
        )
        self.start_button.setObjectName("primary")

    def _update_plot_interval(self, *args):
        del args
        fps = int(self.display_refresh.currentData() or 5)
        if hasattr(self, "plot_timer"):
            self.plot_timer.setInterval(max(1, round(1000 / fps)))

    def _update_display_options(self, *args):
        del args
        unit_modes = [
            str(self.display_unit_a.currentData() or "voltage"),
            str(self.display_unit_b.currentData() or "voltage"),
        ]
        self.full_scale_a.setEnabled(unit_modes[0] == "voltage")
        self.vertical_scale_a.setEnabled(unit_modes[0] == "voltage")
        self.vertical_offset_a.setEnabled(unit_modes[0] == "voltage")
        self.full_scale_b.setEnabled(unit_modes[1] == "voltage")
        self.vertical_scale_b.setEnabled(unit_modes[1] == "voltage")
        self.vertical_offset_b.setEnabled(unit_modes[1] == "voltage")
        for waveform in (self.scope_a.waveform, self.scope_b.waveform):
            waveform.set_display_options(
                unit_modes,
                [self.full_scale_a.value(), self.full_scale_b.value()],
                [self.vertical_scale_a.currentData(), self.vertical_scale_b.currentData()],
                [self.vertical_offset_a.value(), self.vertical_offset_b.value()],
            )
        self.refresh_plot()

    def connect_board(self):
        try:
            control = ControlClient(self.board_ip.text().strip(), timeout=0.8)
            response = control.request(Command.GET_INFO)
            if response.data_format != DATA_FORMAT_DUAL_S16:
                raise RuntimeError(
                    f"数据格式 0x{response.data_format:08X} 不是 AD9269 双通道格式"
                )
            if not response.flags & FLAG_LINK_UP:
                raise RuntimeError("板卡响应正常，但以太网链路未报告 UP")
            self.control = control
            if response.flags & FLAG_RUNNING:
                response = control.request(Command.STOP)
            self._start_poller()
            self.start_button.setEnabled(not bool(response.flags & FLAG_RUNNING))
            self.stop_button.setEnabled(bool(response.flags & FLAG_RUNNING))
            self.connect_button.setText("已连接")
            self.run_badge.setText("已连接  等待启动")
        except Exception as exc:
            QMessageBox.critical(self, "连接失败", str(exc))

    def _stop_receiver(self):
        receiver = self.receiver
        self.receiver = None
        if receiver is None:
            return
        receiver.stop()
        if not receiver.wait(1500):
            raise RuntimeError("UDP 接收线程未能在 1.5 秒内停止")
        receiver.deleteLater()

    def _start_receiver(self, *, restart: bool = False):
        if restart:
            self._stop_receiver()
        elif self.receiver and self.receiver.isRunning():
            return
        self.receiver = UdpDualReceiver(
            self.ring, DATA_PORT, board_ip=self.board_ip.text().strip()
        )
        self.receiver.metrics.connect(self.on_metrics)
        self.receiver.failed.connect(self.on_receiver_error)
        self.receiver.start()
        if not self.receiver.wait_until_ready(1.0):
            message = self.receiver.startup_error or "UDP 5001 端口无法启动"
            raise RuntimeError(message)

    def _reset_stream_view(self):
        self.ring.clear()
        self.latest_metrics = {}
        self.latest_status = None
        self._last_display_window = None
        self._frozen_snapshot = None
        for scope in (self.scope_a, self.scope_b):
            scope.waveform.clear()
            scope.set_measurement("等待数据")
        self._reset_rate_measurement()
        self.update_metrics_text()

    def _configure_board(self):
        config_flags = 0
        if self.trigger_channel.currentData():
            config_flags |= CONFIG_TRIGGER_B
        if self.channel_swap.isChecked():
            config_flags |= CONFIG_CHANNEL_SWAP
        config_flags |= int(self.test_mode.currentData()) << CONFIG_TEST_SHIFT
        return self.control.request(
            Command.CONFIG,
            sample_rate_hz=int(self.rate.currentData()),
            trigger_mode=int(self.trigger_mode.currentData()),
            threshold=self.threshold.value(),
            flags=config_flags,
        )

    def _start_board_once(self):
        self.control.request(Command.STOP)
        self._start_receiver(restart=True)
        self._reset_stream_view()
        self._configure_board()
        response = self.control.request(Command.START, value0=DATA_PORT)
        self._expected_stream_id = int(response.stream_id)
        self.receiver.prepare_stream(response.stream_id)
        return response

    def _start_poller(self):
        if self.poller and self.poller.isRunning():
            return
        self.poller = StatusPoller(self.control)
        self.poller.received.connect(self.on_status)
        self.poller.failed.connect(lambda text: self.run_badge.setText(f"状态查询失败: {text}"))
        self.poller.start()

    def start_stream(self):
        if self.control is None or self._transitioning:
            return
        self._transitioning = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.run_badge.setText("正在启动...")
        try:
            response = self._start_board_once()
            if not self.receiver.wait_for_stream(response.stream_id, 1.5):
                # A stale SG-DMA/UDP session can survive a quick restart.  One
                # complete stop/socket/config/start cycle recovers it without
                # requiring the user to click Stop and Start manually.
                self.run_badge.setText("首包超时，正在自动恢复...")
                response = self._start_board_once()
                if not self.receiver.wait_for_stream(response.stream_id, 2.0):
                    status = self.control.request(Command.STATUS)
                    raise RuntimeError(
                        "板卡已启动但 2 秒内没有收到 UDP 数据；"
                        f"FIFO 当前占用={status.fifo_level}，"
                        f"累计溢出={status.fifo_overflow}，"
                        f"DMA 错误={status.dma_errors}，"
                        f"状态={status.daq_state}，最后错误={status.last_error}"
                    )
            self.latest_status = response
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.freeze_button.setEnabled(True)
            self.record_button.setEnabled(True)
            self.run_badge.setText(
                f"运行中  {response.sample_rate_hz // 1_000_000} MSPS  "
                f"Stream {response.stream_id}"
            )
        except Exception as exc:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
            self._expected_stream_id = None
            try:
                self._stop_receiver()
            except Exception:
                pass
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.record_button.setEnabled(bool(self._record_rows))
            self.run_badge.setText("启动失败")
            QMessageBox.critical(self, "启动失败", str(exc))
        finally:
            self._transitioning = False

    def stop_stream(self):
        if self.control is None or self._transitioning:
            return
        self._transitioning = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.run_badge.setText("正在停止...")
        stop_error = None
        try:
            response = self.control.request(Command.STOP)
            if response.flags & FLAG_RUNNING:
                raise RuntimeError("板卡回复 STOP 后仍报告 RUNNING")
            self.latest_status = response
        except Exception as exc:
            stop_error = exc
        finally:
            self._finish_recording_without_dialog()
            self._expected_stream_id = None
            try:
                self._stop_receiver()
            except Exception as exc:
                if stop_error is None:
                    stop_error = exc
            self._transitioning = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.record_button.setEnabled(bool(self._record_rows))
            self.run_badge.setText("已停止" if stop_error is None else "停止未确认")
            self._reset_rate_measurement()
            self.update_metrics_text()
            if stop_error is not None:
                QMessageBox.warning(self, "停止警告", str(stop_error))

    def _reset_rate_measurement(self):
        self.measured_pair_rate_hz = 0.0
        self._status_pair_count = None
        self._status_timestamp = None

    def on_status(self, response):
        # A reply queued before STOP may be delivered after the transition.
        # With no expected stream, do not let an old RUNNING reply revive the UI.
        if self._expected_stream_id is None and (response.flags & FLAG_RUNNING):
            return
        if (
            self._expected_stream_id is not None
            and int(response.stream_id) != self._expected_stream_id
        ):
            return
        now = time.monotonic()
        pair_count = int(response.sample_pair_count)
        running = bool(response.flags & FLAG_RUNNING)
        if (
            running
            and self._status_pair_count is not None
            and self._status_timestamp is not None
            and pair_count >= self._status_pair_count
        ):
            elapsed = now - self._status_timestamp
            if elapsed > 0.0:
                measured = (pair_count - self._status_pair_count) / elapsed
                if self.measured_pair_rate_hz > 0.0:
                    self.measured_pair_rate_hz = (
                        0.7 * self.measured_pair_rate_hz + 0.3 * measured
                    )
                else:
                    self.measured_pair_rate_hz = measured
        elif not running:
            self.measured_pair_rate_hz = 0.0
        self._status_pair_count = pair_count
        self._status_timestamp = now
        self.latest_status = response
        if self._transitioning:
            self.update_metrics_text()
            return
        self.start_button.setEnabled(not running and self.control is not None)
        self.stop_button.setEnabled(running)
        if running:
            self.run_badge.setText(
                f"运行中  {response.sample_rate_hz // 1_000_000} MSPS  "
                f"Stream {response.stream_id}"
            )
        self.update_metrics_text()

    def on_metrics(self, metrics: dict):
        if self._expected_stream_id is None:
            return
        if int(metrics.get("stream_id", 0)) != self._expected_stream_id:
            return
        self.latest_metrics = metrics
        self.update_metrics_text()

    def update_metrics_text(self):
        metrics = self.latest_metrics
        status = self.latest_status
        flags = status.flags if status is not None else int(metrics.get("flags", 0))
        fifo_level = status.fifo_level if status else 0
        fifo_overflow = status.fifo_overflow if status else 0
        dma = status.dma_errors if status else 0
        otr_a = status.otr_a_count if status else 0
        otr_b = status.otr_b_count if status else 0
        dco_rate = status.dco_frequency_hz if status else 0
        daq_state = status.daq_state if status else 0
        last_error = status.last_error if status else 0
        health = []
        if flags & FLAG_FIFO_OVERFLOW:
            health.append("FIFO溢出")
        if flags & FLAG_DMA_ERROR:
            health.append("DMA错误")
        if flags & FLAG_SPI_ERROR:
            health.append("SPI错误")
        if not flags & FLAG_DCO_ALIVE and flags:
            health.append("DCO停止")
        if flags & FLAG_OTR_A:
            health.append("A过量程")
        if flags & FLAG_OTR_B:
            health.append("B过量程")
        health_text = "正常" if not health else "/".join(health)
        pl_gap = int(metrics.get("pl_sample_gap", 0))
        gap_actual = metrics.get("last_gap_actual")
        gap_text = (
            f"（最近从索引 {int(gap_actual)} 继续）"
            if pl_gap and gap_actual is not None else ""
        )
        self.metrics_label.setText(
            f"吞吐 {metrics.get('throughput_mbps', 0.0):.1f} Mbit/s    "
            f"DCO {dco_rate / 1_000_000:.3f} MSPS    "
            f"包 {metrics.get('packets', 0)}    网络丢包 {metrics.get('packet_loss', 0)}    "
            f"PL样点空洞 {pl_gap}{gap_text}    "
            f"丢块 {metrics.get('block_loss', 0)}    "
            f"FIFO占用 {fifo_level}    溢出累计 {fifo_overflow}    "
            f"DMA {dma}    OTR A/B {otr_a}/{otr_b}    "
            f"状态 {daq_state}/错误 {last_error}    {health_text}"
        )

    @staticmethod
    def _measurement_voltage(value: float) -> str:
        if abs(value) >= 1.0:
            return f"{value:.3f} V"
        return f"{value * 1e3:.2f} mV"

    @staticmethod
    def _measurement_frequency(value: float) -> str:
        if value >= 1e6:
            return f"{value / 1e6:.4g} MHz"
        if value >= 1e3:
            return f"{value / 1e3:.4g} kHz"
        return f"{value:.4g} Hz"

    def _update_measurements(
        self,
        a: np.ndarray,
        b: np.ndarray,
        valid: np.ndarray,
        effective_rate: float,
    ):
        if not valid.any():
            self.measurements_label.setText("A: --    B: --")
            self.scope_a.set_measurement("A: --")
            self.scope_b.set_measurement("B: --")
            self._latest_analysis = {}
            return
        step = max(1, a.size // 250_000)
        mask = valid[::step]
        summaries = []
        analysis = {}
        for label, values, full_scale in (
            ("A", a, self.full_scale_a.value()),
            ("B", b, self.full_scale_b.value()),
        ):
            factor = float(full_scale) / 32768.0
            voltage = values[::step].astype(np.float64) * factor
            voltage = voltage[mask]
            if voltage.size == 0:
                summaries.append(f"{label}: --")
                continue
            low, high = np.percentile(voltage, (0.5, 99.5))
            mean = float(np.mean(voltage))
            ac_rms = float(np.sqrt(np.mean(np.square(voltage - mean))))
            prefix = label.lower()
            analysis.update(
                {
                    f"{prefix}_min_v": float(np.min(voltage)),
                    f"{prefix}_max_v": float(np.max(voltage)),
                    f"{prefix}_vpp_v": float(np.max(voltage) - np.min(voltage)),
                    f"{prefix}_vpp99_v": float(high - low),
                    f"{prefix}_mean_v": mean,
                    f"{prefix}_ac_rms_v": ac_rms,
                }
            )
            summaries.append(
                f"{label}: Vpp99 {self._measurement_voltage(high - low)}  "
                f"平均 {self._measurement_voltage(mean)}  "
                f"AC-RMS {self._measurement_voltage(ac_rms)}"
            )
        frequency_trace = b if self.trigger_channel.currentData() else a
        frequency = estimate_frequency(frequency_trace, valid, effective_rate)
        frequency_text = (
            self._measurement_frequency(frequency) if frequency > 0.0 else "--"
        )
        channel_text = "B" if self.trigger_channel.currentData() else "A"
        analysis["frequency_hz"] = float(frequency)
        analysis["frequency_channel"] = channel_text
        analysis["valid_samples"] = int(np.count_nonzero(mask))
        self._latest_analysis = analysis
        self.measurements_label.setText(
            "    |    ".join(summaries) + f"    |    频率({channel_text}) {frequency_text}"
        )
        self.scope_a.set_measurement(summaries[0] if summaries else "A: --")
        self.scope_b.set_measurement(summaries[1] if len(summaries) > 1 else "B: --")

    def refresh_plot(self, *args):
        del args
        if self.frozen:
            return
        effective_rate = self.ring.effective_rate_hz
        if effective_rate <= 0:
            return
        duration = float(self.timebase.currentData())
        samples = max(1, int(effective_rate * duration))
        pixels = max(
            400,
            self.scope_a.waveform.width() - 100,
            self.scope_b.waveform.width() - 100,
        )
        scope_mode = self.display_mode.currentData() == "scope"
        snapshot_samples = samples
        if scope_mode:
            search_margin = max(samples // 2, int(effective_rate * 0.002))
            snapshot_samples = min(self.ring.capacity, samples + search_margin)
        a, b, valid, raw_rate, stride = self.ring.snapshot(snapshot_samples)
        if a.size == 0:
            return

        trigger_position = None
        trigger_level = None
        if scope_mode:
            a, b, valid, trigger_position, trigger_level = select_scope_window(
                a,
                b,
                valid,
                samples,
                int(self.trigger_channel.currentData()),
                int(self.trigger_mode.currentData()),
                self.threshold.value(),
            )
        elif a.size > samples:
            a = a[-samples:]
            b = b[-samples:]
            valid = valid[-samples:]

        envelope = make_dual_envelope(
            a,
            b,
            valid,
            pixels,
            smooth=self.smooth_display.isChecked(),
        )
        if envelope is not None:
            for scope in (self.scope_a, self.scope_b):
                scope.waveform.set_envelope(
                    envelope,
                    duration,
                    trigger_position=trigger_position,
                    trigger_level_code=trigger_level,
                    trigger_channel=int(self.trigger_channel.currentData()),
                )
            display_rate = float(raw_rate) / max(1, int(stride))
            self._last_display_window = (a, b, valid, raw_rate, stride)
            self._update_measurements(a, b, valid, display_rate)

    def toggle_freeze(self):
        if not self.frozen:
            self._frozen_snapshot = self._last_display_window
            self.frozen = True
        else:
            self.frozen = False
            self._frozen_snapshot = None
        self.freeze_button.setText("继续滚动" if self.frozen else "冻结窗口")
        if not self.frozen:
            self.refresh_plot()

    def toggle_recording(self):
        if self._recording:
            self._finish_recording_without_dialog()
            self._export_experiment_record()
            return
        if self._record_rows:
            self._export_experiment_record()
            return
        if self._expected_stream_id is None:
            QMessageBox.information(self, "无法记录", "请先启动板卡连续采集。")
            return
        self._recording = True
        self._record_rows = []
        self._record_started_monotonic = time.monotonic()
        self._record_started_wall = datetime.now()
        self._last_record_monotonic = 0.0
        self.record_button.setText("结束并导出 CSV")
        self.record_button.setObjectName("recording")
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)
        self.record_status.setText("正在记录：0.0 s / 0 条")
        self._append_record_point(force=True)

    def _finish_recording_without_dialog(self):
        if not self._recording:
            return
        self._append_record_point(force=True)
        self._recording = False
        self.record_button.setText("导出实验记录")
        self.record_button.setObjectName("")
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)
        elapsed = max(0.0, time.monotonic() - self._record_started_monotonic)
        self.record_status.setText(
            f"记录已结束：{elapsed:.1f} s / {len(self._record_rows)} 条，等待导出"
        )

    def _append_record_point(self, *, force: bool = False):
        if not self._recording:
            return
        now = time.monotonic()
        if not force and now - self._last_record_monotonic < RECORD_INTERVAL_SECONDS:
            return
        effective_rate = float(self.ring.effective_rate_hz)
        if effective_rate <= 0.0:
            return

        duration = min(float(self.timebase.currentData()), 0.02)
        sample_count = min(
            RECORD_MAX_ANALYSIS_SAMPLES,
            max(1024, int(effective_rate * duration)),
        )
        a, b, valid, raw_rate, stride = self.ring.snapshot(sample_count)
        if a.size == 0 or not valid.any():
            return

        step = max(1, a.size // RECORD_MAX_ANALYSIS_SAMPLES)
        mask = valid[::step]
        channel_values = {}
        for prefix, values, full_scale in (
            ("a", a, self.full_scale_a.value()),
            ("b", b, self.full_scale_b.value()),
        ):
            statistics = voltage_statistics(values[::step], mask, full_scale)
            if statistics is None:
                return
            channel_values.update({f"{prefix}_{key}": value for key, value in statistics.items()})

        frequency_values = b if self.trigger_channel.currentData() else a
        frequency = estimate_frequency(frequency_values, valid, effective_rate)
        status = self.latest_status
        metrics = self.latest_metrics
        row = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "elapsed_s": now - self._record_started_monotonic,
            "stream_id": self._expected_stream_id or 0,
            "configured_rate_hz": int(self.rate.currentData()),
            "dco_rate_hz": int(status.dco_frequency_hz) if status else 0,
            "preview_rate_hz": effective_rate,
            "preview_stride": int(stride),
            "analysis_window_s": a.size / effective_rate,
            "valid_samples": int(np.count_nonzero(valid)),
            "hardware_sample_pair_count": int(status.sample_pair_count) if status else 0,
            "blocks_completed": int(status.blocks_completed) if status else 0,
            "blocks_dropped": int(status.blocks_dropped) if status else 0,
            "frequency_channel": "B" if self.trigger_channel.currentData() else "A",
            "frequency_hz": float(frequency),
            **channel_values,
            "throughput_mbps": float(metrics.get("throughput_mbps", 0.0)),
            "packets": int(metrics.get("packets", 0)),
            "packet_loss": int(metrics.get("packet_loss", 0)),
            "block_loss": int(metrics.get("block_loss", 0)),
            "fifo_level": int(status.fifo_level) if status else 0,
            "fifo_overflow": int(status.fifo_overflow) if status else 0,
            "dma_errors": int(status.dma_errors) if status else 0,
            "otr_a_count": int(status.otr_a_count) if status else 0,
            "otr_b_count": int(status.otr_b_count) if status else 0,
            "daq_state": int(status.daq_state) if status else 0,
            "last_error": int(status.last_error) if status else 0,
        }
        self._record_rows.append(row)
        self._last_record_monotonic = now
        self.record_status.setText(
            f"正在记录：{row['elapsed_s']:.1f} s / {len(self._record_rows)} 条"
        )

    def _export_experiment_record(self):
        if not self._record_rows:
            QMessageBox.information(self, "没有记录", "当前没有可导出的实验记录。")
            return
        started = self._record_started_wall or datetime.now()
        default_name = f"ad9269_experiment_{started:%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出实验记录",
            default_name,
            "CSV (*.csv)",
        )
        if not path:
            self.record_button.setText("导出实验记录")
            return
        target = Path(path)
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(".csv")
        try:
            with target.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(self._record_rows[0]))
                writer.writeheader()
                writer.writerows(self._record_rows)
        except OSError as exc:
            QMessageBox.critical(self, "导出失败", f"无法写入 CSV：\n{exc}")
            self.record_button.setText("导出实验记录")
            return
        row_count = len(self._record_rows)
        self._record_rows = []
        self.record_button.setText("开始实验记录")
        self.record_button.setEnabled(self._expected_stream_id is not None)
        self.record_status.setText(f"已导出 {row_count} 条：{target.name}")

    def on_receiver_error(self, message: str):
        QMessageBox.critical(self, "UDP 接收失败", message)

    def closeEvent(self, event):
        self.scope_a.close()
        self.scope_b.close()
        if self.control is not None:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
        if self.poller is not None:
            self.poller.stop()
            self.poller.wait(1500)
        if self.receiver is not None:
            try:
                self._stop_receiver()
            except RuntimeError:
                pass
        event.accept()


def main():
    # Compatibility launcher: all new operation uses the unified GUI.
    try:
        from daq_pc.unified_daq_gui import main as unified_main
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from daq_pc.unified_daq_gui import main as unified_main
    raise SystemExit(unified_main(preset_model=1))


if __name__ == "__main__":
    main()
