from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from one_click_lock_app.models import (
    DlcSnapshot,
    FalcSnapshot,
    LaserSetSnapshot,
    LockInSnapshot,
    LockSettingsSnapshot,
    PidSnapshot,
    ScanSnapshot,
)


PC_VOLTAGE = 50
TRIANGLE = 1


class DlcproService:
    def __init__(self) -> None:
        self.dlc: Any | None = None
        self.connection_label: str | None = None
        self.sdk_module_path: str | None = None

    def connect_network(
        self,
        host: str,
        command_line_port: int = 1998,
        monitoring_line_port: int = 1999,
        timeout_s: float = 5.0,
    ) -> str:
        import toptica.lasersdk.dlcpro.v3_3_3 as sdk

        self.close()
        self.sdk_module_path = str(Path(sdk.__file__).resolve())
        self.dlc = sdk.DLCpro(
            sdk.NetworkConnection(
                host.strip(),
                command_line_port=command_line_port,
                monitoring_line_port=monitoring_line_port,
                timeout=timeout_s,
            )
        )
        self.dlc.open()
        self.connection_label = f"LAN {host.strip()}:{command_line_port}/{monitoring_line_port}"
        return self.identify()

    def connect_serial(self, port: str, baudrate: int = 115200, timeout_s: float = 5.0) -> str:
        import toptica.lasersdk.dlcpro.v3_3_3 as sdk

        self.close()
        self.sdk_module_path = str(Path(sdk.__file__).resolve())
        self.dlc = sdk.DLCpro(sdk.SerialConnection(port.strip(), baudrate=baudrate, timeout=timeout_s))
        self.dlc.open()
        self.connection_label = f"USB/Serial {port.strip()} @ {baudrate}"
        return self.identify()

    def close(self) -> None:
        if self.dlc is not None:
            try:
                self.dlc.close()
            finally:
                self.dlc = None
                self.connection_label = None

    def require_connected(self):
        if self.dlc is None:
            raise RuntimeError("DLC pro is not connected.")
        return self.dlc

    def _try_get(self, dotted_path: str, warnings: list[str]) -> Any | None:
        try:
            node = self.require_connected()
            for part in dotted_path.split("."):
                node = getattr(node, part)
            return node.get()
        except Exception as exc:
            warnings.append(f"{dotted_path}: {exc}")
            return None

    def _try_set(self, dotted_path: str, value: Any) -> None:
        node = self.require_connected()
        for part in dotted_path.split("."):
            node = getattr(node, part)
        node.set(value)

    def identify(self) -> str:
        warnings: list[str] = []
        label = self._try_get("system_label", warnings)
        serial = self._try_get("serial_number", warnings)
        firmware = self._try_get("fw_ver", warnings)
        parts = [str(x) for x in (label, serial, firmware) if x not in (None, "")]
        return " | ".join(parts) if parts else (self.connection_label or "DLC pro connected")

    def read_snapshot(self, falc_index: int = 1) -> DlcSnapshot:
        warnings: list[str] = []
        scan = ScanSnapshot(
            enabled=self._try_get("laser1.scan.enabled", warnings),
            hold=self._try_get("laser1.scan.hold", warnings),
            frequency_hz=self._try_get("laser1.scan.frequency", warnings),
            output_channel=self._try_get("laser1.scan.output_channel", warnings),
            signal_type=self._try_get("laser1.scan.signal_type", warnings),
            offset_v=self._try_get("laser1.scan.offset", warnings),
            amplitude_vpp=self._try_get("laser1.scan.amplitude", warnings),
            start_v=self._try_get("laser1.scan.start", warnings),
            end_v=self._try_get("laser1.scan.end", warnings),
            unit=self._try_get("laser1.scan.unit", warnings),
        )
        lock_settings = LockSettingsSnapshot(
            enabled=self._try_get("laser1.dl.lock.lock_enabled", warnings),
            hold=self._try_get("laser1.dl.lock.hold", warnings),
            spectrum_input_channel=self._try_get("laser1.dl.lock.spectrum_input_channel", warnings),
            lock_type=self._try_get("laser1.dl.lock.type", warnings),
            error_channel=self._try_get("laser1.dl.lock.error_channel", warnings),
            error_channel_inverted=self._try_get("laser1.dl.lock.error_channel_inverted", warnings),
            pid_selection=self._try_get("laser1.dl.lock.pid_selection", warnings),
            lock_without_lockpoint=self._try_get("laser1.dl.lock.lock_without_lockpoint", warnings),
            setpoint_v=self._try_get("laser1.dl.lock.setpoint", warnings),
            state_text=self._try_get("laser1.dl.lock.state_txt", warnings),
        )
        pid1 = self.read_pid_snapshot(1, warnings)
        pid2 = self.read_pid_snapshot(2, warnings)
        lockin = LockInSnapshot(
            modulation_enabled=self._try_get("laser1.dl.lock.lockin.modulation_enabled", warnings),
            input_channel=self._try_get("laser1.dl.lock.lockin.input_channel", warnings),
            modulation_output_channel=self._try_get("laser1.dl.lock.lockin.modulation_output_channel", warnings),
            frequency_hz=self._try_get("laser1.dl.lock.lockin.frequency", warnings),
            amplitude=self._try_get("laser1.dl.lock.lockin.amplitude", warnings),
            phase_shift_deg=self._try_get("laser1.dl.lock.lockin.phase_shift", warnings),
            lock_level_v=self._try_get("laser1.dl.lock.lockin.lock_level", warnings),
        )
        laser_set = LaserSetSnapshot(
            cc_current_ma=self._try_get("laser1.dl.cc.current_set", warnings),
            pc_voltage_v=self._try_get("laser1.dl.pc.voltage_set", warnings),
            tc_temperature_c=self._try_get("laser1.dl.tc.temp_set", warnings),
        )
        falc = self.read_falc_snapshot(falc_index)
        return DlcSnapshot(
            connected=self.dlc is not None,
            system_label=self._try_get("system_label", warnings),
            serial_number=self._try_get("serial_number", warnings),
            firmware=self._try_get("fw_ver", warnings),
            health_text=self._try_get("system_health_txt", warnings),
            emission=self._try_get("emission", warnings),
            interlock_open=self._try_get("interlock_open", warnings),
            laser_enabled=self._try_get("laser1.enabled", warnings),
            laser_emission=self._try_get("laser1.emission", warnings),
            lock_enabled=self._try_get("laser1.dl.lock.lock_enabled", warnings),
            lock_state_text=self._try_get("laser1.dl.lock.state_txt", warnings),
            scan=scan,
            lock_settings=lock_settings,
            pid1=pid1,
            pid2=pid2,
            lockin=lockin,
            laser_set=laser_set,
            falc=falc,
            warnings=warnings + falc.unavailable,
        )

    def read_pid_snapshot(self, pid_index: int, warnings: list[str]) -> PidSnapshot:
        prefix = f"laser1.dl.lock.pid{pid_index}"
        return PidSnapshot(
            enabled=self._try_get(f"{prefix}.enabled", warnings),
            output_channel=self._try_get(f"{prefix}.output_channel", warnings),
            gain_all=self._try_get(f"{prefix}.gain.all", warnings),
            gain_p=self._try_get(f"{prefix}.gain.p", warnings),
            gain_i=self._try_get(f"{prefix}.gain.i", warnings),
            gain_d=self._try_get(f"{prefix}.gain.d", warnings),
        )

    def read_falc_snapshot(self, falc_index: int = 1) -> FalcSnapshot:
        unavailable: list[str] = []
        prefix = f"falc{falc_index}"
        return FalcSnapshot(
            index=falc_index,
            serial_number=self._try_get(f"{prefix}.serial_number", unavailable),
            path_selection=self._try_get(f"{prefix}.path_selection", unavailable),
            hold_state=self._try_get(f"{prefix}.hold_state", unavailable),
            main_enabled=self._try_get(f"{prefix}.main.enabled", unavailable),
            main_lock_state=self._try_get(f"{prefix}.main.lock_state", unavailable),
            main_gain_db=self._try_get(f"{prefix}.main.gain.all", unavailable),
            unlim_enabled=self._try_get(f"{prefix}.unlim.enabled", unavailable),
            unlim_lock_state=self._try_get(f"{prefix}.unlim.lock_state", unavailable),
            unlim_hold_state=self._try_get(f"{prefix}.unlim.hold_state", unavailable),
            unlim_regulating_state=self._try_get(f"{prefix}.unlim.regulating_state", unavailable),
            unlim_output_range_v=self._try_get(f"{prefix}.unlim.output_range", unavailable),
            unlim_input_offset_mv=self._try_get(f"{prefix}.unlim.input_offset", unavailable),
            unlim_gain=self._try_get(f"{prefix}.unlim.gain", unavailable),
            unavailable=unavailable,
        )

    def configure_scan_for_piezo_triangle(self, frequency_hz: float = 1.0) -> None:
        self._try_set("laser1.scan.output_channel", PC_VOLTAGE)
        self._try_set("laser1.scan.signal_type", TRIANGLE)
        self._try_set("laser1.scan.frequency", frequency_hz)
        self._try_set("laser1.scan.enabled", True)

    def set_scan_settings(
        self,
        enabled: bool,
        hold: bool,
        output_channel: int,
        signal_type: int,
        frequency_hz: float,
        offset_v: float,
        amplitude_vpp: float,
    ) -> None:
        if amplitude_vpp <= 0:
            raise ValueError("Scan Amplitude must be positive.")
        self._try_set("laser1.scan.output_channel", output_channel)
        self._try_set("laser1.scan.signal_type", signal_type)
        self._try_set("laser1.scan.frequency", frequency_hz)
        self._try_set("laser1.scan.offset", offset_v)
        self._try_set("laser1.scan.amplitude", amplitude_vpp)
        self._try_set("laser1.scan.hold", hold)
        self._try_set("laser1.scan.enabled", enabled)

    def set_scan_offset_amplitude(self, offset_v: float, amplitude_vpp: float) -> None:
        if amplitude_vpp <= 0:
            raise ValueError("Scan Amplitude must be positive.")
        self._try_set("laser1.scan.offset", offset_v)
        self._try_set("laser1.scan.amplitude", amplitude_vpp)

    def set_scan_enabled(self, enabled: bool) -> None:
        self._try_set("laser1.scan.enabled", enabled)

    def set_lock_settings(
        self,
        enabled: bool,
        hold: bool,
        spectrum_input_channel: int,
        lock_type: int,
        error_channel: int,
        error_channel_inverted: bool,
        pid_selection: int,
        lock_without_lockpoint: bool,
    ) -> None:
        self._try_set("laser1.dl.lock.spectrum_input_channel", spectrum_input_channel)
        self._try_set("laser1.dl.lock.type", lock_type)
        self._try_set("laser1.dl.lock.error_channel", error_channel)
        self._try_set("laser1.dl.lock.error_channel_inverted", error_channel_inverted)
        self._try_set("laser1.dl.lock.pid_selection", pid_selection)
        self._try_set("laser1.dl.lock.lock_without_lockpoint", lock_without_lockpoint)
        self._try_set("laser1.dl.lock.hold", hold)
        self._try_set("laser1.dl.lock.lock_enabled", enabled)

    def set_pid_gains(self, pid_index: int, gain_all: float, gain_p: float, gain_i: float, gain_d: float) -> None:
        prefix = f"laser1.dl.lock.pid{pid_index}.gain"
        self._try_set(f"{prefix}.all", gain_all)
        self._try_set(f"{prefix}.p", gain_p)
        self._try_set(f"{prefix}.i", gain_i)
        self._try_set(f"{prefix}.d", gain_d)

    def set_lockin_settings(self, enabled: bool, frequency_hz: float, amplitude: float) -> None:
        self._try_set("laser1.dl.lock.lockin.frequency", frequency_hz)
        self._try_set("laser1.dl.lock.lockin.amplitude", amplitude)
        self._try_set("laser1.dl.lock.lockin.modulation_enabled", enabled)

    def set_laser_setpoints(self, cc_current_ma: float, pc_voltage_v: float, tc_temperature_c: float) -> None:
        self._try_set("laser1.dl.cc.current_set", cc_current_ma)
        self._try_set("laser1.dl.pc.voltage_set", pc_voltage_v)
        self._try_set("laser1.dl.tc.temp_set", tc_temperature_c)

    def set_falc_paths_enabled(self, falc_index: int, main_enabled: bool, unlim_enabled: bool) -> FalcSnapshot:
        prefix = f"falc{falc_index}"
        self._try_set(f"{prefix}.main.enabled", main_enabled)
        self._try_set(f"{prefix}.unlim.enabled", unlim_enabled)
        return self.read_falc_snapshot(falc_index)

    def set_lock_enabled(self, enabled: bool) -> None:
        self._try_set("laser1.dl.lock.lock_enabled", enabled)


def snapshot_with_falc(snapshot: DlcSnapshot, falc: FalcSnapshot) -> DlcSnapshot:
    return replace(snapshot, falc=falc)
