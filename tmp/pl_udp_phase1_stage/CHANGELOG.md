# 阶段0/1变更日志

## 2026-07-27

- 冻结 Vivado 实际启用的 RTL/XDC/IP/仿真源及 SHA-256。
- 保存权威位流、PC程序、实现报告和测试基线。
- 新建 `reports/pl_udp_pc_v2/baseline` 与 `phase1`。
- 在 `dual_adc_pl_io.xdc` 增加 RGMII-ID 双沿输入/输出延时及 forwarded clock。
- 将 ±0.5 ns PCB skew 显式参数化并标为待替换。
- `pl_rgmii_clock.v` 增加可由 Tcl 覆盖的合法 MMCM 相位宏。
- `rgmii_tx.v` 将 TXC 改为 ODDR2 转发，使其与 TXD/TX_CTL 采用同类 OLOGIC 路径。
- 新增 `tb_rgmii_ddr_mapping.sv` 自检。
- 修正回归脚本的缺失文件检查，并固定运行冻结的13项测试加RGMII测试。
- 新增全实现报告脚本与独立相位扫描/自动评分脚本。
- 完成14项RTL仿真与27项Python测试。
- 完成综合、实现、DRC、methodology、unconstrained timing、utilization、power和bitstream。
- 候选因 RX setup、TX hold 为负被拒绝；未板测、未晋升、未覆盖最终版。

