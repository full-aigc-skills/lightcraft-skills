# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与返回值绑定 |
| --- | --- | --- |
| 1. 列出当前库照片，按光线分组并保留目标ID清单 | `catalog.query` | `{}` |
| 2. 读取已有预设 | `presets.list` | `{}` |
| 3. 明确把样张设为唯一选择和active，避免从错误照片创建预设 | `library.select` | `{"ids":["$sample.id"],"active":"$sample.id","mode":"replace"}；绑定：sample.id从当前catalog.query实际照片中选择；ids整字段示例[12]，active示例12，必须为同一照片` |
| 4. 读取当前active样张设置后再修改 | `develop.get` | `{"id":"$sample.id"}；绑定：id换成上一步active的真实样张ID` |
| 5. 在样张确定曝光起点 | `develop.set` | `{"control":"light.exposure","value":0.25,"ids":["$sample.id"]}；绑定：ids只含样张真实ID，与library.select.active相同` |
| 6. 只把适合共享的参数保存为预设 | `preset.create` | `{"name":"Session baseline","groups":["light"]}` |
| 7. 对本组目标照片实际应用样张预设 | `preset.apply` | `{"id":"$preset.id","amount":100,"ids":"$group.photoIds"}；绑定：id = 创建的真实预设ID；ids整字段替换为目标数字数组，例如[12,13]。调用前断言非空、每项为整数且没有嵌套数组。不能传入["$group.photoIds"]或[[12,13]]。` |
| 8. 逐张回读目标照片参数并核对共享项与单张曝光 | `develop.get` | `{"id":"$photo.id"}；绑定：对组内每个真实photo ID分别执行；导出联系表比较结果` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "presets.list", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

按光线分组逐张核对，不同光照不强套同一曝光或白平衡。

边界：预设groups需当前schema确认；当前样张的所有值不应不加判断复制到整组。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

返回值绑定说明：表中的 `$...` 是待解析参数，不是发送给引擎的字符串。逐步取得真实返回ID后替换，再调用下一步。若实际返回结构不同，先检查结果，不猜ID。

返回值绑定说明：表中的 `$...` 是待解析参数，不是发送给引擎的字符串。逐步取得真实返回ID后替换，再调用下一步。若实际返回结构不同，先检查结果，不猜ID。
