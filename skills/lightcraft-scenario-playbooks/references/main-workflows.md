# LightCraft main参数模板与新流程

固定main `f34c7a8a89e0d1bade0a6889185f40acecc84a9f`，实际原生目录371条，相对稳定版313条新增58个标识、7处契约变化。[完整参数目录](main-command-catalog.json)可在Web没有实时command_list时按需读取；[差异](main-command-delta.json)单独记录新增方法。目录仅证明原生main定义，不保证当前Web前端、GPU或宿主支持全部方法；新增流程尚未业务验收，不计入原8条手册通过数。

当前Web插件通过`command_run {"id":"方法名","params":{参数}}`执行同会话方法。先`editor_status`确认ready，再`inspect`/`library.info`确认库和选择；不要把其他库的照片ID带来。旧版不支持的新命令应返回缺口，不能另起CLI并声称当前画面已同步。

## 联系印样：保存布局模板并输出PDF

用途：给客户选片或内部审片提供统一的缩略图页面。先在当前库选择实际需要交付的照片，确认原片在线、顺序与照片数量；不要默认全库。

1. `print.get {}`读取当前纸张、可打印区域与布局。长度单位为英寸，不能把mm数值直接传入。若改纸张，从返回papers选择当前确有的纸张标识。
2. `print.set {"layout":{"style":"contactSheet","grid":{"columns":3,"rows":3,"spacingX":0.12,"spacingY":0.12,"keepSquare":false}},"image":{"zoomToFill":false,"rotateToFit":true},"job":{"ppi":150}}`，这是审片预览起点，不是印厂标准。
3. 再`print.get {}`检查页数、边距、图像裁切与单元格，过多照片需要多页；不能只看第1页。自定义图片包可用`print.layout.autoLayout {}`重新打包，但此方法会重排现有单元格，不当作纯查询。
4. `print.template.save {"name":"Contact proof 3x3 150ppi"}`，保存前先`print.template.list {}`确认同名项；同名不区分大小写会替换。模板保存布局、图像、page/job设置，不保存照片绑定和guides。
5. 后续选片时`print.template.apply {"name":"Contact proof 3x3 150ppi"}`，重新核对当前照片选择和`print.get`，不能假设模板恢复了上次的照片。
6. `print.exportPdf {"path":"output/contact-proof.pdf"}`，使用全新输出路径；原生接口可能替换已有输出，宿主的工作区/覆盖规则仍优先。检查返回photos/pages、实际PDF页数、所选照片数量、照片顺序和缩略图清晰度，再重开抽查。

此流程目前是固定main方法和参数的适配，尚未执行本流程的PDF交付与真实宿主画面验收。

## 将一次局部修饰做成蒙版效果模板

用途：复用局部提亮/色调设置，同时保留每张照片自己的蒙版位置。先对代表照片的一个蒙版完成试调，查看边缘和修改强度；复制的是效果参数，不是主体识别结果或空间遮罩。

1. `mask.effects {}`读取已有名称、当前效果和工具默认值；确认当前只选择目标蒙版。
2. `mask.saveEffect {"name":"Soft local lift","fields":"changed","amount":false}`保存变化的滑块，不把所有默认值一并覆盖目标。保存同名会替换，用本任务新名字。必要时单独明确brush设置，不顺便改用户画笔。
3. 在另一目标蒙版上调用`mask.applyEffect {"name":"Soft local lift","remember":false}`，仅作用于当前目标；不传all或photos:selected，除非确有批量需求。Amount只在预设携带时改变，应用后检查原有其他滑块和蒙版边界。
4. `mask.exportEffects {"path":"output/soft-local.lceffect","names":["Soft local lift"]}`导出命名效果，检查实际文件及重新导入。这个格式是参数数据，不能当成已修复图片或完整蒙版备份。

蒙版模板流程尚未业务执行；代表样片、原片保护、导出图像和重开是后续验收。

## 幻灯片导出等其余新增能力

`slideshow.templates.list {}`返回真实builtin/user标识，不猜模板名称；选择后再apply。`slideshow.export`可输出PDF/JPEG/AV1视频，默认后台运行：读取返回taskId，再用`slideshow.exportStatus {}`等待完成并检查warnings/skipped/error，或在后端确实支持时明确wait:true。视频无音轨，不能当带音乐成片；格式为mp4/webm容器中的AV1，不等于H.264。文件未完成或照片被跳过时不能宣称全量交付。

`faces.gpu`等命令受运行平台限制；方法出现在原生目录不代表浏览器具备该GPU后端。逐项按当前前端结果判断。
