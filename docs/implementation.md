# 当前实现与验收边界

已实现的本地能力包括纯诊断、固定身份发现、唯一进程监督、逐步骤回执、写入预检、自包含资源生成、照片结果/局部参数契约和真实图像文件验证。插件提供持久任务锁、只读核对、停止请求、有界修订、内容绑定审阅与交付门禁。

结构与模拟回归不等于 Lightcraft CLI 原生验证。当前没有实际 CLI 安装、RAW 原生解码、Codex 插件热加载、独立视觉结果或远端发布证据；真实 RAW 样本仅完成来源与摘要准备；对应任务保持未完成。Python CI 的 3.11/3.12/3.13 矩阵已配置，远端运行状态单列。

## 检查入口

```bash
python3 -I -B scripts/validate_package.py
python3 -I -B -m unittest discover -s tests -v
```

报告在 docs/verification/，sourceFingerprint 由 scripts/verify_evidence.py 绑定当前实现文件。release_preflight.py 只读报告缺失门禁，不创建 Git、tag、远端或发布。

## 扩展保留

Connect/MCP、批量与更多 RAW/SAM、多平台与 ArtCraft 已建立配套独立变更，状态 OPEN。原任务中的“建立独立规格”可完成，但实际扩展门禁不因文档存在关闭。

## 完整操作资料

当前任务、实现文件与失败回归映射见 [实施证据](verification/implementation-evidence.md)。待授权的原生驱动在配套技能库 scripts/native_acceptance.py 与 scripts/raw_acceptance.py；不得因驱动存在把原生任务勾选。

原生验收驱动现已覆盖两个合成输入的前后导出与独立重开；RAW 的预览回退原因按运行时字符串/null 字段记录。驱动协议只通过模拟测试；实际原生验收仍等待授权。在线命令可用 --require-installed 禁止隐式安装。
