# 工作日志

## 说明

这份文档用于独立记录项目开发日志，便于在不翻聊天记录的情况下恢复开发上下文。

如果需要了解当前最适合继续做什么，配合以下文档一起看：

- [DEV_HANDOFF_2026-05-15.md](/Users/YieFanMeng/Documents/DlcPro_v1/DEV_HANDOFF_2026-05-15.md)
- [ONE_CLICK_LOCK_PLAN.md](/Users/YieFanMeng/Documents/DlcPro_v1/ONE_CLICK_LOCK_PLAN.md)

## 2026-04-29

- 创建项目目录，作为当前 DLC pro 自定义 GUI 项目的本地工作起点

## 2026-04-30

- 建立项目说明文档雏形，形成最初的项目目标与实现范围记录

## 2026-05-01

- 按工程阶段推断，这一天大概率处于“把项目目标从说明文档转成可执行 GUI 方案”的准备阶段
- 应该已经明确了三条基础路线：使用 TOPTICA 官方 SDK、采用 `PySide6`、并把主界面做成后续可继续扩展的桌面控制台，而不是一次性脚本

## 2026-05-02

- 按工程阶段推断，这一天大概率在为主程序骨架做铺垫，包括连接层、主窗口、双语文本和基础参数展示的结构准备
- 从后续文件成型方式看，这一阶段应该已经开始固定 `app.py + dlcpro_service.py + ui_text.py` 这种核心拆分思路

## 2026-05-03

- 形成当前主代码文件雏形，包括 [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)、[dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)、[ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)

## 2026-05-04

- 建立并稳定 `Laser` 按钮弹出独立 `QMainWindow` 的交互模型
- 统一主界面与 `Laser` 弹窗的整体风格
- 完成 `CC / TC / PC` 基础控制区
- 完成模块级步进控制与“当前调节目标”交互
- 增加关闭确认框
- 修复掉线后后台轮询重复弹框问题

## 2026-05-05

- 将 `Laser` 独立窗口正式拆到 [windows/laser_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/laser_window.py)
- `Scan&Lock / Relock / Stabilization` 改成独立弹窗入口
- 拆分 `widgets/laser/*` 与 `controllers/laser_controller.py`
- `Scan&Lock` 独立演进，接入 `SC` 与 `Lock Settings` 基础项

## 2026-05-06

- 新增 `FALC` 导航入口
- 将 [windows/falcpro_window.py](/Users/YieFanMeng/Documents/DlcPro_v1/windows/falcpro_window.py) 改造成真实页面
- 接入 `falc1.input / main / unlim` 基础参数

## 2026-05-07 到 2026-05-14

- 持续扩展 `Scan&Lock / FALC / Auto Lock` 页面与 service 参数树
- 补充双语文本
- 持续整理窗口结构和页面拆分
- 逐步把锁频相关参数从“只读/占位”推进到“真实可写入”

说明：

- 这几天没有在当前仓库里整理出逐日的独立明细
- 但从现有代码结果可以确认，重点工作集中在锁频链路、FALC 参数页、Auto Lock 页面与 service 层参数扩展

## 2026-05-15

今天的工作重点是 `Auto Lock / 一键锁定` 的流程化和产品化。

### 已完成

- 完成 `Auto Lock V1` 状态机雏形
  - 自动预扫
  - 自动缩扫
  - 自动找候选点
  - 自动选点
  - 自动切到 `Lock Without Lockpoint`
  - 自动居中
  - 自动开锁
  - 自动读 `lock_state`
  - 失败切下一套固定模板

- 完成 `service` 层锁频扩展参数接入
  - `lock_state / lock_state_txt`
  - `lock.error_channel`
  - `lock.falc_selection`
  - `candidate_filter.*`
  - `lockin.*`
  - `falc.path_selection`

- `Scan&Lock / FALC / Auto Lock` 页面补齐关键控件
  - `Error Input`
  - `FALC Selection`
  - `FALC Path`
  - `Candidate Filter`
  - 若干 FALC 状态读回

- `Auto Lock` 页面 UI 重构
  - 运行状态置顶
  - 运行状态改成单行状态栏
  - `一键锁定链路配置` 单独一排
  - `本地预设` 单独一排
  - `预扫并缩扫` 增加说明与确认框

- `本地预设` 交互重做
  - 下拉框改成按钮切换
  - 支持 `新增预设 / 保存预设 / 删除预设`
  - 切换预设前增加确认框
  - 创建/保存/切换/删除成功均弹提示框
  - `保存预设` 不再偷偷承担“新增”语义

- `预设内容` 展示重做
  - 纯文本改为卡片式
  - 改成按宽度自适应列数
  - 明确区分“会保存什么 / 不会保存什么 / 具体保存值”

- 修复运行问题
  - 修复 `QTextEdit` import 缺失导致的启动报错

### 今天解决掉的具体问题

- 用户不清楚 `预扫并缩扫` 会做什么
- 用户不清楚预设到底保存什么
- 下拉框式预设切换很不顺手
- 点预设名字立刻切换，容易误操作
- `新增预设` 和 `保存预设` 语义混乱
- `Auto Lock` 参数区布局左右失衡
- 预设内容展示不适合快速比较

### 当前还没做完

- 自动 PID / FALC 调参策略还没确定
- `Auto Lock V1` 成功/失败判据还需继续收紧
- 固定模板比例还没做成可配置模板组

### 当前最适合继续开发

1. 收紧 `Auto Lock V1` 的成功/失败判据与模板重试逻辑
2. 把固定模板组做成可配置并纳入预设
3. 等师兄确认后再接自动 PID / FALC 调参策略

