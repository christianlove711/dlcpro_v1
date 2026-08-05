from pathlib import Path
import unittest

from daq_pc.fpga_programmer import (
    PROGRESS_MESSAGES,
    friendly_program_error,
    vivado_batch_command,
)


class FpgaProgrammerTest(unittest.TestCase):
    def test_progress_protocol_uses_ascii_ids_and_chinese_gui_text(self):
        self.assertEqual(
            PROGRESS_MESSAGES["STARTING_HW_SERVER"],
            "正在启动 Vivado 硬件服务",
        )
        self.assertEqual(
            PROGRESS_MESSAGES["SCANNING_JTAG"], "正在扫描 JTAG 设备"
        )
        self.assertTrue(all(key.isascii() for key in PROGRESS_MESSAGES))

    def test_missing_jtag_device_has_actionable_error(self):
        message = friendly_program_error(
            ["FPGA_PROGRAM_ERROR:NO_ZYNQ_DEVICE"], 1
        )
        self.assertIn("JTAG 未检测到 Zynq-7000", message)
        self.assertIn("USB-JTAG", message)
        self.assertNotIn("WinError 32", message)

    def test_hardware_server_and_target_failures_are_distinguished(self):
        server = friendly_program_error(
            ["FPGA_PROGRAM_ERROR:HW_SERVER_CONNECT_FAILED:refused"], 1
        )
        target = friendly_program_error(
            ["FPGA_PROGRAM_ERROR:JTAG_TARGET_OPEN_FAILED:no targets"], 1
        )
        self.assertIn("硬件服务器", server)
        self.assertIn("JTAG 连接失败", target)

    def test_vivado_command_keeps_batch_mode_and_paths(self):
        command = vivado_batch_command(
            Path(r"C:\Vivado Install\vivado.bat"),
            Path(r"C:\DAQ App\program.tcl"),
            Path(r"D:\bits\top test.bit"),
        )
        joined = " ".join(command)
        self.assertIn("-mode batch", joined)
        self.assertIn("top test.bit", joined)


if __name__ == "__main__":
    unittest.main()
