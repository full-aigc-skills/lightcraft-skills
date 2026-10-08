# SAM 只读契约与当前缺口

2026-10-08。本次完成身份/状态评估及拒绝回归，不勾选扩展照片任务 1.3。

固定 CLI 0.2.1（macOS arm64，二进制 SHA256 `45d6f10c7d15c9cf051d23629ab14d0e8ca4c3bb9e3192393f726a918ab1c8da`）实际发现 231 条命令，没有 `segment.*`，状态命令调用在原生计划执行前返回 `unknown_command: segment.model.status`。因此编译标记 UNKNOWN，不等同于 available=false，更不能根据 research 主线的 `sam` 源码断定发布二进制支持。此次仅运行命令/控件发现，没有运行模型推理。

模型来源：[Meta 官方 facebook/sam3](https://huggingface.co/facebook/sam3/tree/3c879f39826c281e95690f02c7821c4de09afae7)，固定 revision `3c879f39826c281e95690f02c7821c4de09afae7`，需要账户手动获批，许可 [SAM License](https://github.com/facebookresearch/sam3/blob/main/LICENSE)。此处没有接受许可或读取账户 token，也没有下载模型文件。

| 文件 | 字节数 | 身份来源 |
|---|---:|---|
| model.safetensors | 3,439,938,512 | 上游 Lightcraft 配置 SHA256 `6d06f0a5f84e435071fe6603e61d0b4cc7b40e0d39d487cfd4d67d8cc11cc14a`；官方受限 API 的 LFS 摘要被遮盖，未独立验证模型 |
| vocab.json | 862,328 | 官方 Git blob SHA1 `182766ce89b439768edadda342519f33802f5364`；读取现有文件后另记录实际 SHA256 |
| merges.txt | 524,619 | 官方 Git blob SHA1 `76e821f1b6f0a9709293c3b6b51ed90980b3166b`；读取现有文件后另记录实际 SHA256 |

不将 Git blob SHA1 描述为官方 SHA256。固定 revision 的官方树元数据保存在 official-pinned-tree.json；模型 API 信息在 official-model.json。权重加分词文件合计 3,441,325,459 字节，运行内存需求另计。没有分发权重或分词原文件。

sam_contract.py 只读取明确提供的快照、可选状态和模型目录。命令存在不能单独证明编译启用，状态布尔值严格校验，来源不匹配或数据自相矛盾拒绝。现有文件按大小、权重 SHA256 或 Git blob 身份逐项核对，拒绝目录/文件符号链接和读取期间变更；不创建目录、不下载、不执行原生程序或推理。

sam-inspect 重新验证固定模型清单、快照/状态摘要、当前模型文件和评估结果，拒绝改写摘要后替换模型、伪造启用或授权、文件漂移；旧格式仅可读历史查看。评估报告是观察输入，不是原生回执证明，输出始终禁止下载、任务执行、交付与重放；这不是给通用原生调用增加沙箱或权限系统。

真实 SAM 可用二进制/桌面、用户获批的模型来源与许可接受、明确模型下载及执行授权、实际分割/产物/独立重开和宿主视觉验收仍缺失。任务 1.3/1.4 保持 OPEN，现有公开插件技能快照没有改动。其他扩展任务继续按原规格推进。

五项当前实际观察报告篡改均拒绝：编译状态提升、下载放行、执行放行、伪造模型已验证、清空阻塞项，见 actual-report-rejections.json。离线回归技能库 90 项、插件 57 项，Python 3.12/3.13；插件测试通过 LIGHTCRAFT_SOURCE_GIT 显式绑定本地来源 tag/commit，不省略来源核验。
