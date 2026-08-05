# PS/Linux 取数与武装顺序

最终硬件只有 AD9269，并提供两条相互独立的 DDR 数据路径：

```text
自动锁频：peak_feature_engine → Event FIFO → DMA0 → HP0 → DDR
普通示波器：双BRAM窗口 → Scope AXIS → DMA1 → HP1 → DDR
```

两套 DMA 可同时初始化，但采集模式互斥。HP0/HP1 是独立 AXI 端口，最终仍共享
同一 DDR 控制器。

## Event 自动锁频模式

- DMA：`0x40400000`，HP0，`IRQ_F2P[0]`
- 64 个 SG 槽
- 每帧有效 8320 字节，槽步长 12288 字节
- 帧内容：128 字节特征头 + 峰前 1024 组 A/B + 峰后 1024 组 A/B

必须先成功提交全部描述符，再把 `0x43C10068.bit0` 置 1。该位是 PL 内部
`EVENT_DMA_ARMED`，不是外部 FPGA 引脚，也不需要 PS GPIO。未武装时检测到的峰
只计入 `SUPPRESSED_EVENTS`；武装后仍因背压无法交付的帧才计入
`DROPPED_EVENTS`。

推荐直接调用：

```c
int fd = zynq_daq_open();
zynq_daq_start(fd, 80000000, 0);
```

驱动会自动执行“STOP → 提交 64 个描述符 → 选择 Event 模式 → 武装 →
CONFIG_COMMIT → START”。

## Scope 普通示波器模式

- DMA：`0x40410000`，HP1，`IRQ_F2P[1]`
- 16 个 SG 槽
- 每帧有效 32832 字节，槽步长 36864 字节
- 帧内容：64 字节 `SCOP` 头 + 8192 组 A/B
- 支持 1…256 抽取、A/B 上升/下降沿触发、10/20 FPS

示例：

```c
struct zynq_scope_config cfg = {
    .rate_hz = 80000000,
    .decimation_log2 = 0,
    .trigger_mode = ZYNQ_SCOPE_TRIGGER_FREE,
    .trigger_channel = 0,
    .trigger_level = 0,
    .fps = 10,
};
zynq_scope_start(fd, &cfg);
```

驱动会先提交 16 个 Scope 描述符，再把 `0x43C10074.bit0` 置 1。未武装时跳过
的窗口记入 `SCOPE_SUPPRESSED`，只有武装后的双BRAM/DMA拥塞才记入
`SCOPE_DROPPED`。

## 统一取帧

两种模式均使用同一用户态接口：

```c
struct zynq_daq_frame frame;

while (zynq_daq_dequeue_frame(fd, &frame) == 0) {
    void *slot = zynq_daq_map_slot(fd, frame.slot);
    process_frame(slot, frame.length, frame.mode);
    zynq_daq_release_frame(fd, frame.slot);
}
```

`frame.mode` 区分 Scope/Event，`frame.length` 是有效长度，`frame.stride` 是
mmap 槽步长。每个租借槽必须及时 `release`，否则会耗尽描述符并产生真实背压。

## 不使用交付驱动时的严格顺序

Event：

```text
CONTROL.STOP
EVENT_CONTROL=0
提交并启动64个BTT=8320的S2MM SG描述符
ACQ_MODE=1，写ADC_CONFIG，CONFIG_COMMIT
EVENT_CONTROL=1
CONTROL.START
```

Scope：

```text
CONTROL.STOP
SCOPE_CONTROL.ABORT=1且ARMED=0
提交并启动16个BTT=32832的S2MM SG描述符
ACQ_MODE=0，写ADC_CONFIG和SCOPE_CONFIG，CONFIG_COMMIT
SCOPE_CONTROL.ARMED=1
CONTROL.START
```

停止时必须先让 PL 收到 `CONTROL.STOP`，再解除 ARMED，最后 terminate DMA。
不得先武装再准备描述符。

## 关键状态

| 寄存器 | 含义 |
|---:|---|
| `0x43C10054` | `stream_id` |
| `0x43C10058` | 实测采样率 |
| `0x43C10060` | Event 真正背压丢帧 |
| `0x43C10068` | Event DMA 武装 |
| `0x43C1006C` | Event 未武装抑制 |
| `0x43C1007C` | Scope busy/trigger/overflow/armed |
| `0x43C10080` | Scope 完成帧数 |
| `0x43C10094` | Event DMA/SPI 状态 |
| `0x43C10098` | Scope 未武装抑制 |
| `0x43C1009C` | Scope 真正背压丢帧 |

完整寄存器位定义见 `REGISTER_MAP.md`，两种帧格式分别见
`EVNT_FRAME_FORMAT.md` 和 `SCOP_FRAME_FORMAT.md`。
