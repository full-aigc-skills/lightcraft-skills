# 公共运行契约

仅锁定 macOS arm64 / CLI 0.2.1 / Python 3.11+；研究源码不证明固定发行具备相同能力。

把 `SKILL_DIR` 设置为宿主实际加载的本技能绝对目录，命令路径始终加引号。

纯检查不安装、不执行原生程序，不创建运行目录：

```bash
python3 -I -B "$SKILL_DIR/scripts/bootstrap.py" --no-install
```

已授权安装时才运行安装器；`--runtime-home` 可隔离到指定数据目录，`--archive` 仍强制校验固定摘要。已有损坏版本保留，不覆盖。原生调用会复用该版本；缺失时安装器下载固定制品，不改 PATH、不用 sudo。权限与完整性错误不自动重试编辑。

```bash
python3 -I -B "$SKILL_DIR/scripts/bootstrap.py" --runtime-home "/absolute/runtime"
python3 -I -B "$SKILL_DIR/scripts/commands.py" discover --runtime-home "/absolute/runtime"
```

能力快照将实际二进制、版本、Headless 模式、命令与 controls 摘要绑定。目录 enabled 仅是观察值，选择状态仍由目标会话判断。离线 `--catalog` 可 list/describe/check，不能 run。查询也可能首次安装，只有 doctor 或 bootstrap --no-install 是纯诊断。

计划保留 `{"domain":"lightcraft","steps":[{"command":"library.info","params":{}}]}`。先 check；Lightcraft 参数文档是文本，不是机器 Schema。交付执行默认 run，单计划一个原生会话：

```bash
python3 -I -B "$SKILL_DIR/scripts/commands.py" run "/absolute/plan.json" --library "/absolute/library" --input "/absolute/originals" --output-root "/absolute/exports" --output "/absolute/new-run"
```

输入原片须保持；照片库和工作副本预期可变。已知写入目标与原片/既有文件冲突会执行前拒绝，未识别参数副作用仍不受通用沙箱保护。摘要改变是检测，不提供回滚。不要使用 move 导入已登记需保持的原片。

回执 schemaVersion=1，含 runId、时间、计划/技能/运行时锁/原片身份、逐步骤状态和日志。原生监督器独占超时；stdout/stderr 流式落盘，回执只保留有界尾部，协议从日志逐行解释。UNKNOWN 禁止重放；APPLIED_NOT_SAVED 表示修改在内存生效但持久化未确认。FAILED 后可信 NOT_EXECUTED 步骤只是后续计划候选，还需恢复会话选择与已有授权。

```bash
python3 -I -B "$SKILL_DIR/scripts/commands.py" inspect "/absolute/new-run/receipt.json"
```

inspect 与旧回执读取均只读。直接 cli.py 透传 argv 保持兼容，但缺少完整交付回执和输入保全；不把其零退出当作验收。

实际文件验证使用 Pillow（若已有）或 macOS sips 解码，不静默安装依赖。尺寸/格式/位深读取文件；色彩仅确认可得元数据，不代表视觉保真。缺少解码器或色彩证据时返回失败/未确认。

## 只用现有安装

已有原生运行许可但没有安装许可时，commands.py 的在线 list/describe/check/discover/run 和直接 cli.py 可传 --require-installed。缺失、损坏或平台不支持时拒绝，不创建运行时目录、不调用安装器；不能与 --archive 混用。纯检查仍用 doctor 或 bootstrap.py --no-install，不执行原生程序。

## Connect/MCP 只读探测（扩展实施中）

Headless 计划入口保持不变。`cli.py` 现在在安装前检查实际模式；Connect 与 `--library`、`--import`、`--demo`、`--headless` 或 MCP 素材参数互斥。固定 0.2.1 客户端可能重试连接请求，因此禁止经 Connect 透传修改命令，交互式 Connect MCP 也未开放。只读查询的原生重试单独记录。

```bash
python3 -I -B "$SKILL_DIR/scripts/session_probe.py" --runtime-home "/absolute/runtime" --output "/absolute/new-probe"
python3 -I -B "$SKILL_DIR/scripts/session_probe.py" --runtime-home "/absolute/runtime" --connect "127.0.0.1:18991" --output "/absolute/new-connect-probe"
```

探测只消费已安装并校验通过的固定运行时，不安装；initialize、tools/list 和实际库资源查询在同一 MCP 进程完成。协议握手成功不等于桌面已连接；逐项核对 `backendQuery`、`runtimeIdentity.mode`、传输、地址及执行回执。原生不提供远端会话 UUID 时保留 NOT_PROVIDED，不用客户端 runId 冒充。只读表示不发送照片修改命令；Headless 打开持久库仍可能执行原生库初始化或迁移，严格文件只读任务不要传 `--library`。

当前已验证 Headless MCP 与 Connect 失联的失败路径；桌面真实会话、重启身份和修改/写回门禁仍 OPEN，不宣称完整 Connect/MCP 宿主接入。

### 显式批量范围

使用当前技能的 `scripts/batch_scope.py prepare request.json --output contract.json` 生成合同（输入含 scope/changes/controls，可选 parent）；scope 明确 targetIds、observedIds、allowedFields，changes 每项含明确 ids 和局部 values。controls 必须取当前原生发现结果，不能假定未列出的字段可用。合同的 plan 另存 JSON 后通过本技能 commands.py run 执行；修改只在已授权范围内发生。

执行后用 `scripts/batch_scope.py verify contract.json --receipt /absolute/run/receipt.json --output facts.json` 核对完整前后设置、原片和当前资源身份。修订 prepare 必须带上前次完整合同 parent，保持同一 scope，只提交需要修订的 ID/字段。缺失观测、越界、未知执行或未落盘不能产生通过结论。settings 核对不等于视觉或最终照片交付。

### RAW 样本身份

原生执行前用 `python3 -I -B "$SKILL_DIR/scripts/raw_contract.py" /absolute/manifest.json` 检查版本化样本清单。清单字段为 schemaVersion=1、samples；每项明确 sampleId、make、model、variant、license/licenseUrl、sourceUrl/catalogUrl、path、bytes、sha256，可附 catalogEntryPath/catalogEntrySha256。检查只读，不下载、安装或启动原生程序；缺失、漂移或重复样本在执行前拒绝。

通过后仍须用本技能 commands.py 对明确照片 ID 执行已授权计划，登记原片并保存逐步骤回执。RAW 变体从绑定来源条目记录，不能从文件扩展名推断。catalog.query 的 kind=raw、previewOnly=null 只表示运行时报告完整 RAW；非空原因字符串表示预览回退；缺失或布尔值保持未知。必须核对实际 camera、照片源身份、导出解码和独立会话设置重开；技术通过不等于视觉通过，也不外推其他相机变体。

### SAM 只读评估

用当前技能目录中的 `python3 "$SKILL_DIR/scripts/sam_contract.py" snapshot.json --model-dir /明确的现有模型目录` 检查发现快照和文件；可选 `--status status.json` 只记录报告值，不替代原生回执。无状态命令时编译标记 UNKNOWN。固定 SAM 3 revision/文件身份及未完成门禁见包内 `docs/verification/sam-20261008/README.md`。评估不会下载、接受许可或执行推理；下载和执行须另有明确授权及真实验收，文件匹配不能单独证明可用。
