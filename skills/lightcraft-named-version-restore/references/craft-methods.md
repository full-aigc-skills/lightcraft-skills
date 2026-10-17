# 命名版本试调与准确恢复：实际方法与参数

先执行`lightcraft-cli commands --json`及`lightcraft-cli describe 命令ID`，以当前版本回执核对能力。完整参数在[配方](craft-steps.json)，实际枚举在[命令记录](craft-command-evidence.json)，GitHub固定来源见[来源记录](workflow-sources.json)。

## CLI同进程执行

`lightcraft-cli run --library 新建或已核实的库 --import 工作区照片 --script -`从stdin逐行接收`{"command":"...","params":{...}}`。已有库仅在需要时导入，先查询后绑定真实ID。复制粘贴需同一个run进程；示例中的`$`是Agent手动绑定模板，不是CLI变量。每行检查ok和error，有失败停止依赖步骤，不把退出码当图像效果。

## 插件MCP会话

先读取`lightcraft-editor`实际工具schema。当前插件工具为`command_run {"id":"develop.get","params":{"id":实际照片ID}}`，与原生MCP工具名可能不同。`open_file`用于工作区素材导入；随后`inspect`和真实命令回执核对图库与active，不能把独立CLI库当成已打开的Web库。只有当前Web实际暴露并成功执行相应命令时才走同画面操作，否则明确仅CLI可用，不绕用SDK声称宿主同步通过。`command_list`空回执不授权猜命令；先用查询验证无副作用的方法，再按当前后端能力执行。

## 参数绑定与编辑保护

试调图与基线像素不同，恢复后全部设置和渲染回到基线；版本名在新进程中仍可检索，非目标照片不变。

命名版本保存当前编辑设置，不是副本，也不等同darktable会话快照；不宣称其分屏UI。version.restore没有id参数，必须绑定active。不要猜index为0，不删除/覆盖既有版本。

库目录要完整保留，包括目录元数据及原照片引用；PNG是审稿派生图，不是可继续编辑的库。源照片不变不等于库自动备份。独立进程重开时再次绑定ID并核对设置和实际像素，单凭相同路径返回不能证明重载。

曝光示例为绝对0.7EV，不是追加0.7，也不保证真实图像不过曝。完成后查看高光、阴影、肤色与裁切；合成像素验证不代表真实照片审美或RAW色彩已验收。
