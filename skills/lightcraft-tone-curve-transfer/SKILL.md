---
name: lightcraft-tone-curve-transfer
description: 当用户需要用LightCraft完成仅迁移曲线并保留逐片曝光裁切时使用；通过真实照片ID、同会话命令与可重开检查保护原片和非目标设置。
license: Apache-2.0
---

# 仅迁移曲线并保留逐片曝光裁切

先读取[实际命令与参数](references/craft-methods.md)，按[逐步配方](references/craft-steps.json)执行。来源固定在[GitHub工作流记录](references/workflow-sources.json)。

先确认目标照片、现有库、期望视觉效果和新输出路径，使用查询回执绑定ID。分清独立CLI与插件MCP的当前会话；不要把示例参数或返回的数组当成单个ID。

目标curve完整组等于样片，曝光/色彩/白平衡/裁切等非curve组不变；源与排除照片不变，目标渲染实际改变并可重开。

曲线并非普适风格，需逐张审核曝光/肤色/剪裁。不是复制全部编辑，也不宣称与darktable历史模块一一对应。develop.copy的内存剪贴板不能跨独立CLI进程；多目标逐张回读与导出，不能只检查第一张。

需要在宿主打开界面时交给 **lightcraft-editor** 技能。独立安装：`npx skills add full-aigc-skills/lightcraft-skills --skill lightcraft-editor`。本批技能仍为开发候选，市场新发行尚未完成，命令存在不代表Web支持或真实媒体效果验收。
