# RAW 偏色候选的真实失败审阅（2026-10-09）

当前插件 a9660e6 的真实控制器与受保护公开技能源 v0.1.0-dev.1，固定 LightCraft CLI 0.2.1 / macOS arm64，在全新专用库执行 Nikon D2H NEF 导入、仅曝光 +0.25、PNG 导出与 photo.inspect；原片摘要保持不变。未修改白平衡、配置文件或受管技能。

新导出 exports/nikon-raw.png 经独立 view_image 实际审阅，明显青绿色偏色仍可复现；与同一 NEF 内嵌相机 JPEG nikon-embedded-8256.jpg 对照，墙面与白色色块不通过。相机 JPEG 仅为视觉参照，不代表色度真值或 deltaE；不能把此图的技术解码通过描述为色彩质量通过。

真实控制器链路：PLANNED → 原生执行 → VERIFYING → AWAITING_REVIEW → 记录视觉 FAIL → deliver 拒绝 delivery_visual_review_required。技术检查为 PASS，视觉为 FAIL；拒绝后任务状态字节不变，没有 delivery.json，未重放编辑或伪造修订。result.json 的 PASS_NEGATIVE_DELIVERY_GUARD 仅表示失败候选交付防线有效；creativeAcceptance 仍为 FAIL，未修复原生偏色。

归档包含实际逐步骤回执、进程/输出日志、原生计划、审阅绑定、失败审阅、交付拒绝、状态历史及新导出。输入 NEF 使用既有许可/摘要绑定样本，身份见 task/state.json；原始文件未重复归档，原路径保持用于核对实际输入。没有归档程序、凭据或照片库。

此处是插件候选的实际失败验收，技能源仓库仅保留配套证据，不能据此声明当前技能源原生执行或跨仓库来源升级。两仓库 17 项扩展任务继续 OPEN；桌面 Connect、SAM、移动设备与来源同步等尚未完成，视觉发行门禁仍为 FAIL。脚本 record-fail 分支须在实际查看当前绑定候选后才执行，不能仅按脚本存在或预设文本生成视觉结论。
