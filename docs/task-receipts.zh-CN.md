# 运行回执与输入身份

六技能的 scripts 来自唯一维护源 runtime/，scripts/generate_runtime.py 确定性生成；维护修改在 runtime/ 进行。各技能可单独复制，运行不依赖本地来源库。

## 运行接口

纯诊断使用 bootstrap.py --no-install 或 commands.py doctor。discover 是在线能力查询，绑定实际二进制、版本、Headless 模式、commands/controls 和摘要；首次查询可能安装固定制品。离线 --catalog 仅用于 list/describe/check。

run 接受 domain/steps，每步 command/params；--input 和 --import 登记需保持的原片，--library 是可修改持久库。--output 指向新的回执目录，--output-root 约束已知写入目标；已知导出与原片、硬链接或已有文件冲突时预检拒绝。未识别副作用不受通用沙箱保护，摘要也不会回滚。

## 回执 v1

回执包括 schemaVersion、runId、startedAt/endedAt、planSha256、skillResourceSha256、runtimeLockSha256、runtimeIdentity、原片前后摘要、可变库前后摘要、每步 index/command/status/native 结果及 process 事实。Schema 随每项技能分发。

cli.py 是唯一原生进程生命周期所有者；网关等待其结构化监督结果，不添加第二个竞争超时。日志流式落盘，尾部限 64 KiB；单日志上限 128 MiB，超限保留 UNKNOWN。结果逐行读取，单行 4 MiB、解释预算 16 MiB；超限不默认成功。process-start.json 提供可得的启动事实。

| 状态 | 含义 |
|---|---|
| STARTED | 已写开始记录，执行结果未确认 |
| NATIVE_EXIT_ZERO_REVIEW_REQUIRED | 所有步骤结果完整且执行退出零，仍待文件、重开、视觉验证 |
| FAILED_OR_PARTIAL | 可信结果中有普通失败；保留成功和明确未执行步骤 |
| PERSISTENCE_UNCONFIRMED | 修改在内存生效但未保存，禁止直接重复修改 |
| UNKNOWN | 超时、中断、协议损坏/缺失/超限或未确认进程事实；不自动重放 |
| INPUT_CHANGED_REVIEW_REQUIRED 等 | 输入或技能资源变化，保留差异并复核 |

inspect 对旧回执只读；无版本或未知版本不能作为继续执行许可。启动进程终止不证明所有后代都退出，停止请求也不代表取消成功。

## 分发同步

同步器属于 **lightcraft-skills** 来源项目：

```bash
python3 -I -B scripts/sync_local_snapshot.py --plugin-root "/absolute/lightcraft-plugin"
```

先验证旧快照、明确六技能清单、来源版本；漂移、删除、已发布来源、额外技能均拒绝普通同步。候选没有真实 tag/commit，发行前必须独立验证实际来源与所有验收层。插件用户运行不需要来源仓库。

## 证据

包校验、故障注入与合成图像验证不构成 Lightcraft 原生闭环。原生/宿主/视觉/目标平台/远端 CI 分层保存；scripts/verify_evidence.py 检测当前源码摘要与报告是否一致。相关内容改变使旧报告失效。

## 安装许可与执行许可

--require-installed 贯穿网关与启动器，只核验并使用已有运行时；缺失时拒绝，不回退到下载/安装。它仍会执行原生命令，不是只读 doctor。合成验收驱动只在明确冷安装阶段使用安装器，后续步骤和 RAW 驱动统一要求已有安装。
