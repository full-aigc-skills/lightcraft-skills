# 本地实施证据与未完成门禁

2026-10-08。本变更完成 **21/29** 项任务；勾选表示对应本地实现/契约验证完成，不表示 Lightcraft 原生、宿主或整体发行验收。原生安装授权问题已发出，尚未收到回复。

当前测试与身份见 [分层报告](local-report.json)。所有 Python 原生进程测试使用测试替身或普通 Python 子进程；实际图像解码使用现有 macOS sips。未安装 Lightcraft CLI、插件、Python 包，Git main 已提交推送，开发版发行为草稿；未公开发布。

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
| S-4.2 | OPEN | runtime/coverage.py, tests/test_capability_contract.py。coverage.py 已能绑定快照并列出未覆盖命令；尚无固定原生制品的实际能力快照。 |
| S-4.3 | OPEN | runtime/photo_workflows.py, skills/lightcraft-cli-library/references/workflow.md, scripts/native_acceptance.py。library 工作流、导入结果身份映射和部分失败回归已实现；真实库锁、原生导入和重开仍待验收。 |
| S-4.4 | OPEN | runtime/photo_workflows.py, tests/test_photo_contract.py, skills/lightcraft-cli-develop/references/workflow.md。局部参数保持、控件范围和批量/预览规则已实现；实际前后预览、显影及批量范围仍待原生验证。 |
| S-4.5 | LOCAL_DONE | runtime/artifacts.py, runtime/artifact.schema.json, tests/test_photo_contract.py |
| S-4.6 | OPEN | scripts/native_acceptance.py, scripts/raw_acceptance.py。独立原生重开驱动已准备；原生运行时安装授权待回复。 |
| S-5.1 | LOCAL_DONE | scripts/generate_runtime.py, tests/test_package.py |
| S-5.2 | LOCAL_DONE | runtime/package_checks.py, scripts/validate_package.py, LICENSE, licenses/Apache-2.0.txt |
| S-5.3 | LOCAL_DONE | scripts/verify_evidence.py, tests/test_evidence_identity.py, docs/verification/local-report.json |
| S-5.4 | OPEN | scripts/native_acceptance.py。固定制品冷安装及 PNG/JPEG 驱动已准备；原生安装授权待回复。 |
| S-5.5 | OPEN | scripts/raw_acceptance.py, docs/verification/raw-samples.json。两个具有来源与摘要的真实 RAW 样本和验收驱动已准备；尚未原生解码。 |
| S-6.1 | LOCAL_DONE | scripts/sync_local_snapshot.py, tests/test_snapshot_sync.py, 插件 tests/test_provenance_identity.py |
| S-6.2 | OPEN | scripts/release_preflight.py。本目录没有 Git 身份；未获 Git/远端/发布授权，不伪造发行身份。 |
| S-6.3 | LOCAL_DONE | scripts/sync_local_snapshot.py, tests/test_snapshot_sync.py, 插件 tests/test_snapshot.py |
| S-6.4 | OPEN | docs/verification/local-report.json, docs/verification/implementation-evidence.md。本地适用检查已通过；全部要求仍缺原生、宿主、视觉与发行证据，不 sync/archive。 |
| S-7.1 | LOCAL_DONE | openspec/changes/extend-lightcraft-connect-mcp/ |
| S-7.2 | LOCAL_DONE | openspec/changes/extend-lightcraft-expanded-photo-capabilities/ |
| S-7.3 | LOCAL_DONE | openspec/changes/extend-lightcraft-portable-artcraft-delivery/ |

## 要求映射

每项 requirement 关联上表对应任务和当前测试；涉及运行时/宿主/视觉/发行的验收仍保持 OPEN，不能用静态结果关闭。

| 要求 | 关联任务 | 验收范围 |
|---|---|---|
| EXR-1 版本化身份与持久记录 | S-1.3, S-3.3, S-3.4 | 本地证据见对应任务；整体验收 OPEN |
| EXR-2 超时未知性跨层保留 | S-1.1, S-3.1 | 本地证据见对应任务；整体验收 OPEN |
| EXR-3 逐步骤结果与保存语义 | S-1.2, S-3.2 | 本地证据见对应任务；整体验收 OPEN |
| EXR-4 输入保全与写入边界 | S-3.5 | 本地证据见对应任务；整体验收 OPEN |
| PHW-1 照片库与身份交接 | S-4.3 | 本地证据见对应任务；整体验收 OPEN |
| PHW-2 显影基线与局部修改 | S-4.4 | 本地证据见对应任务；整体验收 OPEN |
| PHW-3 导出与独立文件验证 | S-4.5 | 本地证据见对应任务；整体验收 OPEN |
| PHW-4 照片库重开与能力边界 | S-4.6, S-5.5 | 本地证据见对应任务；整体验收 OPEN |
| QE-1 自包含资源与文档完整性 | S-5.1, S-5.2, S-6.3 | 本地证据见对应任务；整体验收 OPEN |
| QE-2 分层且绑定当前输入的证据 | S-5.3, S-6.1, S-6.2, S-6.4 | 本地证据见对应任务；整体验收 OPEN |
| QE-3 可重复的原生照片闭环 | S-5.4, S-5.5 | 本地证据见对应任务；整体验收 OPEN |
| RTD-1 无安装副作用诊断 | S-2.1, S-5.2 | 本地证据见对应任务；整体验收 OPEN |
| RTD-2 固定身份与安装边界 | S-2.2 | 本地证据见对应任务；整体验收 OPEN |
| RTD-3 版本和模式绑定的发现 | S-2.3, S-3.4 | 本地证据见对应任务；整体验收 OPEN |
| SRT-1 六技能路由与职责 | S-4.1 | 本地证据见对应任务；整体验收 OPEN |
| SRT-2 操作契约与按需资料 |  | 本地证据见对应任务；整体验收 OPEN |
| SRT-3 命令覆盖与领域语言 | S-4.2 | 本地证据见对应任务；整体验收 OPEN |

## 验证边界

- Python 3.12/3.13 本地完整回归：PASS；Python 3.11 本地不可用；远端 Python 3.11/3.12/3.13 离线矩阵全部 PASS，运行身份见 [远端 CI 证据](remote-ci.json)。
- 六技能隔离、中文空格路径、来源快照和实际合成图像解码：本地检查；不构成固定原生制品的能力证明。
- skill-creator 的 quick_validate.py 依赖 PyYAML，当前解释器不可用；使用标准库包校验覆盖 frontmatter、结构与引用，没有安装依赖。
- TRACE 分数仅为静态内容基线，详见配套技能库 docs/verification/trace/，不是路由/模型/原生完成证明。
- 两个真实 RAW 样本只完成来源/摘要准备，不宣称解码通过。
- GitHub 只读查询未能解析两个目标仓库；这不证明其不存在。本轮没有 Git 提交、远端或发行证据。
- P3 三组扩展已登记独立变更：实际功能与各自 4 项任务保持 OPEN；它们不因“建立规格”任务完成而视为实现。
- 不执行 sync/archive，当前正式规格仍为增量 change。

## 本轮协议复核补充

- 导入映射改为读取重复项 existing 与 photo.inspect.source，缺失身份不再计为完整交接。
- RAW 驱动按 previewOnly 的字符串/null 协议区分预览回退；不把布尔值或缺字段当作完整 RAW。核对回执、计划、资源、原片与独立重开持久化；回退单列 PASS_WITH_PREVIEW_FALLBACK，完整 RAW 保持 NOT_PROVEN。
- 合成驱动逐一处理 PNG/JPEG 两个输入，记录前后预览和独立重开。以上驱动只完成模拟协议回归，真实原生任务仍 OPEN。
- --require-installed 的缺失目录拒绝回归及已有安装替身包装链均无下载/安装；真实 CLI 仍未执行。
