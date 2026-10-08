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
