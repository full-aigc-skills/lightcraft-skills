# Lightcraft OpenSpec

基础优化主变更 **harden-lightcraft-skill-workflows** 已完成 29/29 项任务，并于 2026-10-08 同步主规格和归档。

- [归档提案](changes/archive/2026-10-08-harden-lightcraft-skill-workflows/proposal.md)
- [归档设计](changes/archive/2026-10-08-harden-lightcraft-skill-workflows/design.md)
- [完成的任务清单](changes/archive/2026-10-08-harden-lightcraft-skill-workflows/tasks.md)
- [当前主规格](specs/)
- [分层验收与限制](../docs/verification/implementation-evidence.md)
- [同步归档执行回执](../docs/verification/openspec-archive.json)

三个独立扩展变更仍在 `changes/`，每个四项实现任务保持 OPEN：Connect/MCP、扩展照片/SAM、跨平台/ArtCraft/移动交付。基础闭环验收不关闭这些范围。

```bash
openspec list
openspec validate --all --strict --no-interactive
```

任务使用 S-X.Y（技能库）和 P-X.Y（插件）编号。技能库公开来源版本为 v0.1.0-dev.1，插件公开开发版本为 v0.1.0-dev.2；原生 CLI 独立固定为 0.2.1 / macOS arm64。宿主模型验收仅覆盖六技能隔离环境，全量技能列表的上下文预算限制仍保留。
