# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与绑定 |
| --- | --- | --- |
| 1. 列出当前库照片，按光线分组并保留目标ID清单 | `catalog.query` | `{"filter":{}}` |
| 2. 读取已有预设 | `presets.list` | `{}` |
| 3. 明确把样张设为唯一选择和active，避免从错误照片创建预设 | `library.select` | `{"ids":["$sample.id"],"active":"$sample.id","mode":"replace"}` |
| 4. 读取当前active样张设置后再修改 | `develop.get` | `{"id":"$sample.id"}` |
| 5. 在样张确定曝光起点 | `develop.set` | `{"control":"light.exposure","value":0.25,"ids":["$sample.id"]}` |
| 6. 只把适合共享的参数保存为预设 | `preset.create` | `{"name":"Session baseline","groups":["light"]}` |
| 7. 对本组目标照片实际应用样张预设 | `preset.apply` | `{"id":"$preset.id","amount":100,"ids":"$group.photoIds"}` |
| 8. 逐张回读目标照片参数并核对共享项与单张曝光 | `develop.get` | `{"id":"$photo.id"}` |
| 9. 只对组内已确认目标导出JPEG试样，保留原片 | `app.export` | `{"ids":"$group.photoIds","dir":"output/batch","format":"jpeg","longEdge":1600,"dontEnlarge":true,"metadata":"none","conflict":"unique"}` |
| 10. 以同一明确ID集合导出联系表用于整组审阅 | `export.contactSheet` | `{"ids":"$group.photoIds","path":"output/group-proof.pdf","columns":2,"rows":2,"captions":true}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "presets.list", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

按光线分组逐张核对，不同光照不强套同一曝光或白平衡。

边界：只从本库实际catalog ID选择样张和非空扁平目标数组，不能跨库复用。groups:[light]复制整个light组，含曝光/对比/高光等，不能声称只复制曝光或保留目标原有light参数；不共享的color/crop等需前后核对。按光线分组先试样，再实际preset.apply和逐张回读；创建预设不等于批量完成。预设创建依赖active样张，CLI中select/develop/create应放同一次run，捕获创建的真实字符串ID后再apply。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

返回值绑定说明：表中的 `$...` 是待解析参数，不是发送给引擎的字符串。逐步取得真实返回ID后替换，再调用下一步。若实际返回结构不同，先检查结果，不猜ID。

返回值绑定说明：表中的 `$...` 是待解析参数，不是发送给引擎的字符串。逐步取得真实返回ID后替换，再调用下一步。若实际返回结构不同，先检查结果，不猜ID。

变量必须绑定当前库真实返回值：单张id为整数，ids为非空扁平整数数组。CLI用`run --library LIB --script steps.jsonl`，每行`{"command":"实际ID","params":{…}}`，同一批的选择和依赖active的操作保持同一次run。捕获动态返回值后再构造下一批，不把$记号直接发给引擎。

## 限定技术回归

Windows main [39013647220](https://github.com/partme-ai/full-aigc-plugins/actions/runs/39013647220)与稳定CLI 13应用矩阵 [39013640352](https://github.com/partme-ai/full-aigc-plugins/actions/runs/39013640352)通过：明确照片范围、参数/产物回读、非目标与原片保护。RAW只验证固定CC0 Nikon D2H样本的运行时完整解码报告、显影和重开，并查看该输出；不是独立解码器或色彩准确度证明。导出隐私验证使用合成EXIF GPS及保留对照，不代表所有隐私元数据格式认证。真实创作效果与宿主画面同步仍未验收；不替代旧CLI 0.2.1固定资格。
