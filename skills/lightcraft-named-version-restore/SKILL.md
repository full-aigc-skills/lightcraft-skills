---
name: lightcraft-named-version-restore
description: 当用户需要用LightCraft完成命名版本试调与准确恢复时使用；通过真实照片ID、同会话命令与可重开检查保护原片和非目标设置。
license: Apache-2.0
---

# 命名版本试调与准确恢复

先读取[实际命令与参数](references/craft-methods.md)，按[逐步配方](references/craft-steps.json)执行。来源固定在[GitHub工作流记录](references/workflow-sources.json)。

先确认目标照片、现有库、期望视觉效果和新输出路径，使用查询回执绑定ID。分清独立CLI与插件MCP的当前会话；不要把示例参数或返回的数组当成单个ID。

试调图与基线像素不同，恢复后全部设置和渲染回到基线；版本名在新进程中仍可检索，非目标照片不变。

命名版本保存当前编辑设置，不是副本，也不等同darktable会话快照；不宣称其分屏UI。version.restore没有id参数，必须绑定active。不要猜index为0，不删除/覆盖既有版本。

需要在宿主打开界面时交给 **lightcraft-editor** 技能。独立安装：`npx skills add full-aigc-skills/lightcraft-skills --skill lightcraft-editor`。本批技能仍为开发候选，市场新发行尚未完成，命令存在不代表Web支持或真实媒体效果验收。
