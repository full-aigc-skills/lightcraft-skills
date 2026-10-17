# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与绑定 |
| --- | --- | --- |
| 1. 列出本库真实照片ID、相机与previewOnly，避免受当前视图过滤遗漏 | `catalog.query` | `{"filter":{}}` |
| 2. 核对库状态和本次交付ID清单 | `library.info` | `{}` |
| 3. 查看后端真实导出预设，不猜预设名 | `export.presets` | `{}` |
| 4. 只导出明确目标，保留其他元数据时单独去GPS且避免覆盖已有交付 | `app.export` | `{"ids":"$targets.photoIds","dir":"output/web","longEdge":2000,"dontEnlarge":true,"format":"jpeg","quality":90,"colorSpace":"srgb","metadata":"all","removeLocation":true,"conflict":"unique"}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "library.info", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

数量、文件名、尺寸、颜色、锐化和可解码性一致，抽查元数据。

边界：ids必须为本库真实非空整数数组，输出数量按该清单核对。metadata:all配合removeLocation只去位置，不能据此保证所有隐私字段都清除；需要更严格政策时改metadata:none并检查实际文件。conflict:unique保留已存在交付，dontEnlarge不放大小图。必须有含GPS原件与保留GPS的对照导出，才能验证移除效果；不能从原本没有GPS的图片推断参数有效。Web库与原生库不同，磁盘导出/备份以当前宿主实际能力为准。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

变量必须绑定当前库真实返回值：单张id为整数，ids为非空扁平整数数组。CLI用`run --library LIB --script steps.jsonl`，每行`{"command":"实际ID","params":{…}}`，同一批的选择和依赖active的操作保持同一次run。捕获动态返回值后再构造下一批，不把$记号直接发给引擎。
