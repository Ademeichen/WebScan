# Acunetix API Crawler

基于 Python + Playwright 的 Acunetix API 文档爬虫项目，用于爬取 Acunetix API 文档中的所有接口信息。

## 项目结构

```
Spider/
├── requirements.txt       # Python 依赖包
├── main.py              # 主程序入口
├── test_playwright.py    # Playwright 测试脚本
├── .gitignore           # Git 忽略文件
├── src/
│   ├── __init__.py     # Python 包初始化
│   ├── config.py        # 配置文件
│   └── advanced_crawler.py  # 高级爬虫脚本
└── output/              # 输出目录（自动创建）
    ├── acunetix-api.json    # API 接口数据
    ├── summary.json         # 爬取摘要
    └── example-output.json  # 输出格式示例
```

## 功能特性

- 使用 Python + Playwright + BeautifulSoup 进行网页爬取
- 支持爬取 HTTPS 自签名证书网站
- 自动提取 API 接口信息：
  - HTTP 方法（GET, POST, PUT, DELETE 等）
  - API 端点路径
  - 请求参数
  - 接口描述
  - 示例代码
  - 响应状态码
  - 响应格式
  - 认证信息
- 多页面爬取，自动发现相关链接
- 智能去重处理
- 详细的进度显示和错误处理
- 自动保存为 JSON 格式
- 生成爬取摘要报告

## 环境要求

- Python 3.8+
- pip

## 安装依赖

```bash
cd Spider
pip install -r requirements.txt
```

首次运行需要安装 Playwright 浏览器：

```bash
playwright install chromium
```

如果遇到 SSL 证书错误，请参考 [PLAYWRIGHT_INSTALL.md](PLAYWRIGHT_INSTALL.md)。

### 测试 Playwright 安装

安装完成后，可以测试 Playwright 是否正常工作：

```bash
python test_playwright.py
```

如果测试通过，就可以运行爬虫了。

## 使用方法

### 运行爬虫

```bash
python main.py
```

或者直接运行爬虫脚本：

```bash
python src/advanced_crawler.py
```

## 配置

在运行爬虫前，确保 Acunetix 服务运行在 `https://localhost:3443`。

如果需要修改配置，编辑 `src/config.py` 文件：

```python
TARGET_URL = 'https://localhost:3443/Acunetix-API-Documentation.html'
OUTPUT_DIR = BASE_DIR / 'output'

CRAWLER_CONFIG = {
    'headless': False,      # 是否无头模式
    'timeout': 30000,       # 超时时间（毫秒）
    'max_requests': 50,      # 最大请求数
}
```

## 输出说明

爬虫运行完成后，会在 `output/` 目录下生成以下文件：

### acunetix-api.json

包含所有爬取到的 API 接口信息，每个接口包含以下字段：

```json
{
  "sectionTitle": "接口标题",
  "sectionId": "章节ID",
  "methods": ["GET", "POST"],
  "endpoints": ["/api/v1/targets"],
  "description": "接口描述信息",
  "parameters": [
    {
      "name": "参数名",
      "type": "参数类型",
      "description": "参数描述"
    }
  ],
  "examples": ["示例代码"],
  "responseFormat": "响应格式",
  "statusCode": "状态码",
  "authentication": "认证信息",
  "requestHeaders": [],
  "responseHeaders": [],
  "url": ""
}
```

查看 [example-output.json](output/example-output.json) 了解输出格式示例。

### summary.json

爬取摘要信息：

```json
{
  "totalEndpoints": 50,
  "uniqueMethods": ["GET", "POST", "PUT", "DELETE"],
  "uniqueEndpoints": ["/api/v1/targets", "/api/v1/scans"],
  "totalParameters": 150,
  "totalExamples": 80,
  "pagesVisited": 10,
  "timestamp": "2026-01-21T00:00:00.000Z",
  "targetUrl": "https://localhost:3443/Acunetix-API-Documentation.html"
}
```

## 爬虫特性

### 高级爬虫 (advanced_crawler.py)

- 多页面爬取
- 更详细的信息提取
- 支持认证信息提取
- 支持请求/响应头信息
- 智能去重
- 更好的错误处理
- 进度显示
- 自动发现相关链接

### 提取功能

1. **API 端点和方法提取**
   - 自动识别 HTTP 方法（GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS）
   - 提取所有 /api/v1/ 开头的端点路径

2. **参数提取**
   - 从表格中提取参数信息
   - 支持多种参数表格格式

3. **描述提取**
   - 从段落和 div 中提取接口描述
   - 自动去重

4. **状态码和响应格式提取**
   - 识别常见的 HTTP 状态码（200, 201, 204, 400, 401, 403, 404, 500）
   - 提取 JSON 响应格式

5. **认证信息提取**
   - 识别认证相关关键词
   - 提取 API Key、Token、Bearer 等认证信息

6. **示例代码提取**
   - 提取包含 API 调用的代码示例
   - 自动过滤无关代码

## 注意事项

1. 确保 Acunetix 服务正在运行
2. 爬虫默认以非无头模式运行（`headless: False`），可以看到浏览器操作
3. 如果需要无头模式，修改 `src/config.py` 中的 `headless: True`
4. 首次运行需要安装 Playwright 浏览器
5. 爬虫会自动发现并爬取相关页面，受 `max_requests` 限制

## 故障排除

### SSL 证书错误

如果遇到 SSL 证书错误，爬虫已配置 `ignore_https_errors=True`，应该可以正常工作。

### 超时错误

如果页面加载超时，可以增加超时时间：

```python
CRAWLER_CONFIG = {
    'timeout': 60000,  # 增加到60秒
}
```

### 权限问题

确保有权限访问 Acunetix API 文档页面。

### Playwright 浏览器未安装

如果提示浏览器未安装，运行：

```bash
playwright install chromium
```

如果遇到 SSL 证书错误，请参考 [PLAYWRIGHT_INSTALL.md](PLAYWRIGHT_INSTALL.md) 文档。常见解决方案：

```powershell
# 方案一：使用国内镜像（推荐）
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
playwright install chromium

# 方案二：忽略 SSL 验证
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
playwright install chromium
```

### 爬取数据为空

如果爬取结果为空，可能原因：
1. Acunetix 服务未运行
2. URL 配置错误
3. 页面结构与预期不同

可以尝试：
- 检查 Acunetix 服务是否正常运行
- 在浏览器中手动访问 URL 确认页面可访问
- 增加超时时间
- 查看 Playwright 是否正常工作（运行 `python test_playwright.py`）

## 技术栈

- **Python**: 编程语言
- **Playwright**: 浏览器自动化工具
- **BeautifulSoup**: HTML 解析库
- **lxml**: XML/HTML 解析器

## 开发建议

### 添加自定义提取规则

在 `src/advanced_crawler.py` 的 `_extract_section_data` 方法中添加自定义逻辑。

### 修改输出格式

在 `_save_results` 方法中修改 JSON 输出格式。

### 添加新的数据字段

在 section 字典中添加新的字段，并在提取逻辑中填充。

### 调试模式

如果需要调试，可以设置 `headless: False` 并在代码中添加更多打印语句。

## 许可证

MIT
