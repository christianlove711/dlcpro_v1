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
  当前主窗口、`Laser` 弹窗、UI 事件处理、后台任务调度、轮询刷新、错误提示都在这里
- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)
  DLC pro 通信层，负责连接、读快照、写 CC/TC/PC 参数
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
  中英文文案、参数显示名称、单位文本
- [PROJECT_OVERVIEW.md](/Users/YieFanMeng/Documents/DlcPro_v1/PROJECT_OVERVIEW.md)
  当前实现细节与项目总览
- [Manual.md](/Users/YieFanMeng/Documents/DlcPro_v1/Manual.md)
  设备手册
- [python-lasersdk](/Users/YieFanMeng/Documents/DlcPro_v1/python-lasersdk/index.html)
  本地 SDK 文档

## 当前结构判断

现在项目还能继续开发，但 `app.py` 已经承担了太多职责：

- 主窗口布局
- `Laser` 窗口布局
- `CC / TC / PC` 页面构建
- 所有按钮/输入框事件
- 后台任务调度
- 断线处理
- 退出确认
- 文本刷新

这对继续加 `FALC`、扫频、`Scan&Lock`、`Relock`、`Stabilization` 会越来越吃力。

## 推荐的下一步重构方向

我建议不要立刻“大重构”，而是做一轮低风险拆分：

1. 先保留 `MainWindow` 和 `DlcProService`
2. 把 `Laser` 独立窗口拆到单独文件
3. 把 `CC / TC / PC` 三个面板拆成独立 widget 文件
4. 把通用控件封装抽出来
   例如：开关按钮、步进按钮行、带“当前调节”的数值输入行
5. 让主窗口只负责导航、连接区、全局状态和窗口调度

一个比较合适的目标结构可以是：

```text
DlcPro_v1/
  app.py
  dlcpro_service.py
  ui_text.py
  windows/
    laser_window.py
  widgets/
    cc_panel.py
    tc_panel.py
    pc_panel.py
    step_target_spinbox_row.py
    toggle_button.py
  controllers/
    laser_controller.py
```

第一阶段甚至不一定要引入 `controllers/`，只拆 `windows/` 和 `widgets/` 就能明显减轻 `app.py` 的压力。

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
