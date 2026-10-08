# Connect/MCP 当前增量验收

本目录绑定 2026-10-08 的增量源码，未完成公开发行和宿主验收。主变更及公开预发行历史证据保留，不移用旧 PASS。

- Python 3.12、3.13：66 项单元与回归测试通过。包括模式互斥、写入拒绝、脚本变更隔离、有界 stdin、超时、NotSaved 与未知协议分类。
- 固定 macOS arm64 CLI 0.2.1：headless-current/receipt.json 记录 initialize、tools/list、库资源查询成功。
- disconnected-current/receipt.json：绑定未监听端口，初始化和工具目录成功，库资源失败；backendQuery=NOT_CONFIRMED，没有登记桌面连接成功。
- occupied-current/receipt.json：持有真实 catalog.lock 后探测得到 UNKNOWN；occupied-contract.json 确认锁仍被持有且 inode 未改变，没有强制解锁或自动重放。
- native-baseline.json：当前包装器完成两张合成 PNG/JPEG 的导入、显影、导出和独立会话重开；6 个产物技术检查通过。视觉、RAW 与新增宿主验收未执行。

headless-probe.json、disconnected-probe.json 是较早探测，仅保留过程记录；当前结论使用带 current 名称的回执。每份回执包含固定原生版本/二进制摘要、请求摘要、模式、资源摘要、完整日志位置和逐步骤状态。原路径指向本机持久验收目录，旁侧保留日志副本。

固定原生 Remote 客户端可能在网络错误后重复发送请求，因此包装器拒绝 Connect 写入和任意交互 MCP 请求，仅允许封闭只读探测或审计后的只读 run。读取可能被原生客户端重试，已单独披露。Headless 打开库可能初始化/迁移文件，只读表示没有照片编辑命令。

未完成：真实桌面 Connect 查询、桌面重启/失联恢复、真实 NotSaved 故障、Connect 占库恢复、宿主 MCP 加载与当前资源路由。机器 /Applications 和 ~/Applications 未发现 Lightcraft 应用。本次不安装桌面软件、不修改原生客户端。三项能力任务与跨仓库同步归档任务保持 OPEN。

发布准备：版本元数据已递增，仅创建 GitHub 草稿；发行门禁尚未满足，不公开发布、不移动旧标签。原生回执所绑定的运行资源和输入没有因版本元数据调整而改变；本轮重新执行离线测试和分发校验。插件来源仍锁定已公开 v0.1.0-dev.1，不能把待发布技能库版本登记为公开来源。
