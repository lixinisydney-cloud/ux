# RE:FOLD v0.9.1 · RPDC 体验设计材料包

最终产品：[在线 Demo](https://lixinisydney-cloud.github.io/ux/)；[源码基线 6e9cc55](https://github.com/lixinisydney-cloud/ux/tree/6e9cc55b46a4cfa991b69da1df66e0567c55017c)。本次整理不修改 UI、交互、分类答案或产品部署，不制作 PPT。

## 下载与使用

[直接下载 REFOLD_RPDC_FINAL_ASSETS.zip](https://raw.githubusercontent.com/lixinisydney-cloud/ux/refs/heads/rpdc-materials-v091/rpdc-materials/v091/REFOLD_RPDC_FINAL_ASSETS.zip)

如浏览器未自动下载，右键“链接另存为”；也可打开 [GitHub 资料目录](https://github.com/lixinisydney-cloud/ux/tree/rpdc-materials-v091/rpdc-materials/v091)，在 ZIP 文件页面选择 Download raw file。ZIP 存在独立资料分支，产品 main 不变；GitHub Release 的附件上传域名在本环境受网络策略限制，故采用用户允许的 GitHub 文件下载方式。

解压后建议先把这份 README、截图索引和两份研究文档交给 ChatGPT，再选择 PPT 所需图片。请按事实区分概念设计、工程验证与用户研究，不把本地模拟写成真实线上服务。

## 文件索引

| 路径 | 内容 |
| --- | --- |
| [SCREENSHOT_INDEX.md](SCREENSHOT_INDEX.md) | 14 项截图、3 张补充图的状态、来源和模拟边界 |
| `screenshots/` | 14 个要求的文件名 + 正文/标签、原专辑保留、新收藏前态 3 张补充图 |
| `screenshots/high_resolution_2x/` | 同样 17 张的 PPT 清晰版本；手机 390×844 逻辑视口 / 780×1688 像素；桌面 1440×900 |
| [recordings/RECORDING_INDEX.md](recordings/RECORDING_INDEX.md) | 7 段真实连续交互 MP4 的时长、操作和可验证范围 |
| `recordings/Clip_*.mp4` | 原生 Playwright WebM 整段转码，未剪辑、未拼接、无字幕/音乐/配音 |
| [DEVELOPMENT_PROCESS.md](research/DEVELOPMENT_PROCESS.md) | 栈、真实 Git 版本过程、Codex 工作范围、测试及设计者待补充部分 |
| [AI_IMPLEMENTATION_EVIDENCE.md](research/AI_IMPLEMENTATION_EVIDENCE.md) | 分类字段、固定主题、数量、优先级、预计算路径、局限 |
| [CLASSIFICATION_CASES.json](research/CLASSIFICATION_CASES.json) | 5 个案例原始分类输入和已保存理由，非准确率基准 |
| [evidence/TEST_RESULTS.md](evidence/TEST_RESULTS.md) | 本次新跑的 98 项测试和证据说明 |
| `evidence/test_*.log`、`FRESH_TEST_RUN.json` | 新执行的原始日志、命令及退出状态 |
| `evidence/GIT_HISTORY.*`、`GITHUB_BASELINE.json` | 完整提交 ID、变更路径、Pages main 配置与成功部署记录 |
| `evidence/capture_manifest_*.json` | 实际截图来源、操作事件、断言、线上资源 SHA-256 与录制信息 |
| `evidence/VIDEO_FILES.json`、`SCREENSHOT_FILES.json` | 尺寸、编码、时长和文件 hash |
| `evidence/source_files/` | 从最终提交原样复制的白名单源码、分类、测试和历史报告；保持原目录层级 |
| [scripts/README.md](scripts/README.md) | Windows 运行步骤、可自动化手势、云环境适配及边界 |
| `scripts/capture_materials.py` | 真实浏览器输入的截图/录屏重现脚本 |
| `FILE_MANIFEST_SHA256.txt` | ZIP 内文件完整性清单（清单本身除外）；ZIP 外另提供整个压缩包 SHA-256 |

`evidence/source_files/` 供核查，不是完整可运行副本；运行原型应使用在线 Demo 或原仓库。没有包含密钥、鉴权文件、私有设计参考图、真实账号数据、API 缓存或旧本地备份包。

## 核心事实与交付边界

- 初始模拟收藏 35 篇：34 篇分类、1 篇未分类、4 篇双主题；另外 3 篇预备新增已提前分类。
- 分类是 Codex 文本语义预生成，不是实时 Agent、官方点点、在线收费 API 或图片识别。
- 分享仅保存点击时的笔记 ID 范围，后续新增不进入旧快照；好友为本地模拟，没有发送消息。静态链接不提供真正私密数据的访问控制。
- 截图均为实际 DOM；优先原样复用最终仓库截图，同时补拍 DPR2 版本。视频均有真实输入和连续运动，不是截图拼接。
- 6 段手机视频为 Chromium **390×844** 视口录制；Clip 05 为 **1440×900 桌面**，因为模拟新收藏仅有桌面演示入口。它们不是实体手机系统录屏。
- 当前生产笔记均为单图（1/1），没有为素材注入不存在的轮播图。多图能力仅在工程夹具中验证。
- 已重新运行最终 98 项自动化测试。实体 iPhone、iOS Safari/WebView、真实第三方投递和用户研究未验证。
- 另一个 ChatGPT 聊天的设计讨论、真实用户痛点研究、早期独立整理页和个人决策过程，标注“需设计者补充”；不编造访谈或准确率。

素材版权与许可保留在 `evidence/source_files/docs/ASSET_SOURCES_V08.md`、`asset-sources-v08.json` 和 `licenses/`。照片是授权配图；虚构作者不是摄影者。
