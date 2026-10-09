# 已安装桌面 Connect / 故障 / 恢复验收（2026-10-09）

用户已安装 `/Applications/LightCraft.app` 0.4.0。固定 CLI 仍为已验 0.2.1 / macOS arm64，不升级 CLI 或六技能。桌面二进制 SHA256 为 `5145d26032800b810757d23c4f3726c3c6ec08cbcc7e53bb981bda4b9f7a58e7`；客户端摘要及当前运行资源分别绑定在每次 receipt.json 中。两者版本不能混写为同一个 0.2.1 或 0.4.0 环境。

原安装严格签名检查因 FinderInfo 元数据失败。仅在忽略的专用验收目录复制应用并删除副本 com.apple.FinderInfo，随后 codesign --verify --deep --strict 通过；原 Developer ID Learning Machines LLC / DJ6XS33FX8 与公证票据保留，未重签、未移除 quarantine、未绕过检查。原安装与副本所有文件字节一致，清单见 application-identity.json。未修改已安装应用。

以 LIGHTCRAFT_NO_PREFS=1、全新明确库路径及独立 loopback 控制端口启动所属副本，不读取或修改用户照片库/偏好。只结束或短暂暂停记录并核实命令行的验收进程；测试均已结束，没有留下运行的验收桌面进程。原生控制 API 用于明确的 engine 请求，不生成 GUI 点击或替代截图。Cua 界面捕获因 failedToCreateImageDestination 失败，故没有 GUI 视觉通过声明。

## 对应来源任务

SEXT1-1：当前 session_probe 包装器经固定 CLI 0.2.1 的 Connect MCP，在实际桌面 0.4.0 上完成 initialize、tools/list、库资源查询。connect-live/receipt.json 为实际 PASS。原有模式互斥、Connect 写入拒绝、有界请求/脚本和摘要漂移失败回归在 connect-mcp-20261008 中已通过，相关运行源码本轮未变。

SEXT1-2：实际停止桌面后查询不通过；仅暂停所属桌面进程并设置 1 秒客户端监督超时，timeout-reopen-proof/timeout/receipt.json 为 UNKNOWN / NOT_CONFIRMED；恢复后显式新查询为 PASS，没有自动重放编辑。NotSaved 在专用合成库的桌面首次 journal 追加前设置只读，评分 1→4 仅发送一次；实际错误报告内存已应用、磁盘未保存，unsavedOps>0，内存评分 4，磁盘日志字节未变。恢复权限后仅查询，保存队列恢复；独立桌面重开评分仍为 4。当前 command_gateway 对真实错误分类 APPLIED_NOT_SAVED，见 desktop-notsaved-classification.json。

前两次在已有写句柄后改权限/标志的注入没有触发错误，不能当 NotSaved PASS；desktop-result.json、fault-result.json 保留 FAIL，fault-rpc.json 保留第二次完整对话。首次尝试的 desktop-engine-rpc.json 曾被第二次脚本覆盖，因此不将该文件描述为首次完整原始对话；首次 FAIL 汇总及进程日志仍保留。第三次结果见 first-append-result.json / first-append-rpc.json；先以固定 CLI 在新库建立评分 1，然后桌面打开前限制 journal，最后在 finally 恢复原权限。未改写失败结果。

SEXT1-3：桌面实际持有 catalog.lock 时，Headless 打开同一测试库被拒绝，锁 inode 与持有关系未改；停止/重启和恢复均显式发起，只读探测不包含编辑。原片摘要保持不变；独立重开评分 4。原生客户端可能重试只读请求，保存队列重试不等于重放评分，不声明网络 exactly-once。

上述三个技能源能力项满足本轮记录的 macOS arm64 / CLI 0.2.1 + 桌面 0.4.0 范围。不推断其他桌面版本/平台或 GUI 视觉、SAM 分割、RAW 质量。原生协议不提供桌面会话 UUID，保留 NOT_PROVIDED；runId 不冒充远端身份。来源 1.4 的配套证据/同步归档仍 OPEN。

## 插件与 SAM 边界

插件 session-inspect 实际拒绝当前来源回执 probe_runtime_lock_mismatch，因为受管快照固定公开 v0.1.0-dev.1，不能重算或替换回执锁来伪造配套。插件仓库仅保留配套来源证据；未改变 108 个受管文件，也未宣称插件自动 MCP 集成或这三个插件任务通过。

桌面真实 segment.model.status 返回 available=true、installed=false、loaded=false、download.running=false。仅证明桌面 0.4.0 编译具备 SAM；CLI 0.2.1 的 UNKNOWN 仍保留，不能把桌面状态提升为该 CLI 能力。没有下载模型、接受许可或执行分割；等待用户本人许可/访问及明确下载执行授权。

归档不含程序、测试照片库、模型、凭据或隔离 home。原片为已验合成 PNG，摘要可与 mobile-20261009/source-bundle/original.png 核对。驱动为本次明确验收，绝对路径/新目录前提仅用于追溯，不应未经复核直接重跑。SHA256SUMS.json 绑定所有归档材料。
