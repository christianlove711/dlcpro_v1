# AD9269采集卡：PL直连PC网口专项优化交接计划

版本：2026-07-27  
用途：复制到新的Codex对话后，直接继续实施  
范围：只处理“AD9269采样→PL UDP/RGMII→PC”链路

## 0. 给新对话的执行指令

继续优化Zynq-7020 AD9269采集卡的PL直连PC网口链路。不要修改PS端Event/Scope DMA、HP0/HP1、DDR、Linux驱动和设备树；这些已交给PS端同事。

先完整阅读本计划和现有最终报告，基于当前可工作的`top.bit`建立可回退基线。所有网络修改必须在独立开发版本验证，不能直接覆盖当前能正常采集A/B波形的最终bitstream。

工作链路限定为：

```text
AD9269 DCO/数据
→ IDDR源同步采集
→ 采集异步FIFO
→ 100 MHz处理域
→ PL网络监视缓冲
→ DAQD/DAQS/PLDQ
→ UDP/IPv4/Ethernet
→ GMII/RGMII
→ PL PHY
→ 网线
→ PC网卡
→ PC GUI/录制
```

40/80 MSPS继续只供PS路径使用。PL UDP只支持5/10/20 MSPS，不得为了本计划开放40/80 MSPS连续网络发送。

## 1. 工程与交付位置

### 1.1 Vivado工程

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main
```

工程文件：

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main\AXI_DMA.xpr
```

### 1.2 当前RTL

RTL目录：

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main\AXI_DMA.srcs\sources_1\new
```

与PL→PC直接相关：

| 文件 | 作用 |
|---|---|
| `top.v` | 板卡IP/MAC、PHY复位、RGMII、PLDQ、网络数据路径顶层连接 |
| `ad9269_input_frontend.v` | DCO/IDDR源同步采集，A/B配对 |
| `ad9269_ingress.v` | DCO域到100 MHz域的采集异步FIFO和64位样点索引 |
| `daq_acq_manager.v` | START/STOP、采样率、monitor_enable、stream_id |
| `pl_daq_control.v` | 20字节PLDQ命令解析 |
| `pl_daq_control_cdc.v` | PL控制跨时钟 |
| `pl_raw_udp_streamer.v` | 监视FIFO、DAQD/DAQS头、包序号和数据发送 |
| `udp.v` | UDP RX/TX组合顶层 |
| `udp_rx.v` | Ethernet/IPv4/UDP接收解析 |
| `udp_tx.v` | Ethernet/IPv4/UDP发送和IPv4头校验和 |
| `crc32_d8.v` | 发送Ethernet FCS |
| `gmii_to_rgmii.v` | GMII/RGMII桥 |
| `rgmii_rx.v` | RGMII DDR输入 |
| `rgmii_tx.v` | RGMII DDR输出 |
| `pl_rgmii_clock.v` | RXC MMCM和相移 |
| `phy_reset_sequencer.v` | PHY独立20 ms复位 |

PS/DMA相关RTL可以作为只读背景，不纳入本计划修改。

### 1.3 约束

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main\AXI_DMA.srcs\constrs_1\new
```

重点文件：

```text
dual_adc_pl_io.xdc
pin_constraint.xdc
ad9269_clock_domains.xdc
```

`dual_adc_pl_io.xdc`虽仍使用历史文件名，但当前包含有效PL RGMII引脚和`pl_eth_rxc`时钟。后续可以重命名为`ad9269_pl_io.xdc`，但重命名前必须同步修改Vivado工程和可复现Tcl。

### 1.4 仿真

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main\AXI_DMA.srcs\sim_1\new
```

现有相关testbench：

```text
tb_pl_daq_control.sv
tb_pl_daq_control_cdc.sv
tb_udp_control_integration.sv
tb_ad9269_frontend_t9.sv
tb_native_fifo_to_axis_fwft.sv
```

新测试必须放在同一仿真目录，并加入一键仿真Tcl。

### 1.5 PC程序

开发目录：

```text
C:\Users\chris\dlcpro_v1\daq_pc
```

相关文件：

| 文件 | 作用 |
|---|---|
| `daq_protocol_v2.py` | PLDQ、DAQS、DAQD格式和解析 |
| `daq_udp_dual.py` | 控制请求、transaction匹配、UDP接收、样点环形缓冲 |
| `daq_qt_dual.py` | Qt接收线程 |
| `unified_daq_gui.py` | GUI、巨帧检查、状态、绘图和录制 |
| `tests/test_pl_protocol.py` | 协议和乱序/旧stream测试 |
| `tests/test_unified_gui.py` | GUI、录制和长时基测试 |

### 1.6 当前报告

```text
C:\Users\chris\FPGA_Projects\A-high-speed-data-acquisition-framework-main\reports\ad9269_single_dualdma
```

重点：

```text
post_route_timing_summary.rpt
post_route_drc.rpt
post_route_methodology.rpt
simulations\
```

### 1.7 当前最终交付

```text
C:\Users\chris\Desktop\采集卡项目_最终版
```

当前权威硬件：

```text
C:\Users\chris\Desktop\采集卡项目_最终版\02_最终硬件\top.bit
C:\Users\chris\Desktop\采集卡项目_最终版\02_最终硬件\ad9269_single_dualdma.xsa
C:\Users\chris\Desktop\采集卡项目_最终版\02_最终硬件\System.hwh
```

当前`top.bit` SHA-256：

```text
BC2AF12F3DB72E1E2EFAF7B15774167F6C63925A0F9AB82C7F83BF6B3D157F66
```

新网络版本在全部验收通过前不得替换这个文件。

当前PL开发复盘：

```text
C:\Users\chris\Desktop\采集卡项目_最终版\00_交付说明\PL_DEVELOPMENT_REVIEW_AND_OPTIMIZATION.md
```

## 2. 当前网络基线

- PL板卡IP：`192.168.20.2`；
- PC网卡：`192.168.20.1/24`；
- PL板卡MAC：`00:0A:35:02:1E:01`；
- 当前目的MAC：`FF:FF:FF:FF:FF:FF`；
- 控制/状态UDP端口：5000；
- 原始数据UDP端口：5001；
- PL UDP采样率：5/10/20 MSPS；
- 数据格式：A/B双通道，每样点对4字节；
- 标准模式：40 B DAQD头+1408 B样点；
- 巨帧模式：40 B DAQD头+8192 B样点；
- 监视FIFO：当前16384×32 bit，约64 KiB；
- 20 MSPS有效数据率：80 MB/s；
- 标准MTU估算线速约690 Mbit/s；
- 当前PC A/B波形已经板测成功；
- 当前PHY复位、PLDQ最后word提交和FWFT重复首word问题已经修复。

## 3. 严格边界

本计划不得修改：

- Event DMA0、Scope DMA1；
- HP0、HP1；
- SG描述符和DDR槽；
- Linux驱动、设备树、IOCTL；
- EVNT和SCOP帧；
- PL峰算法；
- PS网口和DLCpro网络；
- 40/80 MSPS PS功能。

如果网络状态包仍携带Event/Scope统计，只允许保持兼容或改进快照方式，不改变PS寄存器ABI。

## 4. 实施阶段

## 阶段0：冻结基线和建立回退

### 工作

1. 记录当前XPR、全部活动RTL/XDC、PC程序和最终bit哈希；
2. 导出Vivado实际使用的source/XDC清单；
3. 复制当前实现报告和13项RTL仿真日志；
4. 新建网络专项报告目录，例如：

```text
reports\pl_udp_pc_v2
```

5. 新产物使用独立名字：

```text
top_pl_udp_v2_test.bit
top_pl_udp_v2_test.ltx
```

### 验收

- 不修改当前桌面`top.bit`；
- 当前PC测试27/27仍通过；
- 当前RTL网络相关仿真保持PASS。

## 阶段1：完成RGMII外部时序签核

这是最高优先级。

### 前置资料

必须先确认，不能猜：

1. 开发板PL PHY具体型号；
2. PHY的RGMII内部延迟寄存器和上电默认值；
3. 当前是否为RGMII、RGMII-ID、RGMII-TXID或RGMII-RXID；
4. PHY RXC/RXD、TXC/TXD时序参数；
5. FPGA到PHY的PCB走线长度或时延；
6. PHY供电电压和FPGA I/O标准。

若工程目录没有原理图/PHY手册，应要求用户提供开发板原理图和PHY型号，不能直接写一组通用延迟值。

### 当前缺口

`dual_adc_pl_io.xdc`目前只有：

```tcl
create_clock -name pl_eth_rxc -period 8.000 [get_ports eth_rxc]
```

缺少RGMII数据相对时钟的：

- RX `set_input_delay`；
- TX生成时钟；
- TX `set_output_delay`；
- PHY内部delay与FPGA MMCM相位的统一说明。

### 修改对象

```text
dual_adc_pl_io.xdc
pl_rgmii_clock.v
rgmii_rx.v
rgmii_tx.v
gmii_to_rgmii.v
```

### 实施要求

1. 根据PHY真实模式计算RX最大/最小input delay；
2. 根据TXC产生方式建立generated clock；
3. 根据PHY输入要求计算TX最大/最小output delay；
4. 检查当前`208.125°`相位是否与PHY内部delay重复或冲突；
5. 明确时钟和数据的PCB skew预算；
6. 不用false path掩盖RGMII同步I/O；
7. 运行完整`report_timing_summary -report_unconstrained -check_timing_verbose`。

### 验收

- RGMII数据和控制端口不再出现在`no_input_delay/no_output_delay`；
- RGMII setup/hold均为正；
- WNS/WHS≥0；
- 无TIMING Critical Warning；
- 1 Gbit/s链路反复插拔50次可自动恢复；
- 连续20 MSPS标准MTU运行30分钟无PL监视丢样。

## 阶段2：修复PL内部丢样后的真实样点时间轴

这是数据正确性的最高优先级。

### 当前问题

`pl_raw_udp_streamer.v`中的`first_sample_index`按“已发送样点数”递增。监视FIFO满时，真实ADC样点被丢弃，但后续DAQD索引仍看起来连续。

这会导致：

- PC知道`monitor_drop_count`增加；
- 但不知道数据空洞出现在什么位置；
- 长时间CSV的时间轴可能发生偏移；
- 包序号只能发现网络丢包，不能发现PL FIFO内部丢样位置。

### 修改对象

```text
top.v
ad9269_ingress.v
pl_raw_udp_streamer.v
daq_protocol_v2.py
daq_udp_dual.py
tests/test_pl_protocol.py
```

### 接口修改

把`ad9269_ingress`已有的64位`sample_index`送入网络路径：

```verilog
.sample_index(ingress_index)
```

不要简单地只给每个固定包计算一个连续计数，必须保证DAQD包内数据确实连续。

### 推荐实现

优先采用“包级连续数据组装器”，而不是盲目把64位索引复制到每一个样点：

1. 100 MHz域按标准/巨帧大小组装完整连续包；
2. 每个包保存：
   - 第一个真实64位样点索引；
   - 连续样点数；
   - A/B数据；
3. 若组包资源不足，整包放弃，不允许包中间产生无法标记的空洞；
4. 下一个包从新的真实`sample_index`开始；
5. 包描述符和payload通过异步包FIFO交给GMII域；
6. DAQD的`first_sample_index`直接使用包描述符中的真实索引。

可考虑两块ping-pong包BRAM：

- 标准包约1.4 KiB；
- 巨帧约8 KiB；
- 两块巨帧buffer约16 KiB，比当前64 KiB监视FIFO更容易保证“整包连续”。

如果继续使用样点FIFO，则必须增加gap标记并确保遇到gap时在发送前切包。不能在已经发送固定UDP长度后才发现包中间有gap。

### 协议行为

PC计算：

```text
expected = previous_first_index + previous_sample_count
gap = current_first_index - expected
```

分别统计：

- `packet_sequence`缺口：网络/PC丢包；
- `first_sample_index`缺口：PL组包前丢样；
- 两者同时发生：总缺口按索引为准，避免重复计数。

### 仿真

新增：

```text
tb_pl_monitor_packetizer.sv
tb_pl_monitor_gap_index.sv
```

覆盖：

- 连续标准包；
- 连续巨帧；
- FIFO/包buffer满；
- 包边界前后丢样；
- 64位索引低32位回绕；
- stream_id切换；
- STOP/START清空旧包；
- 反压期间不重复首word；
- 每个包内样点严格连续。

### 验收

- 人为制造PL监视拥塞后，DAQD索引产生准确跳变；
- PC显示PL内部空洞位置和数量；
- 没有拥塞时索引完全连续；
- 10分钟录制跨32位索引回绕仍正确；
- 不增加对ADC主采集路径的反压。

## 阶段3：从广播数据改为PC端点学习和单播

### 当前问题

`top.v`当前写死：

```verilog
HOST_IP  = 192.168.20.1
HOST_MAC = FF:FF:FF:FF:FF:FF
```

因此DAQS和DAQD均为广播以太网帧。

### 目标

- DISCOVER请求仍允许广播；
- 板卡从合法PLDQ包学习PC源MAC/IP/端口；
- 后续DAQS和DAQD单播给已绑定PC；
- 非绑定主机不能在采集中途抢占；
- STOP或租约超时后允许重新绑定。

### 修改对象

```text
udp_rx.v
udp.v
udp_tx.v
pl_daq_control.v
pl_raw_udp_streamer.v
top.v
daq_udp_dual.py
daq_protocol_v2.py
```

### 建议增加的RX输出

```text
source_mac
source_ip
source_udp_port
destination_udp_port
rx_packet_valid
```

### 端点状态机

```text
UNBOUND
→ 接收合法DISCOVER/GET_STATUS
→ LEARNED
→ SELECT/RATE/START确认
→ ACTIVE
→ STOP或租约超时
→ LEARNED/UNBOUND
```

### 安全规则

- 只有通过PLDQ magic、版本、长度和端口验证的包才能更新端点；
- ACTIVE时只接受绑定MAC/IP的控制包；
- 不因为任意广播包更新目标地址；
- stream_id切换后旧主机DAQD自动失效；
- 板卡MAC保持固定且全局唯一。

### 验收

- Wireshark确认DAQD目的MAC为PC单播MAC；
- DISCOVER仍可使用广播；
- 第二台PC不能抢占正在运行的采集；
- PC更换网卡后STOP/超时可重新发现；
- 20 MSPS下广播帧计数接近0，只有发现阶段使用广播。

## 阶段4：完善PL接收协议校验

### 当前缺口

`udp_rx.v`主要验证目的MAC、EtherType和目的IP，没有完整验证：

- 接收Ethernet FCS；
- IPv4版本/IHL；
- IPv4头校验和；
- protocol=`17`；
- 分片字段；
- IP总长度；
- UDP目的端口；
- UDP长度一致性；
- UDP校验和。

### 修改对象

```text
udp_rx.v
udp.v
pl_daq_control.v
crc32_d8.v
```

建议新增独立模块：

```text
eth_rx_fcs_check.v
ipv4_header_check.v
```

### 最低必须实现

1. 目的MAC匹配或DISCOVER广播；
2. EtherType=`0x0800`；
3. IPv4 version=4、IHL=5；
4. protocol=17；
5. 不接受分片PLDQ；
6. 目的IP匹配或本子网广播；
7. 目的UDP端口=5000；
8. IP总长度、UDP长度和实际帧长一致；
9. PLDQ固定20 B；
10. 错误包增加分类计数，不进入控制状态机。

### UDP校验和

IPv4 UDP发送校验和为0是合法的，不列为阻塞项。若实现接收UDP校验和：

- 校验和0表示发送端未提供，可接受；
- 非0则必须验证；
- 不应为了UDP校验和显著降低20 MSPS发送性能。

### 仿真

新增：

```text
tb_udp_rx_validation.sv
```

覆盖：

- 正确单播和广播DISCOVER；
- 错MAC/IP/端口；
- 非UDP；
- 错IHL；
- 错IP头校验和；
- 分片包；
- 长度不一致；
- 错FCS；
- 截断PLDQ；
- 随机噪声帧。

### 验收

- 所有非法帧不产生任何START/STOP/CONFIG；
- 错误分类计数准确；
- 合法PLDQ兼容现有GUI；
- 20 MSPS数据发送不受RX校验逻辑影响。

## 阶段5：巨帧探测、确认和自动回退

### 当前行为

巨帧模式：

```text
DAQD UDP payload = 8232 B
IPv4 total length = 8260 B
DF=1
```

任一链路节点MTU不足时整包消失。

### 目标

巨帧不再是“勾选后立即永久切换”，而是协商状态：

```text
STANDARD
→ JUMBO_PROBE
→ JUMBO_WAIT_ACK
→ JUMBO_ACTIVE
→ 超时/连续丢包
→ STANDARD_FALLBACK
```

### 协议扩展

保留PLDQ v1兼容，可新增命令或arg定义：

```text
JUMBO_PROBE
JUMBO_ACK
JUMBO_DISABLE
```

DAQS增加：

- requested MTU mode；
- actual payload size；
- probe序号；
- probe成功/失败；
- fallback原因；
- 最近ACK时间。

### 修改对象

```text
pl_daq_control.v
pl_raw_udp_streamer.v
daq_protocol_v2.py
daq_udp_dual.py
unified_daq_gui.py
tests/test_pl_protocol.py
tests/test_unified_gui.py
```

### 行为

1. GUI先检查Windows网卡`JumboPacket`；
2. PL发送3～10个带probe标记的大包；
3. PC连续收到后发送ACK；
4. PL才进入JUMBO_ACTIVE；
5. 超时自动回1408 B；
6. 运行中连续检测到PC反馈异常时允许STOP后回退；
7. 标准MTU永远作为安全模式。

### 验收

- PC MTU 1514时自动回退，不冻结波形；
- PC MTU 9014时成功进入巨帧；
- 中间交换机不支持时回退；
- 断网重连后默认标准MTU；
- 状态显示“请求模式”和“实际模式”；
- 巨帧失败不影响START/STOP。

## 阶段6：DAQS原子状态快照

### 当前问题

部分32/64位计数和状态直接逐位两级同步到GMII域，理论上可能出现一次DAQS内字段来自不同计数时刻。

### 目标

```text
GET_STATUS/命令响应
→ GMII域发送snapshot_toggle
→ 100 MHz域一次性锁存PL网络相关状态
→ snapshot_ack
→ GMII域发送冻结的DAQS
```

只需快照PL→PC相关字段：

- acquisition state；
- stream_id；
- configured/measured rate；
- ingress FIFO level；
- ingress overflow；
- monitor FIFO level和最高水位；
- monitor drop；
- TX packet/byte；
- RX分类计数；
- OTR；
- actual MTU/payload；
- link/MMCM/reset状态；
- last network error。

PS Event/Scope字段保持兼容，不修改其寄存器来源。

### 修改对象

```text
pl_raw_udp_streamer.v
top.v
daq_protocol_v2.py
daq_udp_dual.py
```

可新增：

```text
pl_status_snapshot_cdc.v
```

### 验收

- 每个DAQS来自一个冻结快照；
- transaction_id与快照一一对应；
- 高频读取状态时无字段撕裂；
- 现有GUI仍能解析旧字段；
- 新字段使用版本或长度扩展，不破坏DAQS v1。

## 阶段7：控制响应FIFO

### 当前问题

当前`status_pending`只有一位，短时间多个命令可能合并响应；transaction多位总线也可能被后续命令覆盖。

### 目标

增加2～4深度响应FIFO：

```text
transaction_id
command
result/error
snapshot_id
source endpoint
```

每个合法控制命令都有明确响应。STOP仍保持最高优先级，不得因响应FIFO满而延迟停止采集。

### 修改对象

```text
pl_daq_control.v
pl_daq_control_cdc.v
pl_raw_udp_streamer.v
daq_protocol_v2.py
daq_udp_dual.py
```

### 验收

- 连续发送SELECT、RATE、TEST、START时每个transaction均有对应响应；
- 重复transaction可识别并安全重放或拒绝；
- 响应FIFO满有明确错误计数；
- STOP不被队列阻塞；
- GUI重试不会重复START。

## 阶段8：增加PL网口诊断统计

### 建议统计

RX：

- 总帧；
- 合法IPv4；
- 合法UDP；
- 合法PLDQ；
- FCS错误；
- IP校验错误；
- 非UDP；
- 错MAC/IP/端口；
- 长度错误；
- 分片拒绝；
- 非绑定主机控制。

TX：

- DAQD包和字节；
- DAQS包；
- 标准/巨帧包；
- 网络包序号；
- 包buffer最高占用；
- PL组包放弃；
- 真实样点索引空洞；
- MMCM失锁；
- PHY复位/链路重建次数。

PC：

- UDP socket丢包；
- `packet_sequence`缺口；
- `first_sample_index`缺口；
- 旧stream丢弃；
- 录制队列丢样；
- 实际吞吐和包率。

### 显示原则

必须分开显示：

```text
PL组包前丢样
网络/PC丢包
录制磁盘队列丢样
```

不能再使用一个“丢失”数字混合三种来源。

## 阶段9：RGMII底层结构现代化（最后实施）

这项风险最高，只在前面功能稳定后进行。

### 可选改进

- `IDDR2/ODDR2`改为7系列`IDDR/ODDR`；
- RX使用明确的IBUF/BUFIO/BUFR或厂商GMII-to-RGMII IP；
- 必要时使用IDELAYE2；
- TX使用本地独立125 MHz时钟；
- RX只依赖PHY RXC；
- TXC和TXD使用同一个本地源同步时钟；
- 通过MDIO配置和读取PHY的delay、速率、双工和link状态。

### 修改对象

```text
rgmii_rx.v
rgmii_tx.v
gmii_to_rgmii.v
pl_rgmii_clock.v
top.v
dual_adc_pl_io.xdc
```

### 原则

- 先制作独立测试bit；
- 保留现有可用RGMII实现；
- 不在同一次改动中同时更换时钟结构、PHY delay和协议层；
- 每一步都必须可回退。

## 5. PC端配套优化

虽然主要改PL，但协议变化必须同步PC：

1. PC根据DAQD真实`first_sample_index`记录空洞；
2. 分开统计PL内部、网络和磁盘丢样；
3. 保存原始`stream_id/packet_sequence/first_sample_index`；
4. 增加端点绑定/租约显示；
5. 巨帧显示请求、探测、实际和回退状态；
6. Windows socket接收缓冲尽可能增大；
7. 长时间记录优先`.plraw`，CSV只做停止后导出；
8. 继续支持仅A、仅B、A+B同文件和A/B分文件；
9. 不让绘图FPS参与录制数据消费；
10. 旧DAQS/DAQD版本仍可解析或给出明确“不兼容”提示。

## 6. 完整验证矩阵

### 6.1 RTL

必须新增或扩展：

- RGMII合法/非法帧接收；
- FCS/IP/UDP长度和端口；
- PC端点学习；
- 非绑定主机；
- 标准/巨帧组包；
- 真实样点索引；
- PL组包丢样；
- 32位索引回绕；
- START/STOP旧包清理；
- DAQS快照；
- 控制响应FIFO；
- MMCM失锁和恢复。

每个testbench必须：

- 自检；
- 超时；
- PASS/FAIL；
- 非零退出码；
- 写入专项报告目录。

### 6.2 Python

覆盖：

- 新旧协议版本；
- 单播发现和绑定；
- transaction乱序/重复/超时；
- 巨帧探测和回退；
- 包序号缺口；
- 样点索引缺口；
- stream_id切换；
- 10分钟索引回绕模拟；
- A/B录制；
- 绘图不影响录制。

### 6.3 Vivado

每次候选版本必须运行：

- synthesis；
- implementation；
- DRC；
- methodology；
- timing summary；
- report unconstrained；
- utilization；
- power；
- bitstream。

验收：

- WNS/WHS≥0；
- TNS/THS=0；
- DRC Error=0；
- Methodology Critical Warning=0；
- 无RGMII未约束同步I/O；
- 无REQP-1933/LUTAR-1；
- 不使用false path掩盖RGMII真实同步路径。

### 6.4 板级

标准MTU：

1. 5/10/20 MSPS分别运行；
2. 20 MSPS A+B连续30分钟；
3. START/STOP 100次；
4. 拔插网线50次；
5. PC GUI重启、网卡禁用/启用；
6. 波形、包率、索引和丢样统计一致。

故障注入：

1. 故意降低PC处理能力；
2. 故意制造PL包buffer满；
3. PC防火墙阻断；
4. 错IP/错MAC/错端口；
5. 第二台PC发送控制；
6. 错MTU；
7. 随机非法PLDQ；
8. PHY RXC短暂消失。

巨帧：

1. MTU1514必须回退；
2. MTU9014直连必须成功；
3. 经过不支持巨帧的交换机必须回退；
4. 成功后20 MSPS运行30分钟；
5. 包率、吞吐、波形和索引正确。

## 7. 交付要求

新版本通过全部验收后，交付：

```text
top_pl_udp_v2.bit
top_pl_udp_v2.xsa（仅当硬件平台确实变化）
System.hwh（仅当BD/寄存器变化）
PL_UDP_V2_PROTOCOL.md
PL_UDP_V2_REGISTER_AND_STATUS.md
PL_UDP_V2_TIMING_REPORT.md
PL_UDP_V2_BOARD_TEST.md
PL_UDP_V2_CHANGELOG.md
SHA256SUMS.txt
```

如果只改纯PL网络RTL和顶层端口未变，XSA/HWH是否重导出应由实际BD变化决定；不能机械覆盖PS同事正在使用的平台文件。

桌面候选版本先放：

```text
C:\Users\chris\Desktop\采集卡项目_最终版\06_PL网口优化候选
```

通过用户确认后才能替换`02_最终硬件\top.bit`。

## 8. 建议实施顺序

按风险和价值排序：

1. 冻结基线；
2. 确认PHY型号和delay模式；
3. 补齐RGMII I/O约束；
4. 修复DAQD真实样点索引和包内连续性；
5. 增加PL网络分类统计；
6. 改为学习PC MAC/IP后单播；
7. 完善RX协议校验；
8. 巨帧探测和自动回退；
9. DAQS原子快照；
10. 控制响应FIFO；
11. 最后才考虑重构RGMII原语、独立TX时钟和MDIO。

不要把所有项目一次性改完再调试。建议每完成一项：

```text
RTL仿真
→ Python测试
→ Vivado综合/实现
→ 独立测试bit
→ 板级验证
→ 固化报告和哈希
```

## 9. 当前最需要用户补充的资料

开始阶段1前，如果工程资料中无法确认，需要用户提供：

1. PL网口PHY具体型号；
2. 开发板PL PHY原理图页；
3. PHY上电strap配置；
4. PHY RGMII delay相关寄存器当前值；
5. FPGA到PHY的RXC/RXD、TXC/TXD走线长度；
6. 测试时是否直连PC，还是经过交换机；
7. PC网卡型号和支持的最大JumboPacket。

除上述RGMII时序资料外，其余协议、索引、统计和PC程序工作均可先通过仿真推进。

## 10. 完成定义

只有同时满足以下条件，PL→PC网络专项才算完成：

- 20 MSPS双通道标准MTU连续30分钟；
- PL组包丢样、网络丢包、磁盘丢样三类统计完全分离；
- DAQD真实样点索引在故障注入后仍正确；
- RGMII输入/输出时序已根据真实PHY和PCB签核；
- 广播只用于DISCOVER，数据为单播；
- 非法网络包不能触发控制；
- 巨帧失败自动回退，不冻结GUI；
- DAQS状态属于原子快照；
- START/STOP 100次无旧包；
- 所有RTL/Python测试通过；
- WNS/WHS≥0、DRC Error=0；
- 当前可用`top.bit`始终可回退；
- 不影响PS端同事的DMA、DDR、Linux和寄存器ABI。
