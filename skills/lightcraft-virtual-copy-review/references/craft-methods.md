# 独立虚拟副本审稿：实际方法与参数

先执行`lightcraft-cli commands --json`及`lightcraft-cli describe 命令ID`，以当前版本回执核对能力。完整参数在[配方](craft-steps.json)，实际枚举在[命令记录](craft-command-evidence.json)，GitHub固定来源见[来源记录](workflow-sources.json)。

## CLI同进程执行

`lightcraft-cli run --library 新建或已核实的库 --import 工作区照片 --script -`从stdin逐行接收`{"command":"...","params":{...}}`。已有库仅在需要时导入，先查询后绑定真实ID。复制粘贴需同一个run进程；示例中的`$`是Agent手动绑定模板，不是CLI变量。每行检查ok和error，有失败停止依赖步骤，不把退出码当图像效果。

## 插件MCP会话

先读取`lightcraft-editor`实际工具schema。当前插件工具为`command_run {"id":"develop.get","params":{"id":实际照片ID}}`，与原生MCP工具名可能不同。`open_file`用于工作区素材导入；随后`inspect`和真实命令回执核对图库与active，不能把独立CLI库当成已打开的Web库。只有当前Web实际暴露并成功执行相应命令时才走同画面操作，否则明确仅CLI可用，不绕用SDK声称宿主同步通过。`command_list`空回执不授权猜命令；先用查询验证无副作用的方法，再按当前后端能力执行。

## 参数绑定与编辑保护

原片及非目标设置不变，副本copyOf指向源ID，实际导出像素发生变化且新进程重开一致。

这是共享原文件的独立目录项，不是物理备份。不能把暗片提亮预设当成自动修复；不删除原片或副本。创建不是幂等操作，超时先查询copyOf和名称，避免重复创建。

库目录要完整保留，包括目录元数据及原照片引用；PNG是审稿派生图，不是可继续编辑的库。源照片不变不等于库自动备份。独立进程重开时再次绑定ID并核对设置和实际像素，单凭相同路径返回不能证明重载。

曝光示例为绝对0.7EV，不是追加0.7，也不保证真实图像不过曝。完成后查看高光、阴影、肤色与裁切；合成像素验证不代表真实照片审美或RAW色彩已验收。
