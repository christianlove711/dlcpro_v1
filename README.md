# DLC pro 与 Zynq-7020 AD9269 联合控制采集软件

这是面向实验室使用的 Windows 桌面软件，统一提供：

- TOPTICA DLC pro 3.3.3 网络/串口连接与参数控制；
- Laser、Scan&Lock、FALC、Relock、Stabilization 独立控制窗口；
- Zynq-7020 + AD9269 双通道 PL UDP 实时采集；
- 通道 A/B 独立示波器、HDF5 录制和后台 FPGA JTAG 下载；
- 基于 AD9269 原始码的 00 模自动居中、阶梯缩幅和 FALC 接管。

设备编程接口以项目内的 TOPTICA 官方 SDK 3.3 文档镜像为依据，设备行为和安全要求以 [Manual.md](Manual.md) 为依据。ADC/FPGA 协议及自动找峰策略属于本项目实现。

## 快速开始

### 运行源码

要求 Windows、Python 3.13 和项目依赖：

```powershell
python -m pip install -e ".[dev]"
python app.py
```

直接打开 ADC 页面：

```powershell
python app.py --open-adc
```

### 运行打包版

打开发布包中的 `DLCProControl.exe`。打包版不需要单独安装 Python。

FPGA 下载功能不启动 Vivado GUI，但本机仍需安装 Vivado 2020.2（或配置 `XILINX_VIVADO`），并连接 USB-JTAG。Bitstream 不内置在软件中，需在 ADC 页面选择经过板测的 `.bit` 文件。

## 网络配置

### DLC pro

- 命令端口：`1998`
- 监控端口：`1999`
- 直连链路本地地址通常为 `169.254.x.x/16`
- 也支持 SDK 的串口连接，默认波特率 `115200`

连接成功但读取某参数返回 `Error -22: no access`，表示设备拒绝访问该节点，并非子网掩码错误。软件连接层同时依赖 `ifaddr`（网卡枚举）和 `pyserial`（串口枚举）。

### PL UDP 采集网口

- FPGA：`192.168.20.2`
- PC 专用网卡：`192.168.20.1/24`
- 控制/状态：UDP `5000`
- 数据：UDP `5001`

PL 协议不响应 ARP/ICMP，`ping` 失败不能单独作为离线判断。20 MSPS 双通道建议使用 Realtek 千兆网卡并启用 9014 Bytes Jumbo Packet；首次排查仍可先用标准 MTU。

## 当前 ADC 功能

- 5/10/20 MSPS 双通道采集，A/B 显示映射与“交换 AD9269 A/B”一致；
- 通道 A、通道 B、扫频控制、ADC 自动锁频均为互不连带最小化的独立顶层窗口；
- 示波器支持原始 ADC 码/电压、独立纵轴、时基、触发、点/连线/min-max 包络显示；
- HDF5 可选择单通道、记录速率、保存路径，以及是否同步保存 DLC pro 扫描参数；
- FPGA 可在后台自动连接本机硬件服务器并下载 `.bit`，无需打开 Vivado GUI；
- ADC 自动锁频只使用透射峰原始码，控制 `Scan Offset` 与 `Scan Amplitude`，达到最终条件后执行 `Scan Off → FALC Main On → FALC Unlim On` 并逐项读回验证。

自动找峰的公式、独立窗口规则、错误方向恢复、候选不唯一恢复和 FALC 接管顺序见 [算法报告](reports/adc_peak_balance/ALGORITHM_REPORT.md)。

## 文档入口

- [操作与部署指南](docs/USER_GUIDE.md)
- [项目目录说明](docs/PROJECT_STRUCTURE.md)
- [打包与发布指南](docs/PACKAGING.md)
- [2026-08-05 发布说明](docs/RELEASE_NOTES_2026-08-05.md)
- [2026-08-05 发布验证记录](reports/RELEASE_VALIDATION_2026-08-05.md)
- [AD9269 PC 端说明](daq_pc/README_AD9269.md)
- [PL UDP 网络与协议说明](daq_pc/README_PL_UDP.md)
- [ADC 00 模自动找峰算法报告](reports/adc_peak_balance/ALGORITHM_REPORT.md)
- [DLC pro 官方设备手册镜像](Manual.md)
- [TOPTICA Python SDK 文档镜像](python-lasersdk/index.html)

## 测试

```powershell
python -m pytest tests daq_pc/tests -q
```

硬件安全、真实网络吞吐、JTAG 下载和最终 FALC 接管仍必须做板级验证；自动化测试不能替代真实设备验收。

## 源码结构

```text
app.py / dlcpro_service.py    主程序与统一设备服务
controllers/                 主 DLC pro 窗口业务控制器
windows/                     主 DLC pro 独立窗口
widgets/                     可复用面板和控件
daq_pc/                      AD9269 PL UDP、示波器、录制、ADC自动找峰
tools/                       FPGA下载Tcl和硬件辅助源码/脚本
tests/ + daq_pc/tests/       自动化测试
docs/                        操作、结构、打包和历史文档
reports/                     算法报告与验证产物
archive/                     旧交付、FPGA阶段资料、旧构建和非项目仿真
python-lasersdk/             官方SDK文档镜像
work_ad9269_linux/           PS/Linux DMA驱动与协议资料
```

`archive/` 不参与程序运行和发布打包，只用于追溯，详见 [archive/README.md](archive/README.md)。
