# DLC pro 一键锁频项目：DAQ 采购与 Zynq-7020 AD/DA 方案对比报告

日期：2026-06-11

## 结论

当前阶段建议优先买一块现成 USB DAQ 或 USB 示波器型采集设备，不建议把 Zynq-7020 + AD/DA 模块作为第一条工程主线。

原因很直接：咱们现在要验证的是“一键自动找峰、判断误差信号、通过 DLC pro SDK 调 Scan Offset / Scan Amplitude / FALC”的算法闭环。这个闭环的关键瓶颈不是 FPGA 低延迟，而是稳定、同步、可复现地把两路模拟信号送进 Python。

推荐采购优先级：

1. **首选：NI USB-6211 或同级 NI X/M 系列 USB DAQ**
   - 适合实验室长期使用，Python `nidaqmx` 接入成熟。
   - 有模拟输入和模拟输出，后续如果要输出慢速控制量也有余量。
   - 成本较高，但开发风险最低。

2. **性价比首选：MCC / Measurement Computing USB-1608G 系列，优先带 AO 的型号**
   - 16-bit、多路模拟输入、采样率比低端 DAQ 更宽裕。
   - Python 接入比 NI 稍麻烦，但仍属于标准 DAQ 路线。
   - 如果预算卡得紧，这类很合适。

3. **调试型选择：Digilent Analog Discovery 3 或 PicoScope 2000/3000 系列**
   - 更像“电脑示波器 + 函数发生器”，适合看波形、抓 CSV、快速实验。
   - 如果目标是把 Python GUI 做成正式采集控制软件，DAQ 体验通常比 USB 示波器更直接。

4. **不建议作为第一阶段：Zynq-7020 + AD/DA 模块**
   - 它能做，而且潜力最大。
   - 但它不是采集卡成品，而是要先开发出采集卡：ADC 驱动、FPGA 采样、DMA、ARM 端服务、电脑通信协议、Python 接收、校准、异常处理都要自己做。

一句话：**买 DAQ 是买工具；用 7020 是做工具。**

## 咱们项目真正需要什么

当前一键锁频软件需求：

- 输入两路模拟信号：
  - `transmission`：透射峰信号
  - `error`：PDH/误差信号
- 电脑端 Python GUI 显示两路波形。
- 算法判断：
  - 是否扫到透射峰
  - 误差信号零点是否和峰位置匹配
  - 是否 ready for FALC
  - 锁上后是否失锁
- 通过 DLC pro SDK 控制：
  - `laser1.scan.offset`
  - `laser1.scan.amplitude`
  - `laser1.scan.frequency`
  - `laser1.scan.enabled`
  - FALC 相关状态和使能

这意味着采集设备只需要先做好一件事：**可靠同步采两路电压信号，传给 Python。**

由于扫频频率是 1 Hz，一屏通常看 1 到 2 秒，采样率不需要上 MHz 才能做算法验证。实际建议：

- 最低可用：每路 5 kS/s 到 10 kS/s
- 推荐：每路 20 kS/s 到 100 kS/s
- 理想：两路同步或相位误差可忽略
- 分辨率：至少 12-bit，推荐 16-bit
- 输入范围：至少覆盖探测器输出，例如 ±5 V 或 ±10 V
- 输入保护：最好有明确过压保护；没有就加限幅/串阻/保护电路

## DLC pro 相关约束

根据本地 `Manual.md`：

- DLC pro 的 Scan 功能本质是：**Scan Amplitude 的变量电压叠加到 Scan Offset 的常量电压上**，用于通过 piezo 扫描激光频率。见 `Manual.md:1219`。
- Scan 开启后，即使离开 Scan/Lock 界面也会继续运行，但手册说明 scan 只能在未锁定时开启。见 `Manual.md:1229`。
- DLC pro 前面板有 Fine/Fast BNC 模拟输入：
  - Fine 1/2：24-bit A/D，偏精密
  - Fast 3/4：16-bit A/D，手册列出输入范围 -4 V 到 +4 V、采样率 675 kHz
  - 见 `Manual.md:289-304`
- DLC pro 前面板 Out A/B 是 16-bit D/A 输出，范围 -4 V 到 +4 V，手册列出采样率 2.7 MHz。见 `Manual.md:308-310`。
- DLC pro 的触屏 Scan/Lock 显示最多可显示两路 trace：Input Trace 和 Auxiliary Trace。见 `Manual.md:1215`。
- FALC 1..4 只有在 FALC pro 模块连接时才有对应参数。见 `Manual.md:1197`。
- Lock 相关功能通常需要 Lock option license；PDH 模块本身可独立用于外部控制器，但 Scan & Lock/锁点工具等功能涉及 license。见 `Manual.md:1157`、`Manual.md:1165`、`Manual.md:3849`。

重要判断：

**DLC pro 自己有 A/D 和 D/A，但它不是给电脑 Python 当通用高速采集卡用的。**

它的输入更适合 DLC 内部 Scan/Lock、Power Stabilization、Signal Display、PID/FALC 联动。咱们现在要在电脑 GUI 里实时拿两路完整波形，仍然需要外部 DAQ/USB 示波器，或者自己把 7020 做成采集设备。

## DLC pro SDK 接口现状

本工程当前使用：

```python
from toptica.lasersdk.dlcpro.v3_3_3 import DLCpro, NetworkConnection, SerialConnection
```

SDK 文档说明：

- 网络连接使用 `NetworkConnection(host, command_line_port=1998, monitoring_line_port=1999, timeout=5)`。
- 串口/USB 虚拟串口使用 `SerialConnection(port, baudrate=115200, timeout=5)`。
- 网络连接内部通常维护 command line 和 monitoring line 两条 TCP 连接。

本工程当前服务层已经按这个模型实现，见：

- `one_click_lock_app/services/dlcpro_service.py`

当前软件控制重点：

- `laser1.scan.output_channel = PC Voltage`
- `laser1.scan.signal_type = triangle`
- `laser1.scan.frequency = 1 Hz`
- `laser1.scan.offset`
- `laser1.scan.amplitude`
- `falcX.main.enabled`
- `falcX.unlim.enabled`

## 采集卡选型建议

### 必须满足

- 至少 2 路模拟输入。
- 两路时间对齐足够好，最好支持同步采样；如果是多路复用 ADC，也要保证 1 Hz 扫频下相位误差可以忽略。
- Python API 成熟。
- Windows 下驱动稳定。
- 输入范围覆盖实际信号，建议 ±10 V 档。
- 采样率至少每路 10 kS/s，推荐每路 50 kS/s 以上。
- 支持连续采集或分帧采集。

### 最好满足

- 16-bit 分辨率。
- 有 2 路模拟输出，后续如果想输出慢速偏置、测试波形、模拟控制量会方便。
- 有硬件触发/数字输入，未来可接 DLC pro scan trigger 或 lock status。
- 有官方 Python 支持或成熟第三方库。

## 推荐型号对比

| 型号方向 | 适合程度 | 优点 | 风险/缺点 |
|---|---:|---|---|
| NI USB-6211 / 同级 NI USB DAQ | 最高 | 驱动和 Python 生态成熟，适合正式工程，AI/AO/DIO 都有 | 贵，采购周期可能长 |
| NI USB-6002/6003 | 中高 | 成本低，入门简单，1 Hz 扫频算法验证够用 | 采样率和通道性能余量较小 |
| MCC USB-1608G / USB-1608GX-2AO | 高 | 性价比高，16-bit，采样余量比低端 DAQ 好 | Python/驱动体验通常不如 NI 顺滑 |
| Digilent Analog Discovery 3 | 中高 | 两路示波器输入 + 波形输出，调试非常方便，采样率高 | 更像调试仪器，不是传统 DAQ；正式连续采集架构要评估 WaveForms SDK |
| PicoScope 2000/3000 系列 | 中 | PC 示波器体验好，有 SDK，适合看波形和抓数据 | 控制软件和 DAQ 流程不如 NI/MCC 直接；型号差异大 |
| Zynq-7020 + AD/DA | 当前阶段低，长期潜力高 | 可做低延迟闭环、FPGA 实时处理、定制协议 | 开发量最大，调试周期不可控 |

### 我的采购建议

如果实验室能接受价格：

**买 NI USB-6211 或同等级 NI USB DAQ。**

如果预算有限：

**买 MCC USB-1608G 系列，优先选带 2 路 AO 的版本。**

如果只是想先用电脑看波形、快速验证算法：

**Digilent Analog Discovery 3 可以考虑。**

但如果目标是咱们这个 PySide6 一键锁频软件长期维护，我更偏向 NI/MCC 这种 DAQ，而不是 USB 示波器型产品。

## Zynq-7020 + AD/DA 方案开发难度

7020 能不能用？能。

但要看“组里已经有什么”。

### 如果已有完整工程

如果已有：

- ADC 双通道采样 demo
- DAC 输出 demo
- DMA 到 DDR
- ARM/Linux 或裸机端能拿到数据
- 网口/USB 能把数据发给电脑
- Python 端已有接收 demo

那可以作为临时采集设备试一试。预计：

- 接入 Python GUI：1 到 2 周
- 做稳定分帧、时间戳、异常恢复：2 到 4 周
- 做成可靠实验工具：1 个月以上

### 如果只有板子和模块

那开发内容包括：

- 确认 ADC/DAC 芯片型号和接口：SPI、LVDS、CMOS、FMC、自定义排线等
- FPGA 端采样时钟、同步、FIFO、DMA
- ARM 端驱动或裸机程序
- 电脑通信协议：TCP/UDP/USB/UART
- Python 接收、解包、缓存、丢包处理
- 电压量程标定
- 输入保护和接地噪声处理
- DAC 输出限幅，避免误伤 DLC pro/PZT/FALC
- GUI 集成和长期稳定性测试

预计时间：

- 第一帧数据到 Python：2 到 4 周
- 稳定两路连续采集：1 到 2 个月
- 加 DAC 输出和安全保护：再加 2 到 4 周
- 真正能替代 DAQ：更久

### FPGA 的优势什么时候值得

如果未来目标变成：

- MHz 级实时反馈
- 电脑不参与闭环
- FPGA 直接根据 error 输出 DAC 反馈
- 自己做 FALC 类似的高速控制器

那 7020 很有价值。

arXiv 上有类似 FPGA 实验控制系统案例，使用多路 100 MS/s AD/DA、低延迟 PID 和激光锁定应用，说明 FPGA 在高速伺服上是正路，但它对应的是完整控制系统开发，不是“插上就采集”。参考：[A many-channel FPGA control system](https://arxiv.org/abs/2307.16008)。

## DAQ 与 7020 的工程量对比

| 项目 | 现成 DAQ | Zynq-7020 + AD/DA |
|---|---|---|
| 第一次读到两路波形 | 半天到 2 天 | 1 到 4 周，看现成工程 |
| Python GUI 接入 | 简单 | 中到难 |
| 通道同步 | 厂家处理 | 自己保证 |
| 采样率/量程标定 | 厂家规格和驱动 | 自己校准 |
| 连续采集缓存 | 驱动提供 | 自己写 DMA/缓冲/协议 |
| 异常处理 | 驱动/API 较成熟 | 自己处理断连、丢包、溢出 |
| 低延迟闭环 | 一般，不适合高速反馈 | 强项 |
| 采购成本 | 高 | 板子已有则硬件成本低 |
| 人力成本 | 低 | 高 |
| 适合当前一键锁频阶段 | 很适合 | 不适合作为主线 |
| 适合未来自研控制器 | 一般 | 很适合 |

## 关键工程风险

### 1. 输入电压范围

DLC pro 前面板 Fast 输入是 -4 V 到 +4 V，Out A/B 也是 -4 V 到 +4 V。外部 DAQ 或 7020 AD 输入也必须确认范围。

光电探测器输出如果可能超过采集范围，需要：

- 分压
- 限幅
- 串联电阻
- TVS/钳位
- 隔离或差分输入

### 2. 接地和噪声

PDH error 信号通常比较敏感。DAQ/7020/示波器/探测器/DLC pro 之间地线处理不好，会直接污染误差信号。

建议第一阶段只采集，不输出反馈；输出控制仍通过 DLC pro SDK。

### 3. Python 不做高速闭环

Python GUI 适合：

- 慢速找峰
- 判断锁点
- 调 Scan Offset/Amplitude
- 使能 FALC
- 监测是否失锁

Python 不适合做：

- MHz 级 PDH 反馈
- 高速 PID
- 直接替代 FALC

高速闭环应该交给 FALC/DLC pro 或 FPGA。

### 4. 采集率不等于有效带宽

买 DAQ 或用 7020 都要看：

- ADC 分辨率
- ENOB
- 模拟前端带宽
- 输入噪声
- 采样时钟抖动
- 是否同步采样
- 驱动能不能连续稳定吐数据

不要只看“最高采样率”。

## 对当前软件的接入路线

### 用现成 DAQ

软件新增一个采集服务：

```text
one_click_lock_app/services/daq_service.py
```

输出统一数据结构：

```python
SignalFrame(
    time_s,
    transmission_v,
    error_v,
    csv_path=None
)
```

这样现有算法不用大改，只把数据源从：

```text
CSV / MSO64B
```

扩展为：

```text
CSV / MSO64B / DAQ
```

### 用 7020

建议把 7020 也伪装成同样的数据源：

```text
7020 TCP server -> Python client -> SignalFrame
```

Python 不应该关心底层是 NI、MCC、示波器还是 7020。只要拿到：

```text
time, transmission, error
```

算法层就能复用。

## 最终建议

如果目标是尽快把一键锁频软件跑到真实设备上：

**买 DAQ。**

如果老师/师兄坚持用 7020：

先让他们给出这几个信息：

1. AD 芯片型号、分辨率、最高采样率、输入电压范围。
2. DA 芯片型号、输出范围、更新率。
3. 是否已有两路 ADC 同步采集工程。
4. 是否已有 DMA/网口/USB 数据传输工程。
5. 电脑端是否已有 Python 接收 demo。
6. 模拟输入是否有保护电路。
7. DAC 输出是否有硬件限幅，防止误输出。

如果这些都有，7020 可以试。

如果没有，那它不是“凑合一下”，而是一个新的硬件/FPGA/嵌入式开发项目。

我的工程判断：

**当前买 DAQ 最划算，7020 留作后续高速控制器或备份采集平台。**

## 资料依据

- 本地 DLC pro 手册：`Manual.md`
  - Scan Offset / Scan Amplitude：`Manual.md:1219`
  - Scan 使能限制：`Manual.md:1229`
  - Fine/Fast BNC 输入和 Out A/B 输出：`Manual.md:289-310`
  - 两路 trace 显示：`Manual.md:1215`
  - Lock/FALC/PDH license 相关：`Manual.md:1157`、`Manual.md:1165`、`Manual.md:3849`
- 本地 SDK 文档：`python-lasersdk/_sources/getting_connected.rst.txt`
  - `NetworkConnection` 默认 command line port 1998、monitoring line port 1999
  - `SerialConnection` 默认 115200 baud
- 本工程 SDK 接入：`one_click_lock_app/services/dlcpro_service.py`
- FPGA 控制系统参考：[A many-channel FPGA control system](https://arxiv.org/abs/2307.16008)
- USB 示波器/PC scope 软件生态参考：[PicoScope software](https://en.wikipedia.org/wiki/PicoScope_%28software%29)
