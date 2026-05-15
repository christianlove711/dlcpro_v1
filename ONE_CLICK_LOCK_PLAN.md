# DLC pro 一键锁定实现方案

## 1. 文档目标

本文档用于规划当前项目中的“一键锁定”功能实现。

这里的“一键锁定”不是单纯打开 `lock_enabled`，而是一条完整流程：

1. 自动扫频
2. 自动寻找候选锁点
3. 自动选择目标锁点
4. 自动切换到合适的锁定链路
5. 自动尝试预设 PID / FALC 参数
6. 自动判断是否锁住
7. 失败后自动重试
8. 成功后进入持续监测与自动重锁

本文档优先依据以下资料：

- SDK：`toptica.lasersdk.dlcpro.v3_3_3`
- 手册：`Manual.md`
- 项目当前代码结构

## 2. 当前结论

### 2.1 当前项目已经具备的基础

当前项目已经实现了以下与一键锁定强相关的部分：

- `SC - Scan Control`
- `Lock Settings` 基础项
- `PID 1 / PID 2` 基础项
- `Auto Lock` 独立窗口
- `Auto Lock` 中的候选点读取与显示
- `Auto Lock` 中的自动选点、自动居中、自动开锁
- `ReLock` 基础参数页
- `FALC` 基础参数页

当前 `Auto Lock` 控制器的实际行为是：

1. 读取 `laser1.dl.lock.candidates`
2. 自动选择一个候选点
3. 切换 `lock_without_lockpoint`
4. 把 `scan.offset` 移到目标位置
5. 打开 `lock_enabled`
6. 轮询 `lock_state`
7. 失败后重新搜索

这说明当前实现已经不是空壳，而是“一键锁定”的早期雏形。

### 2.2 当前项目还缺少的关键能力

如果目标是做老师想要的“真正可用的一键锁定”，当前还缺：

- `Lock` 与 `FALC` 的挂接关系
- 自动锁定前的合法性检查
- 多套预设锁定模板
- 自动调参和自动重试策略
- 更细的锁定成功判据
- 锁后稳定性评估

## 3. 官方能力边界

### 3.1 官方已经明确支持的能力

根据 SDK 和手册，可以确认 DLC pro 官方支持：

- 扫描显示
- 自动生成锁点候选
- 锁点选择
- `Lock Without Lockpoint`
- `PID 1 / PID 2`
- `ReLock`
- `Lock-In`
- `PDH`
- `FALC Selection`
- `FALC path selection`

可直接确认的 `lock` 节点包括：

- `type`
- `lock_without_lockpoint`
- `state`
- `state_txt`
- `lock_enabled`
- `hold`
- `spectrum_input_channel`
- `error_channel`
- `error_channel_inverted`
- `pdh_selection`
- `pid_selection`
- `falc_selection`
- `setpoint`
- `relock`
- `reset`
- `window`
- `pid1`
- `pid2`
- `lockin`
- `lockpoint`
- `candidate_filter`
- `candidates`
- `locking_delay`
- `background_trace`
- `lock_tracking`
- `find_candidates()`
- `select_lockpoint(...)`
- `open()`
- `close()`

### 3.2 官方未明确提供的能力

当前没有在 SDK 中确认到“自动整定 PID”之类的直接接口。

因此：

- 自动找锁点：官方已经支持
- 自动开锁：官方已经支持
- 自动调 PID / 自动调 FALC：需要项目自己实现策略层

这意味着“一键锁定”里的难点不在 SDK 调用本身，而在上层控制逻辑设计。

## 4. 对老师需求的工程化拆解

建议把老师要的“一键锁定”拆成两个阶段。

### 4.1 一键锁定 V1

目标：

- 在正常实验条件下
- 按一次按钮
- 自动找到目标谱线并尽可能锁上

特点：

- 主要依赖预设模板
- 不追求自动找到最优 PID
- 先保证成功率和流程完整性

### 4.2 一键锁定 V2

目标：

- 在 V1 已经能稳定锁上的基础上
- 对锁后参数做小范围自动优化

特点：

- 增加自动试探
- 增加评分函数
- 增加回退机制

建议先做 V1，再做 V2。

## 5. 当前项目建议补充的服务层参数

以下内容建议优先补进 [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)。

### 5.1 `Lock Settings` 扩展项

建议新增到 `DeviceSnapshot`：

- `lock_state`
- `lock_state_txt`
- `lock_error_channel`
- `lock_error_channel_inverted`
- `lock_pdh_selection`
- `lock_falc_selection`
- `lock_setpoint`
- `lock_locking_delay`

建议新增 setter：

- `set_lock_error_channel`
- `set_lock_error_channel_inverted`
- `set_lock_pdh_selection`
- `set_lock_falc_selection`
- `set_lock_setpoint`
- `set_lock_locking_delay`

### 5.2 `Lock Candidate Filter` 扩展项

建议新增到 `DeviceSnapshot`：

- `lock_candidate_edge_min_distance`
- `lock_candidate_top_enabled`
- `lock_candidate_bottom_enabled`
- `lock_candidate_positive_edge_enabled`
- `lock_candidate_negative_edge_enabled`
- `lock_candidate_peak_noise_tolerance`

说明：

- `peak_noise_tolerance` 是否存在，需要以当前设备型号和 SDK 实际参数树再确认
- 手册多次提到 `P/N Tolerance`，但项目当前还没接出来

建议新增 setter：

- `set_lock_candidate_edge_min_distance`
- `set_lock_candidate_top_enabled`
- `set_lock_candidate_bottom_enabled`
- `set_lock_candidate_positive_edge_enabled`
- `set_lock_candidate_negative_edge_enabled`
- `set_lock_candidate_peak_noise_tolerance`

### 5.3 `Lock-In` 扩展项

建议新增到 `DeviceSnapshot`：

- `lockin_modulation_enabled`
- `lockin_frequency`
- `lockin_amplitude`
- `lockin_phase_shift`
- `lockin_output_channel`

建议新增 setter：

- `set_lockin_modulation_enabled`
- `set_lockin_frequency`
- `set_lockin_amplitude`
- `set_lockin_phase_shift`
- `set_lockin_output_channel`

### 5.4 `FALC` 挂接与状态扩展项

当前 `FalcSnapshot` 还不够支撑一键锁定。

建议新增：

- `path_selection`
- `hold_state`
- `main_lock_state`
- `unlim_lock_state`
- `unlim_regulating_state`
- `mon_config`
- `main_use_external_input`

建议新增 setter：

- `set_falc1_path_selection`
- `set_falc1_mon_config`
- `set_falc1_main_use_external_input`

### 5.5 `Lock` 事件调用封装

建议新增 service 方法：

- `find_lock_candidates()`
- `select_lockpoint(x, y, type_)`
- `open_lock()`
- `close_lock()`

即使 V1 不一定都用到，也建议 service 层先补齐，后续实现更稳。

## 6. 建议补充的界面结构

### 6.1 `Scan&Lock` 页建议新增的控制区

建议在 `Scan&Lock` 页面新增以下区域：

- `Advanced Lock Settings`
- `Candidate Filter`
- `Lock-In / PDH`
- `FALC Link`

#### `Advanced Lock Settings`

建议控件：

- `Error Input Signal`
- `Error Input Inverted`
- `PDH Selection`
- `Locking Delay`
- `Setpoint`

#### `Candidate Filter`

建议控件：

- `Edge Min Distance`
- `Peak Candidates`
- `Trough Candidates`
- `Positive Edge Candidates`
- `Negative Edge Candidates`
- `Peak/Noise Tolerance`

#### `FALC Link`

建议控件：

- `FALC Selection`
- `FALC Path Selection`
- `Main Lock State` 只读
- `Unlim Lock State` 只读
- `Unlim Regulating State` 只读

### 6.2 `Auto Lock` 页建议新增的配置项

建议在 [widgets/auto_lock/config_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/config_panel.py) 中新增：

- `Lock Profile` 下拉
- `Auto Retry Count`
- `PID/FALC Strategy` 下拉
- `Initial Narrow Scan Amplitude`
- `Narrow Scan Frequency`
- `Success Hold Time`
- `RMS Check Window`
- `Max Output Excursion Ratio`

### 6.3 `FALC` 页面建议新增的内容

建议在 [windows/falcpro_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/falcpro_window.py) 中补充：

- `Path Selection`
- `Monitor Output Config`
- `Use External Gain Input`
- `Hold State` 只读
- `Main Lock State` 只读
- `Unlim Lock State` 只读
- `Unlim Regulating State` 只读

## 7. 建议新增的数据结构

建议新增一个“一键锁定模板”数据结构，用于把实验经验写成配置。

建议放在：

- 新文件 `controllers/auto_lock_profiles.py`
- 或新文件 `one_click_lock_profiles.py`

建议字段：

- `name`
- `lock_type`
- `scan_output_channel`
- `scan_amplitude_wide`
- `scan_frequency_wide`
- `scan_amplitude_narrow`
- `scan_frequency_narrow`
- `lock_input_channel`
- `error_channel`
- `pid_selection`
- `falc_selection`
- `falc_path_selection`
- `pid1_defaults`
- `pid2_defaults`
- `falc_main_defaults`
- `falc_unlim_defaults`
- `candidate_strategy`
- `candidate_filter_defaults`
- `success_window_ms`
- `retry_sequence`

这样做的好处是：

- 不把实验规则写死在 UI 控件回调里
- 可以针对不同实验对象保存不同模板
- 后续做配置保存更方便

## 8. 一键锁定状态机设计

建议不要把一键锁定写成一串 if/else 和定时器堆叠，而是明确状态机。

建议状态如下：

1. `idle`
2. `prepare`
3. `wide_scan`
4. `find_candidates`
5. `pick_candidate`
6. `narrow_scan_setup`
7. `coarse_lock_attempt`
8. `lock_verify`
9. `parameter_retry`
10. `post_lock_optimize`
11. `monitoring`
12. `reacquire`
13. `failed`

### 8.1 `prepare`

动作：

- 检查连接状态
- 检查当前锁是否已打开
- 检查当前 `pid_selection`
- 检查输出通道是否已配置
- 检查如果要用 FALC，则 `falc_selection` 和 `path_selection` 是否完整
- 停止普通页面刷新，切换到自动锁定专用轮询

### 8.2 `wide_scan`

动作：

- 应用宽扫描模板
- 打开 scan
- 等待若干个刷新周期
- 确保图上已经形成稳定候选

### 8.3 `find_candidates`

动作：

- 主动调用 `find_lock_candidates()` 或读取 `candidates`
- 应用 `candidate_filter`
- 若没有候选，继续等待或失败重试

### 8.4 `pick_candidate`

动作：

- 按当前策略自动挑一个候选点

候选策略建议支持：

- `nearest_center`
- `highest_y`
- `leftmost`
- `rightmost`
- `nearest_last_locked`
- `manual_seed_then_nearest`

### 8.5 `narrow_scan_setup`

动作：

- 缩小 scan amplitude
- 调高或调低 scan frequency 到模板值
- 可选切换 `lock_without_lockpoint`
- 把目标点移动到中心附近

### 8.6 `coarse_lock_attempt`

动作：

- 应用一套预设 PID/FALC 参数
- 打开 `lock_enabled`
- 记录起始时间
- 开始监测锁定状态

### 8.7 `lock_verify`

动作：

- 观察 `lock_state`
- 观察 `tracking`
- 观察 `background_trace`
- 观察锁定保持时间
- 观察输出是否撞上 limit

成功判据建议至少满足：

- `lock_state` 进入 locked 状态
- 持续保持超过 `success_window_ms`
- 输出不长期顶到 limit
- 目标点没有快速丢失

### 8.8 `parameter_retry`

动作：

- 如果当前参数失败，关闭 lock
- 切换到下一组模板参数
- 重新尝试

### 8.9 `post_lock_optimize`

这是 V2 使用的状态。

动作：

- 锁上后小幅调整一个参数
- 如果评分更好则保留
- 如果评分更差则回退

### 8.10 `monitoring`

动作：

- 周期性检查是否掉锁
- 若掉锁则转到 `reacquire`

### 8.11 `reacquire`

动作：

- 关闭 lock
- 恢复到宽扫描或窄扫描
- 根据上次成功点优先尝试附近候选

## 9. V1 推荐策略

### 9.1 设计原则

V1 不做真正意义上的“自动整定最优 PID”。

V1 只做：

- 自动找点
- 自动试预设
- 自动验证
- 自动切换下一套参数重试

这会比直接做连续自动调参稳很多。

### 9.2 推荐的 V1 锁定模板策略

每个实验类型准备 3 组参数模板：

1. `Conservative`
2. `Balanced`
3. `Aggressive`

每组模板包括：

- `PID 1 / PID 2` 参数
- `FALC Main / Unlim` 参数
- scan 宽窄切换参数

推荐流程：

1. 先用 `Conservative`
2. 如果锁不上，切 `Balanced`
3. 如果还是不行，再切 `Aggressive`
4. 全部失败则报告失败并保留最后波形

### 9.3 如果实验室主要用 FALC pro

V1 更建议优先用：

- `lock.falc_selection`
- `falc.path_selection`
- 固定一套 `Main + Unlim` 预设

而不是先在数字 PID 上做复杂自动搜索。

原因：

- 这更贴近实验室实际工作方式
- 也更符合手册中 FALC 被用作 Click & Lock 关联路径的设计

## 10. V2 自动调参建议

### 10.1 不建议直接全空间搜索

不建议一开始就让程序自动扫描：

- `P`
- `I`
- `D`
- `Main Gain`
- `I1`
- `I2`
- `I3`
- `D1`
- `D2`
- `Unlim Slew Rate`
- `Unlim Output Range`

原因：

- 组合空间太大
- 很容易把锁搞丢
- 试探时间过长

### 10.2 推荐的 V2 顺序

建议按下面顺序微调：

1. 先锁上
2. 先试主增益 `gain all`
3. 再试 `I` 或 `Unlim`
4. 最后才试更激进的微分或更高带宽滤波

### 10.3 推荐评分函数

建议综合以下指标：

- 锁定持续时间
- 误差信号 RMS
- `tracking` 漂移量
- 输出离 limit 的安全裕度
- 掉锁次数

可以定义一个简单评分：

- 锁住且噪声更小，加分
- 有振荡，减分
- 输出撞 limit，重罚
- 掉锁，直接失败

## 11. 推荐代码结构变更

### 11.1 controller 层

建议新增：

- [controllers/one_click_lock_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/one_click_lock_controller.py)
- [controllers/auto_lock_profiles.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/auto_lock_profiles.py)

职责建议：

- `AutoLockController`
  继续负责当前自动找点/开锁基础逻辑
- `OneClickLockController`
  负责更完整的一键锁定状态机

也可以反过来，把现有 `AutoLockController` 升级成完整状态机，但那样重构量更大。

### 11.2 widget 层

建议新增：

- `widgets/auto_lock/strategy_panel.py`
- 或在现有 `config_panel.py` 中逐步扩展

### 11.3 service 层

建议继续保持“所有设备访问都集中在 service 层”的原则，不要把 SDK 调用散落到 controller 和 window 里。

## 12. 推荐开发顺序

### 第一步

补齐 service 层缺失参数：

- `lock.falc_selection`
- `falc.path_selection`
- `lock.error_channel`
- `lockin.*`
- `candidate_filter.*`
- `lock_state_txt`

### 第二步

补齐 UI：

- `FALC Link`
- `Candidate Filter`
- `Advanced Lock Settings`

### 第三步

把当前 `Auto Lock` 流程升级成模板驱动：

- 支持 `Lock Profile`
- 支持多组参数重试

### 第四步

实现锁定成功判据：

- 保持时间
- 状态检查
- limit 检查

### 第五步

实现 V1 一键锁定。

### 第六步

在 V1 稳定后，再加 V2 锁后自动优化。

## 13. 不建议现在就做的事情

以下内容不建议第一版就上：

- 自动连续扫描全 PID 参数空间
- 自动学习所有不同谱线的最佳参数
- 同时支持所有 lock type 和所有实验配置
- 在没有模板和实验经验前做完全黑箱优化

原因不是不能做，而是第一版容易失控、难调、难验收。

## 14. 对当前项目的直接判断

当前项目适合继续做一键锁定，原因有三点：

1. 已经有 `Auto Lock` 基础流程，不是从零开始
2. 已经有 `PID / ReLock / FALC` 相关页面基础
3. service 层结构比较适合继续扩展官方参数树

当前项目不适合直接跳到“全自动最优调参”，原因也有三点：

1. `Lock` 与 `FALC` 的关键挂接参数还没接全
2. 还没有模板化实验经验
3. 还没有明确的锁定评分函数

## 15. 本文档建议的近期交付目标

建议近期目标定为：

“在典型实验配置下，实现可演示、可复现、可自动重试的一键锁定 V1”

这版的定义是：

- 可以自动找候选点
- 可以自动选择目标点
- 可以自动切换到预设锁定链路
- 可以自动尝试 2 到 3 组预设参数
- 可以自动判断锁定成功或失败
- 可以在掉锁后自动重找和重锁

如果这版做稳了，再继续做 V2 的自动微调，会更符合实际研发节奏。

