# Lightcraft 独立技能库

开发候选 `0.1.0-dev.1`，固定原生 CLI `0.2.1`；当前目标为 macOS arm64、Python 3.11+。六项技能可以独立分发：`lightcraft-use`、`lightcraft-cli-setup`、`lightcraft-cli-library`、`lightcraft-cli-develop`、`lightcraft-cli-export`、`lightcraft-cli`。

已实现纯诊断、带身份的能力发现、唯一进程监督、逐步骤 JSONL 回执、原片与输出预检、实际图像解码及来源快照同步。`runtime/` 是运行资源唯一维护源；通过 `scripts/generate_runtime.py` 生成六份自包含副本。

```bash
python3 -I -B scripts/generate_runtime.py --check
python3 -I -B scripts/validate_package.py
python3 -I -B -m unittest discover -s tests -v
```

技能运行时的 `SKILL_DIR` 必须取宿主实际加载目录；纯检查用 `python3 -I -B "$SKILL_DIR/scripts/bootstrap.py" --no-install`。在线发现或运行可能安装锁定制品，只在相应授权内执行。离线 `--catalog` 不能用于执行。UNKNOWN 不自动重放，零退出仍待文件、重开与视觉验证。

主 OpenSpec 任务 **21/29** 完成，剩余能力快照/照片原生流程、独立重开、PNG/JPEG/RAW 验收及发行门禁保持 OPEN。当前没有 Lightcraft 原生安装、宿主加载、模型分派、视觉通过证据；Git main 已推送，Python 3.11/3.12/3.13 远端离线 CI 全部通过；开发版发行草稿已准备，尚无公开发行。三个 P3 独立扩展变更保持 OPEN。

[任务与规格](openspec/README.md) · [当前证据及差距](docs/verification/implementation-evidence.md) · [分层报告](docs/verification/local-report.json) · [架构](docs/architecture.md) · [运行回执](docs/task-receipts.zh-CN.md)
