## Context

扩展登记，未实施。源码与固定制品能力必须分开。

## Goals / Non-Goals

Goals: 连接模式、桌面库占用与会话身份。Non-Goals: 不修改基础变更验收标准，不从离线测试推导平台、RAW 或宿主通过。

## Decisions

按固定版本、执行模式、素材/制品摘要和明确目标绑定证据；复用版本化回执和任务状态，不建立第二套原生解释器。失败和 UNKNOWN 保留，外部安装/发布按对应授权。

## Risks / Trade-offs

依赖、模型或设备缺失时保留 BLOCKED/NOT_RUN；不能用新文档关闭运行门禁。

## Migration Plan

先建立失败回归，再实现并验证各门禁；兼容旧记录并保留人工修改。

## 2026-10-08 实施细化

当前包装器将所有原生调用登记为 Headless；上游 `crates/mcp/src/backend.rs` 的 `Remote::call` 会在 roundtrip 失败后重连并重新发送同一请求，写命令也不例外。不能在回执中声明自动重放为 false 而放行该原生修改路径。

本阶段在安装前校验 run/MCP 模式，拒绝 Connect 与 `--library`、`--import`、`--demo`、`--headless` 或 MCP 素材参数混用；监督回执记录实际模式、传输和地址。Connect 的 run 只开放审计过的查询，脚本整体校验；交互式 Connect MCP 不开放，改用封闭且有界的只读探测请求。原生客户端仍可能重试查询，明确登记该行为；不声明原生 exactly-once。

探测沿用唯一原生监督器，输入 JSONL 在启动前读入并绑定摘要，单进程完成 initialize、initialized、tools/list 和 library resource read。协议响应必须逐 ID 匹配；失联、缺失响应或超时不当作成功，NotSaved 继续复用既有执行分类。MCP 初始化或工具目录成功不能证明桌面连接成功；只有实际库查询返回才登记查询可达。原生协议不提供桌面会话 UUID 时，保留 NOT_PROVIDED，不用客户端 runId 冒充远端会话身份。

固定版本 Headless MCP 与 Connect 失联/参数拒绝可在当前 macOS arm64 验证；实际桌面会话、重启身份、写回失败和被占用库的完整门禁仍逐项开放，未满足不勾选任务、不归档。
