# AD9269 PC 端说明

这是最终 AD9269 单 ADC 工程的 PC 连续监视入口。运行：

```powershell
python app.py --open-adc
```

板卡固定为 `192.168.20.2`，PC 网卡固定为 `192.168.20.1/24`。PC 路径只允许
5、10、20 MSPS；40、80 MSPS 由 PS/Linux 的独立 Scope DMA 或 Event DMA
处理，不经过 PC 千兆网口。

旧的 `ad9269_daq_gui.py` 仅作为兼容启动器；主程序和协议实现分别位于
`unified_daq_gui.py` 与 `daq_protocol_v2.py`。

## HDF5录制

从DLC pro主程序点击“ADC数据采集”打开采集窗口，可以在录制前选择：

- 通道A或通道B
- 全部样点、1 MSPS、100 kSPS、10 kSPS或1 kSPS
- U盘、移动SSD或本地磁盘上的 `.h5` 保存位置
- “仅保存ADC波形”或“ADC波形＋DLC pro扫描参数”

“DLC pro设置”使用项目现有的官方SDK服务层。通过DLC pro主程序打开采集窗口时
复用主程序连接；单独启动采集窗口时，可以在设置弹窗中选择网络或串口连接。
该弹窗只开放 `Scan Offset` 和 `Scan Amplitude` 的读写，单位使用设备读回值，
不在PC端假设。

降低记录速率只会按真实64位样点索引抽取数据，不会改变FPGA的5/10/20 MSPS
实际采样率。HDF5文件包含：

- `samples/raw_code`：校准无关的原始ADC码
- `samples/voltage_v`：按当前项目换算系数得到的电压
- `samples/sample_index`：原始PL样点索引，丢样位置不会被抹平
- `features/*`：每个UDP数据块的最小值、最大值、峰峰值、均值和RMS
- `dlcpro/*`：组合模式下SDK快照中的扫描开关、偏置、幅度、频率、输出通道、波形和单位
- `quality/*`：网络丢包、PL样点空洞及录制队列丢样统计

仅波形模式不需要连接DLC pro，文件中不创建 `dlcpro` 数据组。组合模式必须先
连接DLC pro并成功读取扫描参数；录制中DLC pro掉线不会停止ADC波形写入，但文件
会标记 `dlcpro_metadata_complete = false` 和中断原因。
