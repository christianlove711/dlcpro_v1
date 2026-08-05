# Zynq-7020 AD9269 单 ADC、双 DMA/双 HP 最终交付

本交付只保留 AD9269。原 AD9280、AD9708 DAC、正弦 ROM、J25 按键和硬触发逻辑已从最终 PL 工程移除，J25 FPGA 信号脚已释放，可供屏幕使用。

## 两种 PS 工作模式

- 普通示波器：Scope DMA（`0x40410000`）经 `S_AXI_HP1` 写 DDR，使用 `IRQ_F2P[1]`。
- 自动锁频：Event DMA（`0x40400000`）经 `S_AXI_HP0` 写 DDR，使用 `IRQ_F2P[0]`。

两套 DMA、SG 描述符、FIFO、IRQ 和用户态缓冲区相互独立。软件可以同时初始化两套 DMA，但硬件只允许当前 `ACQ_MODE` 对应的数据路径产生帧。

## 交付目录

- `01_FPGA源码/vivado_project/AXI_DMA.xpr`：可直接打开的最终 Vivado 工程骨架。
- `01_FPGA源码` 下的 `rtl`、`bd`、`constraints`、`sim` 和 `scripts`：便于审阅的源码快照及一键构建脚本。
- `02_最终硬件`：通过签核的 `top.bit`、XSA 和 HWH。
- `03_PC_GUI`：PL UDP PC 界面；连续原始数据支持 5/10/20 MSPS。
- `04_Linux`：双 DMA 驱动、设备树、用户态库/示例和协议文档。
- `05_验证报告`：时序、DRC、方法学、资源、功耗和仿真报告。

详细的架构设计、开发问题根因、修复过程、剩余风险和优化优先级见
`00_交付说明/PL_DEVELOPMENT_REVIEW_AND_OPTIMIZATION.md`。

## 关键规格

- AD9269：5/10/20/40/80 MSPS；DCO=T9、D0=V5、ADC CLK=U15。
- Event 帧：8320 B；64 个 SG 槽，每槽 12288 B。
- Scope 帧：32832 B；16 个 SG 槽，每槽 36864 B。
- Scope BRAM：2×8192×32 bit；默认 10 FPS，最高 20 FPS。
- DAQ AXI-Lite：`0x43C10000`。
- PL UDP：板卡 `192.168.20.2`，PC `192.168.20.1`；40/80 MSPS 禁止连续网络监视。

## Linux 启动顺序

1. 为当前模式提交全部 SG 描述符并执行 `issue_pending`。
2. 设置对应 DMA `ARMED`。
3. 写入模式、采样率和 Scope 配置，再执行 `CONFIG_COMMIT`。
4. 写 `START`。
5. 模式切换时按以下顺序执行：
   `STOP → 解除旧 ARMED → 清旧路径 → 提交新描述符 → 设置新 ARMED → CONFIG_COMMIT → START`。

XSA 不内嵌 bitstream。`top.bit`、XSA 和 HWH 独立交付，以避开 Vivado 2020.2 的硬件平台 bit 关联问题。
