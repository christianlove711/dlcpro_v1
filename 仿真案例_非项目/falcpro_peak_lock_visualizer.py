from __future__ import annotations

import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class SignalDataset:
    x: list[float]
    transmission: list[float]
    error1: list[float]
    error2: list[float]
    source: str


@dataclass(frozen=True)
class ScanPoint:
    t_s: float
    pzt: float
    transmission: float
    error1: float
    error2: float


@dataclass(frozen=True)
class PeakDecision:
    found: bool
    confirmed: bool
    message: str
    peak_pzt: float | None = None
    peak_snr: float | None = None
    zero_pzt: float | None = None
    slope: float | None = None
    suggested_center: float | None = None
    suggested_bias: float | None = None


def make_synthetic_dataset(points: int = 22_000) -> SignalDataset:
    rng = random.Random(852)
    x_min, x_max = -2.0, 2.0
    xs: list[float] = []
    trans: list[float] = []
    err1: list[float] = []
    err2: list[float] = []
    resonances = [
        (-1.54, 0.08, 0.055),
        (-1.08, 0.16, 0.038),
        (-0.72, 0.31, 0.030),
        (-0.18, 0.11, 0.070),
        (0.38, 0.92, 0.023),
        (0.63, 0.18, 0.041),
        (1.12, 0.42, 0.045),
        (1.55, 0.12, 0.032),
    ]
    for i in range(points):
        x = x_min + (x_max - x_min) * i / (points - 1)
        y = 0.045 + 0.018 * math.sin(2.0 * math.pi * x * 0.33)
        y += 0.010 * math.sin(2.0 * math.pi * x * 1.7 + 0.5)
        e1 = 0.020 * math.sin(2.0 * math.pi * x * 4.7)
        e2 = 0.017 * math.cos(2.0 * math.pi * x * 3.4 + 0.8)
        for center, amp, width in resonances:
            u = (x - center) / width
            lorentz = 1.0 / (1.0 + u * u)
            y += amp * lorentz
            dispersive = u / (1.0 + u * u)
            e1 += amp * 0.72 * dispersive
            e2 += -amp * 0.45 * dispersive
        y += 0.010 * max(0.0, math.sin(2.0 * math.pi * x * 8.0)) ** 2
        y += rng.gauss(0.0, 0.010)
        e1 += rng.gauss(0.0, 0.018)
        e2 += rng.gauss(0.0, 0.020)
        xs.append(x)
        trans.append(y)
        err1.append(e1)
        err2.append(e2)
    return SignalDataset(xs, trans, err1, err2, "内置模拟 CSV 数据")


def read_combined_csv(path: Path) -> SignalDataset:
    rows = read_numeric_rows(path)
    headers = list(rows[0].keys())
    x_key = choose_column(headers, ("pzt", "x", "freq", "frequency", "voltage", "time"), required=False) or headers[0]
    t_key = choose_column(headers, ("transmission", "trans", "透射", "pd", "peak"), required=True)
    e1_key = choose_column(headers, ("error1", "error_a", "error", "err1", "pdh1", "误差1"), required=True)
    e2_key = choose_column(headers, ("error2", "error_b", "err2", "pdh2", "误差2"), required=False)
    x = [row[x_key] for row in rows]
    transmission = [row[t_key] for row in rows]
    error1 = [row[e1_key] for row in rows]
    error2 = [row[e2_key] for row in rows] if e2_key else [0.0 for _ in rows]
    return normalize_dataset(SignalDataset(x, transmission, error1, error2, str(path)))


def read_single_signal_csv(path: Path) -> tuple[list[float], list[float]]:
    rows = read_numeric_rows(path)
    headers = list(rows[0].keys())
    x_key = choose_column(headers, ("pzt", "x", "freq", "frequency", "voltage", "time"), required=False)
    y_key = next(header for header in headers if header != x_key)
    x = [row[x_key] for row in rows] if x_key else [float(i) for i in range(len(rows))]
    y = [row[y_key] for row in rows]
    return x, y


def read_numeric_rows(path: Path) -> list[dict[str, float]]:
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError("CSV 没有表头")
        rows: list[dict[str, float]] = []
        for raw in reader:
            parsed: dict[str, float] = {}
            for key, value in raw.items():
                if key is None or value is None or value == "":
                    continue
                try:
                    parsed[key.strip()] = float(value)
                except ValueError:
                    continue
            if parsed:
                rows.append(parsed)
    if len(rows) < 16:
        raise ValueError("CSV 点数太少")
    return rows


def choose_column(headers: Sequence[str], names: Sequence[str], required: bool) -> str | None:
    lowered = {header.lower(): header for header in headers}
    for name in names:
        for key, header in lowered.items():
            if name.lower() in key:
                return header
    if required:
        raise ValueError(f"CSV 缺少列: {names[0]}")
    return None


def normalize_dataset(dataset: SignalDataset) -> SignalDataset:
    rows = sorted(zip(dataset.x, dataset.transmission, dataset.error1, dataset.error2), key=lambda item: item[0])
    x, t, e1, e2 = zip(*rows)
    return SignalDataset(list(x), list(t), list(e1), list(e2), dataset.source)


def merge_separate_signals(
    transmission: tuple[list[float], list[float]],
    error1: tuple[list[float], list[float]],
    error2: tuple[list[float], list[float]] | None,
    source: str,
) -> SignalDataset:
    x = transmission[0]
    t = transmission[1]
    e1 = resample(error1[0], error1[1], x)
    e2 = resample(error2[0], error2[1], x) if error2 else [0.0 for _ in x]
    return normalize_dataset(SignalDataset(list(x), list(t), e1, e2, source))


def resample(xs: Sequence[float], ys: Sequence[float], target_xs: Sequence[float]) -> list[float]:
    if len(xs) != len(ys):
        raise ValueError("CSV x/y 长度不一致")
    pairs = sorted(zip(xs, ys), key=lambda item: item[0])
    sx = [p[0] for p in pairs]
    sy = [p[1] for p in pairs]
    out: list[float] = []
    j = 0
    for x in target_xs:
        while j < len(sx) - 2 and sx[j + 1] < x:
            j += 1
        if x <= sx[0]:
            out.append(sy[0])
        elif x >= sx[-1]:
            out.append(sy[-1])
        else:
            dx = sx[j + 1] - sx[j]
            frac = 0.0 if abs(dx) < 1e-12 else (x - sx[j]) / dx
            out.append(sy[j] * (1.0 - frac) + sy[j + 1] * frac)
    return out


def build_triangular_scan(dataset: SignalDataset, center: float, bias: float, span: float, sample_count: int) -> list[ScanPoint]:
    effective_center = center + bias
    half = span / 2.0
    points: list[ScanPoint] = []
    count = max(32, sample_count)
    for i in range(count):
        phase = i / (count - 1)
        tri = -1.0 + 4.0 * phase if phase <= 0.5 else 3.0 - 4.0 * phase
        pzt = effective_center + tri * half
        points.append(
            ScanPoint(
                t_s=phase,
                pzt=pzt,
                transmission=interp(dataset.x, dataset.transmission, pzt),
                error1=interp(dataset.x, dataset.error1, pzt),
                error2=interp(dataset.x, dataset.error2, pzt),
            )
        )
    return points


def interp(xs: Sequence[float], ys: Sequence[float], x: float) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo = 0
    hi = len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    dx = xs[hi] - xs[lo]
    frac = 0.0 if abs(dx) < 1e-12 else (x - xs[lo]) / dx
    return ys[lo] * (1.0 - frac) + ys[hi] * frac


class VisualLockAlgorithm:
    def __init__(self, min_height: float, min_snr: float, min_slope: float, zero_window: float) -> None:
        self.min_height = min_height
        self.min_snr = min_snr
        self.min_slope = min_slope
        self.zero_window = zero_window

    def evaluate(self, scan: Sequence[ScanPoint], error_channel: int) -> PeakDecision:
        if len(scan) < 16:
            return PeakDecision(False, False, "扫描点太少")
        ordered = sorted(scan, key=lambda item: item.pzt)
        pzt = [p.pzt for p in ordered]
        trans = smooth([p.transmission for p in ordered], 9)
        error = smooth([p.error1 if error_channel == 1 else p.error2 for p in ordered], 7)
        baseline = percentile(trans, 15.0)
        noise = robust_noise(trans)
        peaks = []
        for i in range(1, len(trans) - 1):
            height = trans[i] - baseline
            snr = height / max(noise, 1e-9)
            if trans[i] > trans[i - 1] and trans[i] > trans[i + 1] and height >= self.min_height and snr >= self.min_snr:
                peaks.append((height * min(snr, 80.0), i, height, snr))
        if not peaks:
            return PeakDecision(False, False, f"未看到可信透射峰: height<{self.min_height:.3g} 或 SNR<{self.min_snr:.1f}")

        _, peak_i, _height, snr = max(peaks)
        peak_pzt = pzt[peak_i]
        zeros = []
        for i in range(1, len(error)):
            if abs(pzt[i] - peak_pzt) > self.zero_window:
                continue
            if error[i - 1] == 0.0 or error[i - 1] * error[i] > 0.0:
                continue
            frac = abs(error[i - 1]) / max(abs(error[i - 1]) + abs(error[i]), 1e-12)
            zero_pzt = pzt[i - 1] + (pzt[i] - pzt[i - 1]) * frac
            slope = local_slope(pzt, error, i)
            score = abs(slope) / max(abs(zero_pzt - peak_pzt), 1e-4)
            zeros.append((score, zero_pzt, slope))
        if not zeros:
            return PeakDecision(True, False, "看到透射峰，但峰附近没有 error 零交叉", peak_pzt=peak_pzt, peak_snr=snr)

        _, zero_pzt, slope = max(zeros)
        confirmed = abs(slope) >= self.min_slope
        message = "确认: 透射峰 + error 零交叉满足判据" if confirmed else "看到峰和零交叉，但 error 斜率不足"
        return PeakDecision(
            True,
            confirmed,
            message,
            peak_pzt=peak_pzt,
            peak_snr=snr,
            zero_pzt=zero_pzt,
            slope=slope,
            suggested_center=zero_pzt,
            suggested_bias=-zero_pzt,
        )


class SignalPlot(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(520)
        self.dataset: SignalDataset | None = None
        self.scan: list[ScanPoint] = []
        self.scope_history: list[ScanPoint] = []
        self.decision: PeakDecision | None = None
        self.center = 0.0
        self.bias = 0.0
        self.span = 0.6

    def set_state(
        self,
        dataset: SignalDataset | None,
        scan: list[ScanPoint],
        scope_history: list[ScanPoint],
        decision: PeakDecision | None,
        center: float,
        bias: float,
        span: float,
    ) -> None:
        self.dataset = dataset
        self.scan = scan
        self.scope_history = scope_history
        self.decision = decision
        self.center = center
        self.bias = bias
        self.span = span
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#10151f"))
        if self.dataset is None:
            painter.setPen(QColor("#d7deea"))
            painter.drawText(self.rect(), Qt.AlignCenter, "加载 CSV 或生成模拟数据后开始")
            return

        if len(self.scope_history) > 2:
            self._draw_scope_view(painter)
            return

        margin_l, margin_r, margin_t, margin_b = 54, 20, 24, 28
        width = self.width() - margin_l - margin_r
        height = self.height() - margin_t - margin_b
        panel_h = height / 3.0
        panels = [
            (margin_t, "透射峰信号", QColor("#79d17c")),
            (margin_t + panel_h, "误差信号 error1/error2", QColor("#7db7ff")),
            (margin_t + panel_h * 2, "1 Hz 三角波扫频 PZT", QColor("#ffd166")),
        ]
        for top, title, _color in panels:
            self._draw_panel_frame(painter, margin_l, top, width, panel_h - 10, title)

        min_x, max_x = self.dataset.x[0], self.dataset.x[-1]
        scan_left = self.center + self.bias - self.span / 2.0
        scan_right = self.center + self.bias + self.span / 2.0
        self._draw_scan_band(painter, margin_l, margin_t, width, height, min_x, max_x, scan_left, scan_right)

        self._draw_series(painter, self.dataset.x, self.dataset.transmission, margin_l, panels[0][0], width, panel_h - 10, min_x, max_x, QColor("#294534"))
        if self.scan:
            sx = [p.pzt for p in self.scan]
            self._draw_series(painter, sx, [p.transmission for p in self.scan], margin_l, panels[0][0], width, panel_h - 10, min_x, max_x, QColor("#75e083"), 2)

            self._draw_series(painter, self.dataset.x, self.dataset.error1, margin_l, panels[1][0], width, panel_h - 10, min_x, max_x, QColor("#293a54"))
            self._draw_series(painter, self.dataset.x, self.dataset.error2, margin_l, panels[1][0], width, panel_h - 10, min_x, max_x, QColor("#4d314d"))
            self._draw_series(painter, sx, [p.error1 for p in self.scan], margin_l, panels[1][0], width, panel_h - 10, min_x, max_x, QColor("#7db7ff"), 2)
            self._draw_series(painter, sx, [p.error2 for p in self.scan], margin_l, panels[1][0], width, panel_h - 10, min_x, max_x, QColor("#e17bd5"), 2)
            self._draw_triangle(painter, margin_l, panels[2][0], width, panel_h - 10)

        if self.decision is not None:
            if self.decision.peak_pzt is not None:
                self._draw_marker(painter, self.decision.peak_pzt, margin_l, margin_t, width, height, min_x, max_x, QColor("#75e083"), "peak")
            if self.decision.zero_pzt is not None:
                self._draw_marker(painter, self.decision.zero_pzt, margin_l, margin_t, width, height, min_x, max_x, QColor("#ffd166"), "zero")

    def _draw_panel_frame(self, painter: QPainter, x: float, y: float, w: float, h: float, title: str) -> None:
        painter.setPen(QPen(QColor("#283142"), 1))
        painter.drawRect(int(x), int(y), int(w), int(h))
        painter.setPen(QColor("#aeb8c8"))
        painter.drawText(int(x + 8), int(y + 18), title)
        painter.setPen(QPen(QColor("#1d2635"), 1))
        for i in range(1, 4):
            gy = y + h * i / 4.0
            painter.drawLine(QPointF(x, gy), QPointF(x + w, gy))

    def _draw_scope_view(self, painter: QPainter) -> None:
        margin_l, margin_r, margin_t, margin_b = 54, 20, 24, 28
        width = self.width() - margin_l - margin_r
        height = self.height() - margin_t - margin_b
        panel_h = height / 3.0
        panels = [
            (margin_t, "Transmission scope"),
            (margin_t + panel_h, "Error scope"),
            (margin_t + panel_h * 2, "1 Hz PZT triangle"),
        ]
        for top, title in panels:
            self._draw_panel_frame(painter, margin_l, top, width, panel_h - 10, title)

        t = [p.t_s for p in self.scope_history]
        min_t, max_t = t[0], t[-1]
        if abs(max_t - min_t) < 1e-12:
            max_t = min_t + 1.0
        self._draw_scope_series(
            painter, t, [p.transmission for p in self.scope_history],
            margin_l, panels[0][0], width, panel_h - 10, min_t, max_t, QColor("#75e083"), 2
        )
        self._draw_scope_series(
            painter, t, [p.error1 for p in self.scope_history],
            margin_l, panels[1][0], width, panel_h - 10, min_t, max_t, QColor("#7db7ff"), 2
        )
        self._draw_scope_series(
            painter, t, [p.error2 for p in self.scope_history],
            margin_l, panels[1][0], width, panel_h - 10, min_t, max_t, QColor("#e17bd5"), 2
        )
        self._draw_scope_series(
            painter, t, [p.pzt for p in self.scope_history],
            margin_l, panels[2][0], width, panel_h - 10, min_t, max_t, QColor("#ffd166"), 2
        )
        if self.decision is not None:
            painter.setPen(QColor("#52b788") if self.decision.confirmed else QColor("#d9a441"))
            painter.drawText(int(margin_l + 8), int(margin_t + 40), self.decision.message)

    def _draw_scan_band(
        self,
        painter: QPainter,
        x: float,
        y: float,
        w: float,
        h: float,
        min_x: float,
        max_x: float,
        left: float,
        right: float,
    ) -> None:
        px1 = x + (left - min_x) / max(max_x - min_x, 1e-12) * w
        px2 = x + (right - min_x) / max(max_x - min_x, 1e-12) * w
        painter.fillRect(int(px1), int(y), int(px2 - px1), int(h), QColor(70, 90, 125, 42))

    def _draw_series(
        self,
        painter: QPainter,
        xs: Sequence[float],
        ys: Sequence[float],
        x0: float,
        y0: float,
        w: float,
        h: float,
        min_x: float,
        max_x: float,
        color: QColor,
        line_width: int = 1,
    ) -> None:
        if not xs or not ys:
            return
        y_min, y_max = percentile(ys, 2.0), percentile(ys, 98.0)
        if abs(y_max - y_min) < 1e-12:
            y_min -= 1.0
            y_max += 1.0
        path = QPainterPath()
        started = False
        step = max(1, len(xs) // 2500)
        for x, y in zip(xs[::step], ys[::step]):
            px = x0 + (x - min_x) / max(max_x - min_x, 1e-12) * w
            py = y0 + h - (y - y_min) / (y_max - y_min) * h
            if not started:
                path.moveTo(px, py)
                started = True
            else:
                path.lineTo(px, py)
        painter.setPen(QPen(color, line_width))
        painter.drawPath(path)

    def _draw_scope_series(
        self,
        painter: QPainter,
        xs: Sequence[float],
        ys: Sequence[float],
        x0: float,
        y0: float,
        w: float,
        h: float,
        min_x: float,
        max_x: float,
        color: QColor,
        line_width: int = 1,
    ) -> None:
        if not xs or not ys:
            return
        y_min, y_max = percentile(ys, 2.0), percentile(ys, 98.0)
        pad = max((y_max - y_min) * 0.12, 1e-6)
        y_min -= pad
        y_max += pad
        path = QPainterPath()
        for idx, (x, y) in enumerate(zip(xs, ys)):
            px = x0 + (x - min_x) / max(max_x - min_x, 1e-12) * w
            py = y0 + h - (y - y_min) / max(y_max - y_min, 1e-12) * h
            if idx == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        painter.setPen(QPen(color, line_width))
        painter.drawPath(path)

    def _draw_triangle(self, painter: QPainter, x0: float, y0: float, w: float, h: float) -> None:
        path = QPainterPath()
        path.moveTo(x0, y0 + h)
        path.lineTo(x0 + w / 2.0, y0 + 22)
        path.lineTo(x0 + w, y0 + h)
        painter.setPen(QPen(QColor("#ffd166"), 2))
        painter.drawPath(path)

    def _draw_marker(
        self,
        painter: QPainter,
        pzt: float,
        x0: float,
        y0: float,
        w: float,
        h: float,
        min_x: float,
        max_x: float,
        color: QColor,
        text: str,
    ) -> None:
        px = x0 + (pzt - min_x) / max(max_x - min_x, 1e-12) * w
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(px, y0), QPointF(px, y0 + h))
        painter.drawText(QPointF(px + 5, y0 + 14), text)


class LogWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PZT / bias adjustment log")
        self.resize(760, 520)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap)
        self.setCentralWidget(self.log_view)

    def append_line(self, text: str) -> None:
        self.log_view.append(text)
        bar = self.log_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear(self) -> None:
        self.log_view.clear()


class VisualizerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FALC pro 透射峰/误差信号算法可视化验证")
        self.resize(1180, 780)
        self.dataset = make_synthetic_dataset()
        self.scan: list[ScanPoint] = []
        self.scope_history: list[ScanPoint] = []
        self.cycle_points: list[ScanPoint] = []
        self.decision: PeakDecision | None = None
        self.lock_confirmed = False
        self.search_phase = "coarse"
        self.fine_rounds = 0
        self.target_span = 0.0
        self.live_elapsed_s = 0.0
        self.last_live_phase = 0.0
        self.auto_timer = QTimer(self)
        self.auto_timer.setInterval(1000)
        self.live_timer = QTimer(self)
        self.live_timer.setInterval(25)
        self.live_timer.timeout.connect(self.live_tick)

        self.separate_transmission: tuple[list[float], list[float]] | None = None
        self.separate_error1: tuple[list[float], list[float]] | None = None
        self.separate_error2: tuple[list[float], list[float]] | None = None

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        self.plot = SignalPlot()
        root.addWidget(self.plot, 1)

        side_panel = QWidget()
        side_panel.setMinimumWidth(380)
        side_panel.setMaximumWidth(460)
        side = QVBoxLayout(side_panel)
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(10)
        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        side_scroll.setMinimumWidth(400)
        side_scroll.setMaximumWidth(480)
        side_scroll.setWidget(side_panel)
        root.addWidget(side_scroll, 0)
        self._build_file_group(side)
        self._build_scan_group(side)
        self._build_algorithm_group(side)
        self._build_status_group(side)
        side.addStretch(1)
        self.setCentralWidget(central)
        self._apply_style()
        self.reset_to_dataset(start_outside_peak=True)
        self.scan_group.setVisible(False)
        self.algorithm_group.setVisible(False)

    def _build_file_group(self, parent: QVBoxLayout) -> None:
        group = QGroupBox("CSV 输入")
        layout = QGridLayout(group)
        self.load_combined_btn = QPushButton("加载合并 CSV")
        self.load_t_btn = QPushButton("透射 CSV")
        self.load_e1_btn = QPushButton("error1 CSV")
        self.load_e2_btn = QPushButton("error2 CSV")
        self.merge_btn = QPushButton("合并三路")
        self.synthetic_btn = QPushButton("生成模拟数据")
        self.save_scan_btn = QPushButton("保存当前扫描 CSV")
        self.one_click_btn = QPushButton("One-click lock")
        self.stop_btn = QPushButton("Stop")
        self.advanced_btn = QPushButton("Advanced settings")
        self.advanced_btn.setCheckable(True)
        self.load_combined_btn.clicked.connect(self.load_combined_csv)
        self.load_t_btn.clicked.connect(lambda: self.load_single_csv("t"))
        self.load_e1_btn.clicked.connect(lambda: self.load_single_csv("e1"))
        self.load_e2_btn.clicked.connect(lambda: self.load_single_csv("e2"))
        self.merge_btn.clicked.connect(self.merge_separate_csvs)
        self.synthetic_btn.clicked.connect(self.load_synthetic)
        self.save_scan_btn.clicked.connect(self.save_current_scan)
        self.one_click_btn.clicked.connect(self.one_click_lock)
        self.stop_btn.clicked.connect(self.stop_lock)
        self.advanced_btn.toggled.connect(self.set_advanced_visible)
        layout.addWidget(self.load_combined_btn, 0, 0, 1, 2)
        layout.addWidget(self.one_click_btn, 1, 0, 1, 2)
        layout.addWidget(self.stop_btn, 2, 0, 1, 2)
        layout.addWidget(self.advanced_btn, 3, 0, 1, 2)
        layout.addWidget(self.load_t_btn, 4, 0)
        layout.addWidget(self.load_e1_btn, 4, 1)
        layout.addWidget(self.load_e2_btn, 5, 0)
        layout.addWidget(self.merge_btn, 5, 1)
        layout.addWidget(self.synthetic_btn, 6, 0, 1, 2)
        layout.addWidget(self.save_scan_btn, 7, 0, 1, 2)
        for widget in (self.load_t_btn, self.load_e1_btn, self.load_e2_btn, self.merge_btn, self.synthetic_btn, self.save_scan_btn):
            widget.setVisible(False)
        parent.addWidget(group)

    def _build_scan_group(self, parent: QVBoxLayout) -> None:
        group = QGroupBox("1 Hz 三角波扫频")
        self.scan_group = group
        form = QFormLayout(group)
        self.center_spin = QDoubleSpinBox()
        self.center_spin.setDecimals(5)
        self.center_spin.setRange(-1_000_000.0, 1_000_000.0)
        self.center_spin.valueChanged.connect(self.refresh_scan)
        self.bias_spin = QDoubleSpinBox()
        self.bias_spin.setDecimals(5)
        self.bias_spin.setRange(-1_000_000.0, 1_000_000.0)
        self.bias_spin.valueChanged.connect(self.refresh_scan)
        self.span_spin = QDoubleSpinBox()
        self.span_spin.setDecimals(5)
        self.span_spin.setRange(0.0001, 1_000_000.0)
        self.span_spin.valueChanged.connect(self.refresh_scan)
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(64, 20_000)
        self.samples_spin.setValue(1600)
        self.samples_spin.valueChanged.connect(self.refresh_scan)
        form.addRow("PZT center", self.center_spin)
        form.addRow("bias offset", self.bias_spin)
        form.addRow("scan span", self.span_spin)
        form.addRow("采样点/周期", self.samples_spin)
        parent.addWidget(group)

    def _build_algorithm_group(self, parent: QVBoxLayout) -> None:
        group = QGroupBox("算法判据")
        self.algorithm_group = group
        form = QFormLayout(group)
        self.error_channel_combo = QComboBox()
        self.error_channel_combo.addItem("error1", 1)
        self.error_channel_combo.addItem("error2", 2)
        self.error_channel_combo.currentIndexChanged.connect(self.refresh_scan)
        self.min_height_spin = QDoubleSpinBox()
        self.min_height_spin.setDecimals(4)
        self.min_height_spin.setRange(0.0, 1_000.0)
        self.min_height_spin.setValue(0.12)
        self.min_height_spin.valueChanged.connect(self.refresh_scan)
        self.min_snr_spin = QDoubleSpinBox()
        self.min_snr_spin.setDecimals(2)
        self.min_snr_spin.setRange(0.1, 1_000.0)
        self.min_snr_spin.setValue(5.0)
        self.min_snr_spin.valueChanged.connect(self.refresh_scan)
        self.min_slope_spin = QDoubleSpinBox()
        self.min_slope_spin.setDecimals(3)
        self.min_slope_spin.setRange(0.0, 1_000_000.0)
        self.min_slope_spin.setValue(1.2)
        self.min_slope_spin.valueChanged.connect(self.refresh_scan)
        self.zero_window_spin = QDoubleSpinBox()
        self.zero_window_spin.setDecimals(5)
        self.zero_window_spin.setRange(0.0001, 1_000_000.0)
        self.zero_window_spin.setValue(0.09)
        self.zero_window_spin.valueChanged.connect(self.refresh_scan)
        self.apply_when_confirmed_check = QCheckBox("确认后自动居中")
        self.apply_when_confirmed_check.setChecked(True)
        self.step_btn = QPushButton("单步寻峰")
        self.auto_btn = QPushButton("自动寻峰")
        self.reset_btn = QPushButton("从看不到峰开始")
        self.step_btn.clicked.connect(self.step_search)
        self.auto_btn.clicked.connect(self.toggle_auto)
        self.reset_btn.clicked.connect(lambda: self.reset_to_dataset(start_outside_peak=True))
        form.addRow("error 通道", self.error_channel_combo)
        form.addRow("最小峰高", self.min_height_spin)
        form.addRow("最小 SNR", self.min_snr_spin)
        form.addRow("最小 error 斜率", self.min_slope_spin)
        form.addRow("零交叉窗口", self.zero_window_spin)
        form.addRow(self.apply_when_confirmed_check)
        form.addRow(self.step_btn, self.auto_btn)
        form.addRow(self.reset_btn)
        parent.addWidget(group)

    def _build_status_group(self, parent: QVBoxLayout) -> None:
        group = QGroupBox("判断结果")
        layout = QVBoxLayout(group)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.metrics_label = QLabel()
        self.metrics_label.setWordWrap(True)
        self.phase_line = QFrame()
        self.phase_line.setFrameShape(QFrame.HLine)
        self.log_window = LogWindow(self)
        self.log_view = self.log_window.log_view
        self.show_log_btn = QPushButton("Open adjustment log")
        self.show_log_btn.clicked.connect(self.show_log_window)
        layout.addWidget(self.status_label)
        layout.addWidget(self.phase_line)
        layout.addWidget(self.metrics_label)
        layout.addWidget(self.show_log_btn)
        parent.addWidget(group)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #111822; color: #d9e2ef; font-size: 13px; }
            QGroupBox { border: 1px solid #2d3748; border-radius: 6px; margin-top: 10px; padding: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #edf2f7; }
            QPushButton { background: #253044; border: 1px solid #3a465a; border-radius: 5px; padding: 7px 10px; }
            QPushButton:hover { background: #30405c; }
            QPushButton:checked { background: #285c45; border-color: #52b788; }
            QDoubleSpinBox, QSpinBox, QComboBox { background: #0d131c; border: 1px solid #344055; border-radius: 4px; padding: 4px; min-height: 24px; }
            QPushButton { min-height: 26px; min-width: 128px; }
            QScrollArea { border: none; }
            QLabel { background: transparent; }
            """
        )

    def reset_to_dataset(self, start_outside_peak: bool) -> None:
        if self.dataset is None:
            return
        x_min, x_max = self.dataset.x[0], self.dataset.x[-1]
        span = max((x_max - x_min) * 0.18, 0.001)
        self.span_spin.blockSignals(True)
        self.center_spin.blockSignals(True)
        self.bias_spin.blockSignals(True)
        self.span_spin.setValue(span)
        self.bias_spin.setValue(0.0)
        self.center_spin.setValue(x_min + span * 0.45 if start_outside_peak else (x_min + x_max) / 2.0)
        self.scope_history.clear()
        self.cycle_points.clear()
        self.lock_confirmed = False
        self.search_phase = "coarse"
        self.fine_rounds = 0
        self.target_span = max(span * 0.16, (x_max - x_min) * 0.018)
        self.live_elapsed_s = 0.0
        self.last_live_phase = 0.0
        if hasattr(self, "log_view"):
            self.log_view.clear()
            self._append_log(f"reset: coarse scan, span={span:.5f}, center={self.center_spin.value():.5f}, bias=0")
        self.span_spin.blockSignals(False)
        self.center_spin.blockSignals(False)
        self.bias_spin.blockSignals(False)
        self.refresh_scan()

    def live_tick(self) -> None:
        if self.dataset is None:
            return
        dt = self.live_timer.interval() / 1000.0
        self.live_elapsed_s += dt
        phase = self.live_elapsed_s % 1.0
        tri = -1.0 + 4.0 * phase if phase <= 0.5 else 3.0 - 4.0 * phase
        pzt = self.center_spin.value() + self.bias_spin.value() + tri * self.span_spin.value() / 2.0
        point = ScanPoint(
            t_s=self.live_elapsed_s,
            pzt=pzt,
            transmission=interp(self.dataset.x, self.dataset.transmission, pzt),
            error1=interp(self.dataset.x, self.dataset.error1, pzt),
            error2=interp(self.dataset.x, self.dataset.error2, pzt),
        )
        self.scope_history.append(point)
        self.cycle_points.append(point)
        max_history = max(160, int(5.0 / max(dt, 1e-6)))
        if len(self.scope_history) > max_history:
            del self.scope_history[: len(self.scope_history) - max_history]

        cycle_done = phase < self.last_live_phase
        self.last_live_phase = phase
        if cycle_done and self.cycle_points:
            self.decision = self._algorithm().evaluate(self.cycle_points, self.error_channel_combo.currentData())
            self.cycle_points.clear()
            if self.auto_timer.isActive() and not self.lock_confirmed:
                self._advance_search()
            self._render_status()

        self.plot.set_state(
            self.dataset,
            self.scan,
            self.scope_history,
            self.decision,
            self.center_spin.value(),
            self.bias_spin.value(),
            self.span_spin.value(),
        )

    def refresh_scan(self) -> None:
        if self.dataset is None:
            return
        self.scan = build_triangular_scan(
            self.dataset,
            self.center_spin.value(),
            self.bias_spin.value(),
            self.span_spin.value(),
            self.samples_spin.value(),
        )
        self.decision = self._algorithm().evaluate(self.scan, self.error_channel_combo.currentData())
        self._render_status()
        self.plot.set_state(
            self.dataset,
            self.scan,
            self.scope_history,
            self.decision,
            self.center_spin.value(),
            self.bias_spin.value(),
            self.span_spin.value(),
        )

    def step_search(self) -> None:
        if self.dataset is None or self.decision is None:
            return
        self._advance_search(force=True)
        return
        if self.decision.confirmed:
            if self.apply_when_confirmed_check.isChecked() and self.decision.suggested_center is not None:
                self.center_spin.setValue(self.decision.suggested_center)
                self.bias_spin.setValue(0.0)
            self.auto_timer.stop()
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("自动寻峰")
            return
        direction = 1.0
        step = self.span_spin.value() * 0.45
        next_center = self.center_spin.value() + direction * step
        x_min, x_max = self.dataset.x[0], self.dataset.x[-1]
        if next_center > x_max + self.span_spin.value() / 2.0:
            next_center = x_min - self.span_spin.value() / 2.0
        self.center_spin.setValue(next_center)

    def _advance_search(self, force: bool = False) -> None:
        if self.dataset is None or self.decision is None:
            return
        if self.decision.confirmed:
            if self.search_phase == "coarse":
                self._enter_fine_search()
            else:
                self._fine_tune_or_lock()
            return
        if self.decision.found and self.search_phase == "coarse":
            self._append_log("candidate: transmission peak seen; switch to fine scan")
            self._enter_fine_search()
            return

        step = self.span_spin.value() * (0.28 if self.search_phase == "fine" else 0.34)
        next_center = self.center_spin.value() + step
        x_min, x_max = self.dataset.x[0], self.dataset.x[-1]
        if next_center > x_max + self.span_spin.value() / 2.0:
            next_center = x_min - self.span_spin.value() / 2.0
            self._append_log("coarse: wrap to left edge")
        self._set_center_bias_span(next_center, self.bias_spin.value(), self.span_spin.value())
        self._append_log(
            f"{self.search_phase}: move PZT center -> {next_center:.5f}, "
            f"bias={self.bias_spin.value():.5f}, span={self.span_spin.value():.5f}"
        )

    def _enter_fine_search(self) -> None:
        if self.decision is None:
            return
        target = self.decision.zero_pzt if self.decision.zero_pzt is not None else self.decision.peak_pzt
        if target is None:
            return
        self.search_phase = "fine"
        self.fine_rounds = 0
        current_span = self.span_spin.value()
        next_span = max(current_span * 0.55, self.target_span)
        next_center = self.center_spin.value() + (target - self.center_spin.value()) * 0.55
        next_bias = self.bias_spin.value() + (target - next_center - self.bias_spin.value()) * 0.20
        self._set_center_bias_span(next_center, next_bias, next_span)
        self._append_log(
            f"fine: candidate={target:.5f}; shrink span {current_span:.5f}->{next_span:.5f}; "
            f"PZT center={next_center:.5f}, bias={next_bias:.5f}"
        )

    def _fine_tune_or_lock(self) -> None:
        if self.decision is None or self.decision.suggested_center is None:
            return
        target = self.decision.suggested_center
        current_center = self.center_spin.value()
        current_bias = self.bias_spin.value()
        current_span = self.span_spin.value()
        next_span = max(current_span * 0.72, self.target_span)
        center_error = target - (current_center + current_bias)
        next_center = current_center + center_error * 0.45
        next_bias = current_bias + center_error * 0.20
        self.fine_rounds += 1
        self._set_center_bias_span(next_center, next_bias, next_span)
        self._append_log(
            f"fine[{self.fine_rounds}]: target={target:.5f}, d={center_error:+.5f}, "
            f"PZT center={next_center:.5f}, bias={next_bias:.5f}, span={next_span:.5f}"
        )
        settled = abs(center_error) < max(next_span * 0.045, 1e-5) and next_span <= self.target_span * 1.12
        if settled and self.fine_rounds >= 3:
            self.lock_confirmed = True
            self.search_phase = "locked"
            self.auto_timer.stop()
            self.auto_btn.setChecked(False)
            self._append_log(
                f"locked: keep rolling; final PZT center={next_center:.5f}, "
                f"bias={next_bias:.5f}, span={next_span:.5f}"
            )

    def _set_center_bias_span(self, center: float, bias: float, span: float) -> None:
        self.center_spin.blockSignals(True)
        self.bias_spin.blockSignals(True)
        self.span_spin.blockSignals(True)
        self.center_spin.setValue(center)
        self.bias_spin.setValue(bias)
        self.span_spin.setValue(span)
        self.center_spin.blockSignals(False)
        self.bias_spin.blockSignals(False)
        self.span_spin.blockSignals(False)
        self.refresh_scan()

    def _append_log(self, text: str) -> None:
        if not hasattr(self, "log_window"):
            return
        self.log_window.append_line(f"{self.live_elapsed_s:6.2f}s  {text}")

    def show_log_window(self) -> None:
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def one_click_lock(self) -> None:
        if self.dataset is None:
            QMessageBox.warning(self, "No data", "Please load a CSV first.")
            return
        self.stop_lock()
        self.reset_to_dataset(start_outside_peak=True)
        self.live_timer.start()
        self.auto_timer.start()
        self.auto_btn.setChecked(True)
        self._append_log("one-click lock: started")

    def stop_lock(self) -> None:
        self.live_timer.stop()
        self.auto_timer.stop()
        if hasattr(self, "auto_btn"):
            self.auto_btn.setChecked(False)
        self._append_log("stop")

    def set_advanced_visible(self, visible: bool) -> None:
        self.scan_group.setVisible(visible)
        self.algorithm_group.setVisible(visible)
        for widget in (self.load_t_btn, self.load_e1_btn, self.load_e2_btn, self.merge_btn, self.synthetic_btn, self.save_scan_btn):
            widget.setVisible(visible)

    def toggle_auto(self) -> None:
        if self.auto_timer.isActive():
            self.auto_timer.stop()
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("自动寻峰")
        else:
            self.auto_timer.start()
            self.auto_btn.setChecked(True)
            self.auto_btn.setText("停止自动")

    def _algorithm(self) -> VisualLockAlgorithm:
        return VisualLockAlgorithm(
            self.min_height_spin.value(),
            self.min_snr_spin.value(),
            self.min_slope_spin.value(),
            self.zero_window_spin.value(),
        )

    def _render_status(self) -> None:
        if self.decision is None:
            self.status_label.setText("等待数据")
            self.metrics_label.setText("")
            return
        prefix = "已确认" if self.decision.confirmed else ("已看到峰" if self.decision.found else "搜索中")
        self.status_label.setText(f"{prefix}: {self.decision.message}")
        parts = [
            f"phase: {self.search_phase}, fine_rounds={self.fine_rounds}",
            f"数据源: {self.dataset.source if self.dataset else '--'}",
            f"当前窗口: {self.center_spin.value() + self.bias_spin.value() - self.span_spin.value() / 2.0:.5f} .. "
            f"{self.center_spin.value() + self.bias_spin.value() + self.span_spin.value() / 2.0:.5f}",
        ]
        if self.decision.peak_pzt is not None:
            parts.append(f"透射峰 PZT={self.decision.peak_pzt:.6f}, SNR={self.decision.peak_snr:.2f}")
        if self.decision.zero_pzt is not None:
            parts.append(f"error 零交叉 PZT={self.decision.zero_pzt:.6f}, slope={self.decision.slope:.3f}")
        if self.decision.suggested_center is not None:
            parts.append(f"建议 PZT center={self.decision.suggested_center:.6f}, bias={self.decision.suggested_bias:.6f}")
        self.metrics_label.setText("\n".join(parts))

    def load_combined_csv(self) -> None:
        path = self._pick_csv("选择合并 CSV")
        if path is None:
            return
        try:
            self.dataset = read_combined_csv(path)
            self.reset_to_dataset(start_outside_peak=True)
        except Exception as exc:
            QMessageBox.warning(self, "CSV 读取失败", str(exc))

    def load_single_csv(self, kind: str) -> None:
        path = self._pick_csv("选择 CSV")
        if path is None:
            return
        try:
            data = read_single_signal_csv(path)
            if kind == "t":
                self.separate_transmission = data
            elif kind == "e1":
                self.separate_error1 = data
            else:
                self.separate_error2 = data
            QMessageBox.information(self, "已加载", f"{kind} loaded: {path.name}")
        except Exception as exc:
            QMessageBox.warning(self, "CSV 读取失败", str(exc))

    def merge_separate_csvs(self) -> None:
        if self.separate_transmission is None or self.separate_error1 is None:
            QMessageBox.warning(self, "缺少 CSV", "至少需要透射 CSV 和 error1 CSV")
            return
        try:
            self.dataset = merge_separate_signals(
                self.separate_transmission,
                self.separate_error1,
                self.separate_error2,
                "分路 CSV 合并",
            )
            self.reset_to_dataset(start_outside_peak=True)
        except Exception as exc:
            QMessageBox.warning(self, "合并失败", str(exc))

    def load_synthetic(self) -> None:
        self.dataset = make_synthetic_dataset()
        self.reset_to_dataset(start_outside_peak=True)

    def save_current_scan(self) -> None:
        if not self.scan:
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存当前扫描 CSV", "visual_scan.csv", "CSV Files (*.csv)")
        if not path:
            return
        with Path(path).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["t_s", "pzt", "transmission", "error1", "error2"])
            writer.writeheader()
            for point in self.scan:
                writer.writerow(
                    {
                        "t_s": point.t_s,
                        "pzt": point.pzt,
                        "transmission": point.transmission,
                        "error1": point.error1,
                        "error2": point.error2,
                    }
                )

    def _pick_csv(self, title: str) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(self, title, "", "CSV Files (*.csv);;All Files (*)")
        return Path(path) if path else None


def smooth(values: Sequence[float], window: int) -> list[float]:
    radius = max(0, window // 2)
    out: list[float] = []
    for i in range(len(values)):
        left = max(0, i - radius)
        right = min(len(values), i + radius + 1)
        out.append(sum(values[left:right]) / (right - left))
    return out


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def robust_noise(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 1e-9
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    med = percentile(diffs, 50.0)
    mad = percentile([abs(v - med) for v in diffs], 50.0)
    return max(1e-9, 1.4826 * mad / math.sqrt(2.0))


def local_slope(xs: Sequence[float], ys: Sequence[float], index: int, radius: int = 4) -> float:
    left = max(0, index - radius)
    right = min(len(xs) - 1, index + radius)
    dx = xs[right] - xs[left]
    return 0.0 if abs(dx) < 1e-12 else (ys[right] - ys[left]) / dx


def main() -> int:
    app = QApplication(sys.argv)
    window = VisualizerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
