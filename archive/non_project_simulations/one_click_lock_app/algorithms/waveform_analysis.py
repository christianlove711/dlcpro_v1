from __future__ import annotations

from statistics import median

from one_click_lock_app.models import LockAnalysis, ScanSnapshot, SignalFrame


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def _mad(values: list[float]) -> float:
    if not values:
        return 0.0
    center = median(values)
    return median([abs(v - center) for v in values])


def analyze_lock_candidate(frame: SignalFrame, scan: ScanSnapshot | None = None) -> LockAnalysis:
    n = frame.sample_count
    if n < 20:
        return LockAnalysis(False, False, False, None, None, None, 0.0, None, "数据点太少，无法判断")

    t = frame.time_s[:n]
    transmission = frame.transmission_v[:n]
    error = frame.error_v[:n]

    baseline = _percentile(transmission, 0.20)
    peak_index = max(range(n), key=lambda i: transmission[i])
    peak_value = transmission[peak_index]
    prominence = peak_value - baseline
    noise = max(_mad(transmission), 1e-12)
    trans_span = max(transmission) - min(transmission)
    has_peak = prominence > max(6.0 * noise, 0.10 * max(trans_span, 1e-12))

    window = max(12, n // 12)
    left = max(1, peak_index - window)
    right = min(n - 1, peak_index + window)
    local_error = error[left : right + 1]
    err_center = median(local_error) if local_error else 0.0
    centered = [v - err_center for v in error]
    err_span = max(centered[left : right + 1]) - min(centered[left : right + 1]) if right > left else 0.0
    err_noise = max(_mad(centered), 1e-12)
    has_error_signal = err_span > max(5.0 * err_noise, 1e-4)

    zero_index: int | None = None
    for i in range(left, right):
        a = centered[i]
        b = centered[i + 1]
        if a == 0 or (a < 0 < b) or (a > 0 > b):
            zero_index = i
            break

    zero_time = t[zero_index] if zero_index is not None else None
    peak_time = t[peak_index]
    error_slope = None
    if zero_index is not None:
        j0 = max(0, zero_index - 2)
        j1 = min(n - 1, zero_index + 2)
        dt = max(t[j1] - t[j0], 1e-12)
        error_slope = (centered[j1] - centered[j0]) / dt

    time_tolerance = max(frame.duration_s * 0.06, 0.02)
    zero_close = zero_time is not None and abs(zero_time - peak_time) <= time_tolerance
    ready = bool(has_peak and has_error_signal and zero_close)

    suggested_offset = None
    suggested_amplitude = None
    if scan and scan.offset_v is not None and scan.amplitude_vpp is not None and frame.duration_s > 0:
        center_error = (peak_time / frame.duration_s) - 0.5
        suggested_offset = scan.offset_v + center_error * scan.amplitude_vpp
        if has_peak:
            suggested_amplitude = max(scan.amplitude_vpp * 0.65, 0.05)

    if ready:
        message = "透射峰和误差信号过零点已对齐，可以准备使能 FALC"
    elif has_peak and not has_error_signal:
        message = "看到透射峰，但误差信号线性区/过零不清楚"
    elif has_peak:
        message = "看到透射峰，但误差信号过零点没有贴近峰中心"
    else:
        message = "当前帧没有可靠透射峰，建议继续调 Scan Offset"

    return LockAnalysis(
        has_peak=has_peak,
        has_error_zero=zero_index is not None and has_error_signal,
        ready_to_lock=ready,
        peak_time_s=peak_time,
        zero_time_s=zero_time,
        peak_value=peak_value,
        transmission_prominence=prominence,
        error_slope=error_slope,
        message=message,
        suggested_offset_v=suggested_offset,
        suggested_amplitude_vpp=suggested_amplitude,
    )


def downsample_xy(x: list[float], y: list[float], limit: int = 12000) -> tuple[list[float], list[float]]:
    n = min(len(x), len(y))
    if n <= limit:
        return x[:n], y[:n]
    step = max(1, n // limit)
    return x[:n:step], y[:n:step]
