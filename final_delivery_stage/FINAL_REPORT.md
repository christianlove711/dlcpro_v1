# AD9269 单 ADC、双 DMA/双 HP 最终验证报告

## 完成状态

- 最终工程只保留 AD9269，支持 5/10/20/40/80 MSPS；PL UDP 限制为 5/10/20 MSPS。
- AD9280、AD9708 DAC、正弦 ROM、J25 按键、硬触发和 ILA 已从活动工程移除。
- Event DMA0/HP0 与 Scope DMA1/HP1 完全独立。
- Scope 双 BRAM、触发、抽取、10/20 FPS 和固定 `SCOP` 帧已实现。
- Event DMA 武装抑制与 Scope 抑制/真正丢帧统计已经分离。
- SPI 已实现 3 线 SDIO 写后读回、芯片 ID/寄存器验证、三次重试和失败禁止 START。
- PS/Linux 已具备模式、采样率、START/STOP、DMA ARMED 和状态寄存器接口。

## 地址、中断与帧

| 项目 | 地址/接口 |
|---|---|
| Event AXI DMA | `0x40400000`，HP0，`IRQ_F2P[0]` |
| Scope AXI DMA | `0x40410000`，HP1，`IRQ_F2P[1]` |
| DAQ 控制 | `0x43C10000` |
| Event 帧 | 8320 B，64×12288 B 槽 |
| Scope 帧 | 32832 B，16×36864 B 槽 |

## 自动验证

- RTL 自检：13/13 PASS。
- PC Python：27/27 PASS（含高速 UDP 录制、停止后 CSV 转换、A/B 单独或分文件录制及 1 s/div 长时程缓存）。
- Linux mock：11/11 PASS。
- 最终实现：WNS `+0.140 ns`，WHS `+0.029 ns`，TNS/THS 为 0。
- DRC Error：0。
- Methodology Critical Warning：0。
- TIMING-2、TIMING-4、TIMING-6、TIMING-7、REQP-1933：0。

复位拓扑相关的 `LUTAR-1` 和 `REQP-1933` 已全部清除。DRC 中剩余的是 DSP 流水性能建议、Xilinx FIFO 内部无可路由负载提示及 AXI DMA 内部 BRAM `WRITE_FIRST` 建议；它们不是功能错误，也不阻止 bitstream 生成。

## 最终资源

| 资源 | 使用量 |
|---|---:|
| LUT | 25040 |
| Logic LUT | 22890 |
| LUTRAM | 1876 |
| SRL | 274 |
| FF | 54993 |
| RAMB36 | 65 |
| RAMB18 | 1 |
| DSP | 7 |

## 最终硬件 SHA-256

- `top.bit`: `BC2AF12F3DB72E1E2EFAF7B15774167F6C63925A0F9AB82C7F83BF6B3D157F66`
- `ad9269_single_dualdma.xsa`: `7A4C8EF08B72D49BB868412621D4DC205A2C935D82C76387DB26F6117E594659`
- `System.hwh`: `B5E42D11074DFEEFA9A377E90026DE32BD99A023A075D2C5FCC1985504991B46`

## 板级待验收

- 5/10/20/40/80 MSPS 下 DCO 数据稳定性和 A/B 顺序。
- Scope 在 40/80 MSPS 下的 25/12.5 ns 原始样点间隔。
- Event 峰位置与 Scope 窗口样点索引一致。
- 两种模式连续切换 100 次。
- SPI ID 为 `0x75`，并核对 `0x14=0x21`、`0x17=0x27`、`0x0D=test_mode`。

Linux mock 测试不等同于真实 DMA/DDR 板测；最终硬件链路仍需在目标板 Linux 环境验收。
