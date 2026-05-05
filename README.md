# DLC pro 3.3.3 PySide6 Control App

这是一个基于 TOPTICA 官方 Python SDK 与 `PySide6` 的自定义 DLC pro 控制界面项目，当前重点围绕 `laser` 独立弹窗进行开发。

本项目实现时遵循两条原则：

- 编程接口以官方 SDK `toptica.lasersdk.dlcpro.v3_3_3` 为准
- 设备行为、安全限制、模块职责以 [Manual.md](/Users/YieFanMeng/Documents/DlcPro_v1/Manual.md) 为准

## 当前状态

目前已经实现：

- 网络连接和串口连接
- 基础设备参数读取与展示
- `Laser` 按钮弹出独立 `QMainWindow`
- `CC - 电流控制` 模块
- `TC - 温度控制` 模块
- `PC - 压电控制` 模块
- 中英文界面文本切换
- 主界面与 `Laser` 弹窗一致的深灰主题样式
- 后台线程 + 定时轮询的设备刷新机制
- 大步长调节确认
- 断线后只提示一次的轮询错误处理
- 程序关闭确认框
- `windows / widgets / controllers` 初步分层

## Laser 弹窗已实现内容

`Laser` 独立窗口当前包含以下模块：

- `CC - Current Control`
  支持设定电流、实际电流、最大电流限制、前馈控制、ARC
- `TC - Temperature Control`
  支持启用、设定温度、实际温度、ARC
- `PC - Piezo Control`
  支持启用、设定电压、实际电压、Slew Rate、ARC、Pressure Compensation

说明：

- `Laser` 不是主界面中的切页，而是独立顶层窗口
- 弹窗样式与主界面使用同一套应用级样式表
- 普通文字标签已避免出现不必要的深色背景块

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
  DLC pro 通信层，负责连接、读快照、写 CC/TC/PC 参数
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
  中英文文案、参数显示名称、单位文本
- [windows/](/Users/YieFanMeng/Documents/DlcPro_v1/windows)
  独立窗口外壳与页面装配，当前已包含 `laser_window.py` 及其他预留窗口文件
- [widgets/](/Users/YieFanMeng/Documents/DlcPro_v1/widgets)
  复用控件与功能面板，当前已包含 `CcPanel`、`TcPanel`、`PcPanel` 和通用控件
- [controllers/](/Users/YieFanMeng/Documents/DlcPro_v1/controllers)
  页面级流程与渲染协调，当前已包含 `LaserController`
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

这套结构比之前更适合继续加 `FALC`、扫频、`Scan&Lock`、`Relock`、`Stabilization`。

## 推荐的下一步重构方向

当前这一轮重构已经先完成了第一阶段：

1. 保留 `MainWindow` 和 `DlcProService`
2. 把 `Laser` 独立窗口拆到 `windows/laser_window.py`
3. 把 `CC / TC / PC` 三个面板拆到独立 widget 文件
4. 把通用控件抽到 `widgets/common_controls.py`
5. 增加 `controllers/laser_controller.py` 承接激光页文本刷新和快照渲染

下一步比较合适的是：

1. 让 `Scan&Lock / Relock / Stabilization / FALC pro` 逐步接入各自窗口类
2. 继续把主窗口中的业务事件按功能迁移到更明确的 controller 中
3. 让更多模块直接复用 `widgets/common_controls.py` 里的通用控件

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
    common_controls.py
    cc_panel.py
    tc_panel.py
    pc_panel.py
  controllers/
    laser_controller.py
```

## 依赖说明

- `PySide6`
- `toptica-lasersdk`
- `ifaddr`
- `pyserial`

说明：

- 若本机缺少 `ifaddr` 或 `pyserial`，界面会对网卡/串口枚举做降级提示
- 当前串口路径依然采用定时刷新，不依赖参数订阅

## 当前检查结果

我已用以下命令检查核心代码语法：

```bash
python -m py_compile /Users/YieFanMeng/Documents/DlcPro_v1/app.py /Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py /Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py
```

当前没有语法错误。

## 工作日志

说明：

- 本地目录创建时间可追溯到 `2026-04-29`
- `PROJECT_OVERVIEW.md` 的本地时间可追溯到 `2026-04-30`
- `app.py / dlcpro_service.py / ui_text.py` 的本地时间可追溯到 `2026-05-03`
- 当前仓库可见的首个 git 提交日期是 `2026-05-04`
- `2026-05-01` 和 `2026-05-02` 当前没有查到可靠的本地文件改动或 git 提交痕迹，因此不编造具体工作内容

### 2026-04-29

- 创建项目目录，作为当前 DLC pro 自定义 GUI 项目的本地工作起点

### 2026-04-30

- 建立项目说明文档雏形，形成最初的项目目标与实现范围记录

### 2026-05-01

- 当前未查到可靠的本地文件改动或 git 历史记录，暂不补写具体内容

### 2026-05-02

- 当前未查到可靠的本地文件改动或 git 历史记录，暂不补写具体内容

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
- 新建 `Scan&Lock / Relock / Stabilization / FALC pro` 的独立窗口文件占位
- 将 `CC / TC / PC` 分别拆成独立 widget：
  [widgets/cc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/cc_panel.py)
  [widgets/tc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/tc_panel.py)
  [widgets/pc_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/pc_panel.py)
- 抽出复用控件到 [widgets/common_controls.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/common_controls.py)，统一管理开关按钮、步进按钮行和带“当前调节”按钮的输入行
- 引入 [controllers/laser_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/laser_controller.py)，把激光页文本刷新、读回渲染和页面级协调逻辑从主窗口中拆出
- 补充了简短中文注释，说明结构拆分目的和关键协调规则
- 更新中英文 skill，把窗口拆分、widget 复用、controller 引入时机、中文注释要求写成后续开发标准
