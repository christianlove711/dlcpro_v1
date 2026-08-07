# 文档索引

## 当前版本

- [操作与部署指南](USER_GUIDE.md)
- [项目目录说明](PROJECT_STRUCTURE.md)
- [Windows打包与发布](PACKAGING.md)
- [2026-08-05发布说明](RELEASE_NOTES_2026-08-05.md)
- [AD9269 J24转接板接线设计](AD9269_J24_转接板接线设计.md)

## 算法

- [ADC原始码00模两级自动锁定算法](../reports/adc_peak_balance/ALGORITHM_REPORT.md)：ADC采集页面当前使用的初始化寻峰、理论居中、`0.2 Vpp` 两级 Offset 网格和可选 FALC 接管算法（2026-08-07 更新）。
- [主程序双信号自动锁频配置指南](AUTO_LOCK_ALGORITHM_CONFIG_GUIDE.md)：主 DLC pro 控制台中历史形成的透射/误差信号三策略自动锁频模块，与 ADC 页面“00模自动锁频”不是同一个控制器。

## ADC与PL UDP

- [AD9269 PC端说明](../daq_pc/README_AD9269.md)
- [PL UDP网络与协议说明](../daq_pc/README_PL_UDP.md)
- 架构和时序图片位于 `assets/`。

## 历史

`history/` 保存旧计划、交接记录和阶段报告，只用于追溯，不代表当前软件行为。FPGA阶段工程、旧构建和非项目仿真位于 `../archive/`。
