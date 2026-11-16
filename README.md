# RE｜智能收藏 v0.9.1

现有 HTML / CSS / JavaScript 静态原型，保留桌面双栏和手机展示，无前端框架、无后端、无付费API。

网站：<https://lixinisydney-cloud.github.io/ux/>。

## 这一版的减法

- 分享当前合集：点击好友、渠道或复制链接，直接生成当前全部笔记的静态快照，不再选择笔记或二次确认。后续新收藏不进入旧快照；虚构好友仅本地模拟，系统分享不可用时复制链接。
- 邀请好友：共享专辑设置中开启、选好友、完成，即保存新副本并返回。历史副本和v1链接保留；取消或关闭本地共享不改变个人合集。
- 首页菜单：调整顺序、管理显示、关闭/开启、取消。恢复默认位于排序模式；模拟新收藏和关于说明位于桌面左侧。
- 原生阅读：作者、静态关注、大图/轮播、页码、标题正文、标签时间及固定底部互动展示。没有无意义的互动提示；返回真实可用，分类纠错保留在合集管理。
- 首页“为你整理”只有一个原创薄荷绿AI概念图标，未接入官方点点服务。

保留触控/鼠标横滑、长按拖动排序、自定义/最近收藏排序、隐藏恢复、手动添加、批量移出、全局取消确认/撤销、原专辑保护和localStorage。详情见[本轮验证记录](reports/v091-validation.md)。

## 数据与历史

38篇原创模拟笔记，使用已有Codex语义预分类。不实时调用模型，不分析照片。本轮笔记、图片来源、分类答案、数据hash和预分类机制均未改变。

沿用 `refold-v05-experience-data`，保留旧纠错、隐藏、排序、收藏、专辑与共享副本。新增groupSharing仅保存当前本地共享状态；旧copies与链接不重写。快照冻结笔记ID范围，静态原型不提供真实用户数据的访问控制。

素材均位于本地assets，来源及许可见[记录](docs/ASSET_SOURCES_V08.md)、[逐文件清单](docs/asset-sources-v08.json)和docs/licenses。照片为授权氛围配图，作者和内容均为虚构。

## 开发与验证

仓库根目录启动：

```bash
python3 -m http.server 4173 --bind 127.0.0.1
```

另一个终端执行（需已有Python Playwright与Chromium）：

```bash
python3 -m unittest discover -s tests -p test_classifier.py
python3 -m unittest discover -s tests -p test_precomputed.py
python3 tests/test_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_ai_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_precomputed_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_v08.py --phase all --base-url http://127.0.0.1:4173
python3 tests/test_v09.py --round all --base-url http://127.0.0.1:4173
python3 tests/test_v091.py --base-url http://127.0.0.1:4173
```

98项通过，含71项浏览器检查。布局覆盖375/390/430px与1440×900；实体iOS/Safari未验证。浏览器脚本支持 `--chromium /path/to/chromium`。

截图与离线导出：

```bash
python3 tests/capture_screenshots.py --base-url http://127.0.0.1:4173 --output-dir screenshots/v091
python3 tests/export_standalone.py
```

`screenshots/v091/`含菜单、阅读、分享、共享设置、排序、管理及桌面Demo截图。`RE_FOLD_v06_Demo.html`保留旧下载文件名，内容已同步v0.9.1，内嵌图片、数据和许可。

预分类恢复/校验仍使用原有命令；不生成新分类：

```bash
python3 scripts/restore_precomputed.py
python3 scripts/classify_notes.py --validate-existing data/classifications.precomputed.json
```

修改分类输入文本时才需要更新语义结果、hash及bundle。原可选API脚本的说明保留在docs/AI_CLASSIFICATION.md；本轮没有执行。

## 发布

GitHub Pages使用main分支根目录与.nojekyll。先完成代码、浏览器验证和导出，再推送；发布后核对对应提交、Pages部署及线上交互。
