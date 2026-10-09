## 1. 独立扩展验收（OPEN）

- [x] 1.1 为每个平台真实固定制品、签名/依赖与目标运行建立失败回归，完成适配及实际验证；记录当前身份、结果和不支持范围。（SEXT3-1）
- [x] 1.2 为ArtCraft 的三领域协议、依赖版本及变更失效规则建立失败回归，完成适配及实际验证；记录当前身份、结果和不支持范围。（SEXT3-2）
- [ ] 1.3 为选择性重建和移动交付的输入/产物及设备验收建立失败回归，完成适配及实际验证；记录当前身份、结果和不支持范围。（SEXT3-3）

- [ ] 1.4 核对技能源与插件配套证据，完成规格同步后再归档；不得借范围迁移关闭尚未执行的门禁。

## 2026-10-08 三领域协议验收

1.2 完成：固定 schema/版本、可信兼容表、craft-task 与 craft-artifact 消费和变更失效回归通过；实际 LightCraft→DesignCraft→PrintCraft 产物、ArtCraft 公共校验与 planned 账本及依赖图对照通过。证据：`docs/verification/exchange-20261008/README.md`。不声明 ArtCraft 宿主自动调度或选择性原生重建；其他任务保持 OPEN。

## 2026-10-08 选择性重建增量（1.3 保持 OPEN）

明确曝光 1→2 后，失效选择与实际原生执行均为 photo/layout/pdf；photo-import 复用、基线摘要保持不变。真实三领域产物及独立重开、公共协议复核、篡改/无变化/库占用拒绝回归通过。证据：`docs/verification/rebuild-20261008/README.md`。本轮是显式验收驱动，非 ArtCraft 宿主调度；手机/平板设备与完整移动交付门禁尚未验收，因此不关闭 1.3，不同步或归档整个变更。

## 2026-10-08 平台增量（1.1 保持 OPEN）

技能源已新增 Linux aarch64/x86_64 官方制品锁与安全 tar 安装适配，并增加原生目标 CI；已完成 Linux arm64 容器的两图导入/显影/六产物解码及第二会话重开。macOS Developer ID 签名本机校验通过；本机 Intel 执行因缺少 Rosetta 未通过。其他目标 CI 结果和 Windows、插件受管来源配套仍独立核验，不能用来源候选的平台结果关闭插件或全平台任务。证据：`docs/verification/platform-20261008/README.md`。

四目标原生 CI 与下载产物复核通过：Linux aarch64/x86_64、macOS arm64/x86_64，代码身份 `44503e2`，见 `docs/verification/platform-20261008/ci-artifact-verification.json`。Windows 及插件受管来源配套仍缺失，1.1 继续 OPEN。

## 2026-10-08 六目标平台验收完成

1.1 完成：六个固定官方 CLI 目标真实执行、签名/依赖、精确检出与运行资源、30 会话日志及 36 产物归档复核通过，见 `docs/verification/windows-20261008/README.md`。Windows x86 为 AMD64 主机 32 位进程；Windows ARM64 无固定资产，未声明支持。技能源与插件配套核对属于 1.4，仍 OPEN；插件平台任务不由本轮来源证据关闭。1.3 移动设备仍 OPEN，整个变更不归档。

## 2026-10-09 Android 手机文件交付增量（父任务 1.3 保持 OPEN）

- [x] Android 子验收：两套三领域交付包、原图及工程引用字节保留，14 个设备接收文件摘要一致；两套 PNG/PDF 实际查看通过，打包与篡改/路径/链接/特殊文件失败回归通过。

证据：`docs/verification/mobile-20261009/README.md`。该子项不是新增独立顶层任务，不改变现有父任务统计。平板、iOS 与原生工程设备端编辑未验收；不将本次手机文件显示替代完整移动门禁、RAW 色彩质量或配套来源同步。1.3/1.4 继续 OPEN，变更未归档。
