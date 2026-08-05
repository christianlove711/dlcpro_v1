# FALC pro 透射峰寻峰与锁定算法说明

本文档描述当前可视化验证程序中的算法流程，以及后续接入真实采集卡、PZT、偏置和 FALC pro 时应替换的接口。当前实现只用于算法验证，不连接 DLC pro，不直接控制 FALC pro。

相关文件：

- `falcpro_peak_lock_visualizer.py`：示波器式可视化验证程序，支持 CSV/模拟数据、连续三角波扫频、粗扫、细扫、实时日志。
- `falcpro_peak_lock_sim.py`：命令行算法验证脚本，支持模拟波形或 CSV 输入，输出 JSON/CSV 结果。

## 1. 总体目标

实验目标不是用 Python 替代 FALC pro 做高速 PID，而是让 Python 做上层自动化实验员：

1. 产生或记录 1 Hz 三角波扫频。
2. 同步读取透射峰信号和至少一路 PDH/error 信号。
3. 从大范围扫频中找到候选透射峰。
4. 缩小扫频范围，在峰附近小范围反复扫描。
5. 调整慢变量 `PZT center` 和 `bias offset`，让透射峰稳定出现在扫描窗口中。
6. 在透射峰附近找 error 零交叉。
7. 判断零交叉斜率和信噪比是否足够。
8. 确认锁点后接通 FALC pro。
9. 接通后继续监测透射峰、error RMS 和 FALC correction 是否正常。

当前可视化程序把真实硬件替换成 CSV/模拟数据。后续接真实设备时，只需要替换数据源和写参接口，核心判据和状态机可以保留。

## 2. 输入信号

算法至少需要两路同步信号：

| 信号 | 当前程序字段 | 真实设备来源 | 作用 |
|---|---|---|---|
| 透射峰信号 | `transmission` | 光电探测器、腔透射 PD 或等效透射信号 | 找峰、判断是否扫到共振 |
| 误差信号 1 | `error1` | PDH 解调后的 error output，或 FALC error monitor | 找零交叉、判断斜率 |
| 误差信号 2 | `error2` | 备用 error 通道、反相信号或第二路监视信号 | 对照、调试、判断极性 |
| PZT 位置 | `pzt` | 软件扫频设定值、DAQ 输出值或 DLC scan reference | 把信号特征映射到扫描位置 |
| 时间 | `t_s` | DAQ 采集时间戳 | 示波器滚动显示、周期分段 |

CSV 输入推荐列名：

```text
pzt,transmission,error1,error2
```

也可以使用近似列名，例如 `x`、`freq`、`voltage`、`trans`、`pd`、`error`、`err1`、`err2`。真实设备接入后，应统一转换成内部数据结构：

```python
ScanPoint(
    t_s=float,
    pzt=float,
    transmission=float,
    error1=float,
    error2=float,
)
```

## 3. 输出控制量

算法最终输出三个慢控制量和一个动作：

| 输出 | 当前程序行为 | 真实设备接入后 |
|---|---|---|
| `PZT center` | 修改界面 spinbox | 写入 PZT 扫描中心或 DLC/PZT 慢偏置 |
| `bias offset` | 修改界面 spinbox | 写入偏置通道、DC offset 或 FALC input offset |
| `scan span` | 缩小模拟三角波范围 | 写入扫描幅度或外部 DAQ 输出幅度 |
| `engage FALC` | 当前仅进入 `locked` 状态 | 打开 FALC 主环路或解除 hold |

注意：具体写入哪个硬件参数必须以后按真实接线确认。本文档中的 `PZT center` 和 `bias offset` 是算法层抽象，不等同于某个已确认的官方 SDK 参数名。

## 4. 扫频模型

当前程序使用 1 Hz 三角波：

```text
phase = time % 1.0
tri = -1 + 4 * phase       if phase <= 0.5
tri =  3 - 4 * phase       if phase >  0.5
pzt = PZT_center + bias_offset + tri * scan_span / 2
```

真实设备接入时有两种方式：

1. 软件输出三角波到 DAQ analog out，再同步采集透射/error。
2. DLC pro 或其他硬件负责扫频，Python 读取 scan reference 或用时间轴近似映射。

推荐优先使用真实 scan reference 或 DAQ 输出记录作为 `pzt`，不要只依赖软件时间推算。这样可以避免硬件延迟、非线性、输出限幅造成的峰位置误判。

## 5. 状态机

当前可视化程序的自动流程分为三段：

```text
coarse -> fine -> locked
```

建议真实设备版本扩展为：

```text
IDLE
-> PREPARE_SCAN
-> COARSE_SCAN
-> FIND_TRANSMISSION_PEAK
-> FINE_SCAN
-> FIND_ERROR_ZERO
-> TUNE_PZT_AND_BIAS
-> VALIDATE_LOCK_POINT
-> ENGAGE_FALC
-> VERIFY_LOCK
-> MONITOR_LOCK
-> RELOCK 或 FAILED
```

### 5.1 `IDLE`

空闲状态，不输出自动控制动作。

进入条件：

- 程序启动。
- 用户停止自动流程。
- 自动流程失败并等待人工确认。

退出条件：

- 用户点击自动寻峰。
- 外部控制流程启动。

### 5.2 `PREPARE_SCAN`

准备扫频参数。

需要检查：

- DAQ 是否可用。
- 透射/error 通道是否有数据。
- PZT 或偏置输出是否在允许范围内。
- FALC 是否处于安全状态，例如 hold 或未接通。
- 扫描幅度是否不会超过硬件允许范围。

当前模拟参数：

```text
scan_frequency_hz = 1 Hz
scan_span = 数据范围的约 18%
sample_count = 1600 点/周期
```

真实设备建议：

- 先用较慢、较大的三角波粗扫。
- 每个周期至少采到几十到几百个点覆盖目标峰。
- 若目标峰很窄，提高采样率或减小扫描速度。

### 5.3 `COARSE_SCAN`

大范围移动 `PZT center`，直到看见候选透射峰。

当前可视化程序逻辑：

1. 保持较大的 `scan_span`。
2. 每完成一个 1 Hz 扫频周期，对本周期数据运行寻峰。
3. 如果未看到可信峰，则把 `PZT center` 按当前 `scan_span` 的一部分向右移动。
4. 到达数据右边界后回到左边界。
5. 如果看到候选峰，进入 `fine`。

真实设备接入后：

- 每次移动 `PZT center` 或 `bias` 后，应等待一个短暂 settle time。
- 移动步长应小于粗扫 span，保证相邻扫描窗口有重叠。
- 如果连续多轮没有峰，应该扩大搜索范围或提示人工检查光路/腔。

### 5.4 透射峰检测

当前核心判据在 `VisualLockAlgorithm.evaluate()` 中。

处理步骤：

1. 按 `pzt` 对一个扫描周期的数据排序。
2. 对 `transmission` 做滑动平均平滑。
3. 用低百分位估计 baseline：

```text
baseline = percentile(transmission, 15%)
```

4. 用相邻差分的 MAD 估计噪声：

```text
noise = 1.4826 * MAD(diff(transmission)) / sqrt(2)
```

5. 找局部最大值：

```text
trans[i] > trans[i - 1] and trans[i] > trans[i + 1]
```

6. 计算峰高和 SNR：

```text
height = trans[i] - baseline
snr = height / noise
```

7. 满足以下条件才认为是候选透射峰：

```text
height >= min_peak_height
snr >= min_snr
```

当前默认：

```text
min_peak_height = 0.12
min_snr = 5.0
```

真实设备调参建议：

- 先记录几组真实无峰数据，估计噪声底。
- `min_peak_height` 应略高于光强慢漂和电子噪声造成的伪峰。
- `min_snr` 建议从 5 到 10 之间试。
- 如果腔透射峰高度变化大，优先用 SNR 而不是固定电压阈值。

### 5.5 `FINE_SCAN`

看到候选峰后，缩小扫频范围并逐步靠近目标。

当前程序做法：

1. 选择候选位置：

```text
target = error_zero_pzt if exists else peak_pzt
```

2. 进入 fine：

```text
scan_span = max(scan_span * 0.55, target_span)
PZT_center = PZT_center + 0.55 * (target - PZT_center)
bias_offset = bias_offset + 0.20 * (target - PZT_center - bias_offset)
```

3. 后续每个周期继续细调：

```text
center_error = target - (PZT_center + bias_offset)
PZT_center += 0.45 * center_error
bias_offset += 0.20 * center_error
scan_span = max(scan_span * 0.72, target_span)
```

这里故意不是一步到位，而是模拟真实实验中慢慢调 PZT 和偏置，避免因为噪声或假峰一下跳到错误位置。

真实设备接入后建议：

- 每次写 PZT/bias 后等待硬件响应。
- 单步变化量要有限幅，避免 PZT 或偏置突然大跳。
- 若细扫中丢峰，应不要立刻失败，可以回退到上一次候选位置或稍微扩大 span。
- 若连续多次丢峰，再回到 `COARSE_SCAN`。

### 5.6 error 零交叉检测

在候选透射峰附近搜索 error 零交叉。

步骤：

1. 在 `peak_pzt +/- zero_window` 范围内检查 error 信号。
2. 找相邻点符号变化：

```text
error[i - 1] * error[i] <= 0
```

3. 用线性插值估算零交叉位置：

```text
frac = abs(error[i - 1]) / (abs(error[i - 1]) + abs(error[i]))
zero_pzt = pzt[i - 1] + frac * (pzt[i] - pzt[i - 1])
```

4. 估计局部斜率：

```text
slope = (error[right] - error[left]) / (pzt[right] - pzt[left])
```

5. 按斜率和距离打分：

```text
score = abs(slope) / max(abs(zero_pzt - peak_pzt), small_number)
```

6. 选择分数最高的零交叉。

当前默认：

```text
zero_window = 0.09
min_slope = 1.2
```

真实设备调参建议：

- `zero_window` 应根据峰宽设置，通常取峰宽的数倍，而不是无限大。
- 如果 error 信号噪声大，应先平滑或对多个周期平均。
- 如果 error 极性可能反，允许斜率正负都可接受，但要记录极性。
- 如果 FALC 参数要求固定极性，应根据斜率决定是否翻转 error 通道或 FALC polarity。

### 5.7 锁点确认

当前确认条件：

```text
confirmed = found_transmission_peak
            and found_error_zero
            and abs(error_slope) >= min_slope
```

进入 `locked` 前还需要 fine 阶段满足：

```text
abs(center_error) < max(scan_span * 0.045, 1e-5)
scan_span <= target_span * 1.12
fine_rounds >= 3
```

意思是：

- 不是第一次看到峰就认为完成。
- 必须已经缩小扫频范围。
- 必须多轮细调后锁点仍然稳定出现。
- `PZT center + bias_offset` 已接近候选锁点。

真实设备建议增加：

- 连续 N 个周期都能检测到峰。
- 连续 N 个周期零交叉位置漂移小于阈值。
- error slope 符号稳定。
- 透射峰高度没有明显下降。
- FALC 输入没有饱和。

## 6. 接通 FALC pro

当前程序只进入 `locked` 状态，并没有真的控制 FALC pro。

真实设备接入时，`locked` 前后建议分成两个状态：

```text
VALIDATE_LOCK_POINT -> ENGAGE_FALC -> VERIFY_LOCK
```

### 6.1 接通前

应确保：

- FALC 参数已经人工调好或已加载预设。
- error 信号接到 FALC 输入。
- FALC 输出接到正确执行端。
- FALC 输出不会一接通就打到限幅。
- 扫频幅度已足够小，或者准备停止外部扫频。
- PZT/bias 慢变量已经把锁点移到合适位置。

### 6.2 接通动作

真实程序中这里应替换为设备接口，例如：

```python
falc.set_hold(False)
falc.set_main_enabled(True)
```

以上只是伪代码，不是已确认的 SDK 调用名。真实实现必须以官方 SDK 和实际接线为准。

### 6.3 接通后验证

接通后建议采集一段数据，计算：

```text
error_mean
error_rms
transmission_mean
transmission_drop
correction_rms
correction_max_abs
```

判断建议：

```text
error_rms < error_rms_limit
abs(error_mean) < error_mean_limit
correction_max_abs < correction_limit
transmission_mean 没有明显掉到背景
```

如果失败：

- 先 hold FALC 或关闭主环。
- 回到 fine scan。
- 若多次失败，回到 coarse scan 或提示人工检查 FALC 参数。

## 7. 真实设备接入点

当前程序中最重要的替换点如下。

### 7.1 数据源替换

当前：

```python
point = ScanPoint(
    t_s=self.live_elapsed_s,
    pzt=pzt,
    transmission=interp(dataset.x, dataset.transmission, pzt),
    error1=interp(dataset.x, dataset.error1, pzt),
    error2=interp(dataset.x, dataset.error2, pzt),
)
```

真实设备应替换为：

```python
point = daq.read_latest_sample()
```

或每周期批量读取：

```python
cycle_points = daq.acquire_one_scan_cycle()
```

要求输出仍然转换成 `ScanPoint` 列表。

### 7.2 扫频输出替换

当前：

```python
pzt = center + bias + tri * span / 2
```

真实设备可替换为：

```python
scan_output.write_triangle(center=center, bias=bias, span=span, frequency=1.0)
```

或：

```python
dlc_or_pzt.set_scan_center(center)
dlc_or_pzt.set_scan_amplitude(span)
offset_channel.set_bias(bias)
```

具体接口必须按真实硬件确认。

### 7.3 写 PZT/bias 替换

当前：

```python
_set_center_bias_span(center, bias, span)
```

真实设备应拆成：

```python
hardware.set_pzt_center(center)
hardware.set_bias_offset(bias)
hardware.set_scan_span(span)
```

并加入：

- 限幅。
- 写入失败处理。
- settle delay。
- 实际读回值确认。

### 7.4 FALC 接通替换

当前：

```python
self.search_phase = "locked"
```

真实设备应变成：

```python
falc.apply_preset(preset_name)
falc.engage()
verify_lock()
```

其中 `apply_preset` 和 `engage` 是项目层抽象名，真实底层 API 需要以后根据 SDK/设备接口实现。

## 8. 日志设计

当前可视化程序把日志弹到独立窗口，记录类似：

```text
0.00s reset: coarse scan, span=0.72000, center=-1.67600, bias=0
2.00s coarse: move PZT center -> -1.43120, bias=0.00000, span=0.72000
3.00s candidate: transmission peak seen; switch to fine scan
3.00s fine: candidate=-1.07800; shrink span 0.72000->0.39600; PZT center=-1.23700, bias=0.03180
4.00s fine[1]: target=-1.07910, d=+0.12610, PZT center=-1.18030, bias=0.05702, span=0.28512
...
locked: keep rolling; final PZT center=..., bias=..., span=...
```

真实设备版本应额外记录：

- 每次硬件写入是否成功。
- 写入前后读回值。
- DAQ 通道名和量程。
- FALC preset 名称。
- engage 时间。
- verify 结果。
- 失败原因。

建议保存为 CSV 或 JSONL，便于后续分析。

## 9. 推荐参数表

以下参数是算法层初始值，不是硬件规格。

| 参数 | 当前默认 | 作用 | 真实设备调参建议 |
|---|---:|---|---|
| `scan_frequency_hz` | 1 Hz | 三角波扫频速度 | 先慢后快 |
| `sample_count` | 1600 点/周期 | 每周期采样点 | 真实 DAQ 按采样率决定 |
| `coarse_span` | 数据范围约 18% | 粗扫窗口 | 应覆盖足够宽的频率范围 |
| `target_span` | 粗扫 span 的约 16% | 细扫最终范围 | 应略大于峰宽和漂移 |
| `coarse_step` | `0.34 * span` | 粗扫中心移动 | 保证窗口重叠 |
| `fine_span_factor` | 0.55 / 0.72 | 缩小范围 | 不要一步缩太小 |
| `min_peak_height` | 0.12 | 峰高阈值 | 按真实 PD 电压标定 |
| `min_snr` | 5.0 | 峰信噪比 | 噪声大时提高 |
| `zero_window` | 0.09 | error 零交叉搜索窗口 | 按峰宽调整 |
| `min_slope` | 1.2 | error 斜率阈值 | 按 error 单位调整 |

## 10. 异常与回退

真实设备版本必须处理以下情况：

1. 粗扫找不到峰：
   - 增大搜索范围。
   - 降低阈值但不要低于噪声。
   - 提示检查光路、腔、PD、调制和接线。

2. 看到峰但没有 error 零交叉：
   - 检查 error 通道选择。
   - 检查 PDH 解调相位。
   - 尝试 error2 或反相。
   - 暂不接通 FALC。

3. fine 阶段丢峰：
   - 回退到上一次候选位置。
   - 稍微增大 `scan_span`。
   - 连续多次丢峰后回到 coarse。

4. 接通 FALC 后 error RMS 变大：
   - 立即 hold 或关闭 FALC 输出。
   - 检查 polarity/gain/offset。
   - 回到 fine scan。

5. FALC correction 接近限幅：
   - 说明慢变量中心不合适或漂移太大。
   - 自动调整 bias/PZT center。
   - 必要时重新寻峰。

## 11. 最小真实接入架构

建议真实接入时先做四个抽象层：

```text
signal_source.py
  read_cycle() -> list[ScanPoint]

scan_actuator.py
  set_triangle(center, bias, span, frequency)
  set_center_bias_span(center, bias, span)

falc_controller.py
  apply_preset(name)
  engage()
  hold()
  read_monitor()

peak_lock_algorithm.py
  evaluate(cycle_points)
  advance_state(decision)
```

这样 GUI、算法、采集、硬件写参是分开的。后续即使从 CSV 换成 Digilent AD3、MCC、NI 或其他 DAQ，也只需要换 `signal_source.py` 和 `scan_actuator.py`。

## 12. 当前版本和真实设备版本的差异

当前版本：

- 用 CSV 或模拟数据代替真实采集。
- 用界面 spinbox 代替真实 PZT/bias 写入。
- 用 `locked` 状态代替真实 FALC engage。
- 用插值生成示波器滚动波形。

真实设备版本必须补充：

- DAQ 同步采集。
- PZT/bias 输出。
- 硬件限幅和安全检查。
- FALC 接通和 hold。
- 接通后 monitor 验证。
- 失锁回退和重锁。

## 13. 实施顺序建议

1. 保留当前 CSV 可视化程序，用真实示波器导出的 CSV 验证峰检测和 error 零交叉判据。
2. 接入 DAQ 只读模式：先只采集 transmission/error，不控制 PZT/bias。
3. 接入扫频输出：用软件生成 1 Hz 三角波，确认实时波形和 CSV 回放一致。
4. 接入 PZT center/bias 慢调：只允许小步、限幅、记录日志。
5. 接入 FALC engage：先人工确认后接通。
6. 增加自动 engage 和 verify。
7. 增加失锁监测和自动重锁。

这样风险最低，也最容易定位每一步的问题。
