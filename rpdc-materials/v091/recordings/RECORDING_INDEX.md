# 真实操作录屏索引

来源为未修改的最终 v0.9.1 在线 HTML。Playwright 原生 record_video 连续记录；保留自然停顿和现有网页动效。源 WebM 整段转 H.264 MP4，无剪辑、拼接、配音、字幕、音乐或图片合成。

这是 Linux Chromium 浏览器的手机视口真实交互，不是实体手机系统录屏。6 段手机片为 390×844，Clip 05 如实保留桌面 1440×900 控制区。每段开启新上下文，互不依赖、不影响设计者已保存的用户状态。

| 文件 | 时长 | 画面 | 实际操作与边界 |
| --- | ---: | --- | --- |
| [Clip_01_home_horizontal.mp4](Clip_01_home_horizontal.mp4) | 12.92s | 390×844 | 首页与横滑：真实左滑再右滑，看到后续合集；未进入长按或打开合集。 |
| [Clip_02_collection_note_return.mp4](Clip_02_collection_note_return.mp4) | 16.08s | 390×844 | 合集、阅读和返回：进入设计与创作，竖向浏览，打开实际可见笔记、滑动正文、返回；断言恢复此前合集滚动位置。 |
| [Clip_03_longpress_reorder.mp4](Clip_03_longpress_reorder.mp4) | 18.16s | 390×844 | 长按与拖动排序：按住求职准备 720ms，持续同一触控拖到设计前，点击完成并核对持久化顺序。 |
| [Clip_04_correction_undo.mp4](Clip_04_correction_undo.mp4) | 13.76s | 390×844 | 纠错移出与撤销：管理→批量管理→勾选 d1→移出，数量 11→10、原收藏保留；再真实点击撤销恢复 11。 |
| [Clip_05_new_save_desktop.mp4](Clip_05_new_save_desktop.mp4) | 11.64s | 1440×900 | 桌面模拟新增收藏：通过已有左侧 Demo 控制区收藏 new1，主页家居合集前移；进入家居看到 6 篇及新笔记。不是手机原生入口、不是实时模型调用。 |
| [Clip_06_share_copy_link.mp4](Clip_06_share_copy_link.mp4) | 10.92s | 390×844 | 分享菜单与复制：展示好友和渠道，点击复制；剪贴板真实读回当前 11 篇的公开演示链接，另一个上下文验证能打开。无真实社交消息。 |
| [Clip_07_invite_friends.mp4](Clip_07_invite_friends.mp4) | 12.88s | 390×844 | 邀请好友共享：进入共享设置，开启，选林间同学和乔乔在路上，完成直接返回；显示本地模拟成员和未发消息反馈。 |

操作时间线与断言：`../evidence/capture_manifest_recordings.json`。容器/编码/帧数、源及交付 SHA-256：`../evidence/VIDEO_FILES.json`。画面不是通过 screenshots 目录编码出来的。当前数据全部单图，因此 Clip 02 不假演示多图；阅读返回是真实功能，关注、点赞、评论等未实现元素只作展示。

Clip 06 读回的链接另存 [COPIED_DEMO_LINK.txt](COPIED_DEMO_LINK.txt)。这是公开虚构笔记的静态范围链接，不含 token、真实账号或真实私密数据；不能作为实际权限系统使用。

可在 Windows 重录，脚本及步骤见 `../scripts/README.md`。云录制阶段的 FFmpeg 临时路径和 HTTPS 适配在证据中公开说明，不属于产品更改。实体 iOS、系统原生分享弹窗/第三方 App 消息投递未验证。
