# 发布验证记录 2026-08-05

## 产物

- 发布目录：`release/DLCProControl_2026-08-05/`
- ZIP：`release/DLCProControl_2026-08-05.zip`
- ZIP大小：204.36 MiB
- ZIP SHA-256：`7819236A7C6C1B78BA85A05BC0A075191CFD8B3B38BD7AA8C27AA8B07E2D8BDB`

发布目录内含236个受清单管理的文件；逐项重新计算 SHA-256 后全部匹配 `SHA256SUMS.txt`。

## 自动验证

```text
python -m pytest tests daq_pc/tests -q
124 passed
```

已验证：

- 当前PLDQ/DAQS/DAQD协议测试；
- DLC pro服务和快照写入；
- ADC GUI、HDF5、FPGA下载逻辑；
- ADC 00模峰识别、方向反转、边界/歧义恢复和FALC顺序；
- 独立窗口无Qt父窗口，主ADC窗口最小化不会连带最小化；
- PyInstaller EXE短时启动后保持运行，无启动即崩溃；
- `_internal/tools/program_fpga_bit.tcl`和默认算法预设已包含。

## 构建说明

- Python 3.13.9
- PyInstaller 6.20.0
- GUI绑定仅包含PySide6；显式排除环境中的PyQt5/PyQt6和开发工具包。
- PyInstaller报告缺少若干Anaconda oneAPI/MPI可选DLL；本软件不使用这些后端，且EXE启动冒烟测试通过。
- Qt官方翻译包未收集；项目用户文本由自身中英文资源提供。

## 仍需现场验证

- DLC pro真实网络/串口连接；
- 10/20 MSPS持续采集、HDF5磁盘吞吐和网线恢复；
- Vivado USB-JTAG真实下载；
- 有人监护下的Scan自动开启、00模缩幅和FALC接管。
