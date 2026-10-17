# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与绑定 |
| --- | --- | --- |
| 1. 列出本库真实照片ID、相机与previewOnly，避免受当前视图过滤遗漏 | `catalog.query` | `{"filter":{}}` |
| 2. 将实际目标设为唯一选择和active，后续无ids方法才作用正确 | `library.select` | `{"ids":["$target.id"],"active":"$target.id","mode":"replace"}` |
| 3. 核对控制范围；先按catalog相机和previewOnly判断完整RAW或预览回退 | `develop.controls` | `{}` |
| 4. 仅对确认的RAW目标小幅校正曝光 | `develop.set` | `{"control":"light.exposure","value":0.25,"ids":["$target.id"]}` |
| 5. 回读该目标设置 | `develop.get` | `{"id":"$target.id"}` |
| 6. 只导出该目标的色彩参考 | `app.export` | `{"ids":["$target.id"],"path":"output/raw-proof.jpg","width":1600,"dontEnlarge":true,"colorSpace":"srgb"}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "develop.controls", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

对照实际RAW解码肤色、中性色与高光；色彩异常先停止。

边界：先从catalog.query读取具体相机、RAW变体与previewOnly；出现回退原因只能声明预览显影，不能当完整RAW。无回退标记也是运行时报告，不是独立解码器差分证明。已有固定Nikon D2H NEF可作单一样本验证，但不推广到其他相机、压缩变体或所有RAW。色彩异常时停止，不能靠曝光掩盖解码问题。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

变量必须绑定当前库真实返回值：单张id为整数，ids为非空扁平整数数组。CLI用`run --library LIB --script steps.jsonl`，每行`{"command":"实际ID","params":{…}}`，同一批的选择和依赖active的操作保持同一次run。捕获动态返回值后再构造下一批，不把$记号直接发给引擎。
