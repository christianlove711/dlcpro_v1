# AD9269 PL直连PC：阶段2实施状态

日期：2026-07-29

## 结论

阶段2候选已完成RTL、PC端解析、仿真、综合、实现和独立bit生成。候选尚未经过实体板卡验收，因此不得覆盖或晋升桌面稳定 `top.bit`。

候选：

`reports/pl_udp_pc_v2/phase2/top_pl_udp_v2_phase2_test.bit`

SHA-256：

`0E37A58A375DE38346D2F068A98B0D99295C8C67AF85EEB9DF3F8A6F2102F37D`

桌面稳定bit保持不变：

`BC2AF12F3DB72E1E2EFAF7B15774167F6C63925A0F9AB82C7F83BF6B3D157F66`

## 实现

- `top.v` 将 `ad9269_ingress` 已有的64位 `ingress_index` 接入 `pl_raw_udp_streamer`。
- 监视异步FIFO的每个word携带 `{真实64位样点索引, payload}`。
- GMII域先在8 KiB显式XPM BRAM中组装完整包，再向UDP MAC声明 `tx_start_en`。
- 组包期间逐word检查真实索引；发现空洞时，只丢弃尚未发送的半包，并从空洞后的真实索引重新组包。
- DAQD `first_sample_index` 直接取完整包描述符中的真实首索引，不再按已发送样点数推算。
- 监视路径仍不向ADC主采集路径施加 `ready/backpressure`。
- PC分别累计网络包序号缺口和PL样点索引缺口；总样点空洞以64位索引为准，避免双重计数。
- AD9269及统一GUI显示网络丢包、PL样点空洞累计值和最近恢复索引。

`ad9269_ingress.v` 的计数逻辑未改动；本阶段只把它已有且已在主路径使用的64位索引送入网络监视路径。

## 验证

- Vivado RTL自检：19/19 PASS。
- Python：31/31 PASS。
- 综合：Complete。
- 实现/bitstream：Complete。
- WNS：+0.150303 ns。
- WHS：+0.036275 ns。
- TNS/THS：0。
- DRC Error：0。
- 资源：55227 FF、25282 LUT、62 RAMB36、1 RAMB18；`raw_streamer_inst` 使用13 RAMB36。

新增仿真覆盖：

- 标准包和巨帧包内连续性；
- FIFO满及包边界空洞；
- 64位索引低32位回绕；
- stream_id切换；
- STOP/START清除旧半包；
- TX反压期间不重复首word。

## 已知边界

- 用户明确跳过阶段0/1，因此RGMII基线的7个 `no_input_delay`、10个 `no_output_delay` 和10项 `TIMING-18`仍存在；阶段2未修改XDC或RGMII相位。
- DRC有4项候选包BRAM相关 `REQP-1839` Warning，但无Error/Critical Warning；BRAM内容只在整包完成后读取，复位/切流通过 `packet_ready` 和 `stage_count` 隔离旧内容。
- 设计中没有debug core，`write_debug_probes`报告“No debug cores were found”，因此没有生成LTX。

## 尚未完成

必须在实体板卡上完成以下项目后，候选才能晋升：

1. 标准MTU下5/10/20 MSPS基本采集；
2. 20 MSPS双通道连续10分钟，确认跨低32位回绕；
3. 制造监视拥塞并核对DAQD索引跳变位置、数量与DAQS丢样计数；
4. 确认正常无拥塞时索引完全连续；
5. 确认ADC主采集/DMA路径没有新增背压或丢样。

