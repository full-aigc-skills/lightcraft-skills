# ArtCraft 三领域协议消费

规范事实源是 ArtCraft 的 craft-task/v1 与 craft-artifact/v1，当前消费快照见 exchange-protocol.lock.json。Node 24+ 为这一可选接口的依赖；现有 Python 照片入口保持原使用方式，不会自动安装 Node 或 npm 包。

消费器接受一个显式 JSON bundle 文件，调用 `node /当前安装目录/scripts/craft_exchange.ts bundle.json`。支持以下三种 operation：

- task：提供 request、policy 和 inputs。request 为公共 craft-task/v1，payload 固定为 `{schemaVersion:"craft-native-plan/v1",plan:{domain,steps}}`；inputs 为 `{root,artifact}` 数组。policy 为 `{schemaVersion:1,runtimes:[明确允许的完整 runtimeIdentity]}`，由可信调用方配置，不能照抄请求来授权。任务摘要、领域、固定身份、期限及实际输入文件核对后返回 TASK_PREFLIGHT_ONLY。
- artifact：提供 root 和 artifact，按包内相对路径核对文件、原工程和证据引用，返回 ARTIFACT_IDENTITY_ONLY。PNG/JPEG/PDF 只核对签名与身份，解码/业务及视觉验收由领域和 ArtCraft 专业校验器负责。复杂交换损失报告、其他媒体类型明确拒绝，不声称通用支持。
- invalidate：提供 previous、current 与 policy。节点为 `{id,dependsOn,request,inputs}`，inputs 在此是已登记的 artifact 元数据。按 payload、输入不可变版本、运行时/能力、原工程修订、授权与预算比较；变更节点和传递消费者失效。这个接口只计算，文件接收前仍必须走 task/artifact 校验，不自动重建或重放。

所有入口都不启动原生程序、不下载、不安装、不授予执行权。产物版本不能复用同一 assetId/version 对应不同内容；目录移动不改变产物身份。节点删除须走独立明确流程，本接口拒绝隐式移除。

跨技能交接按名称安装：**designcraft-use**：`npx skills add full-aigc-skills/designcraft-skills --skill designcraft-use`；**printcraft-use**：`npx skills add full-aigc-skills/printcraft-skills --skill printcraft-use`。不依赖本机兄弟目录路径或未安装的技能内部模块。

实际范围、固定二进制与剩余宿主/平台/移动门禁见 [验收记录](verification/exchange-20261008/README.md)。

## 选择性重建验收入口

技能源仓库的 `scripts/craft_exchange_acceptance.py` 支持 `--allow-native --rebuild-from <既有原生报告> --exposure 2 --workdir <不存在的新目录>`，另外必须显式提供三个已有 CLI、三个运行时锁和本次 `--contract` 路径。这个入口是仓库级 macOS 验收驱动，未作为插件宿主调度器或独立安装技能的公共重建 API 分发。

只接受该夹具原生基线的 photo-import/photo/layout/pdf 四节点，当前实测曝光 1→2。运行时、schema、基线产物和整个基线目录核对后，克隆独立库；原库被占用时拒绝，不强制解锁。执行前绑定失效集合与全部三节点原生计划摘要，逐阶段再绑定实际新上游文件版本。只能执行 photo/layout/pdf，导入事实从基线复用；基线输入、旧产物及新产物摘要均保留。`invalidate` 和插件 `craft-inspect` 本身仍不触发执行。详见 [本轮原生证据](verification/rebuild-20261008/README.md)。
