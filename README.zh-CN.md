# Lightcraft 独立技能库

待发布开发预发行 `0.1.0-dev.2`，固定原生 CLI `0.2.1`；Python 3.11+；macOS arm64/x86_64、Linux aarch64/x86_64、Windows x64/x86 六目标 CLI 原生验收已通过，Windows x86 为 64 位主机上的 32 位进程。六项技能可以独立分发：`lightcraft-use`、`lightcraft-cli-setup`、`lightcraft-cli-library`、`lightcraft-cli-develop`、`lightcraft-cli-export`、`lightcraft-cli`。

已实现纯诊断、带身份的能力发现、唯一进程监督、逐步骤 JSONL 回执、原片与输出预检、实际图像解码及来源快照同步。`runtime/` 是运行资源唯一维护源；通过 `scripts/generate_runtime.py` 生成六份自包含副本。

```bash
python3 -I -B scripts/generate_runtime.py --check
python3 -I -B scripts/validate_package.py
python3 -I -B -m unittest discover -s tests -v
```

技能运行时的 `SKILL_DIR` 必须取宿主实际加载目录；纯检查用 `python3 -I -B "$SKILL_DIR/scripts/bootstrap.py" --no-install`。在线发现或运行可能安装锁定制品，只在相应授权内执行。离线 `--catalog` 不能用于执行。UNKNOWN 不自动重放，零退出仍待文件、重开与视觉验证。

主 OpenSpec 任务 **29/29** 完成，主变更适用验收与公开开发预发行已完成。已通过固定 CLI PNG/JPEG 原生闭环、六技能宿主发现及隔离路由和合成图视觉审阅；Codex 0.161.0 六技能隔离环境的五类宿主场景已通过，全量技能环境仍有上下文预算限制，Canon sRAW 预览回退已验收，其他型号未据此扩展；Git main 已推送，Python 3.11/3.12/3.13 远端离线 CI 全部通过；开发预发行 v0.1.0-dev.1 已公开，来源提交为 87fe7ce。三个 P3 独立扩展变更保持 OPEN。

[任务与规格](openspec/README.md) · [当前证据及差距](docs/verification/implementation-evidence.md) · [分层报告](docs/verification/local-report.json) · [架构](docs/architecture.md) · [运行回执](docs/task-receipts.zh-CN.md)

本轮候选状态与实际证据以 [六目标验收记录](docs/verification/windows-20261008/README.md) 为准，历史版本通过记录不能代替当前候选验收。
