# 项目目录说明

## 运行核心

| 路径 | 用途 |
|---|---|
| `app.py` | 主窗口、导航、共享 DLC pro 服务和 ADC 窗口入口 |
| `dlcpro_service.py` | 官方 SDK 连接、快照读取和参数写入 |
| `device_task_coordinator.py` | 设备任务串行化与线程协调 |
| `controllers/` | Laser、Scan&Lock、FALC、Relock 等主流程 |
| `windows/` | DLC pro 功能独立窗口 |
| `widgets/` | 功能面板和复用控件 |
| `daq_pc/` | PL UDP 接收、示波器、HDF5、JTAG 下载、ADC 两级自动找峰与锁定 |

## 验证与资料

| 路径 | 用途 |
|---|---|
| `tests/` | DLC pro 主程序测试 |
| `daq_pc/tests/` | ADC、协议、录制、自动找峰和 GUI 测试 |
| `docs/` | 当前操作、结构、打包和专题文档 |
| `reports/` | 当前算法报告和验证输出 |
| `Manual.md` | TOPTICA 设备手册镜像，设备行为与安全依据 |
| `python-lasersdk/` | TOPTICA Python SDK 官方文档镜像 |
| `skills/` | Codex 项目开发规则，不参与运行 |

## 硬件与历史

| 路径 | 用途 |
|---|---|
| `tools/` | FPGA下载Tcl、硬件辅助RTL/Tcl；打包时只带下载Tcl |
| `work_ad9269_linux/` | PS/Linux DMA驱动、用户态示例和帧格式 |
| `archive/fpga_history/` | 旧FPGA交付、RGMII/阶段1/2实验与回退资料 |
| `archive/non_project_simulations/` | 与当前产品无关但保留追溯的仿真 |
| `archive/generated_legacy_2026-08-05/` | 整理前的旧 build/dist 和缓存 |
| `archive/development_previews/` | 旧UI截图、PDF页面提取和预览配置 |

`archive/` 只读追溯，不应被运行代码导入，也不进入发布 ZIP。

ADC 自动锁定的当前核心文件：

| 路径 | 用途 |
|---|---|
| `daq_pc/adc_peak_balance_algorithm.py` | 跨周期峰族识别、宽扫理论居中、最终定向粗/精调状态机 |
| `daq_pc/adc_peak_balance_controller.py` | DLC pro写入与读回、稳定周期、四类CSV日志、FALC接管 |
| `daq_pc/adc_peak_balance_window.py` | 自动锁定独立窗口、21项参数、旧QSettings迁移与状态显示 |
| `reports/adc_peak_balance/ALGORITHM_REPORT.md` | 当前算法规格与现场验证要求 |

## 窗口生命周期

- 主 DLC pro 功能页使用独立 `QMainWindow`。
- ADC 主界面由主程序共享同一个 DLC pro service。
- ADC 通道 A/B、扫频控制、ADC 自动锁频是无 QWidget 父窗口的独立顶层窗口，因此主 ADC 窗口最小化不会连带它们。
- 主程序退出时仍通过保存的强引用显式关闭所有顶层窗口和后台线程。
