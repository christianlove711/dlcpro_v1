# AD9269 PL直连PC：阶段0/1状态

日期：2026-07-27

## 结论

阶段0已完成，阶段1候选未通过静态时序，状态为 **REJECTED / DO NOT PROMOTE**。

- 权威回退位流保持不变：
  `C:\Users\chris\Desktop\采集卡项目_最终版\02_最终硬件\top.bit`
- 权威位流 SHA-256：
  `BC2AF12F3DB72E1E2EFAF7B15774167F6C63925A0F9AB82C7F83BF6B3D157F66`
- 未通过候选仅供分析：
  `top_pl_udp_v2_test.bit`
- 候选 SHA-256：
  `A26BC5B8E3343AD825E69C6A3A72871ECC396E71D15ABDB38608DF97900EB413`
- 未覆盖桌面最终版，未导出 XSA/HWH，未修改 PC 协议或程序。

## 已通过

- Python：27/27 PASS。
- RTL：冻结的13项 AD9269 回归 + 新增 RGMII 自检，共14项 PASS。
- 新增测试覆盖 DDR 高低半字节、RX_CTL、前导码/SFD、MMCM失锁/恢复、复位后无伪帧。
- 综合、实现、bitstream 均完成。
- DRC：0 Error、13 Warning、2 Advisory；无 Critical Warning。
- RGMII 数据与控制引脚均已有双沿 input/output delay。
- `eth_rxd[*]`、`eth_rx_ctl` 不再出现在 `no_input_delay`。
- `eth_txd[*]`、`eth_tx_ctl` 不再出现在 `no_output_delay`。
- Methodology 中剩余5项 TIMING-18 均为非RGMII端口。

## 未通过

208.125°、临时 PCB clock-minus-data skew ±0.5 ns 条件下：

| 检查 | 最差裕量 |
|---|---:|
| RX setup | -1.093 ns |
| RX hold | +0.774 ns |
| TX setup | +4.150 ns |
| TX hold | -3.431 ns |
| 全局 WNS/TNS | -1.093 ns / -5.370 ns |
| 全局 WHS/THS | -3.431 ns / -17.067 ns |

RX setup 与 hold 随采样相位反向变化，两者裕量之和为 -0.319 ns，因此在当前保守预算与当前结构下不存在同时为正的采样相位。TXC 与 TXD/TX_CTL 共用同一 MMCM 相位；相位平移不会改变它们的相对裕量，故负 TX hold 也不能由 MMCM 扫描修复。

按照计划的停止条件，本候选不进入板测、不晋升、不覆盖最终交付。

## 后续解锁条件

1. 获取 PCB RXC/RXD、TXC/TXD 实际长度及 clock-minus-data skew。
2. 用真实值替换临时 ±0.5 ns，并重新实现。
3. 如真实值仍不能闭合，另立变更范围评估 RX 输入时钟结构/IDELAY 或经验证的厂商 RGMII IP；不得在本阶段隐式加入。
4. 只有静态时序全部闭合后，才执行5/10/20 MSPS、双通道30分钟、拔插50次和GUI重连板测。

