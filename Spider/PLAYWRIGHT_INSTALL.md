# Playwright 浏览器安装 SSL 问题解决方案

## 问题描述

在运行 `playwright install chromium` 时，可能会遇到 SSL 证书验证错误：

```
Error: unable to verify the first certificate
```

## 解决方案

### 方案一：设置环境变量忽略 SSL 验证（推荐）

在 PowerShell 中运行：

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://playwright.azureedge.net"
playwright install chromium
```

或者设置 Node.js 忽略 SSL 错误：

```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
playwright install chromium
```

### 方案二：使用代理

如果网络环境需要代理：

```powershell
$env:HTTPS_PROXY = "http://your-proxy:port"
playwright install chromium
```

### 方案三：手动下载浏览器

1. 访问 Playwright 浏览器下载页面：
   - https://playwright.dev/docs/browsers

2. 手动下载 Chromium 浏览器

3. 将下载的浏览器放到 Playwright 缓存目录：
   - Windows: `%USERPROFILE%\AppData\Local\ms-playwright`

### 方案四：使用国内镜像

设置 Playwright 使用国内镜像：

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
playwright install chromium
```

### 方案五：配置系统信任证书

1. 下载并安装证书
2. 将证书添加到系统信任存储

## 验证安装

安装完成后，验证浏览器是否正确安装：

```powershell
playwright install --help
```

或者运行 Python 脚本测试：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    print("Chromium 安装成功！")
    browser.close()
```

## 常见问题

### Q: 为什么会出现 SSL 错误？

A: 可能是由于网络环境、防火墙、代理或公司网络策略导致的证书验证问题。

### Q: 安装后仍然无法使用？

A: 确保浏览器版本与 Playwright 版本匹配。可以尝试：

```powershell
playwright install chromium --force
```

### Q: 如何查看已安装的浏览器？

A: 运行：

```powershell
playwright install --dry-run
```

## 推荐做法

对于中国大陆用户，推荐使用方案四（国内镜像）：

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
playwright install chromium
```

这样可以避免大多数网络和 SSL 相关的问题。
