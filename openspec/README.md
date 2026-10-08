# Lightcraft 技能库 OpenSpec

当前优化变更为 **harden-lightcraft-skill-workflows**。本轮已实施并验证本地代码；固定 CLI 原生与合成图视觉验收已完成，宿主自然语言路由与发行验收仍待完成；以下产物是本项目本次变更的唯一规格事实源。

- [变更提案与范围](changes/harden-lightcraft-skill-workflows/proposal.md)
- [架构设计、兼容性与依赖](changes/harden-lightcraft-skill-workflows/design.md)
- [能力要求与验收场景](changes/harden-lightcraft-skill-workflows/specs/)
- [唯一实施任务清单](changes/harden-lightcraft-skill-workflows/tasks.md)
- [配套项目规格入口](https://github.com/full-aigc-plugins/lightcraft-plugin/blob/main/openspec/README.md)

任务按 P0–P3 排序，跨项目依赖使用 S-X.Y（技能库）与 P-X.Y（插件）编号。当前主变更任务为 27/29 完成，详见 [实施证据](../docs/verification/implementation-evidence.md)；验收绑定当次源码、输入和产物身份。

`changes/.../specs/` 是当前变更的增量规格；`openspec/specs/` 暂不填入已实现声明。实现、验证和规格同步完成后才能归档，不能用本次文档校验代替原生运行、宿主加载或视觉验收。

在本项目根目录检查产物状态和格式：

```bash
openspec status --change harden-lightcraft-skill-workflows
openspec validate harden-lightcraft-skill-workflows --strict --no-interactive
```

OpenSpec 产物状态完成仅表示 proposal/design/specs/tasks 已准备，不表示实施任务完成。
