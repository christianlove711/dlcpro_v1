# RGMII相位扫描判定

## 当前实现

默认相位208.125°的 routed 结果：

- RX setup = -1.093 ns
- RX hold = +0.774 ns
- TX setup = +4.150 ns
- TX hold = -3.431 ns

## 可行性判定

RX相位平移会等量改善一侧并恶化另一侧；当前 RX setup+hold = -0.319 ns。因此保守 ±0.5 ns PCB预算下没有同时满足 RX setup/hold 的相位。

TXC、TXD和TX_CTL由同一 `shifted_raw` 驱动，统一改变 MMCM 相位只平移三者的绝对时间，不改变 TX 数据相对转发时钟的最差裕量。当前 TX hold 为负，所以不存在使四类 RGMII 裕量同时为正的合法 MMCM 相位。

结论：`NO_PASSING_PHASE`。根据阶段1停止条件，不执行耗时的64次全量实现，不自动选择相位，不生成可晋升候选。

独立脚本 `sweep_rgmii_phase.tcl` 已实现5.625°合法步进、逐相位14项中的RGMII映射自检、四类逐路径裕量记录、最小裕量评分和自动选择。它保留用于 PCB 实际 skew 更新后重新运行；映射失败的相位不会参与选择。

