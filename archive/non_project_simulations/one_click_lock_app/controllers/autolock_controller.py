from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from one_click_lock_app.algorithms.waveform_analysis import analyze_lock_candidate
from one_click_lock_app.models import DlcSnapshot, LockAnalysis, SignalFrame
from one_click_lock_app.services.dlcpro_service import PC_VOLTAGE, TRIANGLE, DlcproService


class AutoLockPhase(str, Enum):
    IDLE = "Idle"
    PREPARE_SCAN = "Prepare scan"
    ANALYZE_FRAME = "Analyze frame"
    READY_FOR_FALC = "Ready for FALC"
    FALC_ENGAGED = "FALC engaged"
    MONITOR_LOCK = "Monitor lock"
    FAULT = "Fault"


@dataclass
class AutoLockState:
    phase: AutoLockPhase = AutoLockPhase.IDLE
    running: bool = False
    stable_ready_frames: int = 0
    last_analysis: LockAnalysis | None = None
    log: list[str] = field(default_factory=list)


class AutoLockController:
    def __init__(self, required_ready_frames: int = 2) -> None:
        self.required_ready_frames = required_ready_frames
        self.state = AutoLockState()

    def start(self) -> AutoLockState:
        self.state = AutoLockState(phase=AutoLockPhase.PREPARE_SCAN, running=True)
        self._log("启动一键锁频：先配置 1 Hz piezo triangle scan，再分析示波器帧")
        return self.state

    def stop(self) -> AutoLockState:
        self._log("停止一键锁频状态机")
        self.state.running = False
        self.state.phase = AutoLockPhase.IDLE
        return self.state

    def prepare_scan(self, dlc: DlcproService, frequency_hz: float = 1.0) -> AutoLockState:
        try:
            dlc.configure_scan_for_piezo_triangle(frequency_hz)
            self.state.phase = AutoLockPhase.ANALYZE_FRAME
            self._log("已设置 Scan Output=PC Voltage, Shape=Triangle, Frequency=1 Hz, Scan enabled")
        except Exception as exc:
            self.state.phase = AutoLockPhase.FAULT
            self.state.running = False
            self._log(f"配置扫描失败：{exc}")
        return self.state

    def evaluate_frame(
        self,
        snapshot: DlcSnapshot,
        frame: SignalFrame,
        allow_falc_enable: bool = False,
        falc_index: int = 1,
        dlc: DlcproService | None = None,
    ) -> AutoLockState:
        analysis = analyze_lock_candidate(frame, snapshot.scan)
        self.state.last_analysis = analysis
        self._log(analysis.message)

        scan_ok = (
            snapshot.scan.output_channel in (PC_VOLTAGE, None)
            and snapshot.scan.signal_type in (TRIANGLE, None)
            and (snapshot.scan.frequency_hz is None or abs(snapshot.scan.frequency_hz - 1.0) < 0.2)
        )
        if not scan_ok:
            self.state.stable_ready_frames = 0
            self._log("扫描设置不是 PC Voltage/Triangle/1 Hz 附近，先不要使能 FALC")
            return self.state

        if analysis.ready_to_lock:
            self.state.stable_ready_frames += 1
            self._log(f"可锁确认帧 {self.state.stable_ready_frames}/{self.required_ready_frames}")
        else:
            self.state.stable_ready_frames = 0
            if analysis.suggested_offset_v is not None:
                self._log(
                    f"建议 Scan Offset -> {analysis.suggested_offset_v:.4f} V, "
                    f"Scan Amplitude -> {analysis.suggested_amplitude_vpp:.4f} Vpp"
                )

        if self.state.stable_ready_frames >= self.required_ready_frames:
            self.state.phase = AutoLockPhase.READY_FOR_FALC
            self._log("连续确认可锁：已进入准备使能 FALC 状态")
            if allow_falc_enable and dlc is not None:
                try:
                    dlc.set_falc_paths_enabled(falc_index, main_enabled=True, unlim_enabled=True)
                    self.state.phase = AutoLockPhase.FALC_ENGAGED
                    self._log(f"已使能 FALC {falc_index} Main + Unlim，进入锁定监测")
                except Exception as exc:
                    self.state.phase = AutoLockPhase.FAULT
                    self.state.running = False
                    self._log(f"FALC 使能失败：{exc}")
        else:
            self.state.phase = AutoLockPhase.ANALYZE_FRAME

        return self.state

    def monitor_snapshot(self, snapshot: DlcSnapshot) -> AutoLockState:
        falc = snapshot.falc
        lock_ok = bool(falc.main_lock_state or falc.unlim_lock_state or snapshot.lock_enabled)
        if lock_ok:
            self.state.phase = AutoLockPhase.MONITOR_LOCK
            self._log("锁定监测：DLC/FALC 状态仍显示锁定")
        else:
            self.state.phase = AutoLockPhase.FAULT
            self.state.running = False
            self._log("锁定监测：未看到锁定状态，判为可能失锁")
        return self.state

    def _log(self, message: str) -> None:
        self.state.log.append(message)
