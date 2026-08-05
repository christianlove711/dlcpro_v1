# DLC pro 3.3.3 项目总览

## 1. 项目目标

本项目基于 TOPTICA 官方 Python SDK 和 `PySide6`，实现一个面向 `DLC pro 3.3.3` 的最小可用自定义控制界面。

当前阶段重点完成了这几个功能：

- 连接 DLC pro 3.3.3
- 读取当前设备参数并显示
- 读取当前电流
- 写入设定电流
- 支持多档电流调节精度
- 写入前二次确认

本次实现遵循的依据：

- SDK 依据：`toptica.lasersdk.dlcpro.v3_3_3`
- 手册依据：`Manual.md`

## 2. 当前文件结构

- [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py)
  PySide6 主界面、刷新逻辑、写入确认逻辑、输入框保护逻辑。
- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py)
  DLC pro 通信层，负责连接、读参数、写电流、计算当前可写入最大电流。
- [ui_text.py](/Users/YieFanMeng/Documents/DlcPro_v1/ui_text.py)
  中英文界面文本和参数显示名称。
- [README.md](/Users/YieFanMeng/Documents/DlcPro_v1/README.md)
  简要启动说明。

## 3. 已实现功能

### 3.1 连接设备

支持两种连接方式：

- 网络连接：SDK 的 `NetworkConnection`
- 串口连接：SDK 的 `SerialConnection`

说明：

- 这是按 SDK 官方连接模型实现的，没有绕开 SDK 自己写协议。
- 串口路径没有 monitoring line，所以这里统一使用定时刷新，而不是参数订阅。

### 3.2 读取当前设备参数

当前界面会显示一组已确认参数，包括：

- `system-label`
- `serial-number`
- `fw-ver`
- `system-type`
- `system-model`
- `uptime-txt`
- `emission`
- `interlock-open`
- `laser1:dl:cc:enabled`
- `laser1:dl:cc:emission`
- `laser1:dl:cc:current-set`
- `laser1:dl:cc:current-act`
- `laser1:dl:cc:current-clip`
- `laser1:dl:cc:current-clip-tuning`
- `laser1:dl:cc:current-clip-limit`
- `laser1:dl:cc:use-current-clip-tuning`
- `laser1:dl:cc:status-txt`
- `system-messages:latest-message`

## 4. 电流控制逻辑

### 4.1 当前读取和写入参数

当前电流相关实现基于 SDK 中已确认存在的参数：

- 实际电流：`laser1:dl:cc:current-act`
- 设定电流：`laser1:dl:cc:current-set`

其中：

- 读取当前电流使用 `current_act.get()`
- 写入设定电流使用 `current_set.set(...)`

### 4.2 当前激光器最大电流

你特别强调“每个激光器最大电流不一样”，所以这版没有写死一个固定上限，而是直接读取当前设备上的几个真实参数：

- `current_clip`
- `current_clip_tuning`
- `current_clip_limit`
- `use_current_clip_tuning`

然后在 service 层计算一个“当前可写入最大电流”：

- 如果启用了 `Use Tuning Clip`，取
  `min(current_clip, current_clip_tuning, current_clip_limit)`
- 如果没启用，取
  `min(current_clip, current_clip_limit)`

对应代码在：

- [dlcpro_service.py](/Users/YieFanMeng/Documents/DlcPro_v1/dlcpro_service.py:1)

这意味着：

- 不同激光头的限制会反映到界面里
- 输入框的最大值也会随着当前设备状态变化

### 4.3 输入框不被自动刷新覆盖

这部分是专门为你后面提出的问题加的。

逻辑目标：

- 你手动改了“设定电流”但还没点写入时，定时刷新不能把你的输入覆盖掉
- 只有在你没有手动修改，或者设备返回值已经和你输入一致时，输入框才恢复自动同步

实现思路：

- `current_set_dirty`
  表示输入框里是否存在“用户改过但未同步完成”的值
- `current_set_programmatic_update`
  用来区分“程序写回输入框”和“用户手动改输入框”

关键代码在：

- [app.py](/Users/YieFanMeng/Documents/DlcPro_v1/app.py:1)

## 5. 调节精度

目前支持这些步进档位：

- 百位：`100 mA`
- 十位：`10 mA`
- 个位：`1 mA`
- 一位小数：`0.1 mA`
- 两位小数：`0.01 mA`
- 三位小数：`0.001 mA`

这部分是通过 `QDoubleSpinBox.setSingleStep(...)` 和 `setDecimals(...)` 联动实现的。

## 6. 写入确认

点击“写入电流”后不会立刻发命令，而是先弹确认框。

确认后才会真正调用：

- `device.laser1.dl.cc.current_set.set(...)`

这样可以减少误操作。

## 7. 安全说明

依据 `Manual.md`，当前界面已加入一条关键提醒：

- 对带 `MOTOR pro` 的激光头，在进行 motor scan 之前应启用 `Use Tuning Clip`，否则可能损伤激光二极管。

这里目前只是做提示，没有强制控制逻辑。

## 8. 线程与刷新

当前实现使用：

- 主线程负责 GUI
- 后台线程负责设备通信
- 主线程定时轮询 Future 完成情况，再回主线程更新界面

这样做的原因是：

- 之前 `PySide6 + QRunnable` 在 macOS / Shiboken 路径上出现过闪退
- 现在改成了更稳的 `ThreadPoolExecutor + QTimer` 轮询结果方式

## 9. 当前限制

- 当前只做了 `laser1` 的电流控制，还没有扩展到 `laser2 ~ laser4`
- 目前只实现了“连接 + 基础参数 + 电流控制”这一层
- 还没有做更完整的状态页、告警页、扫描页、发射控制页
- 没有做配置保存、恢复、历史记录、曲线记录
- 还没有针对每种系统型号做差异化界面

## 10. 后续建议

下一步比较值得继续做的是：

1. 把 `laser1` 扩展成可切换 `laser1 ~ laser4`
2. 增加发射相关状态和更明确的安全联锁提示
3. 增加 `Save` / `Load` / 配置持久化操作
4. 增加更多 DLC pro 参数页
5. 对不同型号激光头做更细的参数适配

## 11. 启动方式

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/toptica-lab/bin/python /Users/YieFanMeng/Documents/DlcPro_v1/app.py
```

如果后面继续迭代，建议默认继续按 `toptica-dlcpro-gui-development-zh` 的规则执行，也就是：

- SDK 接口以官方 `v3_3_3` 为准
- 设备行为和安全约束以 `Manual.md` 为准
- 不凭空发明参数名、状态名、范围和值
