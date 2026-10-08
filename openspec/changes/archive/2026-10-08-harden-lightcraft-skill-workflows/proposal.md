## Why

LightCraft 六项技能已有固定运行时安装与计划执行能力，但专业照片工作流、逐步骤结果解析及恢复证据尚不完整。已复现内层超时被外层记成普通失败；19 项本地测试不证明固定原生程序、宿主或创作交付通过。

## What Changes

- 保留六项技能，明确唯一任务路由、公共 CLI 契约和领域职责，补充 references、examples 与命令覆盖映射。
- 增加无安装副作用的诊断和带版本身份的命令/控件发现；保留当前摘要固定、自包含和 argv 调用机制。
- 统一版本化执行回执，保留超时未知性，解析原生逐步骤结果，区分普通失败、部分执行和未落盘修改。
- 建立照片库、显影、导出的可观察操作与验收契约，支持原片保全、保存重开和输出事实检查。
- 建立独立安装、离线合同、固定原生二进制及真实 RAW 的分层证据。
- **BREAKING（仅针对新回执读取器）**：新版本回执采用显式版本；无版本旧回执只读诊断，不自动接续执行。原生 CLI 透传入口及当前计划格式保持兼容。

## Capabilities

### New Capabilities

- `skill-routing`: 六项技能职责、渐进式资料与命令归属。
- `runtime-discovery`: 无副作用诊断、固定运行时身份和实时能力发现。
- `execution-receipts`: 计划、步骤结果、超时及输入保全的统一回执。
- `photo-workflows`: 照片库、显影、导出及输出验证。
- `quality-evidence`: 自包含分发与分层测试证据。

### Modified Capabilities

无既有主规格；上述 ADDED 要求包含对已有实现的约束与增量优化，不代表所有功能从零开始。

## Impact

影响 `skills/*/SKILL.md`、各技能 references/examples、五份 Python 运行资源、校验器、测试和验证资料。本变更是技能知识与运行资源的唯一规格事实源；插件消费这些资源，不维护另一份执行参数实现。

配套变更：[lightcraft-plugin / harden-lightcraft-plugin-delivery](https://github.com/full-aigc-plugins/lightcraft-plugin/blob/main/openspec/changes/archive/2026-10-08-harden-lightcraft-plugin-delivery/proposal.md)。任务 ID 以 `S-` 标识本项目，以 `P-` 标识插件项目。

本次只写规格与任务，不实施代码、不安装原生程序、不创建 Git/远端、不发布。规格校验通过不改变原生、宿主、模型或创作验收状态。
