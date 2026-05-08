# TOPTICA DLC pro 资料索引

本文件用于快速定位当前项目中的官方资料和关键依赖。

## 官方资料

### SDK 文档

- 官方 SDK 文档目录：`python-lasersdk`
- SDK 总入口：`python-lasersdk/_sources/index.rst.txt`
- 连接说明：`python-lasersdk/_sources/getting_connected.rst.txt`
- 低层 API：`python-lasersdk/_sources/low_level_api.rst.txt`
- 同步高层 API：`python-lasersdk/_sources/synchronous_high_level_api.rst.txt`
- 异步高层 API：`python-lasersdk/_sources/asynchronous_high_level_api.rst.txt`
- 官方示例：`python-lasersdk/_sources/examples.rst.txt`
- 升级说明：`python-lasersdk/_sources/upgrade_to_v3.rst.txt`
- 已安装 SDK 路径：与当前 Python 环境有关，需要时可这样查询：

- æœ¬æœºå·²å®‰è£… SDK è·¯å¾„ï¼š`C:\Users\68310396\miniconda3\envs\dlcpro\Lib\site-packages\toptica\lasersdk`

```bash
python -c "import toptica, pathlib; print(pathlib.Path(toptica.__file__).resolve().parent)"
```

- 设备版本：`DLC pro 3.3.3`

优先查这套官方文档镜像；如果需要确认 SDK 实际模块结构、导入路径或安装后的真实代码，再查 SDK 安装路径。

### 设备手册

- 手册：`Manual.md`

## 当前项目路径

- 项目根目录：仓库根目录

优先在该目录下查找当前实现、界面代码、控制器代码和资源文件。

## 关键依赖

- 串口通信依赖：`pyserial`
- 网络连接依赖：`ifaddr`
- GUI 依赖：`PySide6`

## 推荐检索方式

优先在官方资料中检索，再看项目代码。

```bash
SDK_PATH=$(python -c "import toptica, pathlib; print(pathlib.Path(toptica.__file__).resolve().parent)")
rg -n "Client|NetworkConnection|SerialConnection|connect" python-lasersdk/_sources "$SDK_PATH" .
rg -n "pyserial|serial|ifaddr|network|ethernet" python-lasersdk/_sources "$SDK_PATH" .
rg -n "emission|interlock|safety|laser radiation" Manual.md
rg -n "current|voltage|scan|piezo|temperature" python-lasersdk/_sources "$SDK_PATH" Manual.md
```

## 使用原则

- 优先使用官方 SDK 文档镜像与项目中的 `Manual.md`
- 需要确认真实模块结构或已安装包行为时，再查 SDK 安装路径
- 项目现有代码只能说明“现在怎么写了”，不能自动证明“这样写是对的”
- 连接相关开发时，要同时检查 `pyserial` 与 `ifaddr` 在当前项目中的实际用法
