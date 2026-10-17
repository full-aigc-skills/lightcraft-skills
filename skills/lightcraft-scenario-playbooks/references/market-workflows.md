# 从技能商店适配的场景方法

以下内容是基于已阅读技能的原创 Craft 指导。沿用现有配方的实际命令；这里补充任务判断和结果检查，不将同一配方再计为新增场景。商店提供发现入口，原技能使用的软件、服务和依赖不会随本插件安装。

示例步骤是参数模板，不能直接作为通用执行脚本。先取当前会话的文档、图层、片段或故事ID，解析所有引用，再按实际工具schema执行；尺寸、坐标、路径和文本按本次任务调整。已打开编辑器时使用同一个MCP会话；独立CLI文件编辑不能证明界面同步。

## 按照明分组的白平衡校正

参考：[automaat/lightroom-mcp/raw-photo-lightroom-preset](https://github.com/automaat/lightroom-mcp/blob/35da91d614cccdeead1788148492c4e14aa186c7/skills/raw-photo-lightroom-preset/SKILL.md)；[skillhub:photo-grader](https://api.skillhub.cn/api/v1/download?slug=photo-grader)。

先确认输入是RAW还是已渲染照片，再用本引擎实际渲染选代表图。灰卡有效时取中性参考；同光照照片可参考同一起点，混合光和人脸仍逐张复查。

原配方：`neutral-reference-balance`。输入与边界：方向校正后的完整源图中有已确认中性灰/白参考点；在裁切之前取样。坐标不是当前裁切预览坐标。

| 顺序 | Craft 实际方法 | 参数模板 |
| --- | --- | --- |
| 1 | `develop.controls` | `{}` |
| 2 | `develop.get` | `{}` |
| 3 | `develop.wbPick` | `{"x":0.25,"y":0.5}` |
| 4 | `develop.get` | `{}` |
| 5 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：灰卡中性、肤色正常且各张没有新的高光截断。

能力边界：不把Lightroom XMP、RawTherapee PP3或另一引擎参数直接写进Craft。

原配方结果检查：["参考点的RGB差距减小或原已中性", "肤色没有异常偏绿/洋红", "白平衡设置保存于照片库"]

原配方限制：JPEG参考白平衡与RAW相机色温模型不同；没有中性参考不能任意取背景当灰卡。 若从无旋转裁切预览定位，应先按crop框映射回完整源图；有旋转/拉直时使用真实几何映射，不直接套线性例子。

## 技术纠正先于风格

参考：[calesthio/generative-media-skills/color-grading-finishing](https://github.com/calesthio/generative-media-skills/blob/8c85352d5d75d4dcbe58480bd138e37b9742bab1/skills/production/post-production/color-grading-finishing/SKILL.md)。

先核实输入与目标输出的色彩路径，保护有纹理的亮部，再决定风格对比。每次只调少数相关控制，并与相同渲染条件的前一版比较。

原配方：`highlight-tone-proof`。输入与边界：亮部仍有纹理，已确认RAW或渲染图颜色正常。

| 顺序 | Craft 实际方法 | 参数模板 |
| --- | --- | --- |
| 1 | `develop.controls` | `{}` |
| 2 | `develop.get` | `{}` |
| 3 | `develop.set` | `{"values":{"light.exposure":-0.2,"light.highlights":-25,"light.shadows":10}}` |
| 4 | `develop.get` | `{}` |
| 5 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：亮部纹理仍存在；比较中使用同一输出设置。

能力边界：曲线风格不能代替输入转换；本流程不认证ACES、HDR或相机色彩准确性。

原配方结果检查：["高光层次可见且暗部未糊成灰", "曝光-0.2与高光-25重新打开后仍存在", "原片文件不变"]

原配方限制：纯白剪切不可恢复；相机RAW解码或色彩异常必须先处理，不能靠滑块掩盖。

## 以联系表筛出批量例外

参考：[skillhub:photo-grader](https://api.skillhub.cn/api/v1/download?slug=photo-grader)；[automaat/lightroom-mcp/raw-photo-lightroom-preset](https://github.com/automaat/lightroom-mcp/blob/35da91d614cccdeead1788148492c4e14aa186c7/skills/raw-photo-lightroom-preset/SKILL.md)。

先渲染代表照片并按光照分组，再做联系表，标出过曝、偏色和需局部修的例外。共用风格只是起点，例外照片单独调整后再导出。

原配方：`review-contact-sheet`。输入与边界：已导入同一任务的两张照片；任务允许生成缩略图联系表。

| 顺序 | Craft 实际方法 | 参数模板 |
| --- | --- | --- |
| 1 | `library.selectAll` | `{}` |
| 2 | `export.contactSheet` | `{"path":"contact.pdf","paper":"a4","columns":2,"rows":2,"captions":true}` |

检查：联系表编号对应源文件；抽查原尺寸而不是只看缩略图。

能力边界：不承诺一套参数让全部RAW自动达到成片质量。

原配方结果检查：["联系表含2张照片且1页", "文件不替换原片", "缩略图与文件名对应"]

原配方限制：在共享库不能无条件selectAll；先用catalog.query取得任务照片ID再library.select，避免输出其他照片。

## 版本与执行

执行包装沿用本技能主文件。RAW与已渲染输入分别判断；参数来自LightCraft当前引擎，不套用XMP、PP3或另一软件的滑杆数值。 保存到未占用路径并重开，按实际产物检查；本轮文档适配未新增宿主或真实媒体验收。

本技能内的[商店来源与参数记录](market-adaptations.json)记录版本、内容哈希和观察方法；没有分发第三方脚本或正文。
