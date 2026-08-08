# AD9269 PC端采集说明

## 启动

推荐从 DLC pro 主程序点击“ADC数据采集”，这样 ADC 页面会复用主程序已有的 DLC pro 连接。也可以直接运行：

```powershell
python app.py --open-adc
```

板卡固定为 `192.168.20.2`，PC 的 PL 专用网卡固定为 `192.168.20.1/24`。PC 连续监视只允许 5、10、20 MSPS；40/80 MSPS 属于 PS/Linux DMA 路径。

## 通道映射与窗口

软件默认自动校正当前板卡固件的 DCO 边沿顺序，使物理 INA 始终显示为通道 A、物理 INB 始终显示为通道 B。“手动交换 A/B”只用于有意互换两个逻辑通道，并同时作用于示波器显示、HDF5录制和 ADC 00模算法。因此自动锁频窗口中的“通道A/B”始终与对应示波器一致。

通道 A、通道 B、扫频控制和 ADC 自动锁频是独立顶层窗口：

- 互相切换不会把其它窗口压回主窗口后面；
- 最小化 ADC 主窗口不会连带最小化；
- 关闭整个程序时仍会统一停止任务并关闭窗口。

## HDF5录制

录制前可选择：

- 通道 A 或 B；
- 1 MSPS、100 kSPS、10 kSPS或1 kSPS；
- U盘、移动SSD或本地磁盘上的 `.h5` 路径；
- “仅保存ADC波形”或“ADC波形＋DLC pro参数”。

记录速率不会修改 FPGA 的实际采样率，而是按真实64位样点索引等间隔抽取。文件主要包含：

- `samples/raw_code`：原始有符号 ADC 码；
- `samples/voltage_v`：项目当前换算得到的电压；
- `samples/sample_index`：PL真实样点索引；
- `packets/*`：包序号、首样点索引、源样点数和抽取步长；
- `features/*`：块级最小值、最大值、峰峰值、均值和RMS；
- `dlcpro/*`：组合模式下的Scan Offset、Amplitude、Frequency、单位、波形、输出通道和启用状态；
- `quality/*`：网络丢包、PL样点空洞、录制队列丢样等质量统计。

仅波形模式不要求 DLC pro 连接。组合模式录制期间 DLC pro 断开时，ADC仍继续写入，但文件会标记元数据不完整和中断原因。

## ADC 00模自动锁频

此模块直接读取 `int16` 原始码和 1 ms min/max 历史，只使用透射峰，不使用误差信号。算法只控制 PZT 的 `PC Voltage` Scan Offset、Amplitude 和快速扫频频率。

自动模式使用界面设置的快速频率和初始化Amplitude，新安装默认 `10 Hz / 2.5 Vpp`。初始化窗口无峰时保持幅度，以 `+1、-1、+2、-2… V` 搜索Offset；发现最强完整主峰族后，用三角波间隔计算完整理论距离，只做一次方向试探，然后直接跳转并一步缩到最终Amplitude。

最终阶段不再扩大Amplitude，也不再使用理论跳转或正负网格。Offset沿改善方向以`0.01 V`粗调，变差、过零或接近最佳点后恢复最佳值并转为`0.001 V`精调；所有动作限制在缩幅入口默认`±0.09 V`内。无效窗口保持Offset原地复测，只有连续两窗完全无主峰才进行粗步长重新捕获。

未勾选自动FALC时，首个有效最终窗口达标即停止写入；勾选时按用户窗口数确认后执行`Scan Off → Main On → Unlim On`。每次运行仅记录`START / MEASURE / WRITE / END`并自动保存CSV到`captures/auto_lock_logs/`。

首次板测应按“仅观察 → 自动调整但不接管 FALC → 自动 FALC 接管”三步验证，并人工确认目标不是边带。完整公式和恢复策略见 [`reports/adc_peak_balance/ALGORITHM_REPORT.md`](../reports/adc_peak_balance/ALGORITHM_REPORT.md)。

## FPGA下载

ADC页面可选择并记忆 `.bit` 路径，后台调用 Vivado batch 自动连接 `hw_server` 和 Zynq-7000。无需打开 Vivado GUI，但本机必须安装Vivado且USB-JTAG连接正常。软件不内置也不覆盖最终bitstream。
