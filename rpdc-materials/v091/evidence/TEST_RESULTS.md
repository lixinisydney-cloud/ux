# 本次资料整理的验证结果

产品基线 `6e9cc55b46a4cfa991b69da1df66e0567c55017c`，实际日志 UTC 日期为 2026-11-16。未修改产品、未调用 AI API。

## 新执行的完整回归

| 套件 | 实际测试数 | 结果 | 原始日志 |
| --- | ---: | --- | --- |
| 分类管线 | 24 | 通过 | [test_classifier.log](test_classifier.log) |
| 预分类数据 | 3 | 通过 | [test_precomputed.log](test_precomputed.log) |
| 原 UI 回归 | 10 | 通过 | [test_ui.log](test_ui.log) |
| 合成 API 文件加载（夹具） | 8 | 通过 | [test_ai_ui.log](test_ai_ui.log) |
| 实际预分类联动 | 4 | 通过 | [test_precomputed_ui.log](test_precomputed_ui.log) |
| v0.8 交互回归 | 20 | 通过 | [test_v08.log](test_v08.log) |
| v0.9 原生结构与动效 | 17 | 通过 | [test_v09.log](test_v09.log) |
| v0.9.1 交互减法 | 12 | 通过 | [test_v091.log](test_v091.log) |
| 合计 | 98 | 全部通过（没有跳过） | FRESH_TEST_RUN.json |

27 项管线/数据、71 项浏览器测试；命令、退出码及耗时见 FRESH_TEST_RUN.json。测试服务器使用未修改的仓库 `http://127.0.0.1:4183`。多尺寸与 console/pageerror、图片和溢出断言在对应 UI 测试中执行。合成 API 包络与错误夹具不代表真实模型调用；测试成功不代表语义准确率。

## 线上与最终图片核对

- GitHub main 与本地 HEAD 一致；Pages main 根目录状态 built；最终成功部署 run 43861189551 指向同一提交。详见 GITHUB_BASELINE.json。
- 补拍和录屏实际打开线上 HTTPS，42 个已请求资源（HTML、CSS、JS、数据和图片）逐字节与基线一致，见 LIVE_RESOURCE_PARITY.json。核对的是实际请求的资源，不宣称抓取并比对了站点每一个可能的文件。
- 云 Chromium 缺少代理 CA，使用仅限本站的标准 urllib 上游 TLS 校验转发，页面 URL 不变、响应字节不变；未设置 ignore_https_errors，也未改信任库。该方式验证页面内容与交互，但不等于消除了设备浏览器自身的 CA 差异。
- 优先复用 9 张 v091 已跟踪 PNG；另补拍关键状态和全部手机 DPR2 版本。主目录 17 张（14 项 + 3 补充），高分辨率目录另 17 张，共 34 个 PNG。SCREENSHOT_FILES.json 记录实际尺寸与 hash。
- 每个新拍/录屏会话检查当前图片加载、文档横向溢出及 console/pageerror；均通过。捕获过程不预置 localStorage，不注入 UI 或虚构操作结果。

## 视频与真实操作

7 段原生连续录制全部成功。6 段为 390×844 手机触控模拟，新增收藏段为 1440×900 桌面。重新录制时直接使用与视口相同的录制尺寸，最终交付没有灰色留边、没有后期裁切或拉伸。

长按 720ms 真实触发 450ms 排序入口，持续同一触控拖动后顺序保存；批量移出后笔记数量变化且可撤销；笔记返回滚动位置恢复；共享完成直接返回并保存两个虚构好友。复制通过真实浏览器剪贴板读回，解码确认 11 个 ID，并在另一个新上下文打开只读分享页。具体动作时间线见 capture_manifest_recordings.json。

FFprobe 检查 H.264、尺寸、时长和解码帧数，转码前后时长一致；MP4 没有音轨、字幕或配音。VIDEO_FILES.json 保存源 WebM 与 MP4 hash 及转码命令。保留原始操作，未用截图拼视频。抽样帧仅用于内部检查，未当成截图交付。

## 未验证或无法展示

- 实体手机、iOS Safari、真实 WebView 未运行；不能把 Chromium CDP 当成 iPhone 认证。
- 第三方 App 或真实好友的消息投递没有测试，没有发送任何真实消息；本轮实测复制/打开链接。系统分享 API 的历史单元/浏览器验证含测试替身。
- 当前全部生产笔记只有一张图，未为了录像添加第二张；多图能力仅通过明确夹具验证。
- Windows 脚本提供可运行步骤，但没有在实际 Windows 机器执行。
- 设计者另一 ChatGPT 聊天、用户访谈、早期独立整理页与量化语义准确率不在可核实证据中，需设计者补充。

## 发布边界

资料使用独立 rpdc-materials-v091 分支，不更新产品 main，不触发 main 的 Pages 重部署。发布后的 main/Pages 复核见独立资料分支同目录的 DELIVERY_VERIFICATION.json；该记录发生在 ZIP 封存之后，因此不嵌入 ZIP 以避免循环修改校验值。
