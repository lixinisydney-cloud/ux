# RE｜智能收藏 v0.8

基于现有 HTML / CSS / JavaScript 的 REDNOTE 收藏交互原型，保持桌面双栏介绍与手机展示，无框架、无构建依赖。站点：<https://lixinisydney-cloud.github.io/ux/>。

## 本轮体验

- 首页保留单条横向合集区域，390px 显示三张完整卡片并露出第四张约20px。触控横滑、鼠标拖动、450ms长按排序与点击互不冲突。
- 首页设置统一管理自定义顺序、最近收藏排序、隐藏/恢复和展示开关；旧版固定状态迁移为自定义顺序，封面不随新增收藏切换。
- 合集支持多选管理：虚拟移出、加入其他合集、二次确认后取消收藏。操作有反馈与撤销，取消收藏同步影响原专辑。
- “添加笔记”打开三列已有收藏选择器，手动关联和移出偏好优先于预生成分类，刷新保留。
- 笔记打开完整虚构社区页面，含作者、图片、原创正文、标签和本地互动；分类调整位于次级菜单，返回恢复滚动位置。
- 分享前明确勾选笔记，生成静态共享副本和可打开链接。后续收藏不自动共享。虚构好友可多选、确认、撤销和查看状态，全部仅本机模拟，不发送消息。
- 移动端隐藏模拟系统状态栏；桌面保留手机框与9:41。技术边界集中于桌面介绍和“关于原型”。

## 数据与素材

38篇原创模拟笔记：35篇已有、3篇模拟新增。已有笔记34篇获得分类、1篇未分类、4篇双主题。分类保存在 `data/classifications.precomputed.json`，由 Codex 任务预先完成，不是实时 AI，不调用付费 API，不需要 API Key，不分析照片。

v0.8仅增加作者、正文、图片和展示信息，没有改动分类输入的 `id/title/description/tags`，语义hash仍为 `32ac1b6352714ff4be765cd2e08f47dd1bfc108cb37071f0803508368d011df7`。旧结果通过完整校验后继续使用，没有静默套用过期结果。

按笔记计，摄影65.8%、原创设计26.3%、原创界面示意7.9%。所有图片存于本地 `assets/`，详情见[素材来源](docs/ASSET_SOURCES_V08.md)、[逐文件记录](docs/asset-sources-v08.json)和 `docs/licenses/`。照片是授权氛围配图，不代表虚构作者本人或所述目的地实拍。

沿用 `refold-v05-experience-data`；保留旧版纠错、隐藏、模拟收藏及专辑。新增字段见[实现与验证记录](reports/v08-validation.md)。分享链接只包含主动选择的模拟笔记ID及标题，是静态原型，不能用来承载真实私人数据或真实权限控制。

## 本地运行与验证

```bash
python3 -m http.server 4173 --bind 127.0.0.1
```

另一个终端在仓库根目录运行（Python Playwright与Chromium需已安装）：

```bash
python3 -m unittest discover -s tests -p test_classifier.py -v
python3 -m unittest discover -s tests -p test_precomputed.py -v
python3 tests/test_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_ai_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_precomputed_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_v08.py --phase all --base-url http://127.0.0.1:4173
```

共69项测试通过，包括42项浏览器测试与27项数据/管线测试。浏览器检查375/390/430px、1440×900，支持 `--chromium /path/to/chromium`。触控手势通过Chromium CDP真实触控事件验证；未声称已在实体iPhone/Safari验收。

生成截图：

```bash
python3 tests/capture_screenshots.py --base-url http://127.0.0.1:4173 --output-dir screenshots/v08
```

`screenshots/v08/` 包含主页、合集、完整笔记、管理、多选添加、分享与好友选择等移动端截图及桌面截图。

## 维护静态产物

```bash
python3 scripts/build_data_bundle.py
python3 tests/export_standalone.py
python3 scripts/classify_notes.py --validate-existing data/classifications.precomputed.json
```

`RE_FOLD_v06_Demo.html` 保留旧下载文件名，内容已同步v0.8，内嵌图片、数据和素材许可通知。仅恢复已有预分类时可运行 `python3 scripts/restore_precomputed.py`；它不会重新分类或调用模型。

修改分类输入文本后必须重新完成语义预分类并更新hash及数据包。原独立API分类流程与Windows说明保留在 `docs/AI_CLASSIFICATION.md` 和 `docs/WINDOWS_QUICKSTART.md`；本轮没有执行该可选流程。

## 发布

GitHub Pages使用 `main` 分支仓库根目录，入口 `index.html`，`.nojekyll` 直接提供静态资源。发布前完成测试，推送后核对对应提交的Pages部署和线上交互。不存在新增后端或真实好友服务。
