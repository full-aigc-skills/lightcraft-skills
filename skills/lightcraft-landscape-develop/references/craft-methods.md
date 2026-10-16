# 本场景的 Craft 方法与参数

先读取输入与当前选择。数值、路径、名称和对象编号仅为格式示例；用当前输入、实际返回ID和目标尺寸替换后执行。

| 顺序与目的 | 实际方法 | 参数例子 |
| --- | --- | --- |
| 1. 先检查当前设置 | `develop.get` | `{}` |
| 2. 校正地平线并保留最大可用裁切 | `crop.straighten` | `{"angle":1}` |
| 3. 小幅平衡整体曝光 | `develop.set` | `{"control":"light.exposure","value":0.2}` |
| 4. 输出检查层次 | `app.export` | `{"path":"output/landscape-proof.jpg","longEdge":1600,"dontEnlarge":true,"colorSpace":"srgb"}` |

## 如何调用

宿主内已打开编辑器时使用该同会话MCP；先等待editor_status就绪，读取实际工具schema和当前命令参数。独立CLI可用于文件任务，但新进程与已打开Web编辑器不是同一状态。

本插件MCP包装：`command_run`，参数 `{"id": "develop.get", "params": {}}`。后续行保持同一会话和对象选择，逐条检查实际结果。

LightCraft Web桥没有实时command_list接口，固定CLI目录只帮助定位；先查询develop.controls、develop.get等实际结果。Web库状态与原生库不同，路径导出/备份必须按当前Web API能力核对，不直接套原生磁盘语义。

CLI 语法（下面是展示用写法，实际跨平台执行用argv避免shell引号差异）：

lightcraft-cli run --library LIBRARY --import input.png develop.set control=light.exposure value=0.25 develop.get。一个库由已有桌面会话占用时使用该会话，不另开headless争用。

## 参数核对与完成标准

先查 [当前版本观察目录](craft-command-evidence.json) 中对应方法的完整参数，再按实际运行时查询更新。结构化步骤见 [craft-steps.json](craft-steps.json)。

山脊与建筑无光晕，天空无色带，地平线与裁切正确。

边界：角度需由实际水平参考测量；天空局部调整另查当前mask能力，不假定自动天空选择。

保存可编辑工程后由新进程或重新打开的同一宿主会话核对；导出格式单独解码/查看。方法存在和零退出不代表本场景已经完成。

工作流来源与许可见 [workflow-sources.json](workflow-sources.json)。仅借鉴事实与方法，本文与参数例子原创编写。
