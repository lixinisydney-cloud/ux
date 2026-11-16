# v0.7：真实文本分类的配置、证据与静态演示

## 当前实际状态

默认使用 `data/classifications.precomputed.json`：`mode=precomputed`、`provider=codex`、`model=Codex`。这是本次 Codex 会话按标题、描述与标签重新完成的语义预分类，没有调用付费 API，也不需要 API Key。旧云环境文件不可读取，未能恢复上次产物；本次不是原结果恢复。详见 [恢复记录](../reports/v07-precomputed-validation.md)。

`data/classifications.real.json` 仍为 `unavailable`，表示独立 OpenAI API 流程未运行；不能把 Codex 会话预分类或离线示例冒充为该 API 的输出。下文“真实运行”章节仅描述已有可选流程，本次未执行。

24 项管线单元测试、8 项 AI 文件浏览器集成测试和 10 项原 UI 回归通过。前两类涉及模型输出的测试全部使用明确标注的测试夹具；不证明语义分类准确率。实际案例记录见 `reports/cases-v07.json` 与 `reports/v07-validation.md`。

## 数据与调用边界

`data/notes.json` 包含 35 篇初始笔记，以及 3 篇供“模拟新收藏”使用的预备笔记，共 38 篇。每篇包含：

| 字段 | 用途 | 送入模型 |
| --- | --- | --- |
| id | 稳定的笔记标识，兼容旧纠错记录 | 是 |
| title / description / tags | 原创模拟社区内容 | 是 |
| originalAlbum | 原收藏位置 | 否 |
| savedAt | 收藏排序的 ISO 时间 | 否 |
| cover | 本地封面文件名 | 否 |
| availability | initial / simulated | 否 |

`data/groups.json` 固定六个合集，向模型提供 id、name、description。模型不能新增合集。原始笔记没有预设 `groups` 或 `reason` 字段；脚本按白名单重新构建请求，即使笔记未来加入这些字段，也不会送入模型。

本轮只使用文本，没有图片语义输入。封面只用于显示，不能声称已完成多模态图像理解。

## 安全配置与真实运行

分类脚本仅使用 Python 3.10+ 标准库，不需要安装 AI SDK。默认模型为 `gpt-4.1-mini`，可通过 `OPENAI_MODEL` 或 `--model` 指定支持结构化输出的 OpenAI 模型。

Windows 用户请按 [Windows 操作指南](WINDOWS_QUICKSTART.md) 使用 `py` 命令，无需安装额外的分类依赖。

在仓库根目录先查看**真实会发送的内容和 schema**；此命令不联网：

```bash
python3 scripts/classify_notes.py --dry-run
```

推荐在你自己的交互终端运行：

```bash
python3 scripts/classify_notes.py --ask-key
```

终端会要求输入 OpenAI API Key，输入不回显、不写文件、不进入命令行历史。不要把密钥发到聊天中，也不要填进网页、JSON 或 GitHub 仓库。脚本只向固定的 `https://api.openai.com/v1/chat/completions` 发送请求，保留 TLS 校验，不向重定向地址转发密钥。

也可使用你在本地或安全环境设置中已有的 `OPENAI_API_KEY`，然后运行：

```bash
python3 scripts/classify_notes.py
```

`.env.example` 仅为变量名称模板，脚本不会自动读取 `.env`。真实 `.env` 与 `.cache/` 均已被 Git 忽略。若在受限云环境运行，还需允许访问 `api.openai.com`；GitHub Token 不能代替 AI API Key。

脚本缺少有效密钥、API 拒绝、响应截断、非 JSON 或校验失败时，以非零状态退出，不会生成伪造结果，也不会覆盖已有的有效结果文件。API 失败信息不输出密钥或任意错误响应正文。

## 输出、校验与缓存

成功输出到 `data/classifications.real.json`：

- 元数据：schemaVersion、mode、provider、model、generatedAt、datasetHash、promptVersion、inputFields、notesCount。
- 每篇笔记恰好一项 assignment，包含 noteId、memberships、unclassifiedReason。
- memberships 可以关联多个 groupId；每项有简短 reason。不确定时留空并给出 unclassifiedReason，不强行归类。
- ID 必须属于当前数据集；拒绝遗漏、重复、未知笔记/合集、额外字段、空理由和不匹配的输入 hash。已分类时 unclassifiedReason 必须为 null。
- JSON 通过完整校验后才原子写入结果文件。

执行独立校验和 A/B 评估：

```bash
python3 scripts/classify_notes.py --validate-existing data/classifications.real.json
python3 scripts/evaluate_cases.py
```

案例 A/B 的预期只保存在报告中，不作为模型输入。评估会逐字记录实际归类理由、模型和输入版本；模型没有命中预期时记录 false，不将离线答案补进结果。退出码：0=真实结果评估满足两例预期，1=存在不满足预期，2=没有可评估的真实结果或校验失败。

真实调用的精确请求（不含鉴权头）和原始响应保存到本地忽略目录 `.cache/re-fold/`，POSIX 系统设为私有权限；Windows 使用当前用户的文件夹权限，不依赖 POSIX 模式位提供 ACL 保护。用于复用的已校验缓存按语义输入 hash、模型和 promptVersion 区分，默认 7 天有效；内容或模型改变后不能误用旧缓存。缓存命中不再次请求 API。坏缓存会拒绝使用，需要检查原因；`--force` 会跳过缓存并进行新的真实请求。

## 前端与 GitHub Pages

`classification-store.js` 只加载同源静态 JSON，不含密钥，不访问模型 API。加载前会再次验证结果结构与输入 hash。

- 默认：有有效真实结果文件则使用它，并明确显示“真实 AI 文本分类”及模型名。
- API 文件尚未生成：使用校验过的 Codex 预分类，标注“Codex AI 语义预分类 · 未调用付费 API”；预分类不可用时才使用离线示例。
- API 结果加载失败：仅可使用同一数据集下仍有效的浏览器 API 结果缓存，并显示“本地缓存”；否则回退校验过的 Codex 预分类，再回退离线示例。
- `?classification=offline`：强制离线模拟，不加载真实文件。
- `data/offline-bundle.js`：从 JSON 源文件生成，内嵌笔记、合集、Codex 预分类及回退示例；网页和离线 HTML 读取同一份已校验结果。

修改笔记/合集或离线示例后，重新生成启动数据：

```bash
python3 scripts/build_data_bundle.py
```

新增笔记时离线文件也需包含新 ID；可给不确定内容留空 memberships。脚本会拒绝数据与结果 hash 不一致的文件，避免误展示旧答案。

打开本地预览：

```bash
python3 -m http.server 4173
```

在本机浏览器访问 `http://localhost:4173`。同一套相对路径也适用于 Pages 的 `/ux/` 子目录。无须新增付费后端。成功生成真实结果后，Pages 只需提供 `index.html`、CSS、JS、封面、启动数据及分类 JSON，不需要 API Key。

本轮“模拟新收藏”只释放预备数据集中的笔记并载入已有分类；它不会实时请求 AI。要分类全新内容，先更新数据集，在本地重新运行脚本，再发布已校验的 JSON。

新建专辑的相似提示继续使用已有的轻量确定性规则；本轮未将它包装为真实模型推理。

## 用户纠错与回归

沿用 `refold-v05-experience-data` 保存用户状态。模型结果和用户的 exclude / pins / hidden 分开存储，`inGroup` 总是在读取模型关系后应用用户 exclude。重载或更换分类文件不能清空纠错；撤销只移除用户自己添加的排除关系。原专辑、笔记、封面和权限不由模型修改。

运行工程测试（不会调用真实 AI）：

```bash
python3 -m unittest discover -s tests -p test_classifier.py -v
python3 tests/test_ai_ui.py --base-url http://127.0.0.1:4173
python3 tests/test_ui.py --base-url http://127.0.0.1:4173
```

浏览器测试需要 Python Playwright 和 Chromium，支持 `--chromium /path/to/chromium`。Case C 使用测试文件验证前端优先级，其结果与 A/B 模型质量测试分开记录。

生成离线单文件预览：

```bash
python3 tests/export_standalone.py
```

为兼容旧下载入口，文件名继续为 `RE_FOLD_v06_Demo.html`，内容随当前代码生成；它内嵌当前数据、结果和图片，遵守同样的真实/离线标记。原始响应缓存和密钥不会内嵌。

## 预分类恢复与校验

```bash
python3 scripts/restore_precomputed.py
python3 scripts/classify_notes.py --validate-existing data/classifications.precomputed.json
python3 -m unittest discover -s tests -p test_precomputed.py -v
python3 tests/test_precomputed_ui.py --base-url http://127.0.0.1:4173
```

恢复脚本不调用模型，不重写已有有效分类。源文件必须与当前语义数据 hash 匹配；构建时完整校验 ID、覆盖率、依据、来源和日期。浏览器再次校验嵌入的数据。
