# DLC pro 3.3.3 PySide6 Demo

这是一个基于 TOPTICA 官方 Python SDK 与 PySide6 的最小自定义 GUI，当前实现了：

- 连接 DLC pro 3.3.3
- 读取并显示一组当前设备参数
- 读取 `laser1:dl:cc:current-act`
- 写入 `laser1:dl:cc:current-set`
- 通过步进切换支持 1/2/3 位小数精度调节

依据：

- SDK: `toptica.lasersdk.dlcpro.v3_3_3`
- 手册: `Manual.md` 中 `laser1:dl:cc:*` 参数及 `Use Tuning Clip` 安全说明

运行方式：

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/toptica-lab/bin/python /Users/YieFanMeng/Documents/DlcPro_v1/app.py
```

说明：

- 网络连接使用 SDK 的 `NetworkConnection`
- 串口连接使用 SDK 的 `SerialConnection`
- 串口路径只支持命令线，不支持参数订阅；因此本程序统一采用定时刷新
- 网卡枚举依赖 `ifaddr`，串口枚举依赖 `pyserial`，若本机缺失会在界面中降级提示
# dlcpro_v1
