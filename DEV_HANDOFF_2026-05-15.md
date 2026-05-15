# DLC pro GUI 开发接手说明（2026-05-15）

## 1. 这份文档的用途

这份文档用于在更换电脑后，快速恢复当前项目的开发上下文，尤其是 `Auto Lock / 一键锁定` 相关工作。

本文档重点回答四件事：

1. 项目现在已经做到哪里了
2. 今天具体做了什么
3. 当前最重要的问题已经解决了哪些
4. 下一步最适合开发什么

## 2. 当前项目整体状态

项目已经不是“连接设备 demo”，而是一套可继续扩展的 DLC pro 自定义 GUI。

当前已形成的主要模块：

- 主窗口连接区：网络 / 串口连接、状态显示、轮询与任务调度
- `Laser` 独立窗口：`CC / TC / PC`
- `Scan&Lock` 独立窗口：`SC / Lock Settings / PID`
- `FALC` 独立窗口
- `Relock` 独立窗口
- `Stabilization` 独立窗口
- `Auto Lock` 独立窗口

当前代码结构已经基本固定为：

- [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)
- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)
- [controllers/](/Users/YieFanMeng/Documents/DlcPro_v1/controllers)
- [windows/](/Users/YieFanMeng/Documents/DlcPro_v1/windows)
- [widgets/](/Users/YieFanMeng/Documents/DlcPro_v1/widgets)
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)

## 3. Auto Lock 当前已经开发到哪里

### 3.1 流程能力

当前 `Auto Lock` 已经不是空页面，而是具备 V1 状态机雏形：

- 自动预扫
- 自动缩扫
- 自动找候选锁点
- 自动选点
- 自动切到 `Lock Without Lockpoint`
- 自动把目标移到中心
- 自动开锁
- 自动读取 `lock_state`
- 失败后自动切换到下一套固定模板

当前模板策略还是固定的：

- `1.0`
- `0.7`
- `0.45`

即：基于当前扫描幅度生成 3 套宽扫模板，再按缩扫比例进入窄扫。

### 3.2 参数链路

`service` 层已经补上了后续一键锁定需要的关键参数：

- `lock_state / lock_state_txt`
- `lock.error_channel`
- `lock.falc_selection`
- `candidate_filter.*`
- `lockin.*`
- `falc.path_selection`
- 若干 FALC 状态读回

这些参数已经不仅在 `Scan&Lock / FALC` 页可见，也已经镜像到 `Auto Lock` 页。

### 3.3 预扫功能

已经实现了一个“小闭环”：

- 点一次按钮
- 自动打开扫描（如果需要）
- 按当前 `Scan Amplitude` 扫一段时间
- 自动把 `Scan Amplitude` 缩小到指定比例

这个功能是后续真正一键锁定的前半段基础。

## 4. 今天完成的工作

今天主要集中在 `Auto Lock` 的产品化和可交互性改造。

### 4.1 运行状态区

- 把运行状态放到页面最上方
- 改成一整行的状态展示，而不是纵向堆叠

相关文件：

- [widgets/auto_lock/status_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/status_panel.py)

### 4.2 Auto Lock 参数区重排

- `一键锁定链路配置` 改成单独一整排
- `本地预设` 改成单独一整排
- 不再把二者左右硬拼

相关文件：

- [widgets/auto_lock/config_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/config_panel.py)

### 4.3 预扫并缩扫说明

- 给 `预扫并缩扫` 增加固定说明文案
- 点击按钮时先弹确认/说明框
- 明确说明该功能只做“扫频 + 缩扫”，不会自动找锁点，也不会自动开锁

相关文件：

- [windows/auto_lock_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/auto_lock_window.py)
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)

### 4.4 本地预设机制重做

原先是下拉框切换，现在已经改成按钮式预设管理：

- 一组可点的预设按钮
- `新增预设`
- `保存预设`
- `删除预设`

同时新增了这些交互规则：

- 点预设按钮不会立即切换，而是先弹确认框
- `新增预设` 负责真正创建新预设
- `保存预设` 只允许保存已选中的预设，不再偷偷新增
- `删除预设` 会先确认再删
- 保存成功 / 切换成功 / 删除成功都会弹提示框

相关文件：

- [windows/auto_lock_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/auto_lock_window.py)
- [widgets/auto_lock/config_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/config_panel.py)
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)

### 4.5 预设内容展示重做

预设内容不再是纯文本，而是改成卡片式展示，并支持按可用宽度自适应列数：

- 窄窗口：1 列
- 中窗口：2 列
- 宽窗口：3 列
- 更宽：4 列

卡片内容包括：

- 当前预设/当前界面快照
- 会保存的内容
- 不会保存的内容
- 具体保存值
- 基础参数
- 候选点过滤
- 高级参数

### 4.6 启动错误修复

修复了一个启动时 `QTextEdit` 未导入导致的 `NameError`。

## 5. 今天解决掉的具体问题

今天明确解决了这些用户层问题：

1. `运行状态` 区位置和布局不直观
2. `预扫并缩扫` 的按钮行为不清楚
3. 用户不知道本地预设到底保存什么
4. 下拉框式预设切换不方便
5. 预设按钮点击即切换，容易误操作
6. `新增预设` 和 `保存预设` 语义混乱
7. 本地预设区与链路配置区布局失衡
8. 预设内容展示过于拥挤，不利于比较

## 6. 当前还没做完的关键点

### 6.1 自动 PID / FALC 调参

这部分还没有做，原因不是代码没写，而是策略还没定。

当前结论：

- SDK 没有确认到现成的“自动整定 PID”接口
- 这部分需要结合师兄的实验经验来定规则
- 更可能是“DLC lock 负责找点和开锁，FALC 负责实际环路参数”

所以自动调参目前应视为“待确认策略”的阶段，而不是“待补代码”这么简单。

### 6.2 V1 状态机还要继续收紧

虽然 `Auto Lock V1` 已经有雏形，但还需要继续补强：

- 候选点为空时的重试逻辑
- 候选点很多时的选择策略
- 更清晰的成功/失败判据
- 更稳定的模板切换逻辑
- 更清晰的失败日志

### 6.3 固定模板还没有做成可编辑模板组

当前模板是代码写死的：

- `1.0`
- `0.7`
- `0.45`

后续建议把它变成可配置模板组，并纳入预设保存。

## 7. 当前最适合继续开发什么

在自动 PID 策略没和师兄确认之前，最适合继续做的是：

### 第一优先级

继续开发 `Auto Lock V1` 的成功/失败判据与重试逻辑。

原因：

- 这部分不依赖自动 PID 策略
- 这部分是后续自动调参的基础
- 做完后就能先形成一个可实际跑实验的 V1 自动锁频流程

建议继续补：

- 明确 `lock_state == Locked` 之外是否需要连续稳定若干次轮询
- 超时后切下一模板的条件
- 候选点为空时的退避策略
- 锁上后监测掉锁的判据

### 第二优先级

把固定模板改造成可配置模板组，并纳入本地预设。

### 第三优先级

等师兄确认后，再进入自动 PID / FALC 调参策略。

## 8. 换电脑后如何快速恢复

### 8.1 最重要先看哪几份文件

建议按这个顺序恢复上下文：

1. [DEV_HANDOFF_2026-05-15.md](/Users/YieFanMeng/Documents/DlcPro_v1/DEV_HANDOFF_2026-05-15.md)
2. [WORK_LOG.md](/Users/YieFanMeng/Documents/DlcPro_v1/WORK_LOG.md)
3. [ONE_CLICK_LOCK_PLAN.md](/Users/YieFanMeng/Documents/DlcPro_v1/ONE_CLICK_LOCK_PLAN.md)
4. [windows/auto_lock_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/auto_lock_window.py)
5. [controllers/auto_lock_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/auto_lock_controller.py)
6. [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)

### 8.2 启动命令

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/toptica-lab/bin/python /Users/YieFanMeng/Documents/DlcPro_v1/app.py
```

### 8.3 建议重新验证的内容

换电脑后建议先做这几项最小验证：

1. 主程序能正常启动
2. `Auto Lock` 窗口能打开
3. 预设按钮能新增 / 保存 / 删除 / 确认切换
4. `预扫并缩扫` 能正常弹说明框
5. 语法检查能过

建议使用：

```bash
python3 -m py_compile \
  /Users/YieFanMeng/Documents/DlcPro_v1/app.py \
  /Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py \
  /Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py \
  /Users/YieFanMeng/Documents/DlcPro_v1/windows/auto_lock_window.py \
  /Users/YieFanMeng/Documents/DlcPro_v1/controllers/auto_lock_controller.py
```

## 9. 当前重要文件

- [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)
- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
- [controllers/auto_lock_controller.py](/Users/YieFanMeng/Documents/DlcPro_v1/controllers/auto_lock_controller.py)
- [windows/auto_lock_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/auto_lock_window.py)
- [widgets/auto_lock/config_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/config_panel.py)
- [widgets/auto_lock/status_panel.py](/Users/YieFanMeng/Documents/DlcPro_v1/widgets/auto_lock/status_panel.py)
- [ONE_CLICK_LOCK_PLAN.md](/Users/YieFanMeng/Documents/DlcPro_v1/ONE_CLICK_LOCK_PLAN.md)
- [WORK_LOG.md](/Users/YieFanMeng/Documents/DlcPro_v1/WORK_LOG.md)

