# RTL8211E-VB RGMII时序模型

## 硬件依据

- 皓月底板 PL 侧 PHY：RTL8211E-VB（原理图 U10）。
- PHY 地址 strap：4。
- RXD0/SEL RGV、RXD1/TXDLY、RXD2/AN0、RXD3/AN1 及 LED/PHY_AD strap 与原理图一致。
- RX/TX 内部约2 ns延时由 strap 启用，当前模式按 RGMII-ID 处理。
- RGMII I/O 电源为3.3 V，XDC 使用 LVCMOS33。
- 本阶段不增加 MDC/MDIO 运行时改写。

本地证据：

- `C:\baidunetdiskdownload\EBF_ZYNQ7010_7020_hardware_2026_1\[野火]皓月_开发板硬件规格书V1.2.pdf`，以太网原理图页。
- `C:\baidunetdiskdownload\ebf_zynq7020_pl_tutorial_code_20241217\29_eth_udp_loop\doc\RTL8211E-VB-CG-78567.pdf`，Rev.1.6。
- AMD PG160 “Constraining the Core” 中 RGMII 双沿 input/output delay 示例。

## 临时时序预算

PCB 等长/长度报告尚未取得。`RGMII_PCB_SKEW_NS = 0.500 ns` 是待替换的保守 clock-minus-data skew，绝不能解释为零偏斜或最终签核值。

| 方向 | 数据手册/PG160窗口 | 临时PCB扩展 | 候选XDC窗口 |
|---|---:|---:|---:|
| RX input | [-2.8, -1.2] ns | ±0.5 ns | [-3.3, -0.7] ns |
| TX output | [-2.6, -1.0] ns | ±0.5 ns | [-3.1, -0.5] ns |

RXD[3:0]/RX_CTL 与 TXD[3:0]/TX_CTL 的上升沿和下降沿均分别约束。RGMII 同步 I/O 未使用 false path；已有异步 FIFO 跨域约束保留。

## 时钟结构

- `eth_rxc` 建立8 ns主时钟。
- MMCM 输出相位由 `PL_RGMII_CLKOUT0_PHASE` 控制，默认208.125°。
- `eth_txc` 建立明确的 forwarded/generated clock。
- TXC 使用与 TXD/TX_CTL 相同类别的 ODDR2/OLOGIC 转发路径，以避免 fabric assign 引入不同的封装时钟路径。

## 签核状态

RTL8211E-VB 型号、strap 和3.3 V已确认；±0.5 ns仍是临时保守预算。收到真实走线长度后必须重新计算、重新实现，届时才能标记“最终外部时序签核”。

