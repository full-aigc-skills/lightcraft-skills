# 当前 MCP 与真实 NotSaved 增量证据（2026-10-08 至 09）

Codex CLI 0.161.0，固定 LightCraft CLI 0.2.1（macOS arm64）已实际验证。当前仓库技能字节与前轮宿主已安装六技能完全一致，原生程序摘要与 runtime.lock 固定摘要一致。结果及配置分别保留在本仓库的 source-* 或 plugin-* 文件中；此轮未修改任何技能或运行代码。

## 真实宿主 MCP 查询

临时隔离配置 `lightcraft_readonly`，仅启用 `query_photos` 与 `list_commands`。实际 app-server 目录核对仅有这两个工具；真实模型仅调用一次 query_photos(limit=2, offset=0)，返回 photos=[]、total=0；没有 shell 调用。安装技能和全局配置摘要未变，临时 MCP 配置已恢复、auth 副本已移除。此证据证明手工配置的当前宿主 MCP 加载与查询，不证明插件 manifest 自动注册或桌面 Connect。

首轮工具调用因未设置工具级许可被 CLI 拒绝，原始 FAIL 保留在 approval-required-first-attempt/。按已授权的只读验收，在隔离配置中为这两个允许工具明确设置 approval_mode="approve" 后通过；没有开放编辑工具或修改全局权限。配置语义核对来源：[OpenAI MCP 文档](https://developers.openai.com/codex/mcp/) 的 enabled_tools 与 tools.<tool>.approval_mode。

## 真实磁盘写入故障与恢复

notsaved_acceptance.py 仅操作新建的合成图测试库。先写入评分 1，原生 MCP 会话中选择照片后，把该专用库 catalog.log 暂设只读；显式 photo.rate(rating=4) 只发送一次。真实原生响应为“saved in memory but not written to disk”，内存评分为 4，unsavedOps>0，磁盘 journal 字节未变。包装器从实际错误响应分类为 APPLIED_NOT_SAVED / PERSISTENCE_UNCONFIRMED，未将其认定为保存成功。

恢复原权限后显式查询触发原生保存队列重试；后续 library.info 确认 unsavedOps=0，结束进程后独立重开确认评分为 4，合成原片摘要未变。原生持久化队列重试与重放 photo.rate 是两种行为；此验收没有重放编辑命令，不声明原生从不重试保存。

初次驱动错误地期待状态名 NOT_SAVED，并用恢复后第一条 library.info 的返回值确认清队列，结果为 FAIL，保留在 notsaved-first-attempt/。实际状态契约为 APPLIED_NOT_SAVED；该原生命令先生成查询结果、再尝试保存，因此需下一条观察确认队列清零。修正驱动断言后在另一全新测试库重新执行并通过，未修改或重写首轮结果。

## 仍未完成

真实桌面 Connect、桌面失联/重启恢复、桌面 NotSaved、Connect 占库恢复，以及插件不可变技能源配套仍缺证据。此处的直接 headless 故障注入不替代桌面路径；手工宿主配置不冒充插件自动集成。三个 Connect/MCP 能力任务与跨仓库同步归档任务均继续 OPEN。两仓库合计仍为 17 项 OPEN，Nikon RAW 视觉 FAIL 保持有效，不公开发布候选。

归档不包含隔离 home、凭据、程序或测试库；所有证据摘要见 SHA256SUMS.json。绝对路径用于记录本次执行身份，驱动重跑前需检查参数与新输出目录。
