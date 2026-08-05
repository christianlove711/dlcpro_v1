from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
from threading import RLock

try:
    import ifaddr
except ImportError:
    ifaddr = None

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None

from toptica.lasersdk.client import DecopError, DeviceNotFoundError
from toptica.lasersdk.dlcpro.v3_3_3 import DLCpro, NetworkConnection, SerialConnection


@dataclass(slots=True)
class ConnectionSettings:
    mode: str
    target: str
    baudrate: int = 115200
    timeout: int = 5
    command_line_port: int = 1998
    monitoring_line_port: int = 1999


class SnapshotSection(str, Enum):
    CORE = "core"
    LASER = "laser"
    SCAN_LOCK = "scan_lock"
    FALC = "falc"
    RELOCK = "relock"
    STABILIZATION = "stabilization"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class SnapshotRequest:
    sections: frozenset[SnapshotSection]

    @classmethod
    def full(cls) -> "SnapshotRequest":
        return cls(frozenset({SnapshotSection.ALL}))

    @classmethod
    def core(cls) -> "SnapshotRequest":
        return cls(frozenset({SnapshotSection.CORE}))

    @classmethod
    def for_sections(cls, *sections: SnapshotSection) -> "SnapshotRequest":
        return cls(frozenset(sections))


@dataclass(slots=True)
class FalcMainSnapshot:
    enabled: bool
    lock_state: bool
    gain_all: float
    use_external_input: bool
    i1_enabled: bool
    i1: int
    i2_enabled: bool
    i2: int
    i3_enabled: bool
    i3: int
    d1_enabled: bool
    d1: int
    d2_enabled: bool
    d2: int


@dataclass(slots=True)
class FalcUnlimSnapshot:
    enabled: bool
    hold: bool
    sign: bool
    slew_rate: int
    gain: float
    output_range: float
    input_offset: float
    lock_state: bool
    hold_state: bool
    regulating_state: bool


@dataclass(slots=True)
class FalcSnapshot:
    serial_number: str
    label: str
    fw_ver: str
    status_txt: str
    input_gain: int
    input_offset: float
    path_selection: int
    hold_state: bool
    mon_config: int
    main: FalcMainSnapshot
    unlim: FalcUnlimSnapshot


@dataclass(slots=True)
class StabilizationSnapshot:
    enabled: bool
    input_channel: int
    setpoint: float
    actual_level: float
    hold_output_on_unlock: bool
    output_channel: int
    gain_all: float
    gain_p: float
    gain_i: float
    gain_d: float
    pd_ext_input_channel: int
    pd_ext_photodiode: float
    pd_ext_cal_factor: float
    pd_ext_cal_offset: float
    window_enabled: bool
    window_level_low: float
    window_level_hysteresis: float


@dataclass(slots=True)
class DeviceSnapshot:
    connection_mode: str
    connection_target: str
    system_label: str
    serial_number: str
    fw_ver: str
    system_type: str
    system_model: str
    uptime_txt: str
    emission: bool
    interlock_open: bool
    latest_message: str
    cc_enabled: bool
    cc_emission: bool
    current_set: float
    current_act: float
    current_clip: float
    current_clip_tuning: float
    current_clip_limit: float
    current_clip_writable_limit: float
    effective_current_max: float
    use_current_clip_tuning: bool
    cc_status_txt: str
    feedforward_enabled: bool
    feedforward_factor: float
    arc_enabled: bool
    arc_signal: int
    arc_factor: float
    tc_enabled: bool
    temp_set: float
    temp_act: float
    tc_arc_enabled: bool
    tc_arc_signal: int
    tc_arc_factor: float
    pc_enabled: bool
    pc_voltage_set: float
    pc_voltage_act: float
    pc_slew_rate_enabled: bool
    pc_slew_rate: float
    pc_arc_enabled: bool
    pc_arc_signal: int
    pc_arc_factor: float
    sc_enabled: bool
    sc_amplitude: float
    sc_offset: float
    sc_output_channel: int
    sc_frequency: float
    sc_signal_type: int
    sc_unit: str
    lock_state: int
    lock_state_txt: str
    lock_enabled: bool
    lock_hold: bool
    lock_input_channel: int
    lock_error_channel: int
    lock_type: int
    lock_pid_selection: int
    lock_falc_selection: int
    lock_without_lockpoint: bool
    lock_candidate_top_enabled: bool
    lock_candidate_bottom_enabled: bool
    lock_candidate_positive_edge_enabled: bool
    lock_candidate_negative_edge_enabled: bool
    lock_candidate_edge_level: float
    lock_candidate_peak_noise_tolerance: float
    lock_candidate_edge_min_distance: int
    lock_candidate_top_of_fringe_low_pass: bool
    lockin_modulation_enabled: bool
    lockin_input_channel: int
    lockin_modulation_output_channel: int
    lockin_frequency: float
    lockin_amplitude: float
    lockin_phase_shift: float
    lockin_lock_level: float
    lockin_auto_lir_state: int
    lockin_auto_lir_progress: int
    pid1_enabled: bool
    pid1_gain_all: float
    pid1_gain_p: float
    pid1_gain_i: float
    pid1_gain_d: float
    pid1_output_channel: int
    pid1_sign: bool
    pid1_i_cutoff_enabled: bool
    pid1_i_cutoff: float
    pid1_limit_enabled: bool
    pid1_limit_max: float
    pid2_enabled: bool
    pid2_gain_all: float
    pid2_gain_p: float
    pid2_gain_i: float
    pid2_gain_d: float
    pid2_output_channel: int
    pid2_sign: bool
    pid2_limit_enabled: bool
    pid2_limit_max: float
    relock_detection_enabled: bool
    relock_input_channel: int
    relock_level_high: float
    relock_level_low: float
    relock_level_hysteresis: float
    relock_delay: float
    relock_reset_enabled: bool
    relock_enabled: bool
    relock_amplitude: float
    relock_frequency: float
    relock_output_channel: int
    pressure_comp_enabled: bool
    pressure_comp_air_pressure: float
    pressure_comp_factor: float
    pressure_comp_voltage: float
    stabilization: StabilizationSnapshot | None
    falc1: FalcSnapshot | None


class DlcProService:
    """DLC pro 3.3.3 communication/service layer.

    Basis:
    - SDK: `toptica.lasersdk.dlcpro.v3_3_3`
    - Manual: `Manual.md` for CC ARC options and safety guidance
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._device: DLCpro | None = None
        self._settings: ConnectionSettings | None = None
        self._snapshot_cache: DeviceSnapshot | None = None
        self._unavailable_sections: set[SnapshotSection] = set()

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._device is not None

    def connect(self, settings: ConnectionSettings) -> DeviceSnapshot:
        with self._lock:
            self.disconnect()
            self._settings = settings
            connection = self._build_connection(settings)
            device = DLCpro(connection)
            try:
                device.open()
                self._device = device
                # Do not make optional hardware modules a prerequisite for a
                # valid connection.  Start with a neutral cache and read only
                # the core parameters; feature pages are refreshed on demand.
                self._snapshot_cache = self._empty_snapshot(settings)
                return self._read_snapshot_request_unlocked(SnapshotRequest.core())
            except Exception:
                # Transport setup and the initial parameter snapshot form one
                # connection operation.  A rejected snapshot must not leave a
                # half-connected service behind (for example DECoP error -22).
                try:
                    device.close()
                finally:
                    self._device = None
                    self._settings = None
                    self._snapshot_cache = None
                    self._unavailable_sections.clear()
                raise

    def disconnect(self) -> None:
        with self._lock:
            if self._device is not None:
                try:
                    self._device.close()
                finally:
                    self._device = None
                    self._settings = None
                    self._snapshot_cache = None
                    self._unavailable_sections.clear()

    def read_snapshot(self, request: SnapshotRequest | None = None) -> DeviceSnapshot:
        with self._lock:
            return self._read_snapshot_request_unlocked(request or SnapshotRequest.full())

    def set_current(self, value_ma: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.current_set.set(float(value_ma))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_current_clip(self, value_ma: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.current_clip.set(float(value_ma))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_cc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_feedforward_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.feedforward_enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_feedforward_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.feedforward_factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_tc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            tc = self._tc()
            tc.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_temp_set(self, value_c: float) -> DeviceSnapshot:
        with self._lock:
            tc = self._tc()
            tc.temp_set.set(float(value_c))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_tc_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_tc_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_tc_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            pc = self._pc()
            pc.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_voltage_set(self, value_v: float) -> DeviceSnapshot:
        with self._lock:
            pc = self._pc()
            pc.voltage_set.set(float(value_v))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_slew_rate_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            output_filter = self._pc().output_filter
            output_filter.slew_rate_enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_slew_rate(self, value: float) -> DeviceSnapshot:
        with self._lock:
            output_filter = self._pc().output_filter
            output_filter.slew_rate.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pc_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pressure_comp_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            pressure_comp = self._pressure_comp()
            pressure_comp.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_pressure_comp_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            pressure_comp = self._pressure_comp()
            pressure_comp.factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.LASER)
            )

    def set_sc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_sc_amplitude(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.amplitude.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_sc_offset(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.offset.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_sc_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.output_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_sc_frequency(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.frequency.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_sc_signal_type(self, value: int) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.signal_type.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.lock_enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_hold(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.hold.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_input_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.spectrum_input_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_error_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.error_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_type(self, value: int) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.type.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_pid_selection(self, value: int) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.pid_selection.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_falc_selection(self, value: int) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.falc_selection.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_without_lockpoint(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            lock = self._lock_control()
            lock.lock_without_lockpoint.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_top_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.top.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_bottom_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.bottom.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_positive_edge_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.positive_edge.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_negative_edge_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.negative_edge.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_edge_level(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.edge_level.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_peak_noise_tolerance(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.peak_noise_tolerance.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_edge_min_distance(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.edge_min_distance.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lock_candidate_top_of_fringe_low_pass(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().candidate_filter.top_of_fringe_low_pass.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_modulation_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.modulation_enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_input_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.input_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_modulation_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.modulation_output_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_frequency(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.frequency.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_amplitude(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.amplitude.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_phase_shift(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.phase_shift.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_lockin_lock_level(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().lockin.lock_level.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_gain_all(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.all.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_gain_p(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.p.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_gain_i(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.i.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_gain_d(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.d.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.output_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_sign(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.sign.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_i_cutoff_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.i_cutoff_enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_i_cutoff(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.gain.i_cutoff.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_limit_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.outputlimit.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid1_limit_max(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid1.outputlimit.max.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_gain_all(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.gain.all.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_gain_p(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.gain.p.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_gain_i(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.gain.i.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_gain_d(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.gain.d.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.output_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_sign(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.sign.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_limit_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.outputlimit.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_pid2_limit_max(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().pid2.outputlimit.max.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.SCAN_LOCK)
            )

    def set_relock_detection_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().window.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_input_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().window.input_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_level_high(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().window.level_high.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_level_low(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().window.level_low.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_level_hysteresis(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().window.level_hysteresis.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_delay(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().relock.delay.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_reset_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().reset.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().relock.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_amplitude(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().relock.amplitude.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_frequency(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().relock.frequency.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_relock_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._lock_control().relock.output_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.RELOCK)
            )

    def set_falc1_input_gain(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).input.gain.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_input_offset(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).input.offset.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_path_selection(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).path_selection.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_main_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).main.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_main_gain_all(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).main.gain.all.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_main_use_external_input(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).main.gain.use_external_input.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_main_filter_enabled(self, filter_name: str, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            gain = self._falc(1).main.gain
            getattr(gain, f"{filter_name}_enabled").set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_main_filter_value(self, filter_name: str, value: int) -> DeviceSnapshot:
        with self._lock:
            gain = self._falc(1).main.gain
            getattr(gain, filter_name).set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_unlim_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def engage_falc1_configured_paths(self) -> DeviceSnapshot:
        """Stop Scan and enable only the FALC paths selected on the device.

        This deliberately leaves every FALC gain/filter/range parameter intact.
        The current ``path-selection`` readback is the authority for whether
        Unlim, Main, or both paths are engaged.
        """
        with self._lock:
            board = self._falc(1)
            path = int(board.path_selection.get())
            if path not in (1, 2, 3):
                raise RuntimeError(
                    "FALC pro当前Path Selection为None；请先在FALC pro设置中选择"
                    "Unlim、Main或Unlim + Main。"
                )
            scan = self._scan()
            scan_was_enabled = bool(scan.enabled.get())
            unlim_was_enabled = bool(board.unlim.enabled.get())
            main_was_enabled = bool(board.main.enabled.get())
            try:
                # The peak-balancing acquisition requires Scan, whereas
                # closed-loop FALC operation starts from a stationary output.
                scan.enabled.set(False)
                if path & 1:
                    board.unlim.enabled.set(True)
                if path & 2:
                    board.main.enabled.set(True)
                snapshot = self._read_snapshot_request_unlocked(
                    SnapshotRequest.for_sections(
                        SnapshotSection.SCAN_LOCK, SnapshotSection.FALC
                    )
                )
            except Exception:
                # Never leave a half-engaged loop after a transport/parameter
                # failure. Restore the states that existed before this action;
                # rollback is best-effort so the original SDK error is kept.
                for parameter, old_value in (
                    (board.main.enabled, main_was_enabled),
                    (board.unlim.enabled, unlim_was_enabled),
                    (scan.enabled, scan_was_enabled),
                ):
                    try:
                        parameter.set(old_value)
                    except Exception:
                        pass
                raise
            return snapshot

    def set_falc1_unlim_hold(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.hold.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_unlim_input_offset(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.input_offset.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_unlim_output_range(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.output_range.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_unlim_slew_rate(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.slew_rate.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_unlim_sign(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).unlim.sign.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_falc1_mon_config(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._falc(1).mon.config.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.FALC)
            )

    def set_stabilization_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_setpoint(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().setpoint.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_hold_output_on_unlock(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().hold_output_on_unlock.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_gain_all(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().gain.all.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_gain_p(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().gain.p.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_gain_i(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().gain.i.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_gain_d(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().gain.d.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_pd_ext_input_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            self._device_required().laser1.pd_ext.input_channel.set(int(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_pd_ext_cal_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._device_required().laser1.pd_ext.cal_factor.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_pd_ext_cal_offset(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._device_required().laser1.pd_ext.cal_offset.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_window_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().window.enabled.set(bool(enabled))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_window_level_low(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().window.level_low.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )

    def set_stabilization_window_level_hysteresis(self, value: float) -> DeviceSnapshot:
        with self._lock:
            self._power_stabilization().window.level_hysteresis.set(float(value))
            return self._read_snapshot_request_unlocked(
                SnapshotRequest.for_sections(SnapshotSection.STABILIZATION)
            )
    def list_serial_ports(self) -> list[str]:
        if list_ports is None:
            return []
        return [port.device for port in list_ports.comports()]

    def list_network_adapters(self) -> list[str]:
        if ifaddr is None:
            return []
        lines: list[str] = []
        for adapter in ifaddr.get_adapters():
            for ip in adapter.ips:
                address = ip.ip[0] if isinstance(ip.ip, tuple) else ip.ip
                lines.append(f"{adapter.nice_name}: {address}")
        return lines

    @staticmethod
    def format_error(exc: Exception) -> str:
        if isinstance(exc, DeviceNotFoundError):
            detail = str(exc)
            if "winerror 121" in detail.lower() or "信号灯超时时间已到" in detail:
                return (
                    "DLC pro 的 SDK 连接端口响应超时（WinError 121）。\n"
                    "设备可以联网但其他客户端可能仍占用 1998/1999 端口。请从系统托盘"
                    "彻底退出 TOPAS DLC pro，或在任务管理器结束残留的 "
                    "TOPAS_DLC_pro.exe 后重试。\n"
                    f"原始错误：{detail}"
                )
            if (
                "winerror 5" in detail.lower()
                or "10013" in detail
                or "拒绝访问" in detail
                or "访问权限不允许" in detail
            ):
                return (
                    "Windows 阻止了到 DLC pro 的 TCP 连接。\n"
                    "IP 和子网可能是正确的；请关闭 VPN/网络锁定功能，或在防火墙中允许"
                    "本程序访问 DLC pro 的 169.254.0.0/16 本地网络，然后重试。\n"
                    f"原始错误：{detail}"
                )
            return f"Device not found / 未找到设备: {exc}"
        if isinstance(exc, DecopError):
            detail = str(exc)
            if "-22" in detail or "no access" in detail.lower():
                return (
                    "已连接到 DLC pro，但设备拒绝访问某项参数（Error -22: no access）。\n"
                    "这不是子网掩码错误；通常表示该参数或功能模块在当前设备上不可访问，"
                    "或当前设备状态不允许访问。"
                )
            return f"Device rejected request / 设备拒绝请求: {detail}"
        if isinstance(exc, TimeoutError):
            return f"Timeout / 连接超时: {exc}"
        return f"{type(exc).__name__}: {exc}"

    def _build_connection(self, settings: ConnectionSettings):
        if settings.mode == "network":
            return NetworkConnection(
                settings.target,
                command_line_port=settings.command_line_port,
                monitoring_line_port=settings.monitoring_line_port,
                timeout=settings.timeout,
            )
        if settings.mode == "serial":
            return SerialConnection(
                settings.target,
                baudrate=settings.baudrate,
                timeout=settings.timeout,
            )
        raise ValueError(f"Unsupported connection mode: {settings.mode}")

    def _device_required(self) -> DLCpro:
        if self._device is None:
            raise RuntimeError("DLC pro is not connected / DLC pro 未连接")
        return self._device

    def _cc(self):
        return self._device_required().laser1.dl.cc

    def _tc(self):
        return self._device_required().laser1.dl.tc

    def _pc(self):
        return self._device_required().laser1.dl.pc

    def _pressure_comp(self):
        return self._device_required().laser1.dl.pressure_compensation

    def _scan(self):
        return self._device_required().laser1.scan

    def _lock_control(self):
        return self._device_required().laser1.dl.lock

    def _falc(self, board_index: int):
        return getattr(self._device_required(), f"falc{board_index}")

    def _power_stabilization(self):
        return self._device_required().laser1.power_stabilization

    def _read_snapshot_request_unlocked(self, request: SnapshotRequest) -> DeviceSnapshot:
        device = self._device_required()
        if self._snapshot_cache is None:
            settings = self._settings
            assert settings is not None
            self._snapshot_cache = self._empty_snapshot(settings)

        requested = set(request.sections)
        if SnapshotSection.ALL in requested:
            requested = {
                SnapshotSection.CORE,
                SnapshotSection.LASER,
                SnapshotSection.SCAN_LOCK,
                SnapshotSection.RELOCK,
                SnapshotSection.FALC,
                SnapshotSection.STABILIZATION,
            }

        values: dict[str, object] = {}
        if SnapshotSection.CORE in requested:
            values.update(self._read_core_values(device))
        if SnapshotSection.LASER in requested:
            self._read_optional_section(
                SnapshotSection.LASER,
                lambda: self._read_laser_values(device),
                values,
            )
        if SnapshotSection.SCAN_LOCK in requested:
            # Scan itself is fundamental to this application.  Read it before
            # the larger lock tree so an unavailable optional lock parameter
            # cannot hide valid Scan Offset/Amplitude/Frequency readbacks.
            values.update(self._read_scan_values(device))
            self._read_optional_section(
                SnapshotSection.SCAN_LOCK,
                lambda: self._read_scan_lock_values(device),
                values,
            )
        if SnapshotSection.RELOCK in requested:
            self._read_optional_section(
                SnapshotSection.RELOCK,
                lambda: self._read_relock_values(device),
                values,
            )
        if SnapshotSection.FALC in requested:
            values["falc1"] = self._read_falc_snapshot(device, 1)
        if SnapshotSection.STABILIZATION in requested:
            values["stabilization"] = self._read_stabilization_snapshot(device)
        if values:
            self._snapshot_cache = replace(self._snapshot_cache, **values)
        return self._snapshot_cache

    def _read_optional_section(
        self,
        section: SnapshotSection,
        reader,
        values: dict[str, object],
    ) -> None:
        try:
            values.update(reader())
            self._unavailable_sections.discard(section)
        except DecopError:
            # DLC pro models expose one SDK tree, while individual hardware
            # configurations may deny access to nodes that are not installed.
            # Preserve the last cached values instead of dropping the entire
            # connection with DECoP error -22.
            self._unavailable_sections.add(section)

    @staticmethod
    def _empty_snapshot(settings: ConnectionSettings) -> DeviceSnapshot:
        values: dict[str, object] = {}
        for field in fields(DeviceSnapshot):
            if field.name == "connection_mode":
                values[field.name] = settings.mode
            elif field.name == "connection_target":
                values[field.name] = settings.target
            elif field.name in {"stabilization", "falc1"}:
                values[field.name] = None
            elif field.type == "str":
                values[field.name] = ""
            elif field.type == "bool":
                values[field.name] = False
            elif field.type == "int":
                values[field.name] = 0
            else:
                values[field.name] = 0.0
        return DeviceSnapshot(**values)

    @staticmethod
    def _read_core_values(device: DLCpro) -> dict[str, object]:
        cc = device.laser1.dl.cc
        tc = device.laser1.dl.tc
        pc = device.laser1.dl.pc
        values = {
            "system_label": device.system_label.get(),
            "serial_number": device.serial_number.get(),
            "fw_ver": device.fw_ver.get(),
            "system_type": device.system_type.get(),
            "system_model": device.system_model.get(),
            "uptime_txt": device.uptime_txt.get(),
            "emission": bool(device.emission.get()),
            "interlock_open": bool(device.interlock_open.get()),
            "latest_message": device.system_messages.latest_message.get(),
            "cc_emission": bool(cc.emission.get()),
            "current_act": float(cc.current_act.get()),
            "temp_act": float(tc.temp_act.get()),
            "pc_voltage_act": float(pc.voltage_act.get()),
        }
        try:
            lock = device.laser1.dl.lock
            values.update(
                lock_state=int(lock.state.get()),
                lock_state_txt=lock.state_txt.get(),
            )
        except DecopError:
            pass
        return values

    @staticmethod
    def _read_scan_values(device: DLCpro) -> dict[str, object]:
        scan = device.laser1.scan
        return {
            "sc_enabled": bool(scan.enabled.get()),
            "sc_amplitude": float(scan.amplitude.get()),
            "sc_offset": float(scan.offset.get()),
            "sc_output_channel": int(scan.output_channel.get()),
            "sc_frequency": float(scan.frequency.get()),
            "sc_signal_type": int(scan.signal_type.get()),
            "sc_unit": scan.unit.get(),
        }

    def _read_laser_values(self, device: DLCpro) -> dict[str, object]:
        cc = device.laser1.dl.cc
        ext = cc.external_input
        tc = device.laser1.dl.tc
        tc_ext = tc.external_input
        pc = device.laser1.dl.pc
        pc_ext = pc.external_input
        pc_filter = pc.output_filter
        pressure = device.laser1.dl.pressure_compensation
        return {
            "cc_enabled": bool(cc.enabled.get()),
            "cc_emission": bool(cc.emission.get()),
            "current_set": float(cc.current_set.get()),
            "current_act": float(cc.current_act.get()),
            "current_clip": float(cc.current_clip.get()),
            "current_clip_tuning": float(cc.current_clip_tuning.get()),
            "current_clip_limit": float(cc.current_clip_limit.get()),
            "current_clip_writable_limit": self._compute_current_clip_writable_limit(cc),
            "effective_current_max": self._compute_effective_current_max(cc),
            "use_current_clip_tuning": bool(cc.use_current_clip_tuning.get()),
            "cc_status_txt": cc.status_txt.get(),
            "feedforward_enabled": bool(cc.feedforward_enabled.get()),
            "feedforward_factor": float(cc.feedforward_factor.get()),
            "arc_enabled": bool(ext.enabled.get()),
            "arc_signal": int(ext.signal.get()),
            "arc_factor": float(ext.factor.get()),
            "tc_enabled": bool(tc.enabled.get()),
            "temp_set": float(tc.temp_set.get()),
            "temp_act": float(tc.temp_act.get()),
            "tc_arc_enabled": bool(tc_ext.enabled.get()),
            "tc_arc_signal": int(tc_ext.signal.get()),
            "tc_arc_factor": float(tc_ext.factor.get()),
            "pc_enabled": bool(pc.enabled.get()),
            "pc_voltage_set": float(pc.voltage_set.get()),
            "pc_voltage_act": float(pc.voltage_act.get()),
            "pc_slew_rate_enabled": bool(pc_filter.slew_rate_enabled.get()),
            "pc_slew_rate": float(pc_filter.slew_rate.get()),
            "pc_arc_enabled": bool(pc_ext.enabled.get()),
            "pc_arc_signal": int(pc_ext.signal.get()),
            "pc_arc_factor": float(pc_ext.factor.get()),
            "pressure_comp_enabled": bool(pressure.enabled.get()),
            "pressure_comp_air_pressure": float(pressure.air_pressure.get()),
            "pressure_comp_factor": float(pressure.factor.get()),
            "pressure_comp_voltage": float(pressure.compensation_voltage.get()),
        }

    @staticmethod
    def _read_scan_lock_values(device: DLCpro) -> dict[str, object]:
        scan = device.laser1.scan
        lock = device.laser1.dl.lock
        candidate = lock.candidate_filter
        lockin = lock.lockin
        pid1 = lock.pid1
        pid2 = lock.pid2
        return {
            "sc_enabled": bool(scan.enabled.get()),
            "sc_amplitude": float(scan.amplitude.get()),
            "sc_offset": float(scan.offset.get()),
            "sc_output_channel": int(scan.output_channel.get()),
            "sc_frequency": float(scan.frequency.get()),
            "sc_signal_type": int(scan.signal_type.get()),
            "sc_unit": scan.unit.get(),
            "lock_state": int(lock.state.get()),
            "lock_state_txt": lock.state_txt.get(),
            "lock_enabled": bool(lock.lock_enabled.get()),
            "lock_hold": bool(lock.hold.get()),
            "lock_input_channel": int(lock.spectrum_input_channel.get()),
            "lock_error_channel": int(lock.error_channel.get()),
            "lock_type": int(lock.type.get()),
            "lock_pid_selection": int(lock.pid_selection.get()),
            "lock_falc_selection": int(lock.falc_selection.get()),
            "lock_without_lockpoint": bool(lock.lock_without_lockpoint.get()),
            "lock_candidate_top_enabled": bool(candidate.top.get()),
            "lock_candidate_bottom_enabled": bool(candidate.bottom.get()),
            "lock_candidate_positive_edge_enabled": bool(candidate.positive_edge.get()),
            "lock_candidate_negative_edge_enabled": bool(candidate.negative_edge.get()),
            "lock_candidate_edge_level": float(candidate.edge_level.get()),
            "lock_candidate_peak_noise_tolerance": float(candidate.peak_noise_tolerance.get()),
            "lock_candidate_edge_min_distance": int(candidate.edge_min_distance.get()),
            "lock_candidate_top_of_fringe_low_pass": bool(candidate.top_of_fringe_low_pass.get()),
            "lockin_modulation_enabled": bool(lockin.modulation_enabled.get()),
            "lockin_input_channel": int(lockin.input_channel.get()),
            "lockin_modulation_output_channel": int(lockin.modulation_output_channel.get()),
            "lockin_frequency": float(lockin.frequency.get()),
            "lockin_amplitude": float(lockin.amplitude.get()),
            "lockin_phase_shift": float(lockin.phase_shift.get()),
            "lockin_lock_level": float(lockin.lock_level.get()),
            "lockin_auto_lir_state": int(lockin.auto_lir.state.get()),
            "lockin_auto_lir_progress": int(lockin.auto_lir.progress.get()),
            "pid1_enabled": bool(pid1.enabled.get()),
            "pid1_gain_all": float(pid1.gain.all.get()),
            "pid1_gain_p": float(pid1.gain.p.get()),
            "pid1_gain_i": float(pid1.gain.i.get()),
            "pid1_gain_d": float(pid1.gain.d.get()),
            "pid1_output_channel": int(pid1.output_channel.get()),
            "pid1_sign": bool(pid1.sign.get()),
            "pid1_i_cutoff_enabled": bool(pid1.gain.i_cutoff_enabled.get()),
            "pid1_i_cutoff": float(pid1.gain.i_cutoff.get()),
            "pid1_limit_enabled": bool(pid1.outputlimit.enabled.get()),
            "pid1_limit_max": float(pid1.outputlimit.max.get()),
            "pid2_enabled": bool(pid2.enabled.get()),
            "pid2_gain_all": float(pid2.gain.all.get()),
            "pid2_gain_p": float(pid2.gain.p.get()),
            "pid2_gain_i": float(pid2.gain.i.get()),
            "pid2_gain_d": float(pid2.gain.d.get()),
            "pid2_output_channel": int(pid2.output_channel.get()),
            "pid2_sign": bool(pid2.sign.get()),
            "pid2_limit_enabled": bool(pid2.outputlimit.enabled.get()),
            "pid2_limit_max": float(pid2.outputlimit.max.get()),
        }

    @staticmethod
    def _read_relock_values(device: DLCpro) -> dict[str, object]:
        lock = device.laser1.dl.lock
        relock = lock.relock
        window = lock.window
        reset = lock.reset
        return {
            "relock_detection_enabled": bool(window.enabled.get()),
            "relock_input_channel": int(window.input_channel.get()),
            "relock_level_high": float(window.level_high.get()),
            "relock_level_low": float(window.level_low.get()),
            "relock_level_hysteresis": float(window.level_hysteresis.get()),
            "relock_delay": float(relock.delay.get()),
            "relock_reset_enabled": bool(reset.enabled.get()),
            "relock_enabled": bool(relock.enabled.get()),
            "relock_amplitude": float(relock.amplitude.get()),
            "relock_frequency": float(relock.frequency.get()),
            "relock_output_channel": int(relock.output_channel.get()),
        }

    def _read_snapshot_unlocked(self) -> DeviceSnapshot:
        device = self._device_required()
        settings = self._settings
        assert settings is not None
        cc = device.laser1.dl.cc
        ext = cc.external_input
        tc = device.laser1.dl.tc
        tc_ext = tc.external_input
        pc = device.laser1.dl.pc
        pc_ext = pc.external_input
        pc_filter = pc.output_filter
        pressure_comp = device.laser1.dl.pressure_compensation
        scan = device.laser1.scan
        lock = device.laser1.dl.lock
        candidate_filter = lock.candidate_filter
        lockin = lock.lockin
        pid1 = lock.pid1
        pid2 = lock.pid2
        relock = lock.relock
        relock_window = lock.window
        relock_reset = lock.reset
        snapshot = DeviceSnapshot(
            connection_mode=settings.mode,
            connection_target=settings.target,
            system_label=device.system_label.get(),
            serial_number=device.serial_number.get(),
            fw_ver=device.fw_ver.get(),
            system_type=device.system_type.get(),
            system_model=device.system_model.get(),
            uptime_txt=device.uptime_txt.get(),
            emission=bool(device.emission.get()),
            interlock_open=bool(device.interlock_open.get()),
            latest_message=device.system_messages.latest_message.get(),
            cc_enabled=bool(cc.enabled.get()),
            cc_emission=bool(cc.emission.get()),
            current_set=float(cc.current_set.get()),
            current_act=float(cc.current_act.get()),
            current_clip=float(cc.current_clip.get()),
            current_clip_tuning=float(cc.current_clip_tuning.get()),
            current_clip_limit=float(cc.current_clip_limit.get()),
            current_clip_writable_limit=self._compute_current_clip_writable_limit(cc),
            effective_current_max=self._compute_effective_current_max(cc),
            use_current_clip_tuning=bool(cc.use_current_clip_tuning.get()),
            cc_status_txt=cc.status_txt.get(),
            feedforward_enabled=bool(cc.feedforward_enabled.get()),
            feedforward_factor=float(cc.feedforward_factor.get()),
            arc_enabled=bool(ext.enabled.get()),
            arc_signal=int(ext.signal.get()),
            arc_factor=float(ext.factor.get()),
            tc_enabled=bool(tc.enabled.get()),
            temp_set=float(tc.temp_set.get()),
            temp_act=float(tc.temp_act.get()),
            tc_arc_enabled=bool(tc_ext.enabled.get()),
            tc_arc_signal=int(tc_ext.signal.get()),
            tc_arc_factor=float(tc_ext.factor.get()),
            pc_enabled=bool(pc.enabled.get()),
            pc_voltage_set=float(pc.voltage_set.get()),
            pc_voltage_act=float(pc.voltage_act.get()),
            pc_slew_rate_enabled=bool(pc_filter.slew_rate_enabled.get()),
            pc_slew_rate=float(pc_filter.slew_rate.get()),
            pc_arc_enabled=bool(pc_ext.enabled.get()),
            pc_arc_signal=int(pc_ext.signal.get()),
            pc_arc_factor=float(pc_ext.factor.get()),
            sc_enabled=bool(scan.enabled.get()),
            sc_amplitude=float(scan.amplitude.get()),
            sc_offset=float(scan.offset.get()),
            sc_output_channel=int(scan.output_channel.get()),
            sc_frequency=float(scan.frequency.get()),
            sc_signal_type=int(scan.signal_type.get()),
            sc_unit=scan.unit.get(),
            lock_state=int(lock.state.get()),
            lock_state_txt=lock.state_txt.get(),
            lock_enabled=bool(lock.lock_enabled.get()),
            lock_hold=bool(lock.hold.get()),
            lock_input_channel=int(lock.spectrum_input_channel.get()),
            lock_error_channel=int(lock.error_channel.get()),
            lock_type=int(lock.type.get()),
            lock_pid_selection=int(lock.pid_selection.get()),
            lock_falc_selection=int(lock.falc_selection.get()),
            lock_without_lockpoint=bool(lock.lock_without_lockpoint.get()),
            lock_candidate_top_enabled=bool(candidate_filter.top.get()),
            lock_candidate_bottom_enabled=bool(candidate_filter.bottom.get()),
            lock_candidate_positive_edge_enabled=bool(candidate_filter.positive_edge.get()),
            lock_candidate_negative_edge_enabled=bool(candidate_filter.negative_edge.get()),
            lock_candidate_edge_level=float(candidate_filter.edge_level.get()),
            lock_candidate_peak_noise_tolerance=float(candidate_filter.peak_noise_tolerance.get()),
            lock_candidate_edge_min_distance=int(candidate_filter.edge_min_distance.get()),
            lock_candidate_top_of_fringe_low_pass=bool(candidate_filter.top_of_fringe_low_pass.get()),
            lockin_modulation_enabled=bool(lockin.modulation_enabled.get()),
            lockin_input_channel=int(lockin.input_channel.get()),
            lockin_modulation_output_channel=int(lockin.modulation_output_channel.get()),
            lockin_frequency=float(lockin.frequency.get()),
            lockin_amplitude=float(lockin.amplitude.get()),
            lockin_phase_shift=float(lockin.phase_shift.get()),
            lockin_lock_level=float(lockin.lock_level.get()),
            lockin_auto_lir_state=int(lockin.auto_lir.state.get()),
            lockin_auto_lir_progress=int(lockin.auto_lir.progress.get()),
            pid1_enabled=bool(pid1.enabled.get()),
            pid1_gain_all=float(pid1.gain.all.get()),
            pid1_gain_p=float(pid1.gain.p.get()),
            pid1_gain_i=float(pid1.gain.i.get()),
            pid1_gain_d=float(pid1.gain.d.get()),
            pid1_output_channel=int(pid1.output_channel.get()),
            pid1_sign=bool(pid1.sign.get()),
            pid1_i_cutoff_enabled=bool(pid1.gain.i_cutoff_enabled.get()),
            pid1_i_cutoff=float(pid1.gain.i_cutoff.get()),
            pid1_limit_enabled=bool(pid1.outputlimit.enabled.get()),
            pid1_limit_max=float(pid1.outputlimit.max.get()),
            pid2_enabled=bool(pid2.enabled.get()),
            pid2_gain_all=float(pid2.gain.all.get()),
            pid2_gain_p=float(pid2.gain.p.get()),
            pid2_gain_i=float(pid2.gain.i.get()),
            pid2_gain_d=float(pid2.gain.d.get()),
            pid2_output_channel=int(pid2.output_channel.get()),
            pid2_sign=bool(pid2.sign.get()),
            pid2_limit_enabled=bool(pid2.outputlimit.enabled.get()),
            pid2_limit_max=float(pid2.outputlimit.max.get()),
            relock_detection_enabled=bool(relock_window.enabled.get()),
            relock_input_channel=int(relock_window.input_channel.get()),
            relock_level_high=float(relock_window.level_high.get()),
            relock_level_low=float(relock_window.level_low.get()),
            relock_level_hysteresis=float(relock_window.level_hysteresis.get()),
            relock_delay=float(relock.delay.get()),
            relock_reset_enabled=bool(relock_reset.enabled.get()),
            relock_enabled=bool(relock.enabled.get()),
            relock_amplitude=float(relock.amplitude.get()),
            relock_frequency=float(relock.frequency.get()),
            relock_output_channel=int(relock.output_channel.get()),
            pressure_comp_enabled=bool(pressure_comp.enabled.get()),
            pressure_comp_air_pressure=float(pressure_comp.air_pressure.get()),
            pressure_comp_factor=float(pressure_comp.factor.get()),
            pressure_comp_voltage=float(pressure_comp.compensation_voltage.get()),
            stabilization=self._read_stabilization_snapshot(device),
            falc1=self._read_falc_snapshot(device, 1),
        )
        self._snapshot_cache = snapshot
        return snapshot

    @staticmethod
    def _compute_effective_current_max(cc) -> float:
        current_clip = float(cc.current_clip.get())
        current_clip_limit = float(cc.current_clip_limit.get())
        use_tuning_clip = bool(cc.use_current_clip_tuning.get())
        if use_tuning_clip:
            current_clip_tuning = float(cc.current_clip_tuning.get())
            return min(current_clip, current_clip_tuning, current_clip_limit)
        return min(current_clip, current_clip_limit)

    @staticmethod
    def _compute_current_clip_writable_limit(cc) -> float:
        current_clip_limit = float(cc.current_clip_limit.get())
        use_tuning_clip = bool(cc.use_current_clip_tuning.get())
        if use_tuning_clip:
            current_clip_tuning = float(cc.current_clip_tuning.get())
            return min(current_clip_tuning, current_clip_limit)
        return current_clip_limit

    @staticmethod
    def _read_falc_snapshot(device: DLCpro, board_index: int) -> FalcSnapshot | None:
        board = getattr(device, f"falc{board_index}")
        try:
            main_gain = board.main.gain
            unlim = board.unlim
            return FalcSnapshot(
                serial_number=board.serial_number.get(),
                label=board.label.get(),
                fw_ver=board.fw_ver.get(),
                status_txt=board.status_txt.get(),
                input_gain=int(board.input.gain.get()),
                input_offset=float(board.input.offset.get()),
                path_selection=int(board.path_selection.get()),
                hold_state=bool(board.hold_state.get()),
                mon_config=int(board.mon.config.get()),
                main=FalcMainSnapshot(
                    enabled=bool(board.main.enabled.get()),
                    lock_state=bool(board.main.lock_state.get()),
                    gain_all=float(main_gain.all.get()),
                    use_external_input=bool(main_gain.use_external_input.get()),
                    i1_enabled=bool(main_gain.i1_enabled.get()),
                    i1=int(main_gain.i1.get()),
                    i2_enabled=bool(main_gain.i2_enabled.get()),
                    i2=int(main_gain.i2.get()),
                    i3_enabled=bool(main_gain.i3_enabled.get()),
                    i3=int(main_gain.i3.get()),
                    d1_enabled=bool(main_gain.d1_enabled.get()),
                    d1=int(main_gain.d1.get()),
                    d2_enabled=bool(main_gain.d2_enabled.get()),
                    d2=int(main_gain.d2.get()),
                ),
                unlim=FalcUnlimSnapshot(
                    enabled=bool(unlim.enabled.get()),
                    hold=bool(unlim.hold.get()),
                    sign=bool(unlim.sign.get()),
                    slew_rate=int(unlim.slew_rate.get()),
                    gain=float(unlim.gain.get()),
                    output_range=float(unlim.output_range.get()),
                    input_offset=float(unlim.input_offset.get()),
                    lock_state=bool(unlim.lock_state.get()),
                    hold_state=bool(unlim.hold_state.get()),
                    regulating_state=bool(unlim.regulating_state.get()),
                ),
            )
        except DecopError:
            return None

    @staticmethod
    def _read_stabilization_snapshot(device: DLCpro) -> StabilizationSnapshot | None:
        try:
            stabilization = device.laser1.power_stabilization
            pd_ext = device.laser1.pd_ext
            return StabilizationSnapshot(
                enabled=bool(stabilization.enabled.get()),
                input_channel=int(stabilization.input_channel.get()),
                setpoint=float(stabilization.setpoint.get()),
                actual_level=float(stabilization.input_channel_value_act.get()),
                hold_output_on_unlock=bool(stabilization.hold_output_on_unlock.get()),
                output_channel=int(stabilization.output_channel.get()),
                gain_all=float(stabilization.gain.all.get()),
                gain_p=float(stabilization.gain.p.get()),
                gain_i=float(stabilization.gain.i.get()),
                gain_d=float(stabilization.gain.d.get()),
                pd_ext_input_channel=int(pd_ext.input_channel.get()),
                pd_ext_photodiode=float(pd_ext.photodiode.get()),
                pd_ext_cal_factor=float(pd_ext.cal_factor.get()),
                pd_ext_cal_offset=float(pd_ext.cal_offset.get()),
                window_enabled=bool(stabilization.window.enabled.get()),
                window_level_low=float(stabilization.window.level_low.get()),
                window_level_hysteresis=float(stabilization.window.level_hysteresis.get()),
            )
        except DecopError:
            return None
