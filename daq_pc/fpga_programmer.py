"""Background Vivado batch programmer used by the ADC GUI."""
from __future__ import annotations

import locale
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal


KNOWN_VIVADO_BATCHES = (
    Path(r"C:\baidunetdiskdownload\Vivado2020_2\Vivado\2020.2\bin\vivado.bat"),
)

PROGRESS_MESSAGES = {
    "STARTING_HW_SERVER": "正在启动 Vivado 硬件服务",
    "SCANNING_JTAG": "正在扫描 JTAG 设备",
    "LOADED_PROBES": "已加载同名 ILA 探针文件",
    "READY_BITSTREAM": "已准备好 bitstream",
    "PROGRAMMING_FPGA": "正在配置 FPGA",
    "PROGRAM_COMPLETE": "FPGA 下载完成",
}


def find_vivado_batch() -> Path | None:
    """Find an installed Vivado launcher without opening its GUI."""
    xilinx_root = os.environ.get("XILINX_VIVADO")
    candidates = []
    if xilinx_root:
        candidates.append(Path(xilinx_root) / "bin" / "vivado.bat")
    discovered = shutil.which("vivado.bat") or shutil.which("vivado")
    if discovered:
        candidates.append(Path(discovered))
    candidates.extend(KNOWN_VIVADO_BATCHES)
    return next((path.resolve() for path in candidates if path.is_file()), None)


def vivado_batch_command(vivado: Path, script: Path,
                         bitstream: Path) -> list[str]:
    """Build a hidden cmd.exe command that preserves paths containing spaces."""
    arguments = [
        str(vivado), "-mode", "batch", "-nolog", "-nojournal",
        "-notrace", "-source", str(script), "-tclargs", str(bitstream),
    ]
    command_line = subprocess.list2cmdline(arguments)
    return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c",
            command_line]


def friendly_program_error(lines: list[str], return_code: int) -> str:
    """Translate stable Tcl error markers into actionable user messages."""
    detail = "\n".join(lines[-20:])
    if "NO_ZYNQ_DEVICE" in detail:
        return (
            "JTAG 未检测到 Zynq-7000，未执行下载。\n"
            "请确认开发板已上电、USB-JTAG 线已连接，并检查驱动后重试。"
        )
    if "MULTIPLE_ZYNQ_DEVICES" in detail:
        return "JTAG 链中检测到多个 Zynq-7000，无法安全自动选择目标器件。"
    if "JTAG_TARGET_OPEN_FAILED" in detail:
        return (
            "JTAG 连接失败，未发现可打开的硬件目标。\n"
            "请确认开发板已上电、USB-JTAG 线已连接，并检查驱动后重试。"
        )
    if "HW_SERVER_CONNECT_FAILED" in detail:
        return (
            "无法连接本机 Vivado 硬件服务器。\n"
            "程序会自动连接 localhost:3121；请稍后重试，或结束残留的 "
            "hw_server 进程后再试。"
        )
    return detail or f"Vivado 批处理退出码：{return_code}"


class FpgaProgrammer(QThread):
    progress = Signal(int, str)
    output = Signal(str)
    program_succeeded = Signal(str)
    program_failed = Signal(str)

    def __init__(self, vivado: Path, script: Path, bitstream: Path,
                 parent=None):
        super().__init__(parent)
        self.vivado = Path(vivado)
        self.script = Path(script)
        self.bitstream = Path(bitstream)
        self._process: subprocess.Popen | None = None
        self._process_lock = threading.Lock()

    def run(self) -> None:
        lines: list[str] = []
        saw_success = False
        work_dir = Path(tempfile.mkdtemp(prefix="zynq_fpga_program_"))
        try:
            kwargs = {
                "cwd": str(work_dir),
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                # Our Tcl protocol is ASCII. The locale decoder also keeps
                # normal Vivado diagnostics readable on Chinese Windows.
                "encoding": locale.getpreferredencoding(False) or "utf-8",
                "errors": "replace",
                "bufsize": 1,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            command = vivado_batch_command(
                self.vivado, self.script, self.bitstream
            )
            with self._process_lock:
                self._process = subprocess.Popen(command, **kwargs)
            assert self._process.stdout is not None
            for raw_line in self._process.stdout:
                line = raw_line.rstrip()
                if not line:
                    continue
                lines.append(line)
                lines = lines[-80:]
                self.output.emit(line)
                if line.startswith("FPGA_PROGRAM_PROGRESS:"):
                    _, value, message_id = line.split(":", 2)
                    progress_value = max(0, min(100, int(value)))
                    saw_success = saw_success or progress_value == 100
                    message = PROGRESS_MESSAGES.get(message_id, message_id)
                    self.progress.emit(progress_value, message)
                if self.isInterruptionRequested():
                    break
            return_code = self._process.wait()
            self._process.stdout.close()
            if self.isInterruptionRequested():
                self.program_failed.emit("FPGA 下载已取消")
            elif return_code == 0 and saw_success:
                self.program_succeeded.emit(str(self.bitstream))
            else:
                self.program_failed.emit(friendly_program_error(lines, return_code))
        except Exception as exc:
            self.program_failed.emit(str(exc))
        finally:
            with self._process_lock:
                self._process = None
            # Vivado can leave a helper briefly holding its working directory.
            # Cleanup failure must not replace the real JTAG result with the
            # misleading WinError 32 that the user previously saw.
            shutil.rmtree(work_dir, ignore_errors=True)

    def cancel(self) -> None:
        self.requestInterruption()
        with self._process_lock:
            process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
