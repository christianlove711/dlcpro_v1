# AD9269 最终控制与 DMA 地址表

所有寄存器均为 32 位小端。

| 模块 | 基址 | PS 数据路径 | 中断 |
|---|---:|---|---|
| DAQ 控制 | `0x43C10000` | AXI GP 控制面 | — |
| Event AXI DMA | `0x40400000` | `S_AXI_HP0` | `IRQ_F2P[0]` |
| Scope AXI DMA | `0x40410000` | `S_AXI_HP1` | `IRQ_F2P[1]` |

HP0 与 HP1 是独立 AXI 端口，但最终共享 Zynq DDR 控制器和物理 DDR。

| 偏移 | 名称 | 访问 | 定义 |
|---:|---|---|---|
| `0x00` | ID | RO | `0x44415132`（`DAQ2`） |
| `0x04` | VERSION | RO | RTL ABI 版本 |
| `0x08` | CONTROL | W1P | bit0 START，bit1 STOP，bit2 CONFIG_COMMIT，bit3 CLEAR_STATS，bit4/5 MONITOR START/STOP |
| `0x0C` | STATUS | RO | bits2:0 状态，bit3 monitor，bits23:16 last error |
| `0x14` | FIFO_LEVEL | RO | Event FIFO level |
| `0x38` | ADC_CONFIG | RW | bit0 A/B交换，bits6:4测试码，bits10:8速率，bit16恒为AD9269，bit17巨帧 |
| `0x3C` | ADC_STATUS | RO | 实际速率/测试/SPI/DCO/OTR |
| `0x40/44` | OTR_A/B_COUNT | RO | A/B过量程计数 |
| `0x54` | STREAM_ID | RO | 每次有效START或模式切换递增 |
| `0x58` | MEASURED_RATE | RO | 实测DCO样点对速率 |
| `0x5C` | EVENT_COUNT | RO | Event完成帧数 |
| `0x60` | DROPPED_EVENTS | RO | Event已武装后的真实背压丢帧 |
| `0x64` | LAST_ERROR | RO | 状态机错误码 |
| `0x68` | EVENT_CONTROL | RW | bit0 Event DMA armed |
| `0x6C` | SUPPRESSED_EVENTS | RO | Event未武装时抑制的峰 |
| `0x70` | ACQ_MODE | RW | 0 Scope，1 Event；只允许停止态提交 |
| `0x74` | SCOPE_CONTROL | RW/W1P | bit0 ARMED，bit1 ABORT，bit2 CLEAR |
| `0x78` | SCOPE_CONFIG | RW | bits3:0抽取log2，bits5:4触发，bit6通道，bit7 20FPS，bits31:16有符号电平 |
| `0x7C` | SCOPE_STATUS | RO | busy/triggered/overflow/armed |
| `0x80` | SCOPE_FRAME_COUNT | RO | Scope完成帧数 |
| `0x84` | SPI_ID_GRADE | RO | 芯片ID和速度等级 |
| `0x88` | SPI_READBACK_0 | RO | `0x14/0x17/0x0D`读回 |
| `0x8C` | SPI_READBACK_1 | RO | 期望值/版本 |
| `0x90` | SPI_ERROR_DETAIL | RO | 重试和读回错误详情 |
| `0x94` | EVENT_DMA_STATUS | RO | Event armed/SPI状态 |
| `0x98` | SCOPE_SUPPRESSED | RO | Scope未武装跳过窗口 |
| `0x9C` | SCOPE_DROPPED | RO | Scope已武装后的真实背压丢帧 |

速率选择器：`1=5`、`2=10`、`3=20`、`4=40`、`5=80 MSPS`。选择器0
（已删除的3 MSPS）和 AD9280 选择均返回不支持。

## 必须遵守的启动顺序

Event：STOP并解除武装 → 提交64个描述符 → `ACQ_MODE=1`及配置提交 →
Event armed → START。

Scope：STOP并ABORT/解除武装 → 提交16个描述符 → `ACQ_MODE=0`及配置提交 →
Scope armed → START。

停止时必须先让 PL 收到 STOP，再解除 armed，最后终止 DMA。`SUPPRESSED`
不是 DDR 丢帧；只有当前路径已武装后的 `DROPPED` 才是真正无法交付的帧。
