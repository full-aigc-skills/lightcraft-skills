# 发现与协议

list 展示全部目录，describe 返回真实参数原文；discover 记录 commands/controls 及固定制品身份。任何源码新命令必须先出现在实际目录。覆盖工具 `coverage.py` 对照快照将未知 ID 单列，不用命令名称出现在文档中当作测试证明。

check 仅负责结构、命令存在与明确 schema 子集；目标会话照片选择、库锁和文本参数由原生判断。逐步骤返回 command/ok/result 或 error；缺失、额外、重复、截断结果均 UNKNOWN。普通失败后停止的步骤仅在可信协议下为 NOT_EXECUTED。

完整回执字段见本技能 `scripts/execution-receipt.schema.json`；无版本旧回执保持只读。共享接口由技能源维护，插件只消费，不另写一套参数或原生结果解释器。
