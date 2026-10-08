## Purpose

为 Lightcraft Connect/MCP 会话定义独立的运行与证据门禁，防止基础照片闭环、源码存在或结构测试被扩展为未经实际验证的产品支持声明。

## ADDED Requirements

### Requirement: SEXT1-1 固定 CLI 的 Connect/MCP 支持与 Headless 参数互斥

系统 SHALL 验证固定 CLI 的 Connect/MCP 支持与 Headless 参数互斥；证据 MUST 绑定当前版本、执行模式、输入和实际产物。未执行或依赖缺失 SHALL 保留开放状态，不由基础任务替代。

#### Scenario: 缺少该门禁证据
- **WHEN** 只有源码、文档或其他路径的通过报告
- **THEN** 本要求保持未验证，报告实际缺口而不声明已支持

### Requirement: SEXT1-2 只读查询、失联、超时和 NotSaved 的会话事实

系统 SHALL 验证只读查询、失联、超时和 NotSaved 的会话事实；证据 MUST 绑定当前版本、执行模式、输入和实际产物。未执行或依赖缺失 SHALL 保留开放状态，不由基础任务替代。

#### Scenario: 缺少该门禁证据
- **WHEN** 只有源码、文档或其他路径的通过报告
- **THEN** 本要求保持未验证，报告实际缺口而不声明已支持

### Requirement: SEXT1-3 占用照片库不强制解锁，恢复不自动重放

系统 SHALL 验证占用照片库不强制解锁，恢复不自动重放；证据 MUST 绑定当前版本、执行模式、输入和实际产物。未执行或依赖缺失 SHALL 保留开放状态，不由基础任务替代。

#### Scenario: 缺少该门禁证据
- **WHEN** 只有源码、文档或其他路径的通过报告
- **THEN** 本要求保持未验证，报告实际缺口而不声明已支持

#### Scenario: Connect 原生客户端会重试修改请求
- **WHEN** 固定客户端的重连逻辑可能重新发送写命令
- **THEN** 包装器拒绝该修改路径，记录限制；只读查询的原生重试单独披露，不声称修改只执行一次

#### Scenario: MCP 初始化成功但桌面失联
- **WHEN** initialize 和工具目录有响应，实际库资源查询失败
- **THEN** 仅确认 MCP 协议启动，桌面会话和库查询保持失败或未知，不登记为已连接成功
