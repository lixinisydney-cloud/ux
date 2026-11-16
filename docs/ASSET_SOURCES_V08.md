# v0.8 素材来源与许可

完整逐文件记录见 [asset-sources-v08.json](asset-sources-v08.json)，含本地路径、来源、上游署名、许可、照片主题及文件校验值。

## 构成

按当前 38 篇笔记的封面计：

- 25 篇摄影（65.8%）：旅行、食物、生活物件、穿搭、宠物及工作桌面。
- 10 篇原创图文与设计封面（26.3%）：字体、动态视觉研究、品牌应用、网格、作品集等，各自采用不同的色彩与构图。
- 3 篇原创界面/流程示意（7.9%）：网页目录、订单层级、代码与状态流程，均不是真实服务截图。

重复主题的笔记可以复用同一授权照片或原创封面；比例按笔记数计算，不宣称是 38 张不同的照片。全部素材保存在本地 `assets/`，页面不请求图库或随机图片服务。

## 摄影来源

1. **Flutter Gallery Assets 1.0.2**，官方发布页 `https://pub.dev/packages/flutter_gallery_assets`，上游 `https://github.com/flutter/flutter_gallery_assets`。该包将图片和其他资源按 BSD-3-Clause 发布，版权为 The Chromium Authors；单张照片的摄影者在上游未逐一列明，记录中如实保留这一限制，不编造摄影师。分发保留完整 [上游 LICENSE](licenses/flutter_gallery_assets-1.0.2-LICENSE.txt)。下载归档的 SHA-256 为 `f8fecfeebcfbe80a2fabc00c0834046890abe681f59d3e2c5b1028faf887d94b`，使用前已与官方 pub.dev API 的 `archive_sha256` 相符验证。
2. **Google Material Design Lite 官方示例摄影**，上游 `https://github.com/google/material-design-lite`，分支 `mdl-1.x`，按仓库 Apache-2.0 使用。保留 [LICENSE](licenses/material-design-lite-LICENSE.txt)；逐张原始路径列于 JSON。上游未单独注明摄影者，署名记录为 Material Design Lite contributors，不把虚构笔记作者写成摄影师。
3. **scikit-image 样例摄影**：`coffee.png` 摄影师 Rachel Michetti，`chelsea.png` 摄影师 Stefan van der Walt。上游明确标记 CC0，原始图片及 [图片专有说明摘录](licenses/scikit-image-coffee-chelsea-CC0.txt) 均来自 `scikit-image/scikit-image` 的 `v0.25.0`。Coffee 照片原说明亦注明 courtesy of Pikolo Espresso Bar。

摄影仅做本地尺寸优化和 WebP 编码，没有添加水印、重绘人物或伪造照片内容。Pexels 图库域名在本环境不可访问，故使用上述可访问且许可明确的官方素材源；没有通过其他通道绕过被拒绝的图库域名。

## 原创内容与数据边界

原创封面和六个插画头像由 RE:FOLD 原型团队制作，作为 CC0-1.0 资源随原型提供。所有昵称和正文均为本项目原创虚构，不复用真实 REDNOTE 用户的帖子、头像或用户名。

授权照片是虚构笔记的主题/氛围配图，并不证明虚构作者拍摄、到访了对应地点、完成了配方、使用了产品或拥有照片中的房间。地理位置不完全对应的图片在逐文件 `subject` 字段明确记录。照片中的模特不是笔记作者。照片许可和分发记录不代表 Google、Chromium、摄影师或任何服务对本原型背书。

新增的是 `author`、`body`、`images`、`likes`、`ratio` 等展示字段；分类输入 `id/title/description/tags` 保持不变。语义数据 hash 保持 `32ac1b6352714ff4be765cd2e08f47dd1bfc108cb37071f0803508368d011df7`，预分类通过原有结构和版本校验。本轮没有调用多模态模型，不能将图片替换描述成经过 AI 图片分析。
