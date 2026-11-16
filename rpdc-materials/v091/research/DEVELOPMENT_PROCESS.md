# RE:FOLD v0.9.1：可核实的设计开发过程

资料基线：公开仓库 [lixinisydney-cloud/ux](https://github.com/lixinisydney-cloud/ux)，最终产品提交 [`6e9cc55b46a4cfa991b69da1df66e0567c55017c`](https://github.com/lixinisydney-cloud/ux/commit/6e9cc55b46a4cfa991b69da1df66e0567c55017c)。在线 Demo：https://lixinisydney-cloud.github.io/ux/ 。本次仅整理资料、补拍和录制，未修改产品代码、分类答案或部署 UI。

## 可以直接用于 PPT 的工具与过程表述

“我使用 Codex 辅助开发一个 HTML、CSS、原生 JavaScript 静态高保真原型。Codex 在现有项目中完成交互状态、数据联动、兼容迁移、素材记录和浏览器自动化测试，并使用 Git 提交、GitHub Pages 发布。智能分类由 Codex 对原创模拟笔记的文本进行一次语义预分类，保存为经过校验的 JSON；浏览器展示结果并优先应用用户纠错，不实时请求模型。Playwright 用于回归测试、实际 DOM 截图和真实浏览器操作录屏。”

以上描述有仓库及当前会话支持。设计方向、痛点分析、体验策略和提示词推敲发生在设计者的另一个 ChatGPT 聊天中，本材料无法独立核实；相关过程须由设计者补充，不能把代码提交替代为用户研究证据。

## 技术栈与具体用途

| 工具 / 文件 | 真实用途 | 边界 |
| --- | --- | --- |
| HTML：`index.html` | 主页、合集、管理、阅读、共享页面；包含原生 JavaScript 渲染及事件逻辑 | 静态原型，无登录或服务端 |
| CSS：`styles.css` | 桌面双栏、手机容器、瀑布流、Action Sheet、选择状态和 Motion System | 没有切换 React/Vue 等框架 |
| JavaScript：`classification-store.js` | 数据/分类结果结构和 hash 校验、来源选择与加载 | 只读取静态数据；不向 AI 服务发送内容 |
| JavaScript：`index.html` 内联脚本 | 触控/鼠标手势、长按排序、手动加入/排除、撤销、localStorage、共享快照和链接 | 好友、收藏、作者均为模拟数据 |
| JSON：`data/` | 38 篇笔记、6 个预设主题、预生成关系和结果元数据 | 不是真实用户账号导出 |
| Python：`scripts/classify_notes.py` | 请求字段白名单、可选 API 流程、结构校验、语义数据 hash | 默认在线 Demo 未运行独立 API 分类；当前数据是 Codex 预生成 |
| Python：`scripts/restore_precomputed.py`、`build_data_bundle.py` | 恢复/校验已有分类，构建前端嵌入数据包 | 恢复脚本不调用模型；本次资料整理未重建或覆盖结果 |
| Python：`tests/export_standalone.py` | 生成含图片/数据的单文件离线 HTML | 历史文件名 `RE_FOLD_v06_Demo.html` 不代表其内容停留在 v0.6 |
| Playwright + Chromium | 自动化回归、375/390/430 与桌面布局验证、真实输入与 DOM 截图 | Chromium 手机模拟不等于实体 iOS 测试 |
| SVG / WebP | 原创设计封面、统一图标、授权照片本地存储 | 图片是展示素材，未进行多模态分类 |
| Git / GitHub / Pages | 版本差异、公开源码、main 根目录的静态部署 | 当前 Pages 无付费后端、模型服务或运行时 API Key |
| FFmpeg（本次材料整理） | 将 Playwright 原生 WebM 录屏整段转码为 MP4 | 无截图拼接、无重构动画、无字幕/配乐/配音 |

具体许可见材料包 `evidence/source_files/docs/ASSET_SOURCES_V08.md`、逐文件 JSON 与其 `licenses/`。照片实际来自 Flutter Gallery Assets、Google Material Design Lite 官方示例及 scikit-image；不能写成已使用 Pexels。v0.8 报告记录图库访问限制。虚构作者不是照片摄影者。

## 仓库建立、提交与部署

GitHub 公共 API 显示仓库创建于 `2026-11-15T14:08:49Z`，默认分支为 `main`。最早提交仅含 `.gitattributes`；仓库究竟由网页、CLI 还是其他工具创建，现有证据不足，需设计者补充。

当前可核实的发布路径：增量修改静态文件 → 本地服务器运行 → Python/Playwright 检查 → Git 提交并推送 main → GitHub Pages 从 main 的 `/` 部署 → 检查部署记录、线上资源与交互。`.nojekyll` 保持静态文件直接服务。Pages API 返回 `build_type=legacy`、`source.branch=main`、`source.path=/`；不需要 npm 构建或应用服务器。

本次资料交付放在独立资料分支，产品 main 仍以 `6e9cc55` 为基线。发布材料与重新部署产品是两件不同的事。

## 可追溯版本变化

以下是 Git 元数据中的作者时间（UTC），不是工时或经过独立验证的设计日程。提交证明代码变化，不证明设计讨论次数、模型调用次数或用户测试人数。

| 提交 / 作者时间 | 版本与具有产品意义的变化 | 证据 |
| --- | --- | --- |
| [`74ca8f8`](https://github.com/lixinisydney-cloud/ux/commit/74ca8f803f9dda0068e9a531aa8710f2d63b64b1) / 2026-11-15 14:08:30Z | 初始提交，仅 `.gitattributes` | Git 提交树 |
| [`6b08c5b`](https://github.com/lixinisydney-cloud/ux/commit/6b08c5b2e8821214f0092c88659083ccb4e894de) / 2026-11-15 15:30:34Z | v0.6 首次入库的静态 Demo；个人收藏页内嵌横滑“为你整理”，保留原有专辑，桌面双栏与单文件导出 | 该提交的 `index.html`、`styles.css`、`README.md`、`tests/` |
| [`90e61e1`](https://github.com/lixinisydney-cloud/ux/commit/90e61e118c4f6640ac365d17e973b33051c18c48) / 2026-11-15 16:14:52Z | v0.7 数据拆分、文本分类管线、结果校验及 Windows 指南；区分 API 未运行与离线数据 | `data/`、`classification-store.js`、`scripts/`、`docs/AI_CLASSIFICATION.md`、`reports/v07-validation.md` |
| [`d7c602a`](https://github.com/lixinisydney-cloud/ux/commit/d7c602a4b98825c9a974b0e7b68e72c674a02988) / 2026-11-16 05:22:32Z | v0.7 Codex 语义预分类落盘；旧环境文件未恢复，按文本重新生成并如实记录；联动纠错与新增演示 | `data/classifications.precomputed.json`、`scripts/restore_precomputed.py`、`reports/v07-precomputed-validation.md` |
| [`45a0c06`](https://github.com/lixinisydney-cloud/ux/commit/45a0c06cb93e68dabf96f5936af8941fbff5f0f0) / 2026-11-16 07:54:27Z | v0.8：手势冲突处理、排序与状态迁移、批量管理、三列添加、完整虚构笔记、本地授权素材、静态共享副本 | `reports/v08-validation.md`、`tests/test_v08.py`、`docs/ASSET_SOURCES_V08.md`、`index.html` |
| [`eedcc6e`](https://github.com/lixinisydney-cloud/ux/commit/eedcc6e34ebf40dddbc7bc44404dcd03087fb1b1) / 2026-11-16 10:24:04Z | v0.9：原生“分享至”、共享设置、合集层级、精简管理菜单、圆圈多选、拖动与弹层/页面动效 | `reports/v09-validation.md`、`tests/test_v09.py`、`screenshots/v09/` |
| [`6e9cc55`](https://github.com/lixinisydney-cloud/ux/commit/6e9cc55b46a4cfa991b69da1df66e0567c55017c) / 2026-11-16 11:49:56Z | v0.9.1 最终减法：分享与邀请直接生成当前完整静态快照；首页四行设置；恢复默认移入排序；模拟新增移到桌面；原生阅读与一次薄荷绿概念标识 | `reports/v091-validation.md`、`tests/test_v091.py`、`screenshots/v091/`、最终 README |

关于“从独立整理页面改为收藏页内嵌”：最早入库的 v0.6 已经是内嵌结构；仓库不能证明独立整理页阶段的界面和转折过程。该设计决策及早期草稿需设计者补充，不能伪造一张早期截图或虚构提交。

## Codex 工作范围与设计者的工作

当前会话中的需求与提交、报告共同支持：Codex 负责增量代码实现、数据与分类 JSON 整理、校验脚本、授权素材来源记录、测试脚本、截图、离线导出、Git 提交和 Pages 发布验证。本次 Codex 负责证据核对、补拍 DOM、录制真实浏览器交互、文档和资料包，不再次设计产品。

设计者提出了功能边界、原生交互参考、分阶段验收及最终减法要求。ChatGPT 在另一聊天中如何帮助分析用户痛点、组织概念、选择设计策略、撰写给 Codex 的提示词，以及设计者做过哪些取舍或用户访谈，均需设计者自行补充。本仓库没有可验证的用户访谈记录、A/B 实验、业务转化数据、准确率评估或模型调用次数；不据此编造结论。

## 测试事实与可复查文件

最终仓库报告记录 98 项本地自动化测试：分类管线 24、预分类数据 3、UI 回归 10、合成 API 结果加载 8、实际预分类联动 4、v0.8 回归 20、v0.9 原生结构/动效 17、v0.9.1 专项 12，合计 27 项管线/数据与 71 项浏览器检查。材料整理时再次运行同一组套件，实际新日志和各套件退出状态保存在 `evidence/test_*.log` 与 `FRESH_TEST_RUN.json`；以这些新日志为本次结果依据。

覆盖内容包括：输入白名单和无效结果拒绝、真实预生成结果联动、手势冲突、排序/隐藏迁移与持久化、手动加入/移出优先级、原专辑保护、取消收藏二次确认/撤销、直接分享快照、历史链接兼容、好友本地设置、返回滚动位置、图片加载、控制台及布局。375/390/430px 与 1440×900 在相关套件中检查。涉及错误/缓存/API 包络/多图的部分测试使用明确标记的夹具，不等于生产数据有多图或运行过真实 API。

本次补拍和 7 段录屏的逐步操作/断言在 `capture_manifest_*.json`；截图为实际 DOM，视频为 Playwright 原生连续录屏。线上 HTTPS 因云环境 Chromium 代理 CA 缺失，使用仅限本站的标准 urllib 上游 TLS 校验响应转发，原始字节与本地基线比对；没有关闭 TLS 验证或修改产品。该转发属于测试环境适配，不是产品功能。

未验证：实体 iPhone、iOS Safari、真实 WebView、真实好友/第三方消息投递、模型线上调用质量、用户任务成功率或商业效果。系统分享 API 的路径在历史测试中用测试替身验证；本次录屏实测的是剪贴板和可打开链接，不能写成已经分享到微信。

## 设计者仍需补充

- 问题来源与真实用户研究（如有）：参与者、方法、原始材料及结论。
- 另一个 ChatGPT 聊天中的真实提示词、关键回答、设计者的判断与取舍。
- 早于 v0.6 的流程草图、独立整理页方案及改为内嵌的设计依据。
- 真实手机的操作录屏与 iOS 验证；本包提供的是 Chromium 手机视口素材。
- 个人负责范围、最终 PPT 叙事和对原型局限的反思。

建议 PPT 将“工程验证”“语义分类示例”“用户体验研究”分别表述。98 项工程检查不代表 98 名用户，也不代表分类准确率 98%。
