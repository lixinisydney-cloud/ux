# Windows：下载并运行 v0.7 真实分类测试

## 准备项目

1. 打开 https://github.com/lixinisydney-cloud/ux ，选择 `main`。
2. 点击 **Code → Download ZIP**，解压。或者在已有克隆中运行 `git pull --ff-only origin main`。
3. 安装 Python 3.10 或更新版本（建议 3.12），确保安装了 Windows Python Launcher。在 PowerShell 或 CMD 中运行 `py --version`，确认显示 Python 3.10+。
4. 在解压后的 `ux-main` 文件夹打开 PowerShell 或 CMD；此目录应能看到 `index.html`、`scripts` 和 `data`。

**真实分类与案例评估仅使用 Python 标准库，不需要 `pip install`，也不需要 OpenAI SDK。** `.env.example` 只有变量名称，没有密钥；脚本不会自动加载 `.env`。

## 先检查输入（不调用模型）

```powershell
py scripts\classify_notes.py --dry-run
```

输出包括 38 篇模拟笔记会发送的文本、六个合集定义及 JSON schema。不会向模型发送预设分类、原专辑或封面。

## 安全输入密钥并分类

```powershell
py scripts\classify_notes.py --ask-key
```

在终端提示后输入你自己的 OpenAI API Key，输入时不显示字符或星号，这是正常现象。按回车执行。密钥不回显、不写文件，不需要填进 `.env`、网页或仓库。请在正常的 PowerShell、CMD 或 Windows Terminal 中运行；非交互输出窗口不能使用 `--ask-key`。

默认模型为 `gpt-4.1-mini`；也可显式指定你有权限使用且支持结构化 JSON 的模型：

```powershell
py scripts\classify_notes.py --ask-key --model gpt-4.1-mini
```

如果已经在当前终端安全配置 `OPENAI_API_KEY`，可以不加 `--ask-key`。不要把密钥直接拼在命令参数里。

只有真实 API 调用成功、输出通过校验后，脚本才会写入 `data\classifications.real.json`。默认命中有效缓存时不重复调用；`--force` 会重新请求模型。API 需要你的账户有对应模型权限及可用额度。

## 验证实际结果

```powershell
py scripts\classify_notes.py --validate-existing data\classifications.real.json
py scripts\evaluate_cases.py
```

案例报告为 `reports\cases-v07.json`：A/B 会记录实际归类、理由、模型及是否满足人工预期。评估退出码 0 表示两例符合预期，1 表示有不符合预期的真实结果，2 表示还没有真实结果或校验失败。模型未命中预期时不会自动替换答案。

精确请求（无鉴权头）和原始响应保存在 `.cache\re-fold\`，该目录不提交 Git。Windows 下缓存访问权限依赖当前用户的文件夹权限；脚本中的 POSIX 权限位不等同于 Windows ACL。API Key 从不写入缓存。

## 本地查看页面

```powershell
py -m http.server 4173
```

在浏览器打开 http://localhost:4173 。刷新后，页面读取你本地生成的真实结果。没有真实结果时，仍显示明确标注的离线 Demo。

本地生成结果不会自动上传到 GitHub Pages，也不会上传密钥。源码和 JSON 请使用 UTF-8 保存；支持 Windows 编辑器添加的 UTF-8 BOM。控制台 JSON 输出也统一为 UTF-8。

只有开发者运行浏览器自动测试时才需要另外安装 Playwright/Chromium；运行上述分类、评估和预览命令不需要这些测试依赖。
