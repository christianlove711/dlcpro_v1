# PL直连PC板测记录

状态：**NOT RUN — STATIC TIMING FAILED**

禁止将 `top_pl_udp_v2_test.bit` 下载到板卡或晋升为最终版。只有新的候选满足全局 WNS/WHS≥0、TNS/THS=0 且四类 RGMII 双沿裕量均为正后，才填写下表。

| 项目 | 验收条件 | 结果 |
|---|---|---|
| PC网卡 | Realtek PCIe GbE，协商1 Gbit/s | 待测 |
| 5 MSPS | 标准MTU，波形正确，无新增丢样 | 待测 |
| 10 MSPS | 标准MTU，波形正确，无新增丢样 | 待测 |
| 20 MSPS | 标准MTU，波形正确，无新增丢样 | 待测 |
| 双通道20 MSPS | 连续30分钟 | 待测 |
| 网线拔插 | 50次，每次恢复1 Gbit/s | 待测 |
| GUI重连 | 控制、采集与链路恢复 | 待测 |
| 巨帧 | 仅记录9014 B能力，不启用 | 未启用 |

