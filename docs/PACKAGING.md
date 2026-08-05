# Windows 打包与发布

## 环境

- Windows 10/11 x64
- Python `>=3.13,<3.14`
- `pip install -e ".[dev]"`
- PyInstaller `>=6.20,<7`

## 构建

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

脚本会：

1. 运行 `tests` 与 `daq_pc/tests`；
2. 按 `DLCProControl.spec` 构建 GUI 程序；
3. 将可执行目录和用户文档复制到日期版本发布目录；
4. 生成 SHA-256 清单；
5. 生成 ZIP。

默认输出：

```text
release/DLCProControl_2026-08-05/
release/DLCProControl_2026-08-05.zip
```

## 打包内容

- `DLCProControl/`：可执行程序和 PyInstaller 依赖；
- `docs/`：操作指南、发布说明和算法报告；
- `README.txt`：最短启动说明；
- `SHA256SUMS.txt`：发布目录所有文件的 SHA-256。

默认算法预设 `auto_lock_algorithm_presets.json` 和 FPGA 下载脚本 `tools/program_fpga_bit.tcl` 会作为运行资源打入 `_internal`。

## 不打包内容

- `archive/`、测试、SDK文档镜像和开发 skill；
- Vivado 安装本体；
- bitstream、ILA `.ltx` 和用户 HDF5 数据；
- DLC pro IP、串口和实验参数等本机配置。

用户配置写入 `%APPDATA%\DLCProControl` 或 Qt 的用户配置区域，不应放进发布 ZIP。

## 发布前人工检查

1. 在一台未打开 Python IDE 的 Windows 机器启动 EXE。
2. 确认网络和串口连接界面可用。
3. 打开 ADC、A/B、扫频控制和自动锁频窗口，验证独立最小化。
4. 用标准 MTU 做 10 MSPS 采集和短时 HDF5 录制。
5. 若交付 FPGA 下载，接 JTAG 验证 batch 下载进度和错误提示。
6. 仅在安全实验条件下验证 Scan/FALC 接管。
