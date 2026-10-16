# lightcraft 场景步骤

按当前输入先测量声道、时长或完整源图坐标。每条为独立任务；不要对已有工程无条件初始化或导入示例。

## highlight-tone-proof：有纹理亮部的影调整理

输入：亮部仍有纹理，已确认RAW或渲染图颜色正常。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 仅小幅压曝光与高光，保留暗部细节 | `develop.set` | `{"values":{"light.exposure":-0.2,"light.highlights":-25,"light.shadows":10}}` |
| 4. 读取实际保存的调整设置 | `develop.get` | `{}` |
| 5. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：高光层次可见且暗部未糊成灰；曝光-0.2与高光-25重新打开后仍存在；原片文件不变。

边界：纯白剪切不可恢复；相机RAW解码或色彩异常必须先处理，不能靠滑块掩盖。

## monochrome-editable-proof：可继续调整的黑白照片版本

输入：用户要求黑白版本；彩色原片应保留。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 显式切换黑白处理而非不确定地toggle | `develop.treatment` | `{"bw":true}` |
| 4. 根据图像颜色建立初始黑白混合 | `develop.autoBwMix` | `{}` |
| 5. 核对处理模式与当前参数 | `develop.get` | `{}` |
| 6. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：导出RGB三个通道相等或近似；彩色原片仍保留；肤色与背景仍有灰阶区分。

边界：自动黑白混合只是起点，不等于特定胶片模拟；主体层次需实际审阅。

## square-product-crop：商品正方形构图交付

输入：商品位于画面中心，确认四边可裁；示例原图4:3。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 以归一化坐标裁去左右边缘，示例64×48变48×48 | `crop.set` | `{"rect":[0.125,0,0.875,1],"angle":0}` |
| 4. 锁定当前裁切比例，便于后续拖动 | `crop.aspect` | `{"aspect":"1x1"}` |
| 5. 核对裁切设置 | `develop.get` | `{}` |
| 6. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：示例输出48×48；主体没有被裁断；库中保留可重置裁切的原片。

边界：真实图片先重算裁切框；1x1约束不是自动主体识别。

## neutral-reference-balance：灰卡参考白平衡校正

输入：方向校正后的完整源图中有已确认中性灰/白参考点；在裁切之前取样。坐标不是当前裁切预览坐标。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 在方向校正后的完整源图取中性点，归一化坐标不套当前crop | `develop.wbPick` | `{"x":0.25,"y":0.5}` |
| 4. 记录实际色温色调与模式 | `develop.get` | `{}` |
| 5. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：参考点的RGB差距减小或原已中性；肤色没有异常偏绿/洋红；白平衡设置保存于照片库。

边界：JPEG参考白平衡与RAW相机色温模型不同；没有中性参考不能任意取背景当灰卡。 若从无旋转裁切预览定位，应先按crop框映射回完整源图；有旋转/拉直时使用真实几何映射，不直接套线性例子。

## watermarked-review：带署名的照片审稿版

输入：文字署名和图片使用权来自任务输入；保留无水印母版。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","watermark":{"text":"REVIEW","size":0.12,"opacity":0.7,"anchor":"bottomRight","color":[1,1,1],"shadow":true},"bitDepth":8}` |

检查：署名可读且不遮挡主体；审稿版与母版分开命名；成片像素存在实际水印变化。

边界：水印仅用于署名或审稿标记，不能代替权限控制；实际字号按成片尺寸复核。

## screen-print-dual-export：同一编辑的屏幕版与印刷中间稿

输入：已确认输出用途、目标色彩空间与像素要求，打印方接受TIFF。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 输出屏幕sRGB PNG，不放大原图 | `app.export` | `{"path":"screen.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","sharpen":"screen","sharpenAmount":"low","bitDepth":8}` |
| 4. 另存16位TIFF供后续印前流程 | `app.export` | `{"path":"print.tif","format":"tiff","longEdge":0,"dontEnlarge":true,"colorSpace":"adobeRgb","bitDepth":16,"ppi":300,"tiffCompression":"zip","metadata":"copyright"}` |

检查：PNG与16位TIFF都可解码；两者基于同一组编辑设置；TIFF保留色彩配置且未把ppi当像素放大。

边界：这是中间稿交付，不是印厂软打样或CMYK转换；ICC与纸张流程须按实际要求确认。

## review-contact-sheet：多照片联系表供选片

输入：已导入同一任务的两张照片；任务允许生成缩略图联系表。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 选择该专用库的全部照片，真实库应改用明确ID集合 | `library.selectAll` | `{}` |
| 2. 导出带说明的A4联系表 | `export.contactSheet` | `{"path":"contact.pdf","paper":"a4","columns":2,"rows":2,"captions":true}` |

检查：联系表含2张照片且1页；文件不替换原片；缩略图与文件名对应。

边界：在共享库不能无条件selectAll；先用catalog.query取得任务照片ID再library.select，避免输出其他照片。

## reset-light-preserve-color：仅回退曝光区并保留色彩编辑

输入：在当前照片副本中需要回退光照区，保留已确认的色彩设置。

| 顺序与目的 | 命令 | 参数 |
| --- | --- | --- |
| 1. 读取当前滑块与取值范围，不凭UI标签猜controlId | `develop.controls` | `{}` |
| 2. 记录当前照片设置与处理版本 | `develop.get` | `{}` |
| 3. 示例建立可区分的曝光与饱和度设置 | `develop.set` | `{"values":{"light.exposure":0.8,"color.saturation":-20}}` |
| 4. 仅重置Light区，不执行全局reset | `develop.resetSection` | `{"section":"light"}` |
| 5. 核对曝光归零且色彩设置仍在 | `develop.get` | `{}` |
| 6. 导出新成片文件，与原片路径分开 | `app.export` | `{"path":"result.png","format":"png","longEdge":0,"dontEnlarge":true,"colorSpace":"srgb","metadata":"none","bitDepth":8}` |

检查：light.exposure=0；color.saturation=-20仍保留；其他已确认编辑没有被全局清空。

边界：示例set用于新建演示；真实回退任务先读取现有设置并跳过该示例set，不覆盖用户已有色彩值。

