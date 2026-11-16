# v0.7 Codex 预分类：恢复调查与本次验证

## 来源与恢复结论

2026-11-16（北京时间），以 GitHub `main` 的 `90e61e118c4f6640ac365d17e973b33051c18c48` 为基线。

先检查了当前 `/workspace`、`/tmp` 中的分类/恢复文件、本地分支、reflog、不可达 Git 对象及远端 refs。只找到原有 offline 示例和 unavailable API 标记，没有找到上次的预分类 JSON 或恢复脚本。当前没有读取旧 failed/offline 环境磁盘的能力。

因此本文件记录的是 **本次 Codex 会话重新生成**，不是恢复成功，也不保证逐项等同于上次结果。依据是仓库现有笔记的 `id/title/description/tags` 和六个合集的语义定义；未使用封面进行图像理解，未依据原专辑决定分类。没有调用付费 API、没有使用 API Key，也没有将 offline 示例改名冒充为模型结果。

`data/classifications.precomputed.json` 标记 `mode=precomputed`、`provider=codex`、`model=Codex`。`data/classifications.real.json` 保持原有 unavailable 标记，独立 OpenAI API 流程未执行。历史 `reports/cases-v07.json` 的 API 未运行状态不改成成功。

## 实际结果

- 35 篇已有笔记：34 篇获得分类，1 篇未分类（`ambiguous-1`，文字没有明确对象或活动）。
- 4 篇关联两个主题：`d7`（design/career）、`c5`（career/design）、`case-b`（career/design）、`cross-1`（travel/food）。
- 3 篇模拟新增：`new1` → home，`new2` → design，`new3` → travel。
- `case-a`：正文统一招牌、杯子和菜单的字形、主色、字级与留白，归入 design。
- `case-b`：同时涉及投递项目筛选与网格版式，归入 career/design。
- `h2`：照明、墙色和书架的比较服务于阅读角软装，归入 home，不因出现“配色”就额外归入 design。
- 全部 38 篇均有且只有一项 assignment；未分类项有依据，其余每个主题关联各有独立依据。
- 语义数据 hash：`32ac1b6352714ff4be765cd2e08f47dd1bfc108cb37071f0803508368d011df7`。

这是已知小型演示数据集上的 Codex 语义判断，不是独立盲测准确率评估。

## 数据联动与恢复

构建脚本校验 JSON 后，将预分类嵌入 `data/offline-bundle.js`。浏览器再次校验数据 hash、ID、完整性、依据和来源。默认使用该预分类，原有可选 API 结果加载/缓存及强制 offline 模式保留。无有效 API 结果时使用预分类，预分类无效时才回退明确标注的 offline 示例。

页面布局、CSS、原专辑数据和用户存储键均未改变。仅更新已有分类来源/依据说明，避免将 Codex 预分类显示为付费 API 结果。用户排除、撤销、固定、隐藏及模拟收藏逻辑保持原实现。单文件 HTML 已同步。

恢复已有产物：

```bash
python3 scripts/restore_precomputed.py
```

该脚本保留并校验已有 JSON；缺失时从本地 Git HEAD 恢复。它不调用模型或网络，不重新生成分类。数据 hash 不匹配或现有文件无效时直接报错。随后重建 bundle 和离线 HTML。连续执行两次，产物保持一致。

## 本地验证

在仓库根目录以 `python3 -m http.server 4173 --bind 127.0.0.1` 提供静态文件。

| 命令 | 结果 |
| --- | --- |
| `python3 scripts/classify_notes.py --validate-existing data/classifications.precomputed.json` | 38 篇结构和数据版本校验通过 |
| `python3 -m unittest discover -s tests -p test_classifier.py -v` | 24 项通过；原 API 管线使用合成夹具 |
| `python3 -m unittest discover -s tests -p test_precomputed.py -v` | 3 项通过；数量、语义案例、来源、hash 和产物一致性 |
| `python3 tests/test_ui.py --base-url http://127.0.0.1:4173` | 10 项通过；375/390/430px、图片、滚动、纠错/撤销、原专辑、排序、隐藏、创建和持久化 |
| `python3 tests/test_ai_ui.py --base-url http://127.0.0.1:4173` | 8 项通过；合成 API 数据加载/缓存/回退回归，不是 API 调用证据 |
| `python3 tests/test_precomputed_ui.py --base-url http://127.0.0.1:4173` | 4 项通过；使用实际提交的 Codex 分类数据 |

合计 **49 项测试通过**。新增浏览器测试逐个核对六个合集的实际成员与全部已有笔记的分类依据，并验证纠错撤销、刷新后纠错仍有效、原专辑保留、3 篇新增收藏及其刷新持久化。检查 1440×900 桌面与 390px 内容区、图片完整加载；浏览器 JavaScript、控制台和 HTTP 错误为 0，无外部 API 请求。移动端与桌面截图已人工查看，布局无改动。

单文件导出通过 HTTP 验证。当前受管浏览器禁止 `file://` 导航（ERR_BLOCKED_BY_ADMINISTRATOR），因此没有声称本环境完成了直接双击文件模式的验证。

## 发布状态边界

本记录随发布提交保存。提交/推送、GitHub Pages 部署和线上交互验收是不同步骤；以提交后的实际部署记录与线上检查为准。

发布前检查发现：GitHub 原生 Git 读访问正常，GitHub Actions 网页可访问；`api.github.com` 和 `lixinisydney-cloud.github.io` 被运行环境网络策略拒绝（CONNECT 403）。已在环境配置草稿中补充这两个精确域名，草稿保存本身不会应用到运行中的网络。若运行环境仍未允许 Pages 域名，线上验收将保持未完成，不把本地通过或推送成功当作线上验证成功。
