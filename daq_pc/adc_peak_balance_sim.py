"""Deterministic virtual-cavity simulator for the ADC peak-balance algorithm."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .adc_peak_balance_algorithm import (
    PeakBalanceEngine, PeakBalanceSettings, analyze_carrier,
)


@dataclass(slots=True)
class VirtualCavity:
    frequency_hz: float = 1.0
    carrier_position: float = 0.0
    linewidth: float = 0.025
    carrier_height_codes: float = 900.0
    sideband_spacing: float = 0.32
    sideband_fraction: float = 0.18
    baseline_codes: float = 100.0
    noise_codes: float = 3.0
    polarity: int = 1
    seed: int = 7

    def history(self, offset: float, amplitude: float, cycles: float = 4.0,
                gap_slice: slice | None = None):
        bin_seconds = 0.001
        duration = cycles / self.frequency_hz
        bins = max(16, int(round(duration / bin_seconds)))
        # Four sub-samples per history bin emulate the hardware max hold.
        t = (np.arange(bins * 4, dtype=np.float64) + 0.5) * bin_seconds / 4.0
        phase = np.mod(t * self.frequency_hz, 1.0)
        triangle = 1.0 - 4.0 * np.abs(phase - 0.5)
        scan = offset + 0.5 * amplitude * triangle
        detuning = scan - self.carrier_position

        def lorentz(center, height):
            u = (detuning - center) / self.linewidth
            return height / (1.0 + u * u)

        signal = lorentz(0.0, self.carrier_height_codes)
        signal += lorentz(
            self.sideband_spacing,
            self.carrier_height_codes * self.sideband_fraction,
        )
        signal += lorentz(
            -self.sideband_spacing,
            self.carrier_height_codes * self.sideband_fraction,
        )
        rng = np.random.default_rng(self.seed)
        raw = self.baseline_codes + self.polarity * signal
        raw += rng.normal(0.0, self.noise_codes, raw.size)
        raw = np.clip(np.rint(raw), -32768, 32767).astype(np.int16)
        shaped = raw.reshape(bins, 4)
        minimum = shaped.min(axis=1)
        maximum = shaped.max(axis=1)
        valid = np.ones(bins, dtype=bool)
        if gap_slice is not None:
            valid[gap_slice] = False
        zeros = np.zeros(bins, dtype=np.int16)
        if self.polarity > 0:
            min_a, max_a = minimum, maximum
        else:
            min_a, max_a = minimum, maximum
        return SimpleNamespace(
            bin_indices=np.arange(bins, dtype=np.int64),
            minimum_a=min_a, maximum_a=max_a,
            minimum_b=zeros, maximum_b=zeros,
            valid=valid, sample_rate_hz=20_000_000,
            bin_seconds=bin_seconds,
        )


def run_virtual_lock(iterations: int = 60, *, drift_per_step: float = 0.0,
                     frequency_change_at: int | None = None):
    settings = PeakBalanceSettings(
        max_offset_deviation=0.5, offset_step=0.03,
        min_prominence_codes=40, carrier_dominance_ratio=2.0,
        # The synthetic cavity shifts by more than the production default
        # ±5 mV when changing directly from 1.2 to 0.2 Vpp.  Give this
        # long-running drift/frequency simulation enough final-grid coverage;
        # the grid step remains exactly 1 mV.
        final_local_max_distance=0.05,
    )
    cavity = VirtualCavity()
    engine = PeakBalanceEngine(settings)
    offset, amplitude = 0.16, 1.2
    engine.start(offset, amplitude)
    trace = []
    for index in range(iterations):
        if frequency_change_at is not None and index == frequency_change_at:
            cavity.frequency_hz = 0.5 if cavity.frequency_hz == 1.0 else 1.0
        cavity.carrier_position += drift_per_step
        history = cavity.history(offset, amplitude)
        observation = analyze_carrier(
            history, settings, cavity.frequency_hz, engine.fingerprint
        )
        action = engine.update(observation)
        if action.kind == "offset" and action.value is not None:
            offset = float(action.value)
        elif action.kind == "amplitude" and action.value is not None:
            amplitude = float(action.value)
        engine.sync(offset, amplitude)
        if action.kind == "amplitude" and action.value is not None:
            # Match the real controller's post-readback transition handling.
            engine.reset_after_amplitude_change()
        trace.append({
            "step": index, "state": engine.state,
            "carrier_position": cavity.carrier_position,
            "offset": offset, "amplitude": amplitude,
            "valid": observation.valid,
            "balance_error": observation.balance_error,
            "dominance_ratio": observation.dominance_ratio,
            "action": action.kind, "reason": action.reason,
            "frequency_hz": cavity.frequency_hz,
        })
        if action.kind == "stop":
            break
    return trace


def save_trace(trace, directory: str | Path):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "adc_peak_balance_sim.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=trace[0].keys())
        writer.writeheader()
        writer.writerows(trace)
    png_path = directory / "adc_peak_balance_sim.png"
    try:
        import matplotlib.pyplot as plt
        x = [row["step"] for row in trace]
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axes[0].plot(x, [row["carrier_position"] for row in trace], label="cavity")
        axes[0].plot(x, [row["offset"] for row in trace], label="offset")
        axes[0].legend(); axes[0].set_ylabel("scan unit")
        axes[1].plot(x, [row["amplitude"] for row in trace])
        axes[1].set_ylabel("amplitude")
        axes[2].plot(x, [row["balance_error"] * 100 for row in trace])
        axes[2].set_ylabel("imbalance %"); axes[2].set_xlabel("iteration")
        fig.tight_layout(); fig.savefig(png_path, dpi=150); plt.close(fig)
    except ImportError:
        png_path = None
    return csv_path, png_path


if __name__ == "__main__":
    save_trace(run_virtual_lock(), Path("reports") / "adc_peak_balance")
