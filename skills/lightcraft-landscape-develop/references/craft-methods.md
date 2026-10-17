# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子与绑定 |
| --- | --- | --- |
| 1. 列出本库真实照片ID、相机与previewOnly，避免受当前视图过滤遗漏 | `catalog.query` | `{"filter":{}}` |
| 2. 将实际目标设为唯一选择和active，后续无ids方法才作用正确 | `library.select` | `{"ids":["$target.id"],"active":"$target.id","mode":"replace"}` |
| 3. 读取目标原有显影设置 | `develop.get` | `{"id":"$target.id"}` |
| 4. 按已测水平参考校正当前明确选择的目标 | `crop.straighten` | `{"angle":1}` |
| 5. 仅平衡目标曝光 | `develop.set` | `{"control":"light.exposure","value":0.2,"ids":["$target.id"]}` |
| 6. 只输出该目标的风景试样 | `app.export` | `{"ids":["$target.id"],"path":"output/landscape-proof.jpg","longEdge":1600,"dontEnlarge":true,"colorSpace":"srgb"}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "develop.get", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

山脊与建筑无光晕，天空无色带，地平线与裁切正确。

边界：角度1度须由真实水平参考测量后替换；控制ID是crop.angle，develop.get返回值从crop.geometry.angle回读，两者路径不同；crop.straighten依赖当前选择，因此必须先把目标设为唯一选择/active。裁切会损失边缘，先检查主体与最大可用区域；天空局部调整另查mask，不假定自动选天。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。

变量必须绑定当前库真实返回值：单张id为整数，ids为非空扁平整数数组。CLI用`run --library LIB --script steps.jsonl`，每行`{"command":"实际ID","params":{…}}`，同一批的选择和依赖active的操作保持同一次run。捕获动态返回值后再构造下一批，不把$记号直接发给引擎。

## 限定技术回归

Windows main [39013647220](https://github.com/partme-ai/full-aigc-plugins/actions/runs/39013647220)与稳定CLI 13应用矩阵 [39013640352](https://github.com/partme-ai/full-aigc-plugins/actions/runs/39013640352)通过：明确照片范围、参数/产物回读、非目标与原片保护。RAW只验证固定CC0 Nikon D2H样本的运行时完整解码报告、显影和重开，并查看该输出；不是独立解码器或色彩准确度证明。导出隐私验证使用合成EXIF GPS及保留对照，不代表所有隐私元数据格式认证。真实创作效果与宿主画面同步仍未验收；不替代旧CLI 0.2.1固定资格。
