from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QCloseEvent, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class Sample:
    t: float
    pzt_cmd: float
    laser_freq: float
    transmission: float
    error: float


@dataclass(frozen=True)
class Decision:
    found: bool
    confirmed: bool
    message: str
    peak_pzt: float | None = None
    zero_pzt: float | None = None
    snr: float | None = None
    slope: float | None = None
    sideband_score: float | None = None


class VirtualCavity:
    """Dynamic stand-in for DAQ + laser + cavity + PDH error signals."""

    def __init__(self, seed: int = 852) -> None:
        self.rng = random.Random(seed)
        self.target_resonance = 852.102
        self.scan_frequency_hz = 1.0
        self.nominal_pzt_v = 20.0
        self.resonance_pzt_v = 20.860
        self.tuning_coeff = 4.7
        self.linewidth = 0.150
        self.sideband_spacing = 0.78
        self.sideband_amp = 0.23
        self.ram_offset = 0.0
        self.drift = 0.0
        self.thermal_state = 0.0
        self.actual_pzt = self.nominal_pzt_v
        self.pzt_creep = 0.0
        self.span_memory = 1.6
        self.last_pzt = self.nominal_pzt_v
        self.falc_engaged = False
        self.error_offset = 0.0
        self.error_phase = 1.0
        self.false_peaks = [
            (18.70, 0.08, 0.060, 0.10),
            (19.42, 0.14, 0.045, -0.20),
            (22.15, 0.16, 0.055, 0.25),
            (23.05, 0.10, 0.070, -0.10),
        ]

    def reset(self) -> None:
        self.drift = self.rng.uniform(-0.010, 0.010)
        self.thermal_state = self.nominal_pzt_v
        self.actual_pzt = self.nominal_pzt_v + self.rng.uniform(-0.080, 0.080)
        self.pzt_creep = self.rng.uniform(-0.035, 0.035)
        self.span_memory = self.rng.uniform(1.2, 1.8)
        self.last_pzt = self.nominal_pzt_v
        self.falc_engaged = False
        self.error_offset = self.rng.uniform(-0.025, 0.025)
        self.error_phase = self.rng.choice((-1.0, 1.0))
        self.ram_offset = self.rng.uniform(-0.030, 0.030)

    def sample(self, t: float, pzt_center: float, bias: float, span: float) -> Sample:
        phase = (t * self.scan_frequency_hz) % 1.0
        triangle = -1.0 + 4.0 * phase if phase <= 0.5 else 3.0 - 4.0 * phase
        pzt_cmd = pzt_center + bias + triangle * span / 2.0
        direction = 1.0 if pzt_cmd >= self.last_pzt else -1.0
        cmd_delta = pzt_cmd - self.actual_pzt
        response = 0.34 if abs(cmd_delta) > 0.030 else 0.12
        deadband = 0.010 if abs(cmd_delta) > 0.010 else abs(cmd_delta)
        self.actual_pzt += response * (cmd_delta - math.copysign(deadband, cmd_delta))
        self.pzt_creep = 0.999 * self.pzt_creep + 0.001 * (pzt_cmd - self.nominal_pzt_v)
        self.span_memory = 0.992 * self.span_memory + 0.008 * span

        self.drift += self.rng.gauss(0.0, 0.00005)
        self.thermal_state = 0.9985 * self.thermal_state + 0.0015 * self.actual_pzt
        hysteresis = direction * (0.012 * span + 0.018 * abs(span - self.span_memory))
        nonlinearity = 0.018 * math.sin((self.actual_pzt - self.nominal_pzt_v) * 2.3)
        amplitude_pull = 0.115 * (self.span_memory - span)
        thermal_pull = 0.004 * (self.thermal_state - self.actual_pzt) + 0.010 * self.pzt_creep
        laser_freq = (
            self.target_resonance
            + self.tuning_coeff * (self.actual_pzt + amplitude_pull - self.resonance_pzt_v)
            + self.drift
            + hysteresis
            + nonlinearity
            + thermal_pull
        )
        self.last_pzt = pzt_cmd

        transmission = 0.045 + 0.010 * math.sin(2.0 * math.pi * t * 0.37)
        error = self.error_offset + self.ram_offset + 0.010 * math.sin(2.0 * math.pi * t * 11.0)

        detuning = laser_freq - self.target_resonance
        carrier_u = detuning / self.linewidth
        upper_u = (detuning - self.sideband_spacing) / self.linewidth
        lower_u = (detuning + self.sideband_spacing) / self.linewidth
        carrier_lor = lorentz(carrier_u)
        upper_lor = lorentz(upper_u)
        lower_lor = lorentz(lower_u)
        carrier_disp = dispersion(carrier_u)
        upper_disp = dispersion(upper_u)
        lower_disp = dispersion(lower_u)

        transmission += 0.88 * carrier_lor
        transmission += self.sideband_amp * upper_lor + self.sideband_amp * lower_lor
        error += self.error_phase * (
            0.78 * carrier_disp
            - 0.20 * upper_disp
            - 0.20 * lower_disp
            + 0.035 * (upper_lor - lower_lor)
        )

        for center, amp, width, quality in self.false_peaks:
            u = (pzt_cmd - center) / width
            lor = 1.0 / (1.0 + u * u)
            disp = u / (1.0 + u * u)
            transmission += amp * lor
            error += amp * 0.32 * quality * disp + amp * 0.025 * (1.0 - abs(quality)) * lor

        if self.rng.random() < 0.004:
            transmission += self.rng.uniform(0.020, 0.080)
            error += self.rng.uniform(-0.080, 0.080)

        if self.falc_engaged:
            error *= 0.25
            transmission += 0.020

        transmission += self.rng.gauss(0.0, 0.010)
        error += self.rng.gauss(0.0, 0.018)
        return Sample(t, pzt_cmd, laser_freq, transmission, error)


class LockAlgorithm:
    def __init__(self) -> None:
        self.min_height = 0.12
        self.min_snr = 5.0
        self.min_slope = 0.12
        self.zero_window = 0.140

    def evaluate(self, samples: Sequence[Sample]) -> Decision:
        if len(samples) < 30:
            return Decision(False, False, "not enough samples")
        ordered = sorted(samples, key=lambda s: s.pzt_cmd)
        x = [s.pzt_cmd for s in ordered]
        transmission = smooth([s.transmission for s in ordered], 9)
        error = smooth([s.error for s in ordered], 7)
        baseline = percentile(transmission, 15.0)
        noise = robust_noise(transmission)

        peak_candidates: list[tuple[float, int, float, float]] = []
        for i in range(1, len(transmission) - 1):
            height = transmission[i] - baseline
            snr = height / max(noise, 1e-9)
            if transmission[i] > transmission[i - 1] and transmission[i] > transmission[i + 1]:
                if height >= self.min_height and snr >= self.min_snr:
                    peak_candidates.append((height * min(snr, 80.0), i, height, snr))

        if not peak_candidates:
            return Decision(False, False, "no credible transmission peak")

        _, peak_i, _height, snr = self.choose_carrier_peak(peak_candidates, x, transmission)
        peak_pzt = x[peak_i]
        sideband_score = self.sideband_symmetry_score(peak_i, peak_candidates, x, transmission)
        zero_candidates: list[tuple[float, float, float]] = []
        for i in range(1, len(error)):
            if abs(x[i] - peak_pzt) > self.zero_window:
                continue
            if error[i - 1] == 0.0 or error[i - 1] * error[i] > 0.0:
                continue
            frac = abs(error[i - 1]) / max(abs(error[i - 1]) + abs(error[i]), 1e-12)
            zero_pzt = x[i - 1] + (x[i] - x[i - 1]) * frac
            slope = local_slope(x, error, i)
            score = abs(slope) / max(abs(zero_pzt - peak_pzt), 1e-4)
            zero_candidates.append((score, zero_pzt, slope))

        if not zero_candidates:
            return Decision(
                True,
                False,
                "carrier/sideband peak seen, no good PDH zero",
                peak_pzt=peak_pzt,
                snr=snr,
                sideband_score=sideband_score,
            )

        _, zero_pzt, slope = max(zero_candidates)
        confirmed = abs(slope) >= self.min_slope
        return Decision(
            True,
            confirmed,
            "peak + error zero confirmed" if confirmed else "error slope too small",
            peak_pzt=peak_pzt,
            zero_pzt=zero_pzt,
            snr=snr,
            slope=slope,
            sideband_score=sideband_score,
        )

    def choose_carrier_peak(
        self,
        peaks: Sequence[tuple[float, int, float, float]],
        x: Sequence[float],
        transmission: Sequence[float],
    ) -> tuple[float, int, float, float]:
        best = peaks[0]
        best_score = -1e9
        for peak in peaks:
            _score, idx, height, snr = peak
            symmetry = self.sideband_symmetry_score(idx, peaks, x, transmission)
            carrier_score = height * min(snr, 50.0) * (1.0 + 0.45 * symmetry)
            if carrier_score > best_score:
                best_score = carrier_score
                best = peak
        return best

    def sideband_symmetry_score(
        self,
        idx: int,
        peaks: Sequence[tuple[float, int, float, float]],
        x: Sequence[float],
        transmission: Sequence[float],
    ) -> float:
        center = x[idx]
        candidates = [x[pidx] for _score, pidx, _height, _snr in peaks if pidx != idx]
        if not candidates:
            return 0.0
        left = [abs((center - p) - 0.16) for p in candidates if p < center]
        right = [abs((p - center) - 0.16) for p in candidates if p > center]
        if not left or not right:
            return 0.0
        mismatch = min(left) + min(right)
        return max(0.0, 1.0 - mismatch / 0.18)


class ScopeWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(760, 520)
        self.history: list[Sample] = []
        self.decision: Decision | None = None
        self.pzt_center = 0.0
        self.bias = 20.0
        self.span = 1.60

    def update_state(
        self,
        history: list[Sample],
        decision: Decision | None,
        pzt_center: float,
        bias: float,
        span: float,
    ) -> None:
        self.history = history
        self.decision = decision
        self.pzt_center = pzt_center
        self.bias = bias
        self.span = span
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#10151f"))
        if not self.history:
            painter.setPen(QColor("#d7deea"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Press One-click lock")
            return

        margin_l, margin_r, margin_t, margin_b = 54, 22, 24, 30
        width = self.width() - margin_l - margin_r
        height = self.height() - margin_t - margin_b
        panel_h = height / 3.0
        panels = [
            (margin_t, "Transmission"),
            (margin_t + panel_h, "Single PDH error"),
            (margin_t + panel_h * 2, "PZT voltage command [V]"),
        ]
        for top, title in panels:
            self._frame(painter, margin_l, top, width, panel_h - 10, title)

        t = [s.t for s in self.history]
        min_t, max_t = t[0], t[-1]
        self._series(painter, t, [s.transmission for s in self.history], margin_l, panels[0][0], width, panel_h - 10, min_t, max_t, QColor("#75e083"), 2)
        self._series(painter, t, [s.error for s in self.history], margin_l, panels[1][0], width, panel_h - 10, min_t, max_t, QColor("#7db7ff"), 2)
        self._series(painter, t, [s.pzt_cmd for s in self.history], margin_l, panels[2][0], width, panel_h - 10, min_t, max_t, QColor("#ffd166"), 2)

        if self.decision is not None:
            painter.setPen(QColor("#52b788") if self.decision.confirmed else QColor("#d9a441"))
            painter.drawText(int(margin_l + 8), int(margin_t + 38), self.decision.message)

    def _frame(self, painter: QPainter, x: float, y: float, w: float, h: float, title: str) -> None:
        painter.setPen(QPen(QColor("#283142"), 1))
        painter.drawRect(int(x), int(y), int(w), int(h))
        painter.setPen(QColor("#aeb8c8"))
        painter.drawText(int(x + 8), int(y + 18), title)
        painter.setPen(QPen(QColor("#1d2635"), 1))
        for i in range(1, 4):
            gy = y + h * i / 4.0
            painter.drawLine(QPointF(x, gy), QPointF(x + w, gy))

    def _series(
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
        line_width: int,
    ) -> None:
        y_min, y_max = percentile(ys, 2.0), percentile(ys, 98.0)
        pad = max((y_max - y_min) * 0.12, 1e-6)
        y_min -= pad
        y_max += pad
        path = QPainterPath()
        for i, (x, y) in enumerate(zip(xs, ys)):
            px = x0 + (x - min_x) / max(max_x - min_x, 1e-12) * w
            py = y0 + h - (y - y_min) / max(y_max - y_min, 1e-12) * h
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        painter.setPen(QPen(color, line_width))
        painter.drawPath(path)


class LogWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lock algorithm log")
        self.resize(980, 560)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.NoWrap)
        self.log.setFont(QFont("Consolas", 10))
        self.setCentralWidget(self.log)

    def append_line(self, text: str) -> None:
        self.log.append(text)
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())

    def clear(self) -> None:
        self.log.clear()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()


class SimulatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Virtual cavity one-click lock simulator")
        self.resize(1180, 760)
        self.cavity = VirtualCavity()
        self.algorithm = LockAlgorithm()
        self.history: list[Sample] = []
        self.cycle: list[Sample] = []
        self.decision: Decision | None = None
        self.t = 0.0
        self.last_phase = 0.0
        self.pzt_center = 0.0
        self.bias = 20.0
        self.bias_direction = 1.0
        self.span = 1.60
        self.target_span = 0.16
        self.phase = "idle"
        self.fine_rounds = 0
        self.bias_dwell_cycles = 0
        self.peak_confirm_cycles = 0
        self.zero_confirm_cycles = 0
        self.reacquire_rounds = 0
        self.operator_cycle = 0
        self.no_peak_cycles = 0
        self.stable_cycles = 0
        self.bias_only_moves = 0
        self.last_manual_control = "none"
        self.last_peak_pzt: float | None = None
        self.last_zero_pzt: float | None = None
        self.log_window = LogWindow()

        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.tick)

        root = QHBoxLayout()
        self.scope = ScopeWidget()
        root.addWidget(self.scope, 1)

        side = QVBoxLayout()
        side.setSpacing(10)
        self.start_btn = QPushButton("One-click lock")
        self.stop_btn = QPushButton("Stop")
        self.reset_btn = QPushButton("Reset virtual cavity")
        self.log_btn = QPushButton("Open full log")
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumWidth(280)
        self.log.setMaximumHeight(170)
        self.log.setLineWrapMode(QTextEdit.NoWrap)
        self.log.setFont(QFont("Consolas", 9))
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.reset_btn.clicked.connect(self.reset)
        self.log_btn.clicked.connect(self.show_log_window)
        side.addWidget(self.start_btn)
        side.addWidget(self.stop_btn)
        side.addWidget(self.reset_btn)
        side.addWidget(self.log_btn)
        side.addWidget(self.status_label)
        side.addWidget(QLabel("Recent log"))
        side.addWidget(self.log)
        root.addLayout(side)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)
        self.setStyleSheet(
            """
            QWidget { background: #111822; color: #d9e2ef; font-size: 13px; }
            QPushButton { background: #253044; border: 1px solid #3a465a; border-radius: 5px; padding: 9px 12px; min-height: 30px; }
            QPushButton:hover { background: #30405c; }
            QTextEdit { background: #0d131c; border: 1px solid #344055; border-radius: 4px; }
            QLabel { background: transparent; }
            """
        )
        self.update_status()

    def start(self) -> None:
        self.cavity.reset()
        self.reset_runtime(clear_log=True)
        self.phase = "operator_search"
        self.timer.start()
        self.write_log(
            f"start: one-click lock; fixed cavity resonance={self.cavity.target_resonance:.3f}; "
            f"scan frequency={self.cavity.scan_frequency_hz:.3f} Hz; "
            f"initial Scan Offset/Bias={self.bias:.3f} V, PZT fine={self.pzt_center:.3f} V, "
            f"Scan Amplitude={self.span:.3f} Vpp, "
            f"bias direction={'up' if self.bias_direction > 0 else 'down'}"
        )
        self.update_status()

    def stop(self) -> None:
        self.timer.stop()
        self.write_log("stop")
        self.update_status()

    def reset(self) -> None:
        self.timer.stop()
        self.cavity.reset()
        self.reset_runtime(clear_log=True)
        self.write_log("reset virtual cavity")
        self.update_status()

    def reset_runtime(self, clear_log: bool) -> None:
        self.history.clear()
        self.cycle.clear()
        self.decision = None
        self.t = 0.0
        self.last_phase = 0.0
        offset = self.cavity.rng.choice((-1.0, 1.0)) * self.cavity.rng.uniform(1.15, 2.35)
        self.pzt_center = 0.0
        self.bias = clamp(self.cavity.resonance_pzt_v + offset, 17.0, 24.0)
        self.bias_direction = 1.0 if self.bias < self.cavity.resonance_pzt_v else -1.0
        self.span = self.cavity.rng.uniform(1.35, 1.80)
        self.target_span = 0.16
        self.phase = "idle"
        self.fine_rounds = 0
        self.bias_dwell_cycles = 0
        self.peak_confirm_cycles = 0
        self.zero_confirm_cycles = 0
        self.reacquire_rounds = 0
        self.operator_cycle = 0
        self.no_peak_cycles = 0
        self.stable_cycles = 0
        self.bias_only_moves = 0
        self.last_manual_control = "none"
        self.last_peak_pzt = None
        self.last_zero_pzt = None
        self.cavity.falc_engaged = False
        if clear_log:
            self.log.clear()
            self.log_window.clear()
        self.scope.update_state(self.history, self.decision, self.pzt_center, self.bias, self.span)

    def tick(self) -> None:
        dt = self.timer.interval() / 1000.0
        self.t += dt
        sample = self.cavity.sample(self.t, self.pzt_center, self.bias, self.span)
        self.history.append(sample)
        self.cycle.append(sample)
        if len(self.history) > int(5.0 / dt):
            del self.history[: len(self.history) - int(5.0 / dt)]

        phase = (self.t * self.cavity.scan_frequency_hz) % 1.0
        cycle_done = phase < self.last_phase
        self.last_phase = phase
        if cycle_done:
            self.decision = self.algorithm.evaluate(self.cycle)
            self.cycle.clear()
            self.advance()
            self.update_status()

        self.scope.update_state(self.history, self.decision, self.pzt_center, self.bias, self.span)

    def advance(self) -> None:
        if self.decision is None or self.phase == "locked":
            return
        self.operator_cycle += 1
        center = self.command_center()

        if self.decision.peak_pzt is not None:
            self.last_peak_pzt = self.decision.peak_pzt
        if self.decision.zero_pzt is not None:
            self.last_zero_pzt = self.decision.zero_pzt

        if not self.decision.found:
            self.stable_cycles = 0
            self.peak_confirm_cycles = 0
            self.zero_confirm_cycles = 0
            self.no_peak_cycles += 1
            if self.phase in ("operator_focus", "operator_recover") or self.span < 1.05:
                self.operator_recover_peak()
            else:
                self.operator_search_step()
            return

        self.no_peak_cycles = 0
        peak_offset = self.window_offset(self.decision.peak_pzt)
        if self.decision.confirmed and self.decision.zero_pzt is not None:
            self.zero_confirm_cycles += 1
            zero_error = self.decision.zero_pzt - center
            centered = abs(peak_offset) < 0.34 and abs(zero_error) < max(0.035, self.span * 0.08)
            self.stable_cycles = self.stable_cycles + 1 if centered else 0
            self.phase = "operator_focus"

            ready_to_lock = (
                self.span <= 1.05
                and self.stable_cycles >= 2
                and self.zero_confirm_cycles >= 4
                and abs(peak_offset) < 0.28
                and abs(zero_error) < max(0.030, self.span * 0.07)
            )
            if ready_to_lock:
                self.phase = "locked"
                self.cavity.falc_engaged = True
                self.write_log(
                    "FALC engaged: carrier peak and single PDH zero are close enough; stop manual tuning"
                )
                return

            if abs(peak_offset) > 0.48:
                self.operator_adjust_to_target(self.decision.peak_pzt, "peak near scan edge", preferred="bias")
                return
            if abs(zero_error) > max(0.018, self.span * 0.06):
                self.operator_adjust_to_target(self.decision.zero_pzt, "PDH zero off center", preferred="pzt")
                return
            if self.span > self.target_span * 1.18 and self.stable_cycles >= 2:
                old_span = self.span
                self.span = max(self.span * 0.84, self.target_span)
                self.write_log(
                    f"operator_shrink: zero stable for {self.stable_cycles} scans; "
                    f"Scan Amplitude {old_span:.3f}->{self.span:.3f} Vpp, keep watching for peak loss"
                )
                return
            if self.span <= self.target_span * 1.18 and self.stable_cycles >= 8 and self.zero_confirm_cycles >= 8:
                self.phase = "locked"
                self.cavity.falc_engaged = True
                self.write_log("FALC engaged: virtual lock is active; scope keeps rolling")
                return

            self.write_log(
                f"operator_hold: peak/error look usable; center={center:.4f} V, "
                f"peak_offset={peak_offset:+.2f}, sideband={self.decision.sideband_score or 0.0:.2f}, "
                f"stable={self.stable_cycles}"
            )
            return

        self.stable_cycles = 0
        self.peak_confirm_cycles += 1
        self.phase = "operator_focus"
        if abs(peak_offset) > 0.42:
            self.operator_adjust_to_target(self.decision.peak_pzt, "transmission peak only; center peak before shrinking", preferred="bias")
            return
        if self.peak_confirm_cycles < 2:
            self.write_log(
                f"operator_hold: transmission peak seen but error not ready; hold one scan, "
                f"peak_offset={peak_offset:+.2f}"
            )
            return
        self.operator_probe_error()

    def command_center(self) -> float:
        return self.bias + self.pzt_center

    def window_offset(self, target: float | None) -> float:
        if target is None:
            return 0.0
        return clamp((target - self.command_center()) / max(self.span / 2.0, 1e-9), -2.0, 2.0)

    def operator_search_step(self) -> None:
        self.bias_dwell_cycles += 1
        if self.bias_dwell_cycles < 2:
            self.write_log(
                f"operator_search: hold and watch scope, Scan Offset={self.bias:.3f} V, "
                f"PZT fine={self.pzt_center:+.3f} V, Scan Amplitude={self.span:.3f} Vpp"
            )
            return
        self.bias_dwell_cycles = 0
        should_probe_pzt = self.bias_only_moves >= 4 and self.no_peak_cycles >= 8 and self.cavity.rng.random() < 0.45
        if should_probe_pzt:
            old_pzt = self.pzt_center
            step = self.bias_direction * self.cavity.rng.uniform(0.018, 0.040)
            self.pzt_center = clamp(self.pzt_center + step, -1.20, 1.20)
            self.bias_only_moves = 0
            self.write_log(
                f"operator_probe: several bias moves gave no peak; nudge PZT fine "
                f"{old_pzt:+.3f}->{self.pzt_center:+.3f} V, keep Scan Offset={self.bias:.3f} V"
            )
            return

        old_bias = self.bias
        step = self.bias_direction * self.cavity.rng.uniform(0.055, 0.110)
        self.bias = clamp(self.bias + step, 17.0, 24.0)
        self.bias_only_moves += 1
        if self.bias <= 17.0:
            self.bias_direction = 1.0
        if self.bias >= 24.0:
            self.bias_direction = -1.0
        self.write_log(
            f"operator_search: no peak; move Scan Offset {old_bias:.3f}->{self.bias:.3f} V, "
            f"PZT fine={self.pzt_center:+.3f} V"
        )

    def operator_adjust_to_target(self, target: float | None, reason: str, preferred: str) -> None:
        if target is None:
            return
        error = target - self.command_center()
        if abs(error) < 0.006:
            self.write_log(f"operator_adjust: {reason}; correction too small, hold")
            return
        control = preferred
        if preferred == "pzt" and abs(error) > 0.30:
            control = "bias"
        if preferred == "bias" and abs(error) < 0.045 and self.last_manual_control == "bias":
            control = "pzt"

        if control == "bias":
            old_bias = self.bias
            self.bias = clamp(self.bias + clamp(0.18 * error, -0.075, 0.075), 17.0, 24.0)
            self.last_manual_control = "bias"
            self.write_log(
                f"operator_adjust: {reason}; target={target:.4f} V, center_error={error:+.4f} V, "
                f"move Scan Offset {old_bias:.3f}->{self.bias:.3f} V, hold PZT fine={self.pzt_center:+.3f} V"
            )
            return

        old_pzt = self.pzt_center
        self.pzt_center = clamp(self.pzt_center + clamp(0.22 * error, -0.060, 0.060), -1.20, 1.20)
        self.last_manual_control = "pzt"
        self.write_log(
            f"operator_adjust: {reason}; target={target:.4f} V, center_error={error:+.4f} V, "
            f"move PZT fine {old_pzt:+.3f}->{self.pzt_center:+.3f} V, hold Scan Offset={self.bias:.3f} V"
        )

    def operator_probe_error(self) -> None:
        old_span = self.span
        if self.span > 0.55:
            self.span = max(self.span * 0.92, self.target_span)
            self.write_log(
                f"operator_probe: peak centered but error not clean; slightly shrink "
                f"Scan Amplitude {old_span:.3f}->{self.span:.3f} Vpp"
            )
        else:
            old_pzt = self.pzt_center
            direction = -1.0 if self.operator_cycle % 2 else 1.0
            self.pzt_center = clamp(self.pzt_center + direction * 0.018, -1.20, 1.20)
            self.write_log(
                f"operator_probe: peak without error zero; test PZT fine "
                f"{old_pzt:+.3f}->{self.pzt_center:+.3f} V"
            )

    def operator_recover_peak(self) -> None:
        self.phase = "operator_recover"
        self.reacquire_rounds += 1
        old_span = self.span
        if self.no_peak_cycles >= 2:
            self.span = min(1.55, max(self.span * 1.22, self.span + 0.080))
        target = self.last_peak_pzt if self.last_peak_pzt is not None else self.command_center() + self.bias_direction * 0.12
        preferred = "bias" if self.reacquire_rounds % 2 else "pzt"
        self.operator_adjust_to_target(target, "peak disappeared; recover with one knob", preferred=preferred)
        self.write_log(
            f"operator_recover: no peak for {self.no_peak_cycles} scans; "
            f"Scan Amplitude {old_span:.3f}->{self.span:.3f} Vpp"
        )
        return

    def legacy_advance(self) -> None:
        if self.decision is None or self.phase == "locked":
            return
        if self.decision.confirmed:
            self.last_peak_pzt = self.decision.peak_pzt
            self.last_zero_pzt = self.decision.zero_pzt
            if self.phase in ("bias_search", "bias_reacquire"):
                self.peak_confirm_cycles += 1
                if self.peak_confirm_cycles >= 2:
                    self.enter_pzt_fine()
                else:
                    self.write_log("candidate peak + error zero seen; hold bias for one more scan")
            else:
                self.zero_confirm_cycles += 1
                self.fine_tune_or_lock()
            return
        if self.decision.found and self.phase in ("bias_search", "bias_reacquire"):
            self.last_peak_pzt = self.decision.peak_pzt
            self.peak_confirm_cycles += 1
            if self.peak_confirm_cycles >= 3:
                self.write_log("transmission peak repeated while tuning bias; switch to PZT fine scan")
                self.enter_pzt_fine()
            else:
                self.write_log("candidate transmission peak seen; hold bias and confirm")
            return

        if self.decision.found and self.phase == "pzt_fine":
            self.last_peak_pzt = self.decision.peak_pzt
            self.write_log("fine scan sees transmission only; hold amplitude and nudge PZT, wait for error zero")
            self.nudge_pzt_from_peak()
            return

        if self.phase == "bias_search":
            self.peak_confirm_cycles = 0
            self.move_bias_search()
            return

        if self.phase == "bias_reacquire":
            self.peak_confirm_cycles = 0
            self.reacquire_with_bias()
            self.write_log(
                f"bias_reacquire: Scan Offset={self.bias:.3f} V, keep PZT fine={self.pzt_center:+.3f} V, "
                f"Scan Amplitude={self.span:.3f} Vpp"
            )
            return

        self.write_log("fine lost peak after reducing scan; keep PZT estimate and reacquire with Scan Offset")
        self.phase = "bias_reacquire"
        self.peak_confirm_cycles = 0
        self.zero_confirm_cycles = 0
        self.reacquire_rounds += 1
        self.reacquire_with_bias()
        self.span = min(1.45, max(self.span * 1.25, 0.75))
        self.write_log(
            f"bias reacquire: Scan Offset={self.bias:.3f} V, keep PZT fine={self.pzt_center:+.3f} V, "
            f"Scan Amplitude={self.span:.3f} Vpp"
        )

    def move_bias_search(self) -> None:
        self.bias_dwell_cycles += 1
        if self.bias_dwell_cycles < 2:
            self.write_log(
                f"bias_search: hold Scan Offset={self.bias:.3f} V for settling/confirmation, "
                f"PZT fine={self.pzt_center:.3f} V, Scan Amplitude={self.span:.3f} Vpp"
            )
            return
        self.bias_dwell_cycles = 0
        step = self.cavity.rng.uniform(0.055, 0.115)
        old_bias = self.bias
        self.bias = clamp(self.bias + self.bias_direction * step, 17.0, 24.0)
        if self.bias <= 17.0:
            self.bias_direction = 1.0
        if self.bias >= 24.0:
            self.bias_direction = -1.0
        self.write_log(
            f"bias_search: Scan Offset {old_bias:.3f}->{self.bias:.3f} V, "
            f"PZT fine={self.pzt_center:.3f} V, Scan Amplitude={self.span:.3f} Vpp"
        )

    def reacquire_with_bias(self) -> None:
        center_cmd = self.bias + self.pzt_center
        if self.last_peak_pzt is not None:
            error = self.last_peak_pzt - center_cmd
            step = clamp(0.22 * error, -0.075, 0.075)
            if abs(step) < 0.020:
                step = self.bias_direction * self.cavity.rng.uniform(0.025, 0.055)
        else:
            step = self.bias_direction * self.cavity.rng.uniform(0.025, 0.060)
        self.bias = clamp(self.bias + step, 17.0, 24.0)
        if self.bias <= 17.0:
            self.bias_direction = 1.0
        if self.bias >= 24.0:
            self.bias_direction = -1.0

    def nudge_pzt_from_peak(self) -> None:
        if self.decision is None or self.decision.peak_pzt is None:
            return
        center_cmd = self.bias + self.pzt_center
        center_error = self.decision.peak_pzt - center_cmd
        self.pzt_center = clamp(self.pzt_center + 0.12 * center_error, -1.20, 1.20)
        self.span = max(self.span * 0.96, self.target_span)
        self.write_log(
            f"pzt_nudge: peak={self.decision.peak_pzt:.4f} V, center_error={center_error:+.4f} V, "
            f"PZT fine={self.pzt_center:+.4f} V, Scan Amplitude={self.span:.3f} Vpp"
        )

    def enter_pzt_fine(self) -> None:
        if self.decision is None:
            return
        target = self.decision.zero_pzt if self.decision.zero_pzt is not None else self.decision.peak_pzt
        if target is None:
            return
        old_span = self.span
        self.phase = "pzt_fine"
        self.fine_rounds = 0
        self.zero_confirm_cycles = 0
        shrink_factor = 0.48 if self.reacquire_rounds == 0 else 0.72
        self.span = max(self.span * shrink_factor, self.target_span)
        estimate_error = 0.0 if self.reacquire_rounds > 0 else self.cavity.rng.uniform(-0.18, 0.18)
        desired_pzt_center = target - self.bias + estimate_error
        response = 0.12 if self.reacquire_rounds == 0 else 0.28
        self.pzt_center = clamp(self.pzt_center + response * (desired_pzt_center - self.pzt_center), -1.20, 1.20)
        self.write_log(
            f"pzt_fine: peak near PZT={target:.4f} V; Scan Amplitude {old_span:.3f}->{self.span:.3f} Vpp; "
            f"set PZT fine toward {desired_pzt_center:+.4f} V, now {self.pzt_center:+.4f} V; "
            f"Scan Offset stays {self.bias:.3f} V"
        )

    def fine_tune_or_lock(self) -> None:
        if self.decision is None or self.decision.zero_pzt is None:
            return
        target = self.decision.zero_pzt
        desired_pzt_center = target - self.bias
        center_error = desired_pzt_center - self.pzt_center
        shrink = 0.88 if self.zero_confirm_cycles < 3 else 0.80
        self.span = max(self.span * shrink, self.target_span)
        self.pzt_center = clamp(self.pzt_center + 0.25 * center_error, -1.20, 1.20)
        self.fine_rounds += 1
        self.write_log(
            f"pzt_fine[{self.fine_rounds}]: error zero={target:.4f} V, pzt_error={center_error:+.4f} V, "
            f"PZT fine={self.pzt_center:+.4f} V, Scan Offset={self.bias:.3f} V, "
            f"Scan Amplitude={self.span:.3f} Vpp"
        )
        settled = (
            abs(center_error) < max(0.010, self.span * 0.05)
            and self.span <= self.target_span * 1.15
            and self.fine_rounds >= 8
            and self.zero_confirm_cycles >= 6
        )
        if settled:
            self.phase = "locked"
            self.cavity.falc_engaged = True
            self.write_log("FALC engaged: virtual lock is active; scope keeps rolling")

    def update_status(self) -> None:
        msg = [
            f"phase: {self.phase}",
            f"fixed cavity resonance: {self.cavity.target_resonance:.3f}",
            "DAQ inputs: transmission + single PDH error only",
            f"scan frequency: {self.cavity.scan_frequency_hz:.3f} Hz",
            f"Scan Offset/Bias: {self.bias:.3f} V",
            f"PZT fine center: {self.pzt_center:+.3f} V",
            f"Scan Amplitude: {self.span:.3f} Vpp",
            f"PZT command: offset + fine + triangle * amplitude/2",
        ]
        if self.decision is not None:
            msg.append(self.decision.message)
            if self.decision.peak_pzt is not None:
                msg.append(f"peak near PZT command: {self.decision.peak_pzt:.4f} V")
            if self.decision.zero_pzt is not None:
                msg.append(f"error zero near PZT command: {self.decision.zero_pzt:.4f} V")
            if self.decision.sideband_score is not None:
                msg.append(f"sideband symmetry score: {self.decision.sideband_score:.2f}")
        self.status_label.setText("\n".join(msg))

    def write_log(self, text: str) -> None:
        line = f"{self.t:6.2f}s  {text}"
        self.log.append(line)
        self.log_window.append_line(line)
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())

    def show_log_window(self) -> None:
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()


def smooth(values: Sequence[float], window: int) -> list[float]:
    radius = max(0, window // 2)
    out: list[float] = []
    for i in range(len(values)):
        left = max(0, i - radius)
        right = min(len(values), i + radius + 1)
        out.append(sum(values[left:right]) / (right - left))
    return out


def percentile(values: Sequence[float], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
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


def lorentz(u: float) -> float:
    return 1.0 / (1.0 + u * u)


def dispersion(u: float) -> float:
    return u / (1.0 + u * u)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def local_slope(xs: Sequence[float], ys: Sequence[float], index: int, radius: int = 4) -> float:
    left = max(0, index - radius)
    right = min(len(xs) - 1, index + radius)
    dx = xs[right] - xs[left]
    return 0.0 if abs(dx) < 1e-12 else (ys[right] - ys[left]) / dx


def main() -> int:
    app = QApplication(sys.argv)
    window = SimulatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
