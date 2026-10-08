# RAW 逐样本身份与当前原生验收

2026-10-08；扩展照片任务 1.2 完成，仅涵盖下面四个明确样本。1.3 SAM 与 1.4 整体配套同步/归档继续 OPEN。

| 相机与变体 | 固定 CLI 0.2.1 / macOS arm64 结果 |
|---|---|
| Nikon D2H，12bit compressed Lossy type 1 | FULL_RAW_REPORTED：运行时报告完整 RAW，显影导出、相机身份和独立重开通过；不是独立解码器差分证明 |
| Canon EOS 7D，sRAW2 sRAW | PREVIEW_FALLBACK：仅预览回退，原因 Canon sRAW/mRAW，完整 RAW 未证明 |
| Blackmagic Micro Cinema Camera，12bit DNG | UNSUPPORTED：JPEG SOF1 不支持且没有嵌入预览 |
| Canon EOS D30，RAW CRW | UNSUPPORTED：RawOther files are not supported yet |

`matrix-contract.json` 的 PASS 表示逐样本身份、分类和保护门禁通过，绝不表示四个 RAW 全支持。包含不支持样本的驱动正常返回非零；这被记录为支持边界，不掩盖为成功导入。其他环境/协议失败是 FAILED 或 UNCONFIRMED，不能算作 UNSUPPORTED。

manifest.json 绑定制造商、型号、具体变体、字节数、SHA256、来源和许可。四份原始目录条目及摘要从 [raw.pixls.us](https://raw.pixls.us/) 当前目录逐项核实，许可链接为 CC0；记录和派生产物保留，四个原始 RAW 文件不提交至仓库。清单检查不自动下载、安装或运行。原始测试输入仍位于工作区 evaluation-results/lightcraft-raw-20261008/samples。

native/ 保存本仓库对应执行的逐样本回执、计划、日志和派生 PNG，保留真实绝对路径与身份；照片库未打包。原片前后摘要、执行资源、固定原生二进制及版本、实际照片 ID、camera 字符串、previewOnly 原始标记、显影设置与独立重开均单独核对。Nikon 的 NIKON CORPORATION/NIKON 和 Canon 的重复制造商前缀有明确规范化规则，不做同品牌型号的模糊匹配。

五项实际报告篡改全部拒绝：预览伪装为完整 RAW、改写变体并重算 manifest 摘要、改写产物摘要、替换原生版本、改写原片摘要。rejected-*.json 是故意破坏的报告，仅作为负向证据，不能用于执行或支持声明。

插件 raw-inspect 同时核对当前技能源结果和插件公开快照结果。source-final-inspection.json 的 sourceSnapshotMatches=false，plugin-final-inspection.json 为 true；观察入口均不允许任务执行、交付或自动重放。旧报告仅兼容只读历史查看。CLI 宿主加载、真实照片视觉审阅、其他型号和平台均 NOT_RUN，不借本轮技术验证关闭这些门禁。
