# skill-routing Specification

## Purpose
明确六项 LightCraft 技能的唯一职责、交接输入与输出，使用户自然语言任务能够选择最短执行链，并在单技能安装环境中取得当前操作必要的规则和可验证示例。
## Requirements
### Requirement: SRT-1 六技能路由与职责

技能库 SHALL 保留六项既有技能身份，由 lightcraft-use 路由任务，setup/cli/library/develop/export 分别承担诊断、公共契约、照片库、显影与导出；领域技能 MUST NOT 复制另一套公共参数或恢复规则。

#### Scenario: 用户只要求批量显影并导出
- **WHEN** 用户给定已有照片库和导出目标但未指定技能
- **THEN** 路由复用已完成安装及导入，交接照片身份给 develop/export，并分别报告编辑、导出、验证阶段

#### Scenario: 用户显式选择领域技能
- **WHEN** 用户明确请求 lightcraft-cli-export
- **THEN** 保持指定入口，只补充缺失前置条件，不再次启动完整导入流程

### Requirement: SRT-2 操作契约与按需资料

每项领域技能 SHALL 提供输入、前置条件、副作用、输出、恢复及验收契约，以及成功、部分失败、恢复和不安全覆盖拒绝示例；资料 SHALL 位于该技能自身目录，跨技能交接使用技能名和安装说明。

#### Scenario: 只安装显影技能
- **WHEN** 宿主仅复制 lightcraft-cli-develop 到含空格和中文的路径
- **THEN** 技能能访问自身资源，并明确交接缺失技能，不读取兄弟目录或假定固定安装路径

### Requirement: SRT-3 命令覆盖与领域语言

技能库 SHALL 建立版本绑定的命令归属表，标记负责技能、模式、副作用、示例及验证状态；LightCraft 用户说明 MUST NOT 要求执行无关领域命令，未验证能力 MUST 保持可见。

#### Scenario: 新目录出现未覆盖命令
- **WHEN** 当前固定 CLI 的命令目录含覆盖表之外的命令
- **THEN** 校验报告差异并标记未覆盖，不把名称出现在文档中视为已经测试

