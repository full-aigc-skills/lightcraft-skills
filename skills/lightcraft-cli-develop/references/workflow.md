# 显影流程

输入：持久库、目标 ID/选择、用户目标及允许调整集合；前置：当前 controls 与目标照片存在。先查询 develop.get 保存完整基线，读取 develop.controls 当前范围和数值，保存预览。执行 develop.set 的显式 values 或 control/value；不为局部要求调用 reset、完整 develop.replace 或全库同步。

photo_workflows.apply_local_changes 会对显式控件做范围和基线检查、构造比较用设置，不运行原生。实际原生输出仍须读取 develop.get，逐字段核对允许范围之外不变。批量修改先明确 IDs 与要同步的字段；不可将一个照片的结果扩展到所有照片。

交付需前后设置、预览、修改范围、原片摘要、第二会话重开。RAW 区分完整原始解码与嵌入预览回退；HDR 合成不代表 HDR 编辑/预览/导出全链路。NotSaved 不重复编辑，先核对 library.info 的未保存状态和持久化。
