# 重现截图与录屏

本脚本只操作当前页面，不修改仓库产品文件、不注入 UI、不预置 localStorage、不请求 AI API。每段开启独立浏览器上下文，使用真实点击、CDP 触控、长按和现有动画。

Windows PowerShell：

```powershell
py -m pip install playwright
py -m playwright install chromium
py .\capture_materials.py --mode recordings --output .. --base-url https://lixinisydney-cloud.github.io/ux/
```

输出 7 段 WebM 到 `recordings/`。安装 FFmpeg 后可整段转换为 MP4：

```powershell
Get-ChildItem ..\recordings\*.webm | ForEach-Object {
  ffmpeg -i $_.FullName -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -movflags +faststart -an ($_.DirectoryName + '\' + $_.BaseName + '.mp4')
}
```

不要运行到原始交付文件夹以免覆盖素材，建议复制脚本到新的工作目录。使用 `--only 3,6` 可仅重录第 3、6 段。默认链接指向在线网站，未来如果产品版本改变，先使用指定提交的本地静态服务器，并传 `--base-url http://127.0.0.1:4183/`；此时复制的链接只能在该本地服务可用时打开。

补拍截图：

```powershell
py .\capture_materials.py --mode screenshots --output .. --base-url https://lixinisydney-cloud.github.io/ux/
```

`--repo 路径` 可复用当地检出的最终 `screenshots/v091/`，其他截图在当前 DOM 中生成。浏览器为正常 motion；仅静态截图指定减少动态效果以抓稳定帧。录屏保持页面原有动效。

脚本要求 Chromium（CDP 真实触控）；Windows 可直接使用 Playwright 安装的浏览器。不声称在 Windows 已实机运行过此脚本，实际执行环境见材料证据。本轮云环境已有 `/usr/bin/chromium` 和 FFmpeg 7.1.5，但缺少 Playwright 默认编码器路径，使用临时 `PLAYWRIGHT_BROWSERS_PATH` 下的 FFmpeg 符号链接指向已安装系统编码器完成原生录制，没有改系统信任库或产品代码。

本轮 `--verified-transport` 仅解决云环境 Chromium 的代理 CA 缺失：用标准 urllib 校验本站上游 HTTPS、原样转发响应，并与指定本地仓库字节核对。默认不启用；普通 Windows 不需要。它未关闭 TLS 校验、不伪造数据或外观，不代理其他站点。

可自动化的手势：手机横滑、纵向滑动、720ms 长按、同一触控拖动排序、点击/返回、真实剪贴板读写与打开分享链接。未自动化/未验证：实体手机系统手势、iOS Safari/WebView、第三方 App 内发送、系统分享面板的操作选择。当前数据全为单图，不能在本次视频中展示不存在的多图内容。Clip 05 如实使用桌面控制区，未向手机 UI 添加入口。

如要录制真正的手机视频，可直接在手机 HTTPS 浏览器打开最终 Demo，以系统屏幕录制重做 01–04、06–07；新增收藏入口在桌面，需要另录桌面段或在 PPT 中说明这一原型边界。不要用本包视频声称已验证实体 iPhone。
