# 三领域公共协议与失效验收

2026-10-08；本次完成扩展任务 1.2（SEXT3-2），只覆盖协议消费、版本绑定、文件交接及变更失效。

```mermaid
flowchart LR
    I[原创合成 PNG] --> L[LightCraft 显影并导出 PNG]
    L --> D[DesignCraft 放置图片并导出 PDF]
    D --> P[PrintCraft 保存 PDF 并独立重开]
    P --> A[ArtCraft 实际公共校验器及 planned 账本]
    A --> C[对照实际依赖图验证失效集合]
    C -. 计算结果不触发重放 .-> R[变更节点与下游失效 无关节点复用]
```

固定原生 CLI 均为 0.2.1 / macOS arm64，使用已有制品，无安装或升级。LightCraft SHA256 `45d6f10c7d15c9cf051d23629ab14d0e8ca4c3bb9e3192393f726a918ab1c8da`；DesignCraft `e18578b28f43d6c6854ded930065feed5c9ee8af6a2e51338aa675ba4a5723a8`；PrintCraft `b7783b596870ed5a326f29456d4647382d2e1e4d7b7ffe75ded192cd15b86995`。

native/native-exchange-report.json 绑定三份本地锁、当前消费器四份资源、验收驱动/监督器/网关源码、实际目录快照、原生版本输出、逐任务计划及输入/产物摘要。全部输入为本轮原创合成图形，CC0；没有用户媒体、模型或字体。首行版本身份与二进制摘要均核对，PrintCraft 额外帮助链接原样保留。LightCraft 显影、PNG 技术解码及库持久状态通过；DesignCraft 实际放图、工程保存、PDF 页数和无警告导出通过；PrintCraft 三个命令的业务结果和独立重开的一页 96×64pt PDF 通过。

native/protocol-acceptance.json 由实际 ArtCraft 的 contracts.ts、dependency_graph.ts 和 TaskLedger 校验，包含实际来源 commit、版本及完整 src/schemas/package.json 前后身份。四个请求在 ArtCraft 账本登记为 planned，四个实际文件（原始 PNG、显影 PNG、版面 PDF、交付 PDF）及版面原工程引用通过验证；该 planned 状态不等于 ArtCraft 已调度或交付。五组数值/Unicode 规范化摘要与 ArtCraft planHash 差分一致。

协议 schema 固定消费 ArtCraft commit `8e9a519cd2b34187f9dc74cd95ccf98570daeea0` 的精确 blob，并与本次实际 ArtCraft 当前 schema 核对一致。该快照和当前本地源码均不宣称已公开发布。公共事实源仍在 ArtCraft；本仓只维护领域消费和映射。

实际 photo 请求的曝光计划发生变化时，变更 photo 及传递 layout/pdf 失效；无关节点保留。结果与 ArtCraft invalidated 实现一致。单元回归另覆盖能力身份/版本变化、原始修订及输入绑定、同版本不同摘要、引用篡改、路径外逃、循环/缺失/重复边及 JSON 重复字段。只计算失效，不提交第二次原生任务。

接口要求 Node 24+，使用标准库，无 npm 依赖。插件 craft-inspect 已实际调用；它复核交接 JSON/文件并禁止任务执行、交付或自动重放，不把输入的 authorizationRef 当成人类授权。

归档保留原运行绝对路径、回执和相对产物位置；native/ 下库和 SQLite 账本不分发。原验收根目录仍在工作区 evaluation-results/lightcraft-exchange-20261008。归档产物另以当前目录重新进行协议/文件核验，见 archived-artifact-verification.json；历史绝对路径不是可自动重放的计划。

**边界：** 完整 ArtCraft publicSkillFactory 尚未包含 LightCraft，宿主自动路由与 WorkflowEngine/LocalRunner 调度均 NOT_RUN；本轮实际 CLI 由显式验收驱动启动。选择性原生重建、手机/平板、其他平台、市场发行均未验收，分别保留原任务门禁。1.1、1.3、1.4 继续 OPEN，不能用本轮 planned 账本或协议 PASS 关闭这些门禁。

本地回归：Python 3.12/3.13 各 91 项通过，Node 24 协议测试 14 项通过；包结构、资源一致性及 OpenSpec strict 验证通过。当前源码身份见 local-report.json；远端 CI 在推送后单独核验。
