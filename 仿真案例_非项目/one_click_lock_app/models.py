from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SignalFrame:
    time_s: list[float]
    transmission_v: list[float]
    error_v: list[float]
    csv_path: Path | None = None

    @property
    def sample_count(self) -> int:
        return min(len(self.time_s), len(self.transmission_v), len(self.error_v))

    @property
    def duration_s(self) -> float:
        if len(self.time_s) < 2:
            return 0.0
        return self.time_s[-1] - self.time_s[0]


@dataclass(frozen=True)
class ScanSnapshot:
    enabled: bool | None = None
    hold: bool | None = None
    frequency_hz: float | None = None
    output_channel: int | None = None
    signal_type: int | None = None
    offset_v: float | None = None
    amplitude_vpp: float | None = None
    start_v: float | None = None
    end_v: float | None = None
    unit: str | None = None


@dataclass(frozen=True)
class LockSettingsSnapshot:
    enabled: bool | None = None
    hold: bool | None = None
    spectrum_input_channel: int | None = None
    lock_type: int | None = None
    error_channel: int | None = None
    error_channel_inverted: bool | None = None
    pid_selection: int | None = None
    lock_without_lockpoint: bool | None = None
    setpoint_v: float | None = None
    state_text: str | None = None


@dataclass(frozen=True)
class PidSnapshot:
    enabled: bool | None = None
    output_channel: int | None = None
    gain_all: float | None = None
    gain_p: float | None = None
    gain_i: float | None = None
    gain_d: float | None = None


@dataclass(frozen=True)
class LockInSnapshot:
    modulation_enabled: bool | None = None
    input_channel: int | None = None
    modulation_output_channel: int | None = None
    frequency_hz: float | None = None
    amplitude: float | None = None
    phase_shift_deg: float | None = None
    lock_level_v: float | None = None


@dataclass(frozen=True)
class LaserSetSnapshot:
    cc_current_ma: float | None = None
    pc_voltage_v: float | None = None
    tc_temperature_c: float | None = None


@dataclass(frozen=True)
class FalcSnapshot:
    index: int = 1
    serial_number: str | None = None
    path_selection: int | None = None
    hold_state: bool | None = None
    main_enabled: bool | None = None
    main_lock_state: bool | None = None
    main_gain_db: float | None = None
    unlim_enabled: bool | None = None
    unlim_lock_state: bool | None = None
    unlim_hold_state: bool | None = None
    unlim_regulating_state: bool | None = None
    unlim_output_range_v: float | None = None
    unlim_input_offset_mv: float | None = None
    unlim_gain: float | None = None
    unavailable: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DlcSnapshot:
    connected: bool
    system_label: str | None = None
    serial_number: str | None = None
    firmware: str | None = None
    health_text: str | None = None
    emission: bool | None = None
    interlock_open: bool | None = None
    laser_enabled: bool | None = None
    laser_emission: bool | None = None
    lock_enabled: bool | None = None
    lock_state_text: str | None = None
    scan: ScanSnapshot = field(default_factory=ScanSnapshot)
    lock_settings: LockSettingsSnapshot = field(default_factory=LockSettingsSnapshot)
    pid1: PidSnapshot = field(default_factory=PidSnapshot)
    pid2: PidSnapshot = field(default_factory=PidSnapshot)
    lockin: LockInSnapshot = field(default_factory=LockInSnapshot)
    laser_set: LaserSetSnapshot = field(default_factory=LaserSetSnapshot)
    falc: FalcSnapshot = field(default_factory=FalcSnapshot)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LockAnalysis:
    has_peak: bool
    has_error_zero: bool
    ready_to_lock: bool
    peak_time_s: float | None
    zero_time_s: float | None
    peak_value: float | None
    transmission_prominence: float
    error_slope: float | None
    message: str
    suggested_offset_v: float | None = None
    suggested_amplitude_vpp: float | None = None
