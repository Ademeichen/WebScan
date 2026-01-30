# Seebug POC 智能助手 (Seebug Agent)

## 📖 项目简介
**Seebug Agent** 是一个智能化的漏洞验证代码（POC）生成工具。它无缝集成了 **Seebug 漏洞库**的查询能力与 **ModelScope (GLM-4)** 大模型的代码生成能力。

该工具旨在辅助安全研究人员快速获取漏洞信息，并自动生成适配 **Pocsuite3** 框架的 Python 检测脚本，大幅提高漏洞验证效率。

## ✨ 核心功能

1.  **智能双模搜索** 🔍
    *   优先使用 Seebug API 获取官方结构化数据。
    *   **自动降级机制**：当 API 无权限或返回空结果时，自动切换为 **Web Scraping (网页爬虫)** 模式，直接从 Seebug 官网获取公开的漏洞信息（如 SSVID、标题等），确保在非付费账号下也能正常工作。

2.  **AI 代码生成** 🤖
    *   集成 ModelScope (阿里魔搭) 的 GLM-4.7-Flash 模型。
    *   根据漏洞描述、受影响组件和漏洞类型，自动编写标准的 Pocsuite3 POC 代码。
    *   内置重试机制，自动处理 API 限流 (429) 问题。

3.  **全自动化工作流** ⚡
    *   `搜索` -> `详情提取` -> `Prompt 构建` -> `AI 生成` -> `本地保存` 一气呵成。

## 🛠️ 环境准备

确保已安装 Python 3.8+，并安装以下依赖库：

```bash
pip install requests openai
```

*(注：本项目使用 `openai` 库来调用兼容 OpenAI 协议的 ModelScope API)*

## ⚙️ 配置说明

在使用前，请检查并配置以下文件中的 API Key：

1.  **ModelScope API Key (必须)**
    *   文件: `Seebug_Agent/poc_generator.py`
    *   变量: `API_KEY`
    *   说明: 用于调用 AI 模型生成代码。

2.  **Seebug API Key (可选)**
    *   文件: `Seebug_Agent/main.py`
    *   变量: `SEEBUG_API_KEY`
    *   说明: 用于 Seebug API 查询。如果无效或留空，程序将自动使用爬虫模式。

## 🚀 使用指南

### 方式一：交互式模式 (Interactive Mode)
适合人工操作，根据提示逐步进行。

```bash
cd Seebug_Agent
python main.py
```
**操作流程：**
1.  输入搜索关键字（例如 `thinkphp`）。
2.  查看返回的漏洞列表。
3.  输入序号选择要生成 POC 的漏洞（例如 `1`）。
4.  等待 AI 生成并保存文件。

### 方式二：命令行参数模式 (CLI Mode)
适合快速生成或集成到其他自动化脚本中。

```bash
# 语法: python main.py [搜索关键字] [选择序号]

# 示例：搜索 thinkphp 并自动选择第 1 个结果生成 POC
python main.py thinkphp 1
```

## 📂 产出文件
生成的 POC 脚本将保存在项目根目录下，命名格式为：
`poc_{SSVID}_ai.py`

例如：`poc_99617_ai.py`

生成的代码可以直接使用 Pocsuite3 加载运行：
```bash
pocsuite3 -r poc_99617_ai.py -u http://target-url.com --verify
```

## ⚠️ 免责声明
*   本工具生成的代码仅供安全研究和授权测试使用。
*   爬虫模式仅作为 API 限制下的临时兜底方案，请勿高频抓取以免影响目标站点运行。
*   AI 生成的代码可能存在误报或逻辑错误，建议在沙箱环境中人工复核后再使用。
