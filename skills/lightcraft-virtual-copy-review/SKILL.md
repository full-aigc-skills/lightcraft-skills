---
name: lightcraft-virtual-copy-review
description: 当用户需要用LightCraft完成独立虚拟副本审稿时使用；通过真实照片ID、同会话命令与可重开检查保护原片和非目标设置。
license: Apache-2.0
---

# 独立虚拟副本审稿

先读取[实际命令与参数](references/craft-methods.md)，按[逐步配方](references/craft-steps.json)执行。来源固定在[GitHub工作流记录](references/workflow-sources.json)。

先确认目标照片、现有库、期望视觉效果和新输出路径，使用查询回执绑定ID。分清独立CLI与插件MCP的当前会话；不要把示例参数或返回的数组当成单个ID。

原片及非目标设置不变，副本copyOf指向源ID，实际导出像素发生变化且新进程重开一致。

这是共享原文件的独立目录项，不是物理备份。不能把暗片提亮预设当成自动修复；不删除原片或副本。创建不是幂等操作，超时先查询copyOf和名称，避免重复创建。

需要在宿主打开界面时交给 **lightcraft-editor** 技能。独立安装：`npx skills add full-aigc-skills/lightcraft-skills --skill lightcraft-editor`。本批技能仍为开发候选，市场新发行尚未完成，命令存在不代表Web支持或真实媒体效果验收。
