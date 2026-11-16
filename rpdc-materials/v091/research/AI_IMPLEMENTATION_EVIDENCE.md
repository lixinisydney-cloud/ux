# AI 分类实现与技术边界（v0.9.1）

基线：[`6e9cc55`](https://github.com/lixinisydney-cloud/ux/tree/6e9cc55b46a4cfa991b69da1df66e0567c55017c)。所有统计按仓库中的原创模拟数据计算，不含个人浏览器 localStorage 中的后续纠错。

## 一句话准确表述

这是“Codex 对预设主题进行文本语义预分类 + 静态 JSON + 用户偏好覆盖”的交互原型。它不是实时 Agent，不会在线读取真实小红书收藏、调用官方点点或进行图片理解。

## 数据与输入

[`data/notes.json`](https://github.com/lixinisydney-cloud/ux/blob/6e9cc55b46a4cfa991b69da1df66e0567c55017c/data/notes.json) 共 38 篇：35 篇初始模拟收藏，3 篇 `availability=simulated` 的预备新增收藏。id/title/description/tags/originalAlbum/savedAt/cover 等字段属于项目数据，不是授权读取的小红书账号数据。author/body/images/likes 等用于虚构阅读体验。

分类记录声明的 `inputFields` 为 `id、title、description、tags`。id 用于对齐结果，实际语义信息来自标题、描述和标签；同时提供预设合集的 id/name/description。模型不读取 originalAlbum、savedAt、封面照片、正文 body、作者、互动数字或隐藏的预设答案。`classification-store.js` 的 `modelInput` 及 Python 脚本使用相同字段白名单。

分类输入 hash：`32ac1b6352714ff4be765cd2e08f47dd1bfc108cb37071f0803508368d011df7`。展示字段新增与本轮资料整理没有修改该语义输入。

## 主题是预设的，不是模型发现的

[`data/groups.json`](https://github.com/lixinisydney-cloud/ux/blob/6e9cc55b46a4cfa991b69da1df66e0567c55017c/data/groups.json) 固定 6 个主题：

| id | 智能合集 |
| --- | --- |
| design | 设计与创作 |
| travel | 旅行与探索 |
| career | 求职准备 |
| food | 美食与探店 |
| home | 家居灵感 |
| life | 穿搭与生活 |

Codex 判断一篇笔记应关联哪些既定主题，可以多主题或不归类，不自行命名/创建新主题。“智能合集”是虚拟关联层，原专辑仍保留；这不是把原专辑移动或合并。

## 实际保存、读取和校验路径

1. 在 v0.7 的 Codex 会话中按文本完成语义预分类，保存为 [`data/classifications.precomputed.json`](https://github.com/lixinisydney-cloud/ux/blob/6e9cc55b46a4cfa991b69da1df66e0567c55017c/data/classifications.precomputed.json)。元数据 `mode=precomputed / provider=codex / model=Codex / promptVersion=re-fold-text-v1`；文件记录 `generatedAt=2026-11-16T05:18:50.521534Z`。这不是独立 OpenAI API 的运行日志。
2. 旧云环境结果未能恢复，实际重新生成发生在 [`d7c602a`](https://github.com/lixinisydney-cloud/ux/commit/d7c602a4b98825c9a974b0e7b68e72c674a02988)，恢复失败和重新生成事实写在 `reports/v07-precomputed-validation.md`，不能说恢复了原答案。
3. 每篇 `assignment` 包含 noteId、memberships（groupId/reason）及 unclassifiedReason。结构校验检查笔记/主题 ID、完整覆盖、不重复、理由和数据 hash 等。
4. `scripts/build_data_bundle.py` 把当前笔记、主题、离线回退和经过校验的预分类嵌入 `data/offline-bundle.js`；`index.html` 加载数据包和 `classification-store.js`。
5. 浏览器再次计算语义数据 SHA-256 并校验结果；当前 `classifications.real.json` 明确为未运行状态，实际使用有效的 Codex 预分类。代码保留可选真实 API 文件和离线回退机制，不能把这些可选分支写成已调用过。

`scripts/restore_precomputed.py` 是已有预分类的恢复/校验工具，不会调用模型或重写有效结果。本次材料整理未运行结果生成或数据包构建，只进行只读校验。

## 实际数量

| 范围 | 笔记数 | 已关联至少一主题 | 未分类 | 多主题笔记 | 关联总数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 初始收藏 | 35 | 34 | 1 | 4 | 38 |
| 预设新增 | 3 | 3 | 0 | 0 | 3 |
| JSON 总体 | 38 | 37 | 1 | 4 | 41 |

“4 篇多主题”是按笔记数计算；每篇恰为两个主题，不是新增 4 篇笔记。未分类并非被取消收藏。手动移出后页面计数会变化，以上是初始预分类统计，不是所有浏览器状态的统一数量。

## 用户偏好高于模型结果

沿用 localStorage 键 `refold-v05-experience-data`，不清空旧用户记录。`index.html` 的 `inGroup` 可简化为：

```text
当前仍被收藏的笔记
AND（用户手动加入此合集
     OR（预分类有关联 AND 用户未从此合集排除））
```

`addToGroups` 添加 manual 并移除相应 exclude；`removeFromGroup` 移除相应 manual 并添加 exclude。刷新或重新读取预分类不会覆盖这些偏好。全局取消收藏使用 removed 过滤整个模拟收藏库，和“移出本合集”不同。操作前保存相关状态供撤销，原专辑关联字段不因虚拟纠错而改变。

排序 order、自定义/最近收藏、隐藏 hidden、展示开关、撤销、取消收藏确认、好友选择及分享链接均是确定性的 JavaScript 状态和本地持久化，不需要模型。

## 新收藏是预计算演示

3 篇预备笔记及其分类已在 JSON 中：new1 → 家居灵感，new2 → 设计与创作，new3 → 旅行与探索。桌面左侧 Demo 控制区只把预备笔记加入 savedNew，并记录当前模拟收藏时间；前端读取已有分类。因此演示可以即时更新合集，但不能表述为“刚刚实时调用 AI 分析了新内容”。

若未来加入完全不在数据集的新笔记，需要更新数据、重新预分类/校验和构建数据包；当前静态页面不会自动理解任意新文本。v0.9.1 普通手机 App 菜单里没有模拟新增入口。

## 分享的准确边界

点击分享动作或完成好友共享时，以当前合集实际显示的全部已收藏笔记 ID 创建静态副本；尊重手动纠错/加入及全局取消状态。后续新增不会进入旧副本。个人合集和原专辑不被移动或公开改写，虚构好友只保存本地模拟状态，不发送消息。

链接 `#share=` 编码版本、名称和 noteIds，可在同一公开静态站点打开；它固定的是笔记范围，而非永久封存正文/图片的内容档案。Base64 不是加密、鉴权或真正的私密访问控制。演示中全部原始笔记本来就随公开仓库发布；不能据此宣称已实现真实私人收藏的安全分享系统。

## 不包含的能力

- 不接入真实 REDNOTE 账号、收藏、好友、官方点点或官方 API。
- 不进行当前网页运行时的实时模型推理；没有付费 API 调用或前端 API Key。
- 不进行封面/照片的多模态识别。摄影只是授权氛围配图，不能说 AI 看图后给出了分类。
- 不自动发现主题、跨设备同步、后台持续整理或真正协同编辑。
- 新建专辑的“相似专辑”提示沿用确定性词汇规则，不能描述成实时模型推理。
- 关注、点赞、评论及单篇阅读页分享图标主要是静态阅读展示；不证明有社区服务。

仓库的可选 API 脚本和合成测试包络不意味着真实 API 已运行。`data/classifications.real.json` 的 unavailable 状态、预分类的 provider 字段和报告必须一起阅读。

## 分类案例（理由逐字来自预分类 JSON）

| 模拟笔记 | 结果 | 是否跨主题 | 已保存的分类依据 |
| --- | --- | --- | --- |
| case-a：这次终于像一家店了 | 设计与创作 | 否 | 虽未在标题点明设计，正文实际统一招牌、外带杯与菜单的字形、主色、字级和留白，属于品牌与版式设计。 |
| case-b：求职作品集排版技巧 | 求职准备；设计与创作 | 是 | 求职：为投递产品体验岗位筛选和前置相关项目，目的是让招聘方快速理解职责与成果。设计：正文具体采用网格对齐、标题字级和页边距组织正文与配图，也包含版式设计方法。 |
| cross-1：赶路前的一杯热咖啡 | 旅行与探索；美食与探店 | 是 | 旅行：根据首尔转车空档和地铁换乘安排路线，并记录回车站的步行时间。美食：同时具体描述拿铁的坚果香、现做三明治和价格，具有独立的餐饮探店信息。 |
| h2：复古台灯和阅读角 | 家居灵感 | 否 | 比较阅读角的灯罩、墙面颜色、木书架和光源高度，语义集中在居住空间的照明与软装；不扩展为平面或界面设计。 |
| ambiguous-1：今天先记在这里 | 不关联主题，仍保留收藏 | 否 | 只有“下次再认真看”的模糊备忘，没有具体对象、地点或活动，无法可靠判断主题，暂不关联合集。 |

JSON 的“正文”措辞是原有理由的用语；实际分类输入白名单只有 description 等文本，不包含后来加入的阅读页 body。案例原字段和完整理由另见 `research/CLASSIFICATION_CASES.json`，不把这 5 例当成盲测评估。

## 工程测试不等于语义准确率

结构校验、hash 一致、错误输入拒绝、状态持久化、手动优先级及 UI 联动通过，只说明代码在已定义条件下行为符合预期。它不证明主题是否适合所有用户，不证明语义准确率，也不证明用户发现效率提升。

自动化中的 API 包络、异常、多图等夹具服务于工程测试，不能作为模型真实输出或用户数据。少量有解释的案例可说明思路，缺少独立标注集、盲评、样本规模和错误分析时，不给出准确率百分比或“已验证分类准确”的结论。正式语义评估与用户研究需设计者补充。

原始证据：`data/notes.json`、`data/groups.json`、`data/classifications.precomputed.json`、`data/classifications.real.json`、`classification-store.js`、`index.html`、`scripts/`、`docs/AI_CLASSIFICATION.md` 和 `reports/`；材料包提供相应白名单副本与 hash 以便核查。
