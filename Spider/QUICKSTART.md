# Spider 爬虫项目

这是一个独立的 Python 爬虫项目，用于爬取 Acunetix API 文档。

## 快速开始

### 1. 安装依赖

```bash
cd Spider
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

如果遇到 SSL 证书错误，可以使用以下解决方案：

```powershell
# 方案一：使用国内镜像（推荐）
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
playwright install chromium

# 方案二：忽略 SSL 验证
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
playwright install chromium
```

详细解决方案请查看 [PLAYWRIGHT_INSTALL.md](PLAYWRIGHT_INSTALL.md)

### 3. 测试 Playwright 安装

安装完成后，可以测试 Playwright 是否正常工作：

```bash
python test_playwright.py
```

如果测试通过，就可以运行爬虫了。

### 4. 运行爬虫

```bash
python main.py
```

或者直接运行爬虫脚本：

```bash
python src/advanced_crawler.py
```

### 5. 查看结果

爬取完成后，查看 `output/` 目录：

- `acunetix-api.json` - 所有 API 接口数据
- `summary.json` - 爬取摘要

## 项目特点

- 使用 Python + Playwright + BeautifulSoup 强大爬虫框架
- 支持爬取 HTTPS 自签名证书网站
- 自动提取 API 接口详细信息
- 多页面爬取，自动发现相关链接
- 智能去重处理
- 详细的进度显示和错误处理
- 独立项目，与主项目隔离

详细文档请查看 [README.md](README.md)

## 环境要求

- Python 3.8+
- pip

## 爬取目标

默认爬取 URL: `https://localhost:3443/Acunetix-API-Documentation.html`

确保 Acunetix 服务正在运行并可以访问该 URL。
