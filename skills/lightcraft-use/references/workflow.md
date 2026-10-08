# 路由与交接

| 意图 | 入口 | 交接 |
|---|---|---|
| 只检查环境 | setup 的 --no-install | 诊断，不安装 |
| 已有库局部修图 | develop | 当前照片 ID、基线、修改范围 |
| 导入或库占用 | library | 导入报告、ID/路径、选择、库位置 |
| 已有候选导出 | export | 设置、输出目标、原片、技术与视觉验收 |
| 原生命令问题 | cli | 当前命令/控件快照与计划 |

每个领域交接使用技能名；例如 **lightcraft-cli-export**。安装：`npx skills add full-aigc-skills/lightcraft-skills --skill lightcraft-cli-export`。仅安装本技能也有完整公共运行资源，不要求读取兄弟技能文件。

完成报告分别列编辑、保存、实际文件、独立重开、视觉结论。插件若可用，使用其本地控制器维护 taskId 和审阅；技能独立使用时仍可保留网关回执，不伪造插件状态。
