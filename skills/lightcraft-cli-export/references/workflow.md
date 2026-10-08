# 导出流程

输入：照片 ID、当前设置、目标根、格式/尺寸/位深/色彩、元数据/定位移除/水印与命名策略；前置：当前实际目录支持参数组合。不要接受原生静默降级：例如 JPEG 16-bit 应在执行前拒绝。命名冲突默认选新目录/文件；不覆盖原片、硬链接或既有导出。

先保留 app.export 原生返回文件列表，再对每个真实文件调用 artifacts.py。expected JSON 的 format/width/height/bitDepth/colorSpace/iccSha256 按任务要求填写；未指定项只记录事实。色彩没有证据时不宣称一致，水印/肤色/噪点/构图交给目标绑定的视觉审阅。

```bash
python3 -I -B "$SKILL_DIR/scripts/artifacts.py" "/absolute/exports/photo.png" --output-root "/absolute/exports" --expected "/absolute/expected.json"
```

文件存在、哈希一致、零退出分别不是可解码或视觉符合。可继续编辑交付还需要独立库重开回执；保留库、设置、原片及导出，不只交一张预览。
