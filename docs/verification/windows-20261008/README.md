# 六目标固定 CLI 原生验收

2026-10-08，技能源 SEXT3-1 完成。原生 CI [37800975968](https://github.com/full-aigc-skills/lightcraft-skills/actions/runs/37800975968)，代码提交 `4a670975eea3aaf50004d9bb05ea4283fbb083ba`。六个真实执行目标：macOS arm64/x86_64、Linux aarch64/x86_64、Windows x64/x86。Windows x86 为 Windows Server 2022 / AMD64 主机上的 32 位 Python/CLI 进程，不宣称在 32 位 Windows OS 或 Windows ARM64 上验收。固定 0.2.1 无 Windows ARM64 制品，保持不支持；不涉及 Android/iOS 或移动交付。

Windows x64 官方 ZIP/CLI SHA256 分别为 `9fae1279ba7b08e0faf1ca3497c15d0b7130b76822a7992865c221aab5208670` / `4dc3361a25594b417f7763eb56e8e2d56a029861f8a1574deb1070676cbdba74`，x86 分别为 `80b5e84283d61b94e25e676774711ebe3cc2955f12c86d0ac9eaeb591faff37a` / `40e25c444db4cf4c059510d829efe829923b13cdca54c9c9ccc867844d9b5beb`。固定官方 API 元数据随附；在核对归档摘要后才提取 CLI。独立安装只复制 CLI 与许可，不安装桌面，不改 PATH，不覆盖旧版。

新增回归覆盖精确资产名、进程位数、.exe 安装/复用/只读诊断、Windows 安装锁竞争及持锁进程退出后释放、真实进程 stdin/日志/超时，以及 Windows 默认 cp1252 下的中文资料读取。Windows 超时保持 UNKNOWN，只确认启动进程的终止请求，不声称后代全部退出、不自动重放。Python -I 不依赖 PYTHONUTF8；运行文件显式 UTF-8，协议 JSON 标准输出可跨 locale 解码。

首次 Windows CI 因 cp1252 读取中文失败，原日志保留；修复后照片闭环通过，但下载复核拒绝 CRLF 检出导致的字节身份漂移。随后新增 .gitattributes 固定 LF、CI 用 Git blob 对照当前检出原始字节。最终六目标所有运行资源与驱动摘要完全一致，不能通过归一化摘要把旧报告变成当前通过。

每个目标实际导入原创 PNG/JPEG 两图，分别显影、前后导出六份文件并完整解码，再用第二会话独立重开，确认完整设置仅曝光变化、原片不变、库持久化且无未保存操作。ci-native/ 留存 30 会话回执、原生计划及逐进程日志、12 份原图和 36 份产物；不分发运行二进制或照片库。归档后再次逐文件 SHA256 与图像解码，见 ci-artifact-verification.json。

Windows 两个 CLI 的 Authenticode 状态均为 Valid，签名主体 Learning Machines Inc；macOS 两架构 codesign --verify --strict 通过，TeamIdentifier DJ6XS33FX8。不声称独立公证通过。Linux 上游没有单独数字签名资产，固定官方摘要不冒充签名。所有目标保存真实动态依赖清单；Linux ldd 无 not found，原生实际执行证实当前用户空间依赖可用，不扩张为所有发行版或桌面支持。

只读复核命令（不启动 CLI）：

```bash
python3 -I -B docs/verification/windows-20261008/verify-native-archives.py --source . --evidence docs/verification/windows-20261008/ci-native --run docs/verification/windows-20261008/native-ci.json
```

本地 Python 3.12/3.13 各 106 项测试，103 执行通过、3 项 Windows 专用测试跳过；Windows CI 实际运行这 3 项及其余定向回归，不能用本机跳过算通过。Node 14 项通过。离线 CI 绑定上述提交，Python 3.11/3.12/3.13 与 Node 24 全部通过。

本轮未改变插件受管六技能公开快照 v0.1.0-dev.1，插件验收与技能源不可变发行配套仍由 PEXT3-1 / SEXT3-1.4 保持 OPEN。Connect/MCP 桌面、当前宿主与视觉、SAM、移动设备验收仍独立开放；整体计划、公开发布和本变更归档尚未完成。旧 platform-20261008 报告保留历史身份，不能代替本轮当前报告。
