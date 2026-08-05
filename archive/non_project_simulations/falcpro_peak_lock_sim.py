from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence


class LockState(str, Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    FIND_TRANSMISSION_PEAK = "FIND_TRANSMISSION_PEAK"
    FIND_ERROR_ZERO = "FIND_ERROR_ZERO"
    VALIDATE_CANDIDATE = "VALIDATE_CANDIDATE"
    ENGAGE_FALCPRO = "ENGAGE_FALCPRO"
    VERIFY_LOCK = "VERIFY_LOCK"
    MONITOR_LOCK = "MONITOR_LOCK"
    FAILED = "FAILED"
    LOCKED = "LOCKED"


@dataclass(frozen=True)
class ScanConfig:
    scan_frequency_hz: float = 1.0
    sample_rate_hz: int = 2_000
    scan_span: float = 1.0
    pzt_center: float = 0.0
    bias_offset: float = 0.0
    peak_threshold_snr: float = 6.0
    min_peak_height: float = 0.18
    zero_search_half_width: float = 0.09
    min_error_slope: float = 1.5
    max_error_at_lock: float = 0.025
    verify_seconds: float = 0.35
    monitor_seconds: float = 1.5
    error_rms_locked_limit: float = 0.035
    correction_limit: float = 0.85


@dataclass(frozen=True)
class ScanSample:
    t_s: float
    pzt: float
    transmission: float
    error: float


@dataclass(frozen=True)
class PeakCandidate:
    index: int
    pzt: float
    height: float
    baseline: float
    noise_rms: float
    snr: float
    width: float


@dataclass(frozen=True)
class LockCandidate:
    peak: PeakCandidate
    zero_index: int
    pzt: float
    error_at_zero: float
    slope: float
    score: float


@dataclass(frozen=True)
class LockResult:
    locked: bool
    state: LockState
    lock_pzt: float | None
    pzt_center_command: float | None
    bias_offset_command: float | None
    error_rms: float | None
    correction_rms: float | None
    reason: str
    candidate: LockCandidate | None


class SyntheticSignalSource:
    """No hardware: simulate one 1 Hz scan containing transmission and PDH error."""

    def __init__(self, seed: int, cavity_broken: bool) -> None:
        self._rng = random.Random(seed)
        self._cavity_broken = cavity_broken
        self._resonance = self._rng.uniform(-0.25, 0.25)
        self._linewidth = self._rng.uniform(0.018, 0.035)
        self._peak_amp = 0.06 if cavity_broken else self._rng.uniform(0.65, 0.95)
        self._error_amp = 0.08 if cavity_broken else self._rng.uniform(0.55, 0.8)

    def acquire_scan(self, config: ScanConfig) -> list[ScanSample]:
        total = max(8, int(config.sample_rate_hz / config.scan_frequency_hz))
        samples: list[ScanSample] = []
        start = config.pzt_center - config.scan_span / 2.0 + config.bias_offset
        for i in range(total):
            phase = i / (total - 1)
            t_s = phase / config.scan_frequency_hz
            pzt = start + config.scan_span * phase
            x = pzt - self._resonance
            lorentz = 1.0 / (1.0 + (x / self._linewidth) ** 2)
            transmission = 0.04 + self._peak_amp * lorentz
            transmission += self._rng.gauss(0.0, 0.008 if not self._cavity_broken else 0.025)

            # PDH-like dispersive curve: zero crossing sits at the transmission peak.
            error = self._error_amp * (x / self._linewidth) / (1.0 + (x / self._linewidth) ** 2)
            error += 0.015 * math.sin(2.0 * math.pi * 13.0 * phase)
            error += self._rng.gauss(0.0, 0.01 if not self._cavity_broken else 0.04)
            samples.append(ScanSample(t_s=t_s, pzt=pzt, transmission=transmission, error=error))
        return samples

    def acquire_locked_monitor(self, config: ScanConfig, lock_pzt: float, seconds: float) -> list[tuple[float, float]]:
        total = max(10, int(config.sample_rate_hz * seconds))
        monitor: list[tuple[float, float]] = []
        drift = 0.0
        for i in range(total):
            t_s = i / config.sample_rate_hz
            drift += self._rng.gauss(0.0, 0.00003)
            error = 0.018 * math.sin(2.0 * math.pi * 7.0 * t_s)
            error += 0.25 * drift + self._rng.gauss(0.0, 0.009)
            correction = max(-1.0, min(1.0, -7.0 * error + self._rng.gauss(0.0, 0.018)))
            if self._cavity_broken:
                error += self._rng.gauss(0.0, 0.08)
                correction = max(-1.0, min(1.0, correction + self._rng.choice((-0.9, 0.9)) * self._rng.random()))
            monitor.append((error, correction))
        return monitor


class PeakLockProcessor:
    def __init__(self, config: ScanConfig) -> None:
        self.config = config

    def process(self, samples: Sequence[ScanSample], source: SyntheticSignalSource) -> LockResult:
        peak = self.find_best_transmission_peak(samples)
        if peak is None:
            return LockResult(False, LockState.FAILED, None, None, None, None, None, "未找到可信透射峰", None)

        candidate = self.find_error_zero(samples, peak)
        if candidate is None:
            return LockResult(False, LockState.FAILED, None, None, None, None, None, "透射峰附近没有合格 error 零交叉", None)

        if not self.validate_candidate(candidate):
            return LockResult(False, LockState.FAILED, None, None, None, None, None, "候选锁点质量不足", candidate)

        pzt_center_command, bias_offset_command = self.compute_centering_commands(candidate.pzt)
        monitor = source.acquire_locked_monitor(self.config, candidate.pzt, self.config.verify_seconds)
        error_rms, correction_rms, correction_max = self._monitor_stats(monitor)
        locked = error_rms <= self.config.error_rms_locked_limit and correction_max < self.config.correction_limit
        if not locked:
            return LockResult(
                False,
                LockState.FAILED,
                candidate.pzt,
                pzt_center_command,
                bias_offset_command,
                error_rms,
                correction_rms,
                "FALC pro 接通后 error RMS 或 correction 已接近限幅",
                candidate,
            )

        monitor = source.acquire_locked_monitor(self.config, candidate.pzt, self.config.monitor_seconds)
        error_rms, correction_rms, correction_max = self._monitor_stats(monitor)
        locked = error_rms <= self.config.error_rms_locked_limit and correction_max < self.config.correction_limit
        return LockResult(
            locked,
            LockState.LOCKED if locked else LockState.FAILED,
            candidate.pzt,
            pzt_center_command,
            bias_offset_command,
            error_rms,
            correction_rms,
            "锁定保持正常" if locked else "锁后监测发现失锁趋势",
            candidate,
        )

    def find_best_transmission_peak(self, samples: Sequence[ScanSample]) -> PeakCandidate | None:
        y = smooth([s.transmission for s in samples], window=9)
        baseline = percentile(y, 15.0)
        noise = robust_noise(y)
        peaks: list[PeakCandidate] = []
        for i in range(1, len(y) - 1):
            if y[i] <= y[i - 1] or y[i] <= y[i + 1]:
                continue
            height = y[i] - baseline
            snr = height / max(noise, 1e-9)
            if height < self.config.min_peak_height or snr < self.config.peak_threshold_snr:
                continue
            width = estimate_width(samples, y, i, baseline + height * 0.5)
            peaks.append(PeakCandidate(i, samples[i].pzt, height, baseline, noise, snr, width))
        if not peaks:
            return None
        return max(peaks, key=lambda p: p.height * min(p.snr, 50.0) / max(p.width, 1e-4))

    def find_error_zero(self, samples: Sequence[ScanSample], peak: PeakCandidate) -> LockCandidate | None:
        pzt = [s.pzt for s in samples]
        error = smooth([s.error for s in samples], window=7)
        left = peak.pzt - self.config.zero_search_half_width
        right = peak.pzt + self.config.zero_search_half_width
        candidates: list[LockCandidate] = []
        for i in range(1, len(samples)):
            if pzt[i] < left or pzt[i] > right:
                continue
            if error[i - 1] == 0.0 or error[i - 1] * error[i] > 0.0:
                continue
            frac = abs(error[i - 1]) / max(abs(error[i - 1]) + abs(error[i]), 1e-12)
            zero_pzt = pzt[i - 1] + (pzt[i] - pzt[i - 1]) * frac
            slope = local_slope(pzt, error, i)
            distance_penalty = abs(zero_pzt - peak.pzt) / max(self.config.zero_search_half_width, 1e-12)
            score = abs(slope) * peak.snr * (1.0 - min(distance_penalty, 0.95))
            candidates.append(LockCandidate(peak, i, zero_pzt, 0.0, slope, score))
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.score)

    def validate_candidate(self, candidate: LockCandidate) -> bool:
        if abs(candidate.slope) < self.config.min_error_slope:
            return False
        if abs(candidate.pzt - candidate.peak.pzt) > self.config.zero_search_half_width:
            return False
        return True

    def compute_centering_commands(self, lock_pzt: float) -> tuple[float, float]:
        # Here "PZT center" and "bias offset" are simulated slow commands.
        return lock_pzt, -lock_pzt

    @staticmethod
    def _monitor_stats(monitor: Sequence[tuple[float, float]]) -> tuple[float, float, float]:
        errors = [v[0] for v in monitor]
        corrections = [v[1] for v in monitor]
        return rms(errors), rms(corrections), max(abs(v) for v in corrections)


def smooth(values: Sequence[float], window: int) -> list[float]:
    if window <= 1:
        return list(values)
    radius = window // 2
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
        return 0.0
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    median = statistics.median(diffs)
    mad = statistics.median(abs(v - median) for v in diffs)
    return max(1e-9, 1.4826 * mad / math.sqrt(2.0))


def estimate_width(samples: Sequence[ScanSample], y: Sequence[float], peak_index: int, half_level: float) -> float:
    left = peak_index
    right = peak_index
    while left > 0 and y[left] > half_level:
        left -= 1
    while right < len(y) - 1 and y[right] > half_level:
        right += 1
    return max(samples[right].pzt - samples[left].pzt, 1e-9)


def local_slope(x: Sequence[float], y: Sequence[float], index: int, radius: int = 4) -> float:
    left = max(0, index - radius)
    right = min(len(x) - 1, index + radius)
    dx = x[right] - x[left]
    if abs(dx) < 1e-12:
        return 0.0
    return (y[right] - y[left]) / dx


def rms(values: Iterable[float]) -> float:
    data = list(values)
    if not data:
        return 0.0
    return math.sqrt(sum(v * v for v in data) / len(data))


def write_scan_csv(path: Path, samples: Sequence[ScanSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["t_s", "pzt", "transmission", "error"])
        writer.writeheader()
        for sample in samples:
            writer.writerow(asdict(sample))


def read_scan_csv(path: Path) -> list[ScanSample]:
    samples: list[ScanSample] = []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        required = {"t_s", "pzt", "transmission", "error"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"CSV 缺少列: {', '.join(sorted(missing))}")
        for row in reader:
            samples.append(
                ScanSample(
                    t_s=float(row["t_s"]),
                    pzt=float(row["pzt"]),
                    transmission=float(row["transmission"]),
                    error=float(row["error"]),
                )
            )
    if len(samples) < 8:
        raise ValueError("CSV 点数太少，无法寻峰")
    return samples


def write_result_json(path: Path, result: LockResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["state"] = result.state.value
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(result: LockResult) -> None:
    print(f"状态: {result.state.value}")
    print(f"结果: {'锁定成功' if result.locked else '锁定失败'}")
    print(f"原因: {result.reason}")
    if result.candidate is None:
        return
    print(f"透射峰 PZT: {result.candidate.peak.pzt:.6f}")
    print(f"透射峰 SNR: {result.candidate.peak.snr:.2f}")
    print(f"error 零交叉 PZT: {result.candidate.pzt:.6f}")
    print(f"error 斜率: {result.candidate.slope:.3f}")
    print(f"PZT 中心建议: {result.pzt_center_command:.6f}")
    print(f"偏置建议: {result.bias_offset_command:.6f}")
    if result.error_rms is not None:
        print(f"锁后 error RMS: {result.error_rms:.5f}")
    if result.correction_rms is not None:
        print(f"锁后 correction RMS: {result.correction_rms:.5f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-DLCpro/no-DAQ FALC pro peak-lock algorithm simulator.")
    parser.add_argument("--seed", type=int, default=852, help="Random seed for repeatable simulated waveforms.")
    parser.add_argument("--broken-cavity", action="store_true", help="Simulate weak/noisy signals when the cavity is bad.")
    parser.add_argument("--sample-rate", type=int, default=2_000, help="Samples per second during the 1 Hz scan.")
    parser.add_argument("--span", type=float, default=1.0, help="Simulated PZT scan span.")
    parser.add_argument("--input-csv", type=Path, help="Use existing t_s,pzt,transmission,error CSV instead of simulation.")
    parser.add_argument("--csv", type=Path, default=Path("simulation_outputs/scan.csv"), help="Output scan CSV path.")
    parser.add_argument("--json", type=Path, default=Path("simulation_outputs/result.json"), help="Output result JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = ScanConfig(sample_rate_hz=args.sample_rate, scan_span=args.span)
    source = SyntheticSignalSource(seed=args.seed, cavity_broken=args.broken_cavity)
    processor = PeakLockProcessor(config)

    print("流程: 1 Hz 扫频 -> 找透射峰 -> 找 error 零交叉 -> 人工 FALC 参数已就绪 -> 接通并判断")
    samples = read_scan_csv(args.input_csv) if args.input_csv else source.acquire_scan(config)
    result = processor.process(samples, source)
    write_scan_csv(args.csv, samples)
    write_result_json(args.json, result)
    print_summary(result)
    print(f"CSV: {args.csv}")
    print(f"JSON: {args.json}")
    return 0 if result.locked else 2


if __name__ == "__main__":
    raise SystemExit(main())
