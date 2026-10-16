---
name: lightcraft-scenario-playbooks
description: 使用 LightCraft 执行亮部整理、黑白版本、正方形构图、灰卡白平衡、水印审稿、双格式导出、联系表与分区回退时使用；按场景查询具体CLI/MCP参数和检查。
license: Apache-2.0
---

# LightCraft 场景操作手册

从[8条具体流程](references/workflows.md)选择当前任务。详细步骤与参数在[recipes.json](references/recipes.json)，实际方法观察在[命令证据](references/command-evidence.json)，[GitHub来源](references/sources.json)记录工作流事实与许可，正文与例子为原创适配，不复制外部脚本。

## 同会话与独立CLI

已打开内嵌编辑器时使用该MCP会话，等editor_status就绪，读取宿主schema后调用 `command_run {"id":"方法ID","params":{…}}`；不对另一个文件运行CLI后声称画面同步。每步按当前输入和返回对象选择执行，保存源工程与导出文件并重新打开检查。

CLI：`lightcraft-cli run --library <专用库> --import input.png --script steps.jsonl`；JSONL每行为`{"command":"方法ID","params":{…}}`。同一批操作放同一次run，设置随库保存；重开同一库用`develop.get`核对。已有桌面会话占库时连接该会话，不另开headless竞争。

本插件Web桥与原生库分开。先读取`develop.controls`/`develop.get`确认当前支持的controlId；原生`app.export`磁盘路径、TIFF、联系表等能力不能直接当作Web桥已支持。MCP不支持某命令时明确报告，可按已授权的独立CLI路径完成，但不能声称宿主画面同步。JPEG/PNG测试不能证明任意相机RAW正确解码。

## 执行边界

每条例子是独立任务。初始化、新导入和示例set不能无条件用于既有工程。输出路径使用新名称，原始文件保持不变。真实内容必须查看原片/成片，确认肤色、中性色、主体与细节符合用途。结构化assertions仅适用于嵌入的合成输入，不替代真实素材效果验收。
