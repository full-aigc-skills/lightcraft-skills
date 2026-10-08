# 主变更实施与验收证据

2026-10-08。主变更任务 **29/29** 完成；已获安装、Git、推送及发布授权。固定 CLI 0.2.1 / macOS arm64 原生闭环、合成图视觉、Codex CLI 0.161.0 六技能隔离宿主和实际来源/插件升级已验收。公开开发预发行：技能库 v0.1.0-dev.1 / 87fe7ce，插件 v0.1.0-dev.2 / 7b3bfe2。当前分层证据见 [local-report.json](local-report.json)。全量技能上下文预算、RAW 型号与其他平台限制保持明确；三个独立 P3 change 的实现仍 OPEN。

## 任务映射

| ID | 状态 | 实现与证据或剩余差距 |
|---|---|---|
| S-1.1 | LOCAL_DONE | tests/test_execution_protocol.py, tests/test_wrapper_integration.py |
| S-1.2 | LOCAL_DONE | tests/test_execution_protocol.py |
| S-1.3 | LOCAL_DONE | tests/test_gateway_receipts.py, tests/test_execution_protocol.py, tests/test_native_process.py, tests/test_capability_contract.py |
| S-2.1 | LOCAL_DONE | runtime/bootstrap.py, tests/test_execution_protocol.py |
| S-2.2 | LOCAL_DONE | tests/test_installer_boundaries.py, tests/test_runtime_release_identity.py |
| S-2.3 | LOCAL_DONE | runtime/command_gateway.py, tests/test_capability_contract.py |
| S-3.1 | LOCAL_DONE | runtime/native_process.py, tests/test_native_process.py, tests/test_wrapper_integration.py |
| S-3.2 | LOCAL_DONE | runtime/command_gateway.py, tests/test_execution_protocol.py |
| S-3.3 | LOCAL_DONE | runtime/execution-receipt.schema.json, tests/test_gateway_receipts.py, tests/test_capability_contract.py |
| S-3.4 | LOCAL_DONE | runtime/capability.schema.json, examples/receipts/, tests/test_capability_contract.py |
| S-3.5 | LOCAL_DONE | runtime/command_gateway.py, tests/test_execution_protocol.py, tests/test_gateway_receipts.py |
| S-4.1 | LOCAL_DONE | skills/*/SKILL.md, references/, examples/scenarios.md, agents/openai.yaml |
| S-4.2 | DONE | native-20261008/index.json、实际原生回执与宿主缓存控制器交付证据；仅该固定制品与合成样本范围。 |
| S-4.3 | DONE | native-20261008/index.json、实际原生回执与宿主缓存控制器交付证据；仅该固定制品与合成样本范围。 |
| S-4.4 | DONE | native-20261008/index.json、实际原生回执与宿主缓存控制器交付证据；仅该固定制品与合成样本范围。 |
| S-4.5 | LOCAL_DONE | runtime/artifacts.py, runtime/artifact.schema.json, tests/test_photo_contract.py |
| S-4.6 | DONE | native-20261008/index.json、实际原生回执与宿主缓存控制器交付证据；仅该固定制品与合成样本范围。 |
| S-5.1 | LOCAL_DONE | scripts/generate_runtime.py, tests/test_package.py |
| S-5.2 | LOCAL_DONE | runtime/package_checks.py, scripts/validate_package.py, LICENSE, licenses/Apache-2.0.txt |
| S-5.3 | LOCAL_DONE | scripts/verify_evidence.py, tests/test_evidence_identity.py, docs/verification/local-report.json |
| S-5.4 | DONE | native-20261008/index.json、实际原生回执与宿主缓存控制器交付证据；仅该固定制品与合成样本范围。 |
| S-5.5 | DONE | native-20261008/raw*/raw-evidence.json：四个真实 CC0 型号/变体，保留完整/预览回退/不支持三类事实与摘要，不扩大支持范围。 |
| S-6.1 | LOCAL_DONE | scripts/sync_local_snapshot.py, tests/test_snapshot_sync.py, 插件 tests/test_provenance_identity.py |
| S-6.2 | DONE | source-release.json；公开 tag/commit、GitHub release、ZIP 摘要与来源发行 CI。 |
| S-6.3 | LOCAL_DONE | scripts/sync_local_snapshot.py, tests/test_snapshot_sync.py, 插件 tests/test_snapshot.py |
| S-6.4 | DONE | 分层报告、跨项目原生/宿主/视觉/来源发行、实际 CI；主变更同步归档另记执行结果。 |
| S-7.1 | LOCAL_DONE | openspec/changes/extend-lightcraft-connect-mcp/ |
| S-7.2 | LOCAL_DONE | openspec/changes/extend-lightcraft-expanded-photo-capabilities/ |
| S-7.3 | LOCAL_DONE | openspec/changes/extend-lightcraft-portable-artcraft-delivery/ |

## 要求映射

每项 requirement 关联上表对应任务和当前测试；主变更的适用运行时/宿主/视觉/发行证据已齐备，不能将其扩展为未测能力。

| 要求 | 关联任务 | 验收范围 |
|---|---|---|
| EXR-1 版本化身份与持久记录 | S-1.3, S-3.3, S-3.4 | 主变更适用验收已完成；范围见分层报告及末节 |
| EXR-2 超时未知性跨层保留 | S-1.1, S-3.1 | 主变更适用验收已完成；范围见分层报告及末节 |
| EXR-3 逐步骤结果与保存语义 | S-1.2, S-3.2 | 主变更适用验收已完成；范围见分层报告及末节 |
| EXR-4 输入保全与写入边界 | S-3.5 | 主变更适用验收已完成；范围见分层报告及末节 |
| PHW-1 照片库与身份交接 | S-4.3 | 主变更适用验收已完成；范围见分层报告及末节 |
| PHW-2 显影基线与局部修改 | S-4.4 | 主变更适用验收已完成；范围见分层报告及末节 |
| PHW-3 导出与独立文件验证 | S-4.5 | 主变更适用验收已完成；范围见分层报告及末节 |
| PHW-4 照片库重开与能力边界 | S-4.6, S-5.5 | 主变更适用验收已完成；范围见分层报告及末节 |
| QE-1 自包含资源与文档完整性 | S-5.1, S-5.2, S-6.3 | 主变更适用验收已完成；范围见分层报告及末节 |
| QE-2 分层且绑定当前输入的证据 | S-5.3, S-6.1, S-6.2, S-6.4 | 主变更适用验收已完成；范围见分层报告及末节 |
| QE-3 可重复的原生照片闭环 | S-5.4, S-5.5 | 主变更适用验收已完成；范围见分层报告及末节 |
| RTD-1 无安装副作用诊断 | S-2.1, S-5.2 | 主变更适用验收已完成；范围见分层报告及末节 |
| RTD-2 固定身份与安装边界 | S-2.2 | 主变更适用验收已完成；范围见分层报告及末节 |
| RTD-3 版本和模式绑定的发现 | S-2.3, S-3.4 | 主变更适用验收已完成；范围见分层报告及末节 |
| SRT-1 六技能路由与职责 | S-4.1 | 主变更适用验收已完成；范围见分层报告及末节 |
| SRT-2 操作契约与按需资料 |  | 主变更适用验收已完成；范围见分层报告及末节 |
| SRT-3 命令覆盖与领域语言 | S-4.2 | 主变更适用验收已完成；范围见分层报告及末节 |

## 早期离线验证边界（历史记录）

- Python 3.12/3.13 本地完整回归：PASS；Python 3.11 本地不可用；远端 Python 3.11/3.12/3.13 离线矩阵全部 PASS，运行身份见 [远端 CI 证据](remote-ci.json)。
- 六技能隔离、中文空格路径、来源快照和实际合成图像解码：本地检查；不构成固定原生制品的能力证明。
- skill-creator 的 quick_validate.py 依赖 PyYAML，当前解释器不可用；使用标准库包校验覆盖 frontmatter、结构与引用，没有安装依赖。
- TRACE 分数仅为静态内容基线，详见配套技能库 docs/verification/trace/，不是路由/模型/原生完成证明。
- 两个真实 RAW 样本只完成来源/摘要准备，不宣称解码通过。
- GitHub 只读查询未能解析两个目标仓库；这不证明其不存在。本轮没有 Git 提交、远端或发行证据。
- P3 三组扩展已登记独立变更：实际功能与各自 4 项任务保持 OPEN；它们不因“建立规格”任务完成而视为实现。
- 不执行 sync/archive，当前正式规格仍为增量 change。

## 早期协议复核（历史记录）

- 导入映射改为读取重复项 existing 与 photo.inspect.source，缺失身份不再计为完整交接。
- RAW 驱动按 previewOnly 的字符串/null 协议区分预览回退；不把布尔值或缺字段当作完整 RAW。核对回执、计划、资源、原片与独立重开持久化；回退单列 PASS_WITH_PREVIEW_FALLBACK，完整 RAW 保持 NOT_PROVEN。
- 合成驱动逐一处理 PNG/JPEG 两个输入，记录前后预览和独立重开。以上驱动只完成模拟协议回归，真实原生任务仍 OPEN。
- --require-installed 的缺失目录拒绝回归及已有安装替身包装链均无下载/安装；真实 CLI 仍未执行。

## 2026-10-08 获授权后的真实验收

证据见 [原生与宿主验收索引](native-20261008/index.json)。固定制品安装、PNG/JPEG 显影导出及独立重开通过；重复/损坏/缺失导入逐项报告，占用锁未强制解除，显式批量修改只影响指定 ID。缓存插件的控制器完成真实闭环、实际图像审阅和 delivery.json。Nikon D2H 完整 RAW 解码由运行时报告通过；Blackmagic DNG 为明确不支持，Canon EOS 7D sRAW 仅预览回退通过，Canon D30 CRW 不支持。自然语言路由未通过：Codex CLI 0.147.0 配置模型要求更新宿主，且现有技能列表超出上下文预算。加载六技能不代表路由通过；未升级 Codex，也未公开发行。

## 2026-10-08 Codex 0.161.0 宿主验收

已获隔离安装授权，CLI 0.161.0 安装于临时独立前缀；全局 CLI 仍为 0.147.0。插件在含中文和空格的新缓存目录加载六项技能。实际模型分别通过自然语言入口、显式导出入口、UNKNOWN 恢复边界、缺失依赖无安装诊断与无关请求。逐项命令、退出码与模型结果见 [宿主证据](host-0161-20261008/index.json)。验收进程只启用六项 Lightcraft 技能，不修改全局配置；全量 771 技能环境仍超上下文预算，仅通过文件搜索读取入口，不声称完整环境默认发现通过。历史章节描述当时状态，以本节和 local-report.json 为当前结论。

### 实际来源发行

技能库开发预发行 v0.1.0-dev.1 已公开：远端 tag、GitHub release 目标均为 `87fe7cebab2bc687ef7b819eb355e4e28132e6e9`，ZIP 与 SHA256SUMS 已上传；见 [公开来源身份](source-release.json)。该提交 Python 3.11/3.12/3.13 远端 CI 均通过。插件通过真实 `release_upgrade.py --apply` 锁定该来源，108 项技能文件摘要保持一致；迁移日志保留原始 APPLIED_HOST_NOT_VERIFIED 状态，宿主升级另列证据。

### 实际插件版本升级

持久隔离目录中的 Codex 0.161.0 实际安装插件 0.1.0-dev.1 后升级到 0.1.0-dev.2；app-server 强制重载识别六项技能的新缓存路径，缓存来源锁对应公开技能库 87fe7ce。见 [升级回执](host-0161-20261008/upgrade.json)。宿主移除了旧代码缓存，因此不声称旧缓存保留；归档任务与回执副本在升级前后摘要不变。此前临时目录被外部清理，原始工作目录保留状态无法追溯，本次明确使用已归档的历史记录，不执行重放。插件实际来源锁 CI 已通过官方技能源检出与三个 Python 版本测试，见 remote-ci.json（插件仓库）。

## 主变更收口

源码/契约测试、固定原生制品、目标宿主、合成产物视觉和公开发行分别验收；只关闭本主变更。Connect/MCP、扩展照片/SAM、跨平台/ArtCraft/移动交付三个独立 change 各四项任务保持 OPEN。全量 771 技能的描述注入超预算不归为通过，RAW 不支持与预览回退结果不改写为完整解码。

### OpenSpec 同步归档结果

主变更已通过 OpenSpec CLI 同步主规格并归档，实际执行回执见 [openspec-archive.json](openspec-archive.json)。仅关闭基础优化变更；独立扩展仍 OPEN。归档后已修复相对证据链接及跨项目归档链接。公开发行指向验收完成时的不可变提交；后续 main 只补齐收口文档与规格归档，不移动发行标签。
