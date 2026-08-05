# Zynq-7020 AD9269 采集卡 PL 端开发思路、问题复盘与后续优化方案

版本：2026-07-27  
对象：最终 AD9269 单 ADC、PL UDP、Event DMA/HP0、Scope DMA/HP1 工程  
器件：XC7Z020-CLG400-2，Vivado 2020.2

## 1. 文档目的

这份文档不是单纯的“功能说明”，而是对整个 PL 开发过程的技术复盘，回答四个问题：

1. 为什么最终架构这样划分；
2. 每条数据、控制和时钟链路具体如何工作；
3. 开发中出现过什么现象，根因是什么，如何修复；
4. 当前版本还存在哪些工程风险，下一步应按什么优先级优化和验收。

文档依据最终 RTL、XDC、Vivado 报告、Linux 交付接口、PC 程序和实际板级调试记录编写。历史双 ADC 方案仅用于解释设计演进；当前有效 bitstream 已经只保留 AD9269。

## 2. 需求演进与最终决策

### 2.1 初始方案

最初工程需要同时支持：

- AD9280/J25：8 位单通道，用 AD9708 回环临时验证；
- AD9269/J24：16 位双通道交织，作为最终正式 ADC；
- PL 千兆网直接向 PC 发送完整原始数据；
- PL 提取峰特征和局部窗口，经 DMA 写入 PS DDR；
- PL UDP 和 PS/Linux 都可以控制采集。

这种方案适合转接板未到时先打通网络和基本采集，但代价是两套 ADC 前端、两个时钟域、选择器、DAC/ROM、J25 约束和更多调试逻辑同时存在，增加了 LUT、FF、时钟树、复位树和约束复杂度。

### 2.2 最终收敛

AD9269 转接板到货并完成 A/B 两路独立波形验证后，最终工程作出以下收敛：

- 删除 AD9280、AD9708 DAC、正弦 ROM、J25 按键和硬触发；
- J25 全部释放给后续屏幕；
- ADC 固定为 AD9269；
- 保留 `5/10/20/40/80 MSPS`；
- PL UDP 原始监视只允许 `5/10/20 MSPS`；
- `40/80 MSPS` 仅进入 PL 算法和 PS DDR；
- PS 端采用两个独立 DMA：
  - Event DMA0 → HP0；
  - Scope DMA1 → HP1；
- 两种 PS 模式软件互斥，但 DMA、描述符环、中断和 DDR 缓冲区物理独立。

这个收敛减少了不再使用的硬件，消除了 J25 冲突，也让时钟和复位问题更容易被真正解决。

## 3. 最终总体架构

```text
                         ┌──────────────────────────────────┐
AD9269 CLK(U15) ────────→│ ADC转换时钟：80 MHz MMCM+ODDR   │
                         │ 5/10/20/40/80 MSPS               │
                         └──────────────────────────────────┘

AD9269 DCO(T9) ─→ IBUF ─→ BUFIO ─→ IDDR采集D[15:0]/OTR
                        │
                        └→ BUFR ─→ A/B配对 ─→ 34位异步FIFO
                                               │
                                               ▼
                                      100 MHz公共处理域
                                               │
          ┌────────────────────────────────────┼───────────────────────┐
          │                                    │                       │
          ▼                                    ▼                       ▼
 PL UDP原始监视                         峰特征Event路径            Scope捕获路径
 监视异步FIFO                          动态基线/峰检测             双BRAM窗口
 DAQD/DAQS封包                         8320 B EVNT帧              32832 B SCOP帧
 纯PL RGMII                             AXIS → DMA0                AXIS → DMA1
 192.168.20.2                          SG/M_AXI → HP0             SG/M_AXI → HP1
          │                                    │                       │
          ▼                                    └──────────┬────────────┘
         PC                                               ▼
                                                    PS DDR/Linux
```

控制面与数据面分开：

```text
PC ──PLDQ/UDP──→ PL命令解析器 ─┐
                               ├→ daq_acq_manager
PS ──M_AXI_GP0/AXI-Lite───────→│
                               └→ 时钟、FIFO、START/STOP、模式状态
```

AXI-Lite 只传寄存器和命令，不传高速采样数据。高速数据使用 AXI4-Stream 进入 AXI DMA，再由 AXI DMA 的内存映射主口经过 HP0/HP1 写 DDR。

## 4. AD9269 源同步采集思路

### 4.1 为什么必须使用 DCO

AD9269 的双通道复用 CMOS 数据在 DCO 两个边沿上分别对应 A/B 通道。数据与 DCO 同源，最可靠的采集方式是让 DCO 直接驱动 I/O 采样资源，而不是用板上其他时钟“猜”数据何时稳定。

最终引脚关系为：

- FPGA 输出给 ADC 的转换时钟：`U15`；
- ADC 返回 DCO：`T9`，Bank 13 MRCC；
- `D0`：`V5`；
- 其余 D[15:1]、OTR、SPI 按最终 `pin_constraint.xdc`；
- J25 不再有任何有效约束。

### 4.2 FPGA 输入结构

`ad9269_input_frontend.v` 使用：

- `IBUF`：接收 DCO；
- `BUFIO`：驱动 Bank 13 ILOGIC 内的 IDDR；
- `BUFR`：生成同一区域的配对/FIFO写时钟；
- 16 个 `IDDR`：同时捕获数据上升沿和下降沿；
- 1 个 `IDDR`：捕获 OTR 两个边沿；
- A/B 交换寄存器：解决实际转接板边沿映射可能相反的问题。

内部统一样点格式：

```text
sample_pair[15:0]  = A，int16
sample_pair[31:16] = B，int16
sample_otr[0]      = A OTR
sample_otr[1]      = B OTR
```

### 4.3 跨时钟

DCO 域产生的 A/B/OTR 必须作为一个整体跨到 100 MHz 域，因此写入同一个 34 位 `xpm_fifo_async`：

```text
{OTR_B, OTR_A, B[15:0], A[15:0]}
```

这样可以保证 A、B、OTR 和 64 位样点索引不会因为使用多个 FIFO 而相互错位。FIFO 深度为 16384，读侧是 FWFT 模式。

### 4.4 采样率产生

ADC 时钟由一个 80 MHz MMCM 主时钟和一个 ODDR 输出：

- 80 MSPS：ODDR 直接输出 1/0；
- 40/20/10/5 MSPS：80 MHz 域内计数分频，分频电平通过同一个 ODDR 输出。

这比多路 BUFG/BUFGMUX 级联更简单，减少了时钟缓冲拓扑告警。采样率只能在停止状态提交，避免运行时改变多位控制导致毛刺。

## 5. 复位与启动状态机

### 5.1 复位原则

最终采用的原则是：

- 只有板级 `sys_rst_n` 直接进入异步复位端；
- MMCM `locked`、PHY ready 等状态只在相应时钟域内同步判断；
- 异步复位可以立即拉低；
- 释放必须经过多级触发器同步；
- FIFO 在 STOPPED 状态持续保持清空，而不是只给一个很窄的脉冲。

### 5.2 `daq_acq_manager`

统一状态机：

```text
STOPPED → CONFIGURED → ARMING → RUNNING
                       ↘
                        ERROR
```

关键规则：

- 任一控制面的 STOP 都是最高优先级；
- PL UDP 和 PS 同周期 CONFIG 时 PS 优先；
- 配置只允许在 STOPPED/CONFIGURED 状态提交；
- CONFIG+START 同周期时先锁存配置，再进入 ARMING；
- ARMING 等待 SPI 正常、ADC时钟锁定、FIFO复位完成；
- 每次有效 START 增加 `stream_id`；
- RUNNING 时检测采集 FIFO 满或溢出并进入 ERROR；
- 40/80 MSPS 自动禁止 PC 原始监视，但 Event/Scope 仍可工作。

FIFO 复位保持 1024 个 100 MHz 周期，即 10.24 µs。这样即使最低 5 MHz 写时钟，也能观察到足够多的复位边沿并完成 `wr_rst_busy/rd_rst_busy`。

## 6. PL UDP 数据与控制

### 6.1 网络参数

- PL 板卡：`192.168.20.2`；
- PC：`192.168.20.1/24`；
- PS/DLCpro 网络继续使用 `192.168.10.x`；
- 控制/状态端口：5000；
- 原始数据端口：5001。

### 6.2 PLDQ 控制

控制包固定 20 字节，包含：

- `PLDQ` magic；
- 版本和命令；
- `transaction_id`；
- `arg0`；
- `arg1`。

支持 DISCOVER、GET_STATUS、SELECT_ADC、CONFIG_RATE、START、STOP、MONITOR、测试码和清统计。最终硬件仅接受 AD9269；请求 AD9280 或 40/80 MSPS PC 连续监视返回不支持。

### 6.3 原始数据

DAQD 包包含：

- ADC型号和数据格式；
- `stream_id`；
- 包序号；
- 采样率；
- 首样点64位索引；
- 有效载荷长度；
- A/B 小端交织样点。

标准模式有效载荷 1408 B；巨帧模式有效载荷 8192 B。监视 FIFO 满只丢 PC 副本，不向算法路径施加反压，避免 PC 网卡性能影响自动锁频。

20 MSPS 双通道原始有效载荷为：

```text
20,000,000 pair/s × 4 B/pair = 80 MB/s = 640 Mbit/s
```

标准 MTU 在带宽上可行，但包率约 5.7 万包/s，Windows/Python 处理压力较高。巨帧的作用主要是降低包率、CPU中断和协议开销，不参与 PS DDR DMA。

## 7. Event 自动锁频路径

### 7.1 峰检测

峰特征模块使用 A 通道检测峰，B 通道计算误差信号统计。

当前编译期参数：

- 正峰；
- 最小阈值 512；
- 噪声倍率 6；
- 滞回移位 2；
- 最小峰宽 3；
- 最大峰宽 65535；
- 死区 1000 个样点。

动态基线和噪声采用慢速 IIR 更新。进入峰区后冻结基线，避免强透射峰把背景估计拉高。进入阈值为：

```text
max(最小阈值, noise × K)
```

退出阈值更低，形成滞回。模块还计算：

- 基线、峰值、峰峰值、宽度和48位面积；
- 三点抛物线亚采样峰位置；
- 64位峰间隔、间隔均值和方差；
- B通道均值、RMS、峰峰值、过零次数和斜率；
- OTR、削顶和饱和标志；
- 1024个前置和1024个后置 A/B 样点对。

### 7.2 EVNT 帧

每帧固定：

```text
128 B头 + 1024×4 B前窗口 + 1024×4 B后窗口 = 8320 B
```

AXIS 共 2080 个32位 word，最后一个 word 拉高 TLAST。

### 7.3 DMA

- AXI DMA0：`0x40400000`；
- SG描述符：64个；
- 每槽有效 8320 B；
- mmap槽步长：12288 B；
- 数据和SG访问经 HP0；
- 中断：`IRQ_F2P[0]`。

Linux 必须先提交全部描述符，再将 `EVENT_DMA_ARMED` 置1。没有武装时的峰计为 `SUPPRESSED`；只有已经武装但由于反压不能交付的帧才计为 `DROPPED`。

## 8. Scope 普通示波器路径

### 8.1 双 BRAM

Scope 使用两块 8192×32 bit BRAM：

- 一块接收窗口；
- 另一块等待或正在向 DMA 发送；
- 一帧完成后交换。

BRAM 在这里不是用来长期保存数据，而是隔离实时采样和低占空比 DDR 发送。80 MSPS 时仍保留 12.5 ns 原始样点间隔，但只按 10/20 FPS 发送窗口。

### 8.2 功能

- 自由运行；
- A/B通道上升沿或下降沿触发；
- 16位有符号触发电平；
- 25%预触发；
- `1/2/4/.../256` 抽取；
- 默认10 FPS，最高20 FPS。

### 8.3 SCOP 帧和 DMA

```text
64 B头 + 8192×4 B样点 = 32832 B
```

- AXI DMA1：`0x40410000`；
- SG描述符：16个；
- mmap槽步长：36864 B；
- 数据和SG访问经 HP1；
- 中断：`IRQ_F2P[1]`。

10 FPS 平均 DDR 数据量约0.328 MB/s，20 FPS约0.657 MB/s。HP0和HP1是独立AXI端口，但最终共享物理DDR控制器；由于 Scope 和 Event 模式互斥，正常情况下不存在两条采集流争抢DDR的问题。

## 9. AD9269 SPI真实读回

SPI 使用3线 SDIO：

1. 写 `0x14=0x21`；
2. 写 `0x17=0x27`；
3. 写 `0x0D=test_mode`；
4. 写 `0xFF=0x01` 更新；
5. 读芯片ID、速度等级及上述配置寄存器；
6. 验证 ID=`0x75` 和寄存器值；
7. 不匹配时完整重试，最多3次；
8. 三次失败后置 `SPI_ERROR` 并禁止 START。

SPI 只允许在停止状态工作。采集期间 CSB、SCLK、SDIO 保持静止，避免数字串扰进入模拟采样。

## 10. PS/Linux接口

控制寄存器基址为 `0x43C10000`。Linux不需要“拉高一个FPGA外部引脚”，而是按以下顺序写寄存器：

### Event模式

```text
STOP
→ Event armed=0
→ 准备64个SG描述符
→ ACQ_MODE=1 + CONFIG_COMMIT
→ Event armed=1
→ START
→ IRQ/DEQUEUE读取EVNT帧
→ RELEASE归还槽
```

### Scope模式

```text
STOP
→ Scope ABORT并armed=0
→ 准备16个SG描述符
→ ACQ_MODE=0 + Scope配置 + CONFIG_COMMIT
→ Scope armed=1
→ START
→ IRQ/DEQUEUE读取SCOP帧
→ RELEASE归还槽
```

停止顺序必须是：

```text
PL STOP → 解除armed → 终止DMA → 唤醒等待线程
```

这能防止 PL 在 DMA 停止后继续送帧，也能避免用户态永久阻塞。

## 11. 开发问题完整复盘

| 编号 | 现象 | 根因 | 修复 | 验证/当前状态 |
|---:|---|---|---|---|
| 1 | Vivado显示 bitstream complete，但WNS约-115 ns | 64位平方根函数的32次循环被完全展开，形成约427级组合逻辑、374个CARRY4 | 改为32周期迭代平方根；事件特征先锁存，计算完成后再发头 | 最终WNS +0.140 ns |
| 2 | 峰位置和方差仍有长组合路径风险 | 三点插值使用组合除法，宽位乘法/方差同周期完成 | 改迭代有符号除法；平方、方差增加寄存阶段 | `tb_iterative_math`、峰仿真通过 |
| 3 | REQP-1933、LUTAR-1和异步复位告警 | MMCM lock等组合状态直接进入异步复位；时钟缓冲拓扑过于复杂 | 只允许板级复位进入异步端；锁定状态同步采样；单80 MHz BUFG+ODDR | 最终 REQP-1933/LUTAR-1=0 |
| 4 | PL网口插线后PC仍显示电缆拔出 | PHY复位依赖RGMII RXC/MMCM lock，而PHY在复位时不会输出RXC，形成循环依赖 | 用独立50 MHz产生20 ms PHY复位，RXC锁定只控制网络逻辑复位 | PL PHY亮灯并建立链路 |
| 5 | GUI发现板卡超时 | PC曾使用192.168.10.x旧地址；PL实际为192.168.20.2；控制/数据包并存时主机可能读到DAQD | GUI改为192.168.20.2；PC网卡192.168.20.1/24；按magic和transaction过滤DAQS | 发现、状态和START可用 |
| 6 | `SELECT_ADC timed out`或命令无响应 | UDP接收最后一个word与`rec_pkt_done`同周期，旧解析逻辑在最后word尚未锁存时提交 | 命令延后一周期commit，并兼容done提前/延后一拍 | 全部PLDQ和非法包自检通过 |
| 7 | START时报“not a DAQS packet” | 同一个socket可能先收到DAQD，旧PC逻辑把任意UDP包都当状态包 | 只接受DAQS magic、来源地址和当前transaction_id | 控制重试和最终GET_STATUS确认 |
| 8 | 网口持续有数据，但ADC码是一条直线；每次下载后常数不同 | FWFT FIFO读使能被寄存，FIFO前进比发送请求晚一拍，首word被重复 | `fifo_rd_en`改为发送器实际接受payload word时的组合握手 | 正弦波恢复；代码注释保留根因 |
| 9 | ADC码只在127/128附近跳，偶尔出现尖刺 | 前期未接有效模拟信号或DCO/数据边沿不可靠；不是UDP吞吐问题 | 用DAC回环、测试码和正式DCO源同步前端分层验证 | AD9280回环曾成功；最终AD9269两路成功 |
| 10 | AD9269硬连时波形实心、两通道异常 | DCO曾落在非时钟能力引脚V5，普通布线无法可靠驱动IDDR/区域时钟 | 正式转接板改为DCO→T9 MRCC、D0→V5、CLK→U15 | A/B同时输入均正常且互不影响 |
| 11 | ILA窗口中没有ADC探针 | bit与ltx不匹配、ILA被重新综合删除，或直接探测封装引脚会破坏IBUF/IDDR结构 | 调试时只探测缓冲后的DCO和IDDR数据并生成匹配ltx；最终版移除ILA节省资源 | 最终bitstream默认无ILA |
| 12 | 5 MHz正弦看起来像三角形 | 20 MSPS对5 MHz只有4点/周期，线性连线必然呈折线；不是ADC失真 | GUI增加插值平滑，仅影响显示；明确真实采样点限制 | 低频/更高采样率下可观察圆滑波形 |
| 13 | 慢时基下波形“实心”或卡成PPT | 数千周期压缩进几百像素；每帧复制/归约数百万原始样点 | min/max包络；超过50万点改用1 ms历史bin；绘图FPS与接收线程分离 | 1 s/div、10秒窗口可用 |
| 14 | 勾选9 KB巨帧后波形冻结 | PC网卡MTU仍为1514，8192 B payload无法无损接收 | GUI检查Windows `JumboPacket`，要求9014 Bytes；标准MTU作为安全默认 | 巨帧取决于网卡/驱动/交换机整链支持 |
| 15 | 勾巨帧后“DDR丢事件”暴增 | Linux DMA未启动时PL仍生成事件，旧计数把“路径未启用”也当真实丢帧 | 增加EVENT_DMA_ARMED；未武装计SUPPRESSED，武装后背压才计DROPPED | GUI和寄存器已分开显示 |
| 16 | Linux START/STOP/set_rate最初只改驱动变量 | PS控制信号没有真正接入统一状态机，寄存器地址示例也不一致 | `daq_control_regs_v3`接入manager；地址统一为0x43C10000 | RTL寄存器仿真通过，真实Linux板测仍待验 |
| 17 | Linux计划要求64槽，但驱动曾为32槽 | 早期使用32位mask管理slot，直接限制为32 | 改64槽bitmap；Event 64槽、Scope 16槽独立管理 | Linux mock 11/11 |
| 18 | 8320 B槽不能安全mmap | 8320不是页对齐，连续slot地址与用户映射不一致 | Event槽步长PAGE_ALIGN=12288；Scope步长36864 | 文档和用户库统一 |
| 19 | Event和Scope复用同一DMA会让模式切换复杂 | 同一DMA需要终止、重配描述符并共享错误状态 | 新增DMA1/HP1；FIFO、SG环、IRQ和DDR槽独立 | 最终双DMA架构 |
| 20 | 原双ADC占用J25和大量资源 | AD9280只是临时验证源，正式硬件已使用AD9269 | 删除AD9280/DAC/ROM/按键/硬触发及活动约束 | J25完全释放 |
| 21 | GUI找不到或目录里版本混乱 | 最新GUI在`dlcpro_v1\daq_pc`，桌面交付曾是旧版，根目录混有Vivado日志 | 统一GUI入口并同步最终交付，旧版归档；生成SHA256 | 当前桌面最终版校验错误0 |
| 22 | `dual_adc_timing_clean.bit`找不到，用户询问为何不用`top.bit` | 历史交付名和最终实现产物名不一致 | 最终以`top.bit`为权威，并记录SHA-256 | 当前最终bit哈希固定 |
| 23 | CSV录制一启动就弹保存框 | 录制和导出流程混在一个按钮动作 | 开始时写临时二进制，停止后才选CSV路径 | PC自动测试通过 |
| 24 | 高速CSV“丢失数”快速增加 | 旧录制每个绘图tick只从环形缓冲取2000点，20 MSPS绝大多数样点来不及读取 | UDP接收线程直接回调完整包，后台写`.plraw`；停止后流式转CSV | 不再受绘图FPS限制 |
| 25 | 10分钟记录数据量不可接受 | 20 MSPS双通道原始数据80 MB/s，10分钟约48 GB，CSV更大 | 支持仅A、仅B、A+B同文件或A/B分文件；建议增加长期趋势格式 | 单通道约减半；仍受磁盘速度限制 |
| 26 | 峰模块噪声估计异常增大 | 有符号误差曾被当成无符号右移/累加，负误差发生回绕 | 显式扩展符号并进行算术移位 | 漂移/噪声峰场景仿真通过 |
| 27 | 一个峰被计成许多丢事件 | 背压时每个超阈值样点都累加drop | 用`dropped_peak_active`锁存，一次完整峰 excursion只计一次 | 背压场景自检通过 |

## 12. 验证结果

### 12.1 RTL

当前13项RTL自检全部通过：

1. AD9269固定码、棋盘码、递增码、OTR和A/B交换；
2. 五档ADC时钟；
3. Scope双BRAM、TLAST和反压；
4. SPI读回、重试、失败和恢复；
5. 双控制面仲裁和100次START/STOP；
6. AXI-Lite寄存器和DMA armed；
7. 迭代数学；
8. FWFT AXIS反压；
9. 峰特征8320 B帧；
10. 漂移/噪声/正负峰/绝对峰/滞回/削顶；
11. PLDQ全部命令和非法包；
12. 控制CDC；
13. 广播DISCOVER集成。

### 12.2 实现

- WNS：`+0.140 ns`；
- TNS：0；
- WHS：`+0.029 ns`；
- THS：0；
- 未约束内部最大延迟端点：0；
- DRC Error：0；
- Methodology Critical Warning：0；
- TIMING-2/4/6/7、REQP-1933、LUTAR-1：0。

资源：

| 资源 | 使用量 |
|---|---:|
| LUT | 25040 |
| FF | 54993 |
| RAMB36 | 65 |
| RAMB18 | 1 |
| DSP | 7 |

### 12.3 软件

- PC Python：27/27；
- Linux mock：11/11。

需要强调：RTL仿真、Linux mock和Vivado timing closure不能替代40/80 MSPS真实板级DMA/DDR测试。

## 13. 当前仍需优化的地方

### P0：量产或正式实验前必须完成

#### 13.1 补齐外部I/O时序约束

最终报告中内部未约束端点为0，但 `check_timing` 仍显示：

- 7个输入端口没有 input delay；
- 10个输出端口没有 output delay。

这通常涉及 RGMII、SPI和低速控制引脚。当前“所有用户指定约束满足”只代表已写入XDC的约束满足，不代表每个外部接口都完成板级时序签核。

建议：

- 按PHY手册和PCB走线补齐RGMII RX/TX input/output delay；
- 核对RGMII TXC相位和PHY内部delay配置；
- 为ADC输出时钟和SPI建立板级时序预算；
- 重新运行 `report_timing_summary -report_unconstrained -check_timing_verbose`；
- 目标是 `no_input_delay=0`、`no_output_delay=0`，或对明确异步/静态引脚逐项写注释豁免。

#### 13.2 用最终PCB长度重算AD9269输入窗口

当前 `3.48..5.48 ns` 输入延迟预算基于：

- ADC寄存器0x17的4.48 ns名义延迟；
- ±0.8 ns临时PVT裕量；
- ±0.2 ns转接板走线差。

XDC已经明确注明这是布局前预算，不是数据手册保证值。正式PCB长度和层叠确定后，应重新计算每一组DCO/data skew。必要时增加 IDELAYE2 扫描和测试码训练，在启动时寻找稳定采样窗中心。

#### 13.3 完成40/80 MSPS真实DMA验收

至少执行：

- AD9269递增码/棋盘码，连续10分钟；
- Scope抽取1，核对80 MSPS相邻索引和12.5 ns；
- Event帧触发位置与Scope窗口索引一致；
- HP0/HP1分别注入DDR压力；
- 100次Scope/Event模式切换；
- FIFO overflow、DMA error、TLAST长度、描述符cookie均为0异常。

#### 13.4 在目标Linux上验收驱动

重点不是“能加载模块”，而是：

- 64/16槽全部循环租借和释放；
- 用户进程异常退出后回收lease；
- STOP唤醒阻塞DEQUEUE；
- DMA错误和超时可恢复；
- cache/coherent属性与真实内核、设备树一致；
- IRQ号与XSA导出的实际映射一致；
- 连续运行无DMA挂死。

#### 13.5 验证真实SPI读回

读取寄存器确认：

- ID=`0x75`；
- grade合理；
- `0x14=0x21`；
- `0x17=0x27`；
- `0x0D`等于当前测试码；
- 故意断开SDIO时START被禁止。

### P1：建议下一阶段实施

#### 13.6 状态计数器使用原子快照CDC

部分32/64位统计量现在使用逐位两级同步。对“配置在停止时保持不变”的总线是可接受的，但事件计数、间隔统计和overflow计数会连续变化，读取时理论上可能出现跨位不一致。

建议：

- 状态查询触发一次core域snapshot；
- snapshot完成后通过toggle/ack握手交给AXI或GMII域；
- 高频计数器可使用Gray编码；
- overflow错误使用脉冲/事件toggle同步，而不是直接比较异步多位计数。

这不会改变主数据，但能避免极低概率的状态撕裂和假错误。

#### 13.7 增加Event排队能力

峰模块形成一帧并被DMA反压时，后续峰只能计为drop。若透射峰间隔缩短，可增加：

- 2～4组事件窗口bank；
- 小型事件元数据FIFO；
- 峰检测与帧发送解耦；
- 记录“检测到、排队、发出、丢弃”四级计数。

先根据真实最大峰率计算：

```text
Event DDR平均带宽 = 8320 B × 峰率
```

DDR通常不是瓶颈，真正瓶颈是窗口存储和单帧占用时间。

#### 13.8 开放峰参数的PS安全配置

当前阈值等参数固定，`set_threshold`明确返回`EOPNOTSUPP`，不会假成功。后续若不同实验需要不同峰幅度，应增加：

- shadow寄存器；
- STOPPED状态写入；
- CONFIG_COMMIT原子生效；
- 参数范围检查；
- 参数版本写入EVNT帧头；
- 保留现有IOCTL编号。

#### 13.9 网络改为学习主机MAC/单播

当前固定HOST MAC为广播地址，直连调试简单，但在交换网络中会增加无关广播流量。建议：

- 从合法PLDQ控制帧学习源MAC/IP；
- DAQS和DAQD单播回最近控制主机；
- 保留广播DISCOVER；
- 增加主机租约超时和重新发现。

#### 13.10 巨帧自适应

不要只用一个勾选框。可改为：

1. PC查询网卡MTU；
2. 发测试包；
3. 板卡返回包计数；
4. 成功后才切8192 B；
5. 失败自动回退1408 B；
6. 状态中显示实际payload和包率。

### P2：维护性和体验优化

#### 13.11 长时间记录格式

CSV不适合20 MSPS长时间原始记录。建议：

- 默认保存二进制 `.plraw` 或 HDF5/Zarr；
- CSV只导出选定时间段；
- 增加1 ms或10 ms min/max/mean长期趋势；
- 1 Hz扫频可同时保存峰事件表和低速趋势；
- 记录磁盘写速、队列深度和文件剩余时间。

10分钟数据估算：

| 模式 | 原始数据量 |
|---|---:|
| 20 MSPS A+B | 约48 GB |
| 20 MSPS仅A或仅B | 约24 GB |
| 1 ms趋势，A+B min/max/mean | 仅数十MB量级 |

#### 13.12 调试可观测性

最终bitstream无ILA，资源更省，但遇到板级问题时定位较慢。建议保留一个“debug构建”：

- 只探测 `debug_dco_ibuf`、IDDR后的A/B、FIFO write/read和TLAST；
- 生成与bit严格匹配的ltx；
- release构建不含ILA；
- bit和ltx文件名包含同一build ID。

#### 13.13 清理历史命名

活动工程中仍存在 `dual_adc_pl_io.xdc` 这类历史文件名；未加入工程的 `dual_adc_impl_clocks.xdc` 还保存3 MSPS和旧时钟树内容。虽然不影响当前bitstream，但容易误导维护者。

建议：

- 将活动约束重命名为 `ad9269_pl_io.xdc`；
- 将历史XDC移入明确的archive目录；
- Tcl重建脚本只添加白名单文件；
- 每次构建输出实际使用的sources/XDC清单和哈希。

#### 13.14 DRC性能建议

剩余DRC提示主要是：

- 峰模块部分DSP输入/输出未充分流水；
- AXI DMA内部BRAM WRITE_FIRST碰撞建议；
- Xilinx FIFO内部实现提示。

它们不是当前功能错误，且WNS为正。若以后提高core频率或降低功耗，可进一步给平方/噪声乘法加DSP寄存级；AXI DMA内部结构优先保持Xilinx默认，除非仿真或板测证明存在地址碰撞。

## 14. 推荐的最终研究与验收顺序

1. 读取最终bit/XSA/HWH哈希，确认版本一致；
2. 上电后先读SPI ID和配置；
3. 开AD9269固定码，检查A/B边沿和位序；
4. 棋盘码检查位翻转；
5. 递增码检查丢样、重复样和通道交换；
6. 5/10/20/40/80 MSPS分别读取DCO实测速率；
7. 20 MSPS验证PL UDP标准MTU10分钟；
8. 支持条件具备后再测巨帧，不把巨帧作为基本功能前提；
9. 80 MSPS Scope抽取1，核对样点索引；
10. Event模式输入可控峰列，比较Event峰位置与Scope原始窗口；
11. 两种模式切换100次；
12. Linux进程异常退出、DMA错误、网线拔插和ADC时钟消失测试；
13. 温升稳定后再次进行眼图/测试码误码验收；
14. 补齐外部I/O约束后重新生成正式production bitstream。

## 15. 关键文件索引

| 内容 | 文件 |
|---|---|
| 顶层 | `AXI_DMA.srcs/sources_1/new/top.v` |
| AD9269 IDDR前端 | `ad9269_input_frontend.v` |
| 异步FIFO ingress | `ad9269_ingress.v` |
| ADC时钟 | `adc_rate_clock_gen.v` |
| 统一状态机 | `daq_acq_manager.v` |
| AXI-Lite寄存器 | `daq_control_regs_v3.v` |
| PL命令解析 | `pl_daq_control.v` |
| PL UDP封包 | `pl_raw_udp_streamer.v` |
| 峰算法 | `peak_feature_engine.v` |
| Scope双BRAM | `ad9269_scope_capture.v` |
| SPI写读回 | `ad9269_spi_init.v` |
| 引脚/ADC输入时序 | `pin_constraint.xdc` |
| PS/PL时钟组 | `ad9269_clock_domains.xdc` |
| 寄存器表 | `04_Linux/REGISTER_MAP.md` |
| Event帧 | `04_Linux/EVNT_FRAME_FORMAT.md` |
| Scope帧 | `04_Linux/SCOP_FRAME_FORMAT.md` |

## 16. 结论

最终版本已经从“能生成bitstream的双ADC原型”收敛为“AD9269单ADC、源同步采集、PL UDP监视、双DMA/双HP、SPI真实读回”的完整工程。最严重的组合时序、PHY复位死锁、DCO非时钟引脚、FWFT重复首word、命令最后word提交、事件丢帧语义和高速录制丢样问题均已找到明确根因并修复。

当前工程满足已声明的内部时序和DRC验收，AD9269 A/B板级基本波形也已成功。下一阶段不应继续盲目增加功能，而应优先完成外部I/O约束、40/80 MSPS真实DMA、Linux驱动和SPI读回四项正式验收。完成这些以后，再考虑参数可编程、事件多bank、原子状态CDC和长期趋势存储。
