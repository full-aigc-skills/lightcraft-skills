---
name: lightcraft-cli-export
description: 用户显式要求使用 Lightcraft 导出照片、检查格式尺寸色彩或核对实际交付文件时使用。
license: Apache-2.0
---

# Lightcraft 导出验证

输出目标与命名冲突、真实解码及媒体信息；交付需记录重开和视觉结果。
仅声明 CLI 0.2.1 / macOS arm64 / Python 3.11+ 的固定运行范围；原生、宿主和视觉验收状态分别记录。

## 必要输入与执行

先确定原片、持久照片库、目标照片、用户修改范围及输出根；复用已核实的安装和已有阶段。显式指定本技能时保留入口。

把 `SKILL_DIR` 设为宿主实际加载本 SKILL.md 的绝对目录，本技能脚本可独立使用，不猜测开发者路径。

```bash
python3 -I -B "$SKILL_DIR/scripts/bootstrap.py" --no-install
```

只检查环境到此结束。查询/执行可能触发缺失运行时的固定安装，只在已有相应授权时使用。
执行前按需阅读 [公共运行契约](references/runtime.md)，本领域步骤见 [操作与验收](references/workflow.md)。

## 输出与恢复

交接照片 ID/库位置、原片身份、当前设置、版本化执行回执和实际输出。编辑、保存、解码、重开、视觉分别验收；零退出只表示待验证。
UNKNOWN 不重放；部分成功保留已生效步骤，NotSaved 区分内存修改与未落盘。已知导出冲突执行前拒绝，摘要检测不提供回滚或通用沙箱。

[成功、部分失败、恢复与覆盖拒绝示例](examples/scenarios.md)用于决策；公共脚本和契约保留在本技能内。
跨技能交接按名称和安装命令，不读取兄弟目录。需要全流程时使用 **lightcraft-use**；安装：`npx skills add full-aigc-skills/lightcraft-skills --skill lightcraft-use`。
