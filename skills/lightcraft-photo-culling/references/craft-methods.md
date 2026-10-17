# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与绑定 |
| --- | --- | --- |
| 1. 列出本库真实照片ID、相机与previewOnly，避免受当前视图过滤遗漏 | `catalog.query` | `{"filter":{}}` |
| 2. 确认本次两张精选的实际ID清单并替换整个数组 | `library.select` | `{"ids":"$targets.photoIds","active":"$sample.id","mode":"replace"}` |
| 3. 只给确认的精选评级，不按临时选择猜测范围 | `photo.rate` | `{"rating":4,"ids":"$targets.photoIds","advance":false}` |
| 4. 只标记同一精选清单，不删除任何原片 | `photo.flag` | `{"flag":"pick","ids":"$targets.photoIds","advance":false}` |
| 5. 仅把明确精选导出联系表，保留其他拒绝片 | `export.contactSheet` | `{"path":"output/selects.pdf","ids":"$targets.photoIds","columns":4,"rows":5,"captions":true}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "library.info", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

精选数量与联系表一致，检查失焦、闭眼、重复，保留筛选理由。

边界：先枚举真实照片并核对非空、扁平整数ID数组。评级与pick只表示已完成选片决策的元数据写入，不自动判断美感、焦点或重复照片；advance:false避免改变active后误操作。联系表仍需检查缩略图与文件名对应，不删除拒绝片或原片。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

变量必须绑定当前库真实返回值：单张id为整数，ids为非空扁平整数数组。CLI用`run --library LIB --script steps.jsonl`，每行`{"command":"实际ID","params":{…}}`，同一批的选择和依赖active的操作保持同一次run。捕获动态返回值后再构造下一批，不把$记号直接发给引擎。
