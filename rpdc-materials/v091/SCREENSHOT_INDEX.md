# 最终 v0.9.1 截图索引

基线：`6e9cc55b46a4cfa991b69da1df66e0567c55017c`。产品 main、线上 HTML 与已跟踪截图的版本已核对。本包没有修改页面或用图像合成生成界面。

建议制作 PPT 时优先选 `screenshots/high_resolution_2x/` 内的同名图片：手机逻辑视口均为 **390×844**，deviceScaleFactor=2，实际像素 **780×1688**。桌面为 **1440×900、DPR1**。目录名中的 2x 只适用于手机。

`screenshots/` 主目录优先原样复用仓库 `screenshots/v091/` 的最终 PNG（390×844、DPR1），缺失状态则补拍为 DPR2；表中明确区分。复用文件未放大、裁切或重绘。新拍文件全部来自当前运行的真实 DOM。复用来源与 SHA-256、新拍操作和页面状态见 `evidence/capture_manifest_screenshots.json`。两个分辨率目录可能是独立新浏览器会话，勾选的具体笔记或好友等局部状态可能不同，以各图实际显示为准。

所有作者、收藏、朋友和专辑均为原创模拟数据。下表的“模拟”不是指图片是合成界面，而是指原型不连接真实账号或社交服务。

| 文件（主目录） | 展示页面 / 操作状态 | 来源与模拟边界 |
| --- | --- | --- |
| [01_home.png](screenshots/01_home.png) | 完整个人主页、收藏导航、为你整理、原有专辑开头；默认顺序前三张完整、第四张约 20px 提示 | 原样复用 `home_top_390.png`；高分辨率版为新拍。账号/统计是模拟数据 |
| [02_horizontal_scroll.png](screenshots/02_horizontal_scroll.png) | 用真实触控横滑后停留的合集栏；可见后续合集与边缘提示 | 新拍。静态图只记录滑动后的瞬间，实际运动见 Clip 01；三张完整与第四张 20px 的默认比例同时见 01 |
| [03_ai_collection.png](screenshots/03_ai_collection.png) | 设计与创作；标题、管理胶囊、邀请好友、初始 11 篇和双列流 | 原样复用 `collection_390.png`；虚拟主题关联不改变原专辑 |
| [04_note_detail.png](screenshots/04_note_detail.png) | 原生阅读顶部；作者、静态关注/分享、大图、页码、标题/正文开头与固定互动栏 | 原样复用 `note_detail_390.png`；作者/互动数字为模拟，静态按钮未实现社交功能。完整正文/标签见补充图 |
| [05_home_menu.png](screenshots/05_home_menu.png) | 首页三个点菜单，仅调整顺序、管理显示、关闭/开启和取消 | 原样复用 `home_menu_390.png`；无标题、无把手的独立 Action Sheet |
| [06_reorder_mode.png](screenshots/06_reorder_mode.png) | 真实触控按住求职合集 720ms，触发原有 450ms 长按逻辑；排序栏和抬起的卡片可见 | 新拍；持续按住时截图，无菜单注入、无显示移动箭头 |
| [07_reorder_result.png](screenshots/07_reorder_result.png) | 同一手势把求职准备拖到设计前，点击完成；显示顺序已保存 | 新拍；真实修改独立浏览器的本地自定义顺序，不影响真实用户状态 |
| [08_batch_manage.png](screenshots/08_batch_manage.png) | 批量管理并勾选笔记；圆圈状态与底部操作栏 | 原样复用 `manage_390.png`；高分辨率版明确选择 d1，整卡无红色描边 |
| [09_correction_result.png](screenshots/09_correction_result.png) | 把 d1“实验字体与海报排版”移出设计与创作；11→10，反馈“原收藏保留”和撤销 | 新拍；只改变虚拟关联。配合下一张补充图核实原专辑仍在 |
| [10_share_sheet.png](screenshots/10_share_sheet.png) | 原生“分享至”；虚构好友、SVG 渠道、复制链接和静态快照提示 | 原样复用 `share_390.png`；好友明确本地模拟；渠道使用系统分享或复制链接，不代表已投递 |
| [11_invite_friends.png](screenshots/11_invite_friends.png) | 共享专辑设置，开启开关并选择虚构好友 | 原样复用 `friends_390.png`；高分辨率版选择林间同学和乔乔在路上；只生成静态副本 |
| [12_shared_state.png](screenshots/12_shared_state.png) | 完成设置直接返回合集，成员头像更新，显示本地模拟反馈 | 原样复用 `shared_state_390.png`；未发真实消息，后续新增不自动共享 |
| [13_new_save_update.png](screenshots/13_new_save_update.png) | 通过桌面 Demo 收藏 new1 后返回手机视口查看家居灵感；5→6，新笔记置前 | 新拍；预设备选笔记+预计算分类，无实时模型调用。前态见补充图，实际桌面入口见 Clip 05 |
| [14_desktop_demo.png](screenshots/14_desktop_demo.png) | 1440×900 桌面完整双栏；作品说明与手机原型 | 原样复用 `desktop_1440.png`；高分辨率目录另有同尺寸新拍版 |

## 补充截图（独立 DOM 截图，没有拼接）

- [04_note_body_and_tags.png](screenshots/04_note_body_and_tags.png)：同一 d1 笔记向上滑动后的正文、标签、发布时间和固定互动栏。390×844 不能同时容纳整张长图与全部正文，因此提供第二个真实滚动位置。
- [09_original_album_retained.png](screenshots/09_original_album_retained.png)：09 操作之后进入原“视觉设计灵感”专辑，仍显示 d1，原专辑 3 篇不变；该文件与 09 为同一浏览器会话的连续操作。
- [13_before_new_save.png](screenshots/13_before_new_save.png)：13 同一会话新增之前的家居灵感，共 5 篇；未收藏 new1。材料不把前后两图拼成一张伪页面。

手机补充图同样提供 780×1688 版本。分享与共享在此包中均演示当前合集全范围静态快照，不存在旧版“选择分享笔记”流程。

## 无法从当前生产数据展示的状态

当前 38 篇生产笔记每篇仅一张图，页码真实显示 1/1；不能补出一张不存在的第二张图来录制轮播。轮播能力的双图夹具测试见最终报告与新测试日志，但本包截图和视频不注入该夹具。

录屏为 Chromium 手机视口真实操作；并非实体手机录屏。实体 iOS Safari/WebView 尚未验证。截图不包含浏览器地址栏或硬件状态栏。
