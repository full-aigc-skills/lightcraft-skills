# 固定平台原生增量验收

2026-10-08；SEXT3-1/PEXT3-1 保持 OPEN，不将局部平台证据提升为全平台或插件来源配套完成。

Linux aarch64 官方发布包 archive SHA256 为 `57c0c2504de55a8bc6a0c9611a030272abd8e254b255e12f89114ed6bc16c69e`；其中 CLI SHA256 为 `32a45ac2429b72be70bbc72706234d3f322db029825ec3250d8224ce8a1881dc`。Linux x86_64 官方包及 CLI 分别固定 `543f91c96e4081e86065ec8fb3d62447b08bfd6ae0da22df50fc27a55bb9777d`、`b008a5b86ca2a0a727714aa5d30ddcde59cd578ff0bfbda6bee76c7bf1507ab0`。资产来自实际 GitHub 0.2.1 Release API 的摘要，CLI 摘要在核对归档之后取得；没有执行未核验包。

技能源 bootstrap 已支持这两个官方 tar.gz 发布树，精确核对版本/平台/资产名、压缩包摘要、解包安全与 CLI 摘要；只复制 CLI 和许可，不安装桌面、服务，不修改 PATH。既有 ZIP 安装保持兼容。Linux 使用系统 glibc、libgcc_s、libm，当前实际容器依赖全部解析，glibc 版本及完整输入/资源身份在 linux-aarch64/native-evidence.json。该包没有单独发布的代码签名证明，公开制品摘要不冒充发行者数字签名。

原生验收在已有 Docker 服务的隔离 Linux arm64 用户空间运行，精确基础镜像/架构见 container.json。图像解码依赖 Pillow 12.0.0 的官方 wheel SHA256 与原生验收 requirements 一同固定；只在容器内部安装，不修改宿主 Python。实际运行阶段无网络，丢弃全部 Linux capabilities，并启用 no-new-privileges。

两张原创合成 PNG/JPEG 实际导入、显影、导出六个产物、逐个实际解码与第二会话重开通过；完整设置及原片摘要前后保持，记录本轮原生版本、运行资源、计划/步骤、日志、库持久状态。linux-aarch64/ 的原绝对路径为容器 /work，归档不是可自动重放的任务。库与二进制不随证据分发。六个归档产物在当前归档目录再核对摘要和图像解码，见 archived-artifacts.json。

macOS universal CLI 的 codesign --verify --strict 成功，实际 Developer ID/TeamIdentifier 与动态依赖输出保留在 macos-checks/。这只证明所记录二进制的签名校验，不替代单独公证/完整桌面验收。本机 Intel 分支启动返回 Bad CPU type（无 Rosetta），不能声明 Intel 原生通过。

技能源已配置独立 native-platforms CI 对 Linux arm64/x86_64、macOS Intel/arm64 执行同一照片验收；每个目标必须核对实际 platform 字段并上传产物/回执。不从矩阵配置推导运行通过，当前各提交的远端结果另行核验。

插件受管六技能仍来自公开 v0.1.0-dev.1，108 文件未改变；该快照仍只有 macOS arm64 安装锁。本目录的 Linux 结果属于技能源候选，不是当前插件 Linux 安装/任务入口或宿主验收。Windows 未适配，其他平台真实验收及技能源不可变发行配套继续开放，当前综合任务不勾选、不归档、不公开发行。

本地回归：Python 3.12/3.13 各 99 项通过；结构、受管来源/生成资源一致性、OpenSpec strict 均通过。当前指纹见 local-report.json，原生目标 CI 推送后单独核验。
