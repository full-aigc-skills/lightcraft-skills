当前验收以 **final/** 下记录为准；同目录较早文件仅保留过程历史。最终控制器还验证 JSON 布尔类型不能被数字 0/1 替代。

# 明确批量范围与选择性修订验收

2026-10-08；SEXT2-1 完成，扩展任务 1.2/1.3/1.4 继续 OPEN。仅证明固定 CLI 0.2.1 / macOS arm64 的三张合成测试图；不外推 RAW、SAM、其他平台、桌面 Connect 或真实用户照片审美。

目标 ID 为 2、3，对照 ID 为 1，唯一允许字段 light.exposure。初次目标曝光均为 0.5，选择性修订只把 ID 3 改为 0.25。完整设置比对确认 ID 2、对照 ID 1 和所有未声明字段不变；ID 2 前后重新导出的像素、非 ICC 元数据和 ICC 内容一致（仅 ICC 头创建时间可不同），完整文件摘要分别记录；ID 3 导出像素改变。已选候选仍要求文件摘要不变，不豁免 ICC 变化。四个 PNG 技术解码/尺寸检查通过，独立会话重开恢复所有三张设置且 unsavedOps=0。

当前生成的 batch_scope.py 只生成计划和核对回执，不自行运行或重放。prepare 显式接受 scope/changes/controls/parent；scope 含 targetIds、observedIds、allowedFields。verify 要求当前资源摘要、原片前后摘要、固定原生身份、准确逐步骤回执和完整照片身份与设置；不能用缺失观测、NotSaved 或 UNKNOWN 通过。调用者仍须用 commands.py run 执行生成计划。它是显式批量工作流契约，不是通用 CLI 沙箱。

`index.json`、两个合同、两个设置事实、各实际 run 的 receipt/logs、原片及导出副本一并保留。`acceptance.py` 为真实执行驱动，要求明确原生安装目录；不自行安装，不生成视觉审阅结论。副本保留原始验收路径和身份，不重写回执为可重放示例。

插件配套运行使用受保护的公开技能源 v0.1.0-dev.1，不伪造已经升级到本次未发行资源。其任务本地策略在 create/run/revise 限制批量范围，并独立核对 native photo.inspect 的完整设置。实际插件审阅与交付证据见配套插件仓库 `docs/verification/batch-20261008/`。
