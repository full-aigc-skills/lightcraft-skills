# 照片库流程

输入：原片、持久库位置、add/copy/move 意图；前置：库锁可取得，目标盘可用。add 引用原片；copy 写库管理副本；move 可能删除源文件及 sidecar，需要明确授权且不能同时登记为需保持原片。

建议将 library.import 放在 JSONL 计划中，保留 imported、duplicates、failed、moved/kept，再查询照片记录建立 ID/路径映射。顶部 --import 的导入报告不进入逐步骤输出，要求完整导入审计时使用显式命令。部分导入不重做全批；已有 ID 可继续使用。选择通过 library.select 明确 ids/active，不跨独立会话假定选择保留。

当前研究源码的重复项形状为 `{path, existing, reason}`，已有照片 ID 在 existing；catalog.query 是摘要，不保证提供源路径，路径交接应读取 photo.inspect 的 `{source: {type: "file", path}}`。辅助函数 import_summary 同时保留原生记录与标准化路径；不能解析的 ID/重复项明确标记 IDENTITY_UNCONFIRMED。固定制品仍须经实际发现和原生回归确认，研究源码不代表 CLI 0.2.1 已验证。

库占用不强制解锁，不另建同名空库。Connect 仅在独立扩展已验证后使用；基础包装器只声明 Headless。重开应在第二个原生进程再次查询 library.info、照片 ID/路径和 develop.get，绑定两份 runId 与同库身份。只有保存关闭不构成重开证据。
