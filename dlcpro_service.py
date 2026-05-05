from __future__ import annotations

from dataclasses import dataclass
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
    pressure_comp_enabled: bool
    pressure_comp_air_pressure: float
    pressure_comp_factor: float
    pressure_comp_voltage: float


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
            except Exception:
                device.close()
                raise
            self._device = device
            return self._read_snapshot_unlocked()

    def disconnect(self) -> None:
        with self._lock:
            if self._device is not None:
                try:
                    self._device.close()
                finally:
                    self._device = None
                    self._settings = None

    def read_snapshot(self) -> DeviceSnapshot:
        with self._lock:
            return self._read_snapshot_unlocked()

    def set_current(self, value_ma: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.current_set.set(float(value_ma))
            return self._read_snapshot_unlocked()

    def set_current_clip(self, value_ma: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.current_clip.set(float(value_ma))
            return self._read_snapshot_unlocked()

    def set_cc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_feedforward_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.feedforward_enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_feedforward_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            cc = self._cc()
            cc.feedforward_factor.set(float(value))
            return self._read_snapshot_unlocked()

    def set_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_unlocked()

    def set_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._cc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_unlocked()

    def set_tc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            tc = self._tc()
            tc.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_temp_set(self, value_c: float) -> DeviceSnapshot:
        with self._lock:
            tc = self._tc()
            tc.temp_set.set(float(value_c))
            return self._read_snapshot_unlocked()

    def set_tc_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_tc_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_unlocked()

    def set_tc_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._tc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_unlocked()

    def set_pc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            pc = self._pc()
            pc.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_pc_voltage_set(self, value_v: float) -> DeviceSnapshot:
        with self._lock:
            pc = self._pc()
            pc.voltage_set.set(float(value_v))
            return self._read_snapshot_unlocked()

    def set_pc_slew_rate_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            output_filter = self._pc().output_filter
            output_filter.slew_rate_enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_pc_slew_rate(self, value: float) -> DeviceSnapshot:
        with self._lock:
            output_filter = self._pc().output_filter
            output_filter.slew_rate.set(float(value))
            return self._read_snapshot_unlocked()

    def set_pc_arc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_pc_arc_signal(self, signal: int) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.signal.set(int(signal))
            return self._read_snapshot_unlocked()

    def set_pc_arc_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            ext = self._pc().external_input
            ext.factor.set(float(value))
            return self._read_snapshot_unlocked()

    def set_pressure_comp_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            pressure_comp = self._pressure_comp()
            pressure_comp.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_pressure_comp_factor(self, value: float) -> DeviceSnapshot:
        with self._lock:
            pressure_comp = self._pressure_comp()
            pressure_comp.factor.set(float(value))
            return self._read_snapshot_unlocked()

    def set_sc_enabled(self, enabled: bool) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.enabled.set(bool(enabled))
            return self._read_snapshot_unlocked()

    def set_sc_amplitude(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.amplitude.set(float(value))
            return self._read_snapshot_unlocked()

    def set_sc_offset(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.offset.set(float(value))
            return self._read_snapshot_unlocked()

    def set_sc_output_channel(self, value: int) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.output_channel.set(int(value))
            return self._read_snapshot_unlocked()

    def set_sc_frequency(self, value: float) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.frequency.set(float(value))
            return self._read_snapshot_unlocked()

    def set_sc_signal_type(self, value: int) -> DeviceSnapshot:
        with self._lock:
            scan = self._scan()
            scan.signal_type.set(int(value))
            return self._read_snapshot_unlocked()

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
            return f"Device not found / 未找到设备: {exc}"
        if isinstance(exc, DecopError):
            return f"Device rejected request / 设备拒绝请求: {exc}"
        if isinstance(exc, TimeoutError):
            return f"Timeout / 超时: {exc}"
        return f"{type(exc).__name__}: {exc}"

    def _build_connection(self, settings: ConnectionSettings):
        if settings.mode == "network":
            return NetworkConnection(settings.target, timeout=settings.timeout)
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
        return DeviceSnapshot(
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
            pressure_comp_enabled=bool(pressure_comp.enabled.get()),
            pressure_comp_air_pressure=float(pressure_comp.air_pressure.get()),
            pressure_comp_factor=float(pressure_comp.factor.get()),
            pressure_comp_voltage=float(pressure_comp.compensation_voltage.get()),
        )

    @staticmethod
    def _compute_effective_current_max(cc) -> float:
        current_clip = float(cc.current_clip.get())
        current_clip_limit = float(cc.current_clip_limit.get())
        use_tuning_clip = bool(cc.use_current_clip_tuning.get())
        if use_tuning_clip:
            current_clip_tuning = float(cc.current_clip_tuning.get())
            return min(current_clip, current_clip_tuning, current_clip_limit)
        return min(current_clip, current_clip_limit)
