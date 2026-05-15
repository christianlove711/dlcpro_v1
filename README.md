# DLC pro 3.3.3 PySide6 Control App

这是一个基于 TOPTICA 官方 Python SDK 与 `PySide6` 的自定义 DLC pro 控制界面项目，当前重点围绕 `Laser`、`Scan&Lock` 等独立弹窗逐步开发。

本项目实现时遵循两条原则：

- 编程接口以官方 SDK `toptica.lasersdk.dlcpro.v3_3_3` 为准
- 设备行为、安全限制、模块职责以 [Manual.md](/Users/YieFanMeng/Documents/DlcPro_v1/Manual.md) 为准

## 当前状态

目前已经实现：

- 网络连接和串口连接
- 基础设备参数读取与展示
- `Laser` 按钮弹出独立 `QMainWindow`
- `Scan&Lock / Relock / Stabilization` 按钮弹出独立 `QMainWindow`
- `CC - 电流控制` 模块
- `TC - 温度控制` 模块
- `PC - 压电控制` 模块
- `Scan&Lock` 弹窗中的 `SC - Scan Control`
- `Scan&Lock` 弹窗中的 `Lock Settings` 基础项
- `Scan&Lock` 弹窗中的 `PID 1 / PID 2` 基础项
- `FALC` 独立弹窗中的 `Input / Main / Unlim` 基础区
- 中英文界面文本切换
- 主界面与 `Laser` 弹窗一致的深灰主题样式
- 后台线程 + 定时轮询的设备刷新机制
- 大步长调节确认
- 断线后只提示一次的轮询错误处理
- 程序关闭确认框
- `windows / widgets / controllers` 初步分层

当前 `Lock Settings` 已接入的 SDK 字段为：

- `laser1.dl.lock.lock_enabled`
- `laser1.dl.lock.hold`
- `laser1.dl.lock.spectrum_input_channel`
- `laser1.dl.lock.type`
- `laser1.dl.lock.pid_selection`
- `laser1.dl.lock.lock_without_lockpoint`

当前 `PID 1 / PID 2` 已接入的 SDK 字段为：

- `laser1.dl.lock.pid1.enabled`
- `laser1.dl.lock.pid1.gain.all`
- `laser1.dl.lock.pid1.gain.p`
- `laser1.dl.lock.pid1.gain.i`
- `laser1.dl.lock.pid1.gain.d`
- `laser1.dl.lock.pid1.gain.i_cutoff_enabled`
- `laser1.dl.lock.pid1.gain.i_cutoff`
- `laser1.dl.lock.pid1.output_channel`
- `laser1.dl.lock.pid1.sign`
- `laser1.dl.lock.pid1.outputlimit.enabled`
- `laser1.dl.lock.pid1.outputlimit.max`
- `laser1.dl.lock.pid2.enabled`
- `laser1.dl.lock.pid2.gain.all`
- `laser1.dl.lock.pid2.gain.p`
- `laser1.dl.lock.pid2.gain.i`
- `laser1.dl.lock.pid2.gain.d`
- `laser1.dl.lock.pid2.output_channel`
- `laser1.dl.lock.pid2.sign`
- `laser1.dl.lock.pid2.outputlimit.enabled`
- `laser1.dl.lock.pid2.outputlimit.max`

## 已实现弹窗内容

`Laser` 独立窗口当前包含以下模块：

- `CC - Current Control`
  支持设定电流、实际电流、最大电流限制、前馈控制、ARC
- `TC - Temperature Control`
  支持启用、设定温度、实际温度、ARC
- `PC - Piezo Control`
  支持启用、设定电压、实际电压、Slew Rate、ARC、Pressure Compensation

`Scan&Lock` 独立窗口当前包含以下模块：

- `SC - Scan Control`
  支持 `Enable / Scan Amplitude / Scan Offset / Scan Output / Scan Frequency / Scan Shape`
- `Lock Settings`
  支持 `Enable / Hold / Lock Input Signal / Lock Type / PID Selection / Lock Without Lockpoint`
- `PID 1`
  支持 `Gain / P / I / D / Output Channel / Sign Positive / Use I cut-off / I cut-off Frequency / Use Limit / Limit / Enable PID`
- `PID 2`
  支持 `Gain / P / I / D / Output Channel / Sign Positive / Use Limit / Limit / Enable PID`

`FALC` 独立窗口当前包含以下模块：

- `Input`
  支持 `Input Gain / Offset`
- `Main`
  支持 `Enable / I1 / I2 / I3 / D1 / D2 / Gain`
- `Unlim`
  支持 `Enable / Hold / Input Offset / Output Range / Slew Rate / Gain(readback) / Sign Positive`

说明：

- `Laser / Scan&Lock / Relock / Stabilization` 都不是主界面中的切页，而是独立顶层窗口
- 弹窗样式与主界面使用同一套应用级样式表
- 普通文字标签已避免出现不必要的深色背景块
- `FALC` 弹窗内部自建下拉框已单独处理宽度与 popup 宽度，不再依赖主窗口下拉框辅助逻辑
- `FALC Main` 的频点下拉目前采用“原始设备整数值写回 + 人类可读频点文本显示”的安全策略，完整映射仍待更多官方依据或真实设备读值进一步收紧
- `Scan&Lock` 中的 `PID` 显示单位当前按 `Manual.md` 中的输出通道规则动态推导：`CC Current` 显示电流单位，其余已接入输出通道显示电压单位；这是渲染层规则，不改变 SDK 数值写入接口
- 当前界面已开始区分“可离线预览的选择类控件”和“必须连接后才能真实写入的控件”：例如下拉框可在未连接时切换显示，但其写入处理会继续受连接状态保护

关于 `Scan&Lock` 的结构说明：

- `Scan&Lock` 使用独立的 `widgets/scan_lock/` 与 `controllers/scan_lock_controller.py`
- 虽然 `SC` 和 `Lock Settings` 底层仍然复用同一个 DLC pro service / SDK 接口层，但页面 widget 和页面 controller 不再挂在 `Laser` 页面名下
- `PID 1 / PID 2` 也沿用这个结构：共享底层 service 的已验证 SDK 节点，但保持 `Scan&Lock` 页面自己的 widget、渲染和交互逻辑
- 这样后续继续开发 `Lockpoint`、`ReLock`、`PDH`、`FALC` 相关功能时，不会再被 `Laser` 页面的控件命名和布局耦合住

## 数值步进交互

当前采用的是模块级步进控制方案：

- `CC / TC / PC` 各有一排自己的步进按钮
- 每个可编辑数值框右侧有一个“当前调节”按钮
- 点击哪个“当前调节”，该模块的步进按钮就绑定到哪个输入框
- 未连接设备时也可以切换步进目标和步进档位

这个交互模式是为了避免两种问题：

- 每个字段都放一排步进按钮，界面过于臃肿
- 只靠输入焦点隐式切换目标，用户看不出来当前步进控制的是谁

## 运行方式

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/toptica-lab/bin/python /Users/YieFanMeng/Documents/DlcPro_v1/app.py
```

## 主要文件

- [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)
  当前主窗口、连接区、全局导航、后台任务调度、错误提示都在这里
- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)
  DLC pro 通信层，负责连接、读快照、写 `CC / TC / PC / SC / Lock Settings / PID / FALC` 参数
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
  中英文文案、参数显示名称、选项枚举映射、单位文本
- [windows/](/Users/YieFanMeng/Documents/DlcPro_v1/windows)
  独立窗口外壳与页面装配，当前已包含 `laser_window.py`、`scan_lock_window.py`、`falcpro_window.py` 及其他窗口文件
- [widgets/](/Users/YieFanMeng/Documents/DlcPro_v1/widgets)
  复用控件与功能面板，当前已按页面拆分为 `widgets/laser/`、`widgets/scan_lock/` 与通用控件
- [controllers/](/Users/YieFanMeng/Documents/DlcPro_v1/controllers)
  页面级流程与渲染协调，当前已包含 `LaserController`、`ScanLockController`
- [PROJECT_OVERVIEW.md](/Users/YieFanMeng/Documents/DlcPro_v1/PROJECT_OVERVIEW.md)
  当前实现细节与项目总览
- [Manual.md](/Users/YieFanMeng/Documents/DlcPro_v1/Manual.md)
  设备手册
- [python-lasersdk](/Users/YieFanMeng/Documents/DlcPro_v1/python-lasersdk/index.html)
  本地 SDK 文档

## 当前结构判断

现在项目已经比最初清晰很多，但后续继续扩展时仍要注意职责边界：

- `app.py`：全局外壳、连接、导航、任务调度
- `windows/`：独立窗口和页面拼装
- `widgets/`：模块面板与通用控件
- `controllers/`：页面级业务流程和渲染协调

这套结构比之前更适合继续加 `Lockpoint`、`ReLock`、`PDH`、`FALC`、`Stabilization` 等后续页面能力。

## 推荐的下一步重构方向

当前这一轮重构已经先完成了第一阶段：

1. 保留 `MainWindow` 和 `DlcProService`
2. 把 `Laser` 独立窗口拆到 `windows/laser_window.py`
3. 把 `CC / TC / PC` 三个面板拆到 `widgets/laser/`
4. 把通用控件抽到 `widgets/common_controls.py`
5. 增加 `controllers/laser_controller.py` 承接激光页文本刷新和快照渲染
6. 把 `Scan&Lock` 独立窗口拆到 `windows/scan_lock_window.py`
7. 为 `Scan&Lock` 建立 `widgets/scan_lock/` 和 `controllers/scan_lock_controller.py`

下一步比较合适的是：

1. 继续补完 `Scan&Lock` 下的 `Lockpoint / ReLock / PDH / Window/Detection` 相关区域
2. 让 `Relock / Stabilization / FALC pro` 逐步接入各自页面结构和 controller
3. 继续把主窗口中的业务事件按功能迁移到更明确的 controller 中
4. 让更多模块直接复用 `widgets/common_controls.py` 里的通用控件

一个比较合适的目标结构可以是：

```text
DlcPro_v1/
  app.py
  dlcpro_service.py
  ui_text.py
  windows/
    laser_window.py
    scan_lock_window.py
    relock_window.py
    stabilization_window.py
    falcpro_window.py
  widgets/
    laser/
      cc_panel.py
      tc_panel.py
      pc_panel.py
    scan_lock/
      sc_panel.py
      lock_panel.py
    common_controls.py
  controllers/
    laser_controller.py
    scan_lock_controller.py
```

## 依赖说明

- `PySide6`
- `toptica-lasersdk`
- `ifaddr`
- `pyserial`

说明：

- 若本机缺少 `ifaddr` 或 `pyserial`，界面会对网卡/串口枚举做降级提示
- 当前串口路径依然采用定时刷新，不依赖参数订阅
- 当前大量选择类控件支持未连接时的本地预览切换，但真实设备写入仍以连接状态和 SDK 写入保护为准

## 当前检查结果

我已用以下命令检查核心代码语法：

```bash
python -m py_compile /Users/YieFanMeng/Documents/DlcPro_v1/app.py /Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py /Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py
```

当前没有语法错误。

## 工作日志

更完整的独立工作日志见：

- [WORK_LOG.md](/Users/YieFanMeng/Documents/DlcPro_v1/WORK_LOG.md)
- [DEV_HANDOFF_2026-05-15.md](/Users/YieFanMeng/Documents/DlcPro_v1/DEV_HANDOFF_2026-05-15.md)

说明：

- 本地目录创建时间可追溯到 `2026-04-29`
- `PROJECT_OVERVIEW.md` 的本地时间可追溯到 `2026-04-30`
- `app.py / dlcpro_service.py / ui_text.py` 的本地时间可追溯到 `2026-05-03`
- 当前仓库可见的首个 git 提交日期是 `2026-05-04`
- `2026-05-01` 和 `2026-05-02` 当前没有查到可靠的本地文件改动或 git 提交痕迹，因此以下内容按工程阶段连续性做合理推断，并非可核验历史记录

### 2026-04-29

- 创建项目目录，作为当前 DLC pro 自定义 GUI 项目的本地工作起点

### 2026-04-30

- 建立项目说明文档雏形，形成最初的项目目标与实现范围记录

### 2026-05-01

- 按工程阶段推断，这一天大概率处于“把项目目标从说明文档转成可执行 GUI 方案”的准备阶段
- 应该已经明确了三条基础路线：使用 TOPTICA 官方 SDK、采用 `PySide6`、并把主界面做成后续可继续扩展的桌面控制台，而不是一次性脚本
- 可以视为从“想做什么”过渡到“准备怎么搭”的承上启下阶段

### 2026-05-02

- 按工程阶段推断，这一天大概率在为主程序骨架做铺垫，包括连接层、主窗口、双语文本和基础参数展示的结构准备
- 从后续文件成型方式看，这一阶段应该已经开始固定 `app.py + dlcpro_service.py + ui_text.py` 这种核心拆分思路
- 可以视为从“方案准备”过渡到“最小可运行代码骨架”的阶段

### 2026-05-03

- 形成当前主代码文件雏形，包括 [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)、[dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)、[ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
- 项目从“规划/说明阶段”进入“可运行代码搭建阶段”

### 2026-05-04

完成了项目从“最小连接与电流控制 demo”向“可继续扩展的 Laser 控制窗口”阶段的升级，主要包括：

- 建立并稳定了 `Laser` 按钮弹出独立 `QMainWindow` 的交互模型
- 统一了主界面与 `Laser` 弹窗的整体风格、配色、边框、间距和标签背景处理
- 完成 `CC - Current Control` 区域的增强整理
- 新增 `TC - Temperature Control` 模块
- 新增 `PC - Piezo Control` 模块
- 为 `CC / TC / PC` 建立模块级步进控制
- 将步进交互优化为“每个可编辑数值框右侧显式选择当前调节目标”
- 完成 `CC / TC / PC` 的中英文界面文本统一与单位显示整理
- 修复未连接状态下只读框单位缺失的问题
- 修复步进按钮不应依赖设备连接状态的问题
- 增加程序关闭确认框
- 修复拔掉网线后后台轮询重复弹出 `Device rejected request / 设备拒绝请求` 的问题，改为只提示一次并重置为未连接状态
- 更新中英文 skill，沉淀弹窗风格一致、模块级步进和轮询错误处理等流程经验
- 更新 README，使其反映当前真实功能、结构现状和下一步重构方向

### 2026-05-05

- 将 `Laser` 独立窗口正式拆到 [windows/laser_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/laser_window.py)
- 将主窗口中的 `Scan&Lock / Relock / Stabilization` 从页签入口改为和 `Laser` 一样的独立弹窗入口
- 将 `CC / TC / PC` 分别拆到 `Laser` 专属目录：
  [widgets/laser/cc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/laser/cc_panel.py)
  [widgets/laser/tc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/laser/tc_panel.py)
  [widgets/laser/pc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/laser/pc_panel.py)
- 抽出复用控件到 [widgets/common_controls.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/common_controls.py)，统一管理开关按钮、步进按钮行和带“当前调节”按钮的输入行
- 引入 [controllers/laser_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/laser_controller.py)，把激光页文本刷新、读回渲染和页面级协调逻辑从主窗口中拆出
- 建立 [windows/scan_lock_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/scan_lock_window.py)、[widgets/scan_lock/](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/scan_lock)、[controllers/scan_lock_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/scan_lock_controller.py)，让 `Scan&Lock` 开始独立演进
- 将 `Laser` 页面里的旧 `SC` 面板移除，避免 `Laser` 与 `Scan&Lock` 共用同一套页面 widget / 页面 controller
- 在 `Scan&Lock` 弹窗中实现 `SC - Scan Control`
- 在 `Scan&Lock` 弹窗中实现 `Lock Settings` 基础项，并接入以下 SDK 字段：
  `laser1.dl.lock.lock_enabled`、
  `laser1.dl.lock.hold`、
  `laser1.dl.lock.spectrum_input_channel`、
  `laser1.dl.lock.type`、
  `laser1.dl.lock.pid_selection`、
  `laser1.dl.lock.lock_without_lockpoint`
- 按 Manual 中确认的枚举补上 `Lock Input Signal / Lock Type / PID Selection` 选项文本
- 补充了简短中文注释，说明结构拆分目的和关键协调规则
- 更新中英文 skill，把“同一 SDK 参数组可被多个页面复用，但页面 widget/controller 不应混挂”的经验写成后续开发标准
- 更新 README，使其反映当前真实窗口结构、目录结构和 `Scan&Lock` 进展

### 2026-05-06

- 新增 `FALC` 导航入口，使其与 `Laser / Scan&Lock / Relock / Stabilization` 一样作为独立顶层弹窗工作
- 将原本仅占位的 [windows/falcpro_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/falcpro_window.py) 改造成真实页面，完成 `Input / Main / Unlim` 三个基础分组
- 在 [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py) 中新增 `FalcSnapshot / FalcMainSnapshot / FalcUnlimSnapshot`，把 `falc1` 状态读回组织成更清晰的快照子树
- 接入 `falc1.input.gain / offset`
- 接入 `falc1.main.enabled / gain.all / gain.i1 / i2 / i3 / d1 / d2` 及其 enable 状态
- 接入 `falc1.unlim.enabled / hold / input_offset / output_range / slew_rate / gain / sign`
- 在 [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py) 中补齐 `FALC` 页面事件处理、刷新渲染和断开连接后的重置流程
- 修复 `FALC` 独立弹窗里下拉框显示不全的问题，确认“主窗口下拉宽度修正不会自动作用于弹窗内部自建 `QComboBox`”，因此将宽度适配逻辑直接下沉到弹窗类内部
- 对 `FALC Main` 的频点下拉采用“原始设备整数值写回 + 频点文本显示”的过渡方案，避免在官方资料未给出完整映射表时把推断误当成已验证枚举
- 修复主窗口关闭后辅助弹窗仍然存活的问题，在共享弹窗基类中区分“用户手动关闭时隐藏窗口”和“应用退出时真正关闭窗口”两条生命周期
- 调整主窗口 busy/连接态控件策略，不再把所有选择类控件都做成“未连接不可用”，开始明确区分“可离线预览的选择类控件”和“必须连机后才可真实写入的控件”
- 在 `Scan&Lock` 中新增 `PID 1 / PID 2` 面板，完成 [widgets/scan_lock/pid_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/scan_lock/pid_panel.py) 以及对应的页面装配、事件处理和快照渲染
- 在 [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py) 中接入 `laser1.dl.lock.pid1.*` 与 `laser1.dl.lock.pid2.*` 相关字段的读取和写入，包括 `gain / output_channel / sign / outputlimit / enabled`，并为 `PID 1` 额外接入 `i_cutoff_enabled / i_cutoff`
- 根据 `Manual.md` 中 PID 输出通道定义，在渲染层为 `PID` 增益与限幅动态推导单位显示：`CC Current` 走电流单位，其余已接入输出通道走电压单位；保持 service 层继续只处理纯数值和已验证 SDK 节点
- 更新 skill，把今天沉淀出的三条规则写成后续开发标准：断连预览与真实写入分离、辅助弹窗的退出生命周期、以及“SDK 无单位节点时按 Manual 在渲染层推导单位”的处理方式
- 根据今天的实现经验，更新 skill：补充独立弹窗下拉宽度、FALC 页面本地化结构、以及 preset 原始值/显示值分层处理的开发规则
- 更新 README，使其反映 `FALC` 页面当前能力和今天的开发进展
- 连上真实 DLC pro 后，对 `Laser / Scan&Lock` 做了一轮现场交互修正，把“普通设定值”与“上限类高风险值”的确认框策略分开，保留 `Current Clip` 这类上限写入确认，移除温度、压电、扫描等常规调节上的频繁弹框
- 修复 `Laser` 页面调节电流时页面会被直接拉到底部的问题，刷新和写入前后开始显式保留弹窗滚动位置
- 修复 `Scan Shape / Scan Output` 以及 `Scan&Lock` 相关下拉框在后台轮询时被强制收起的问题：当用户正在展开或聚焦下拉框时，轮询刷新会暂缓同步该控件
- 修复后台轮询对正在编辑数值框的覆盖问题：当前有焦点的 `spinbox` 在 render 阶段不再被读回值立即写回
- 调整 busy 策略，区分“真实写入忙碌”和“后台 poll 刷新”，避免轮询时把整页控制区冻结，改善连机状态下的连续调参体验
- 重新总结并更新中英文 skill，把今天沉淀出的几条现场经验写成开发标准：确认框边界、轮询不打断用户交互、滚动位置保留、以及自动写入与后台轮询共用执行器时的防吞写处理
