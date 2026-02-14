# Plugins 包说明文档

## 简介

`plugins` 是 AI_WebSecurity 项目的插件模块集合，提供了多种网站安全检测和信息收集功能。这些插件可以独立使用，也可以被主程序调用，为网络安全分析提供丰富的工具支持。

## 功能模块列表

| 模块名称 | 功能描述 | 文件位置 |
|---------|---------|---------|
| **baseinfo** | 网站基础信息收集 | `baseinfo/baseinfo.py` |
| **cdnexist** | CDN存在检测 | `cdnexist/cdnexist.py` |
| **common** | 通用工具函数 | `common/common.py` |
| **infoleak** | 信息泄露检测 | `infoleak/infoleak.py` |
| **iplocating** | IP地址定位 | `iplocating/iplocating.py` |
| **loginfo** | 日志信息分析 | `loginfo/loginfo.py` |
| **portscan** | 端口扫描 | `portscan/portscan.py` |
| **randheader** | 随机HTTP请求头生成 | `randheader/randheader.py` |
| **subdomain** | 子域名枚举 | `subdomain/subdomain.py` |
| **waf** | WAF检测 | `waf/waf.py` |
| **webside** | 网站信息检测 | `webside/webside.py` |
| **webweight** | 网站权重查询 | `webweight/webweight.py` |
| **whatcms** | CMS识别 | `whatcms/whatcms.py` |

## 核心功能说明

### 1. 网站基础信息收集 (baseinfo)
- 收集网站的服务器类型、编程语言、框架等信息
- 识别网站使用的技术栈

### 2. CDN存在检测 (cdnexist)
- 检测目标网站是否使用了CDN服务
- 帮助分析网站的真实服务器位置

### 3. 信息泄露检测 (infoleak)
- 扫描常见的信息泄露点
- 检测敏感文件和目录

### 4. IP地址定位 (iplocating)
- 根据IP地址获取地理位置信息
- 提供IP所属国家、地区等详细信息

### 5. 端口扫描 (portscan)
- 扫描目标服务器开放的端口
- 识别可能的服务和漏洞入口

### 6. 子域名枚举 (subdomain)
- 枚举目标域名的子域名
- 发现更多潜在的攻击面

### 7. WAF检测 (waf)
- 检测网站是否部署了WAF(Web应用防火墙)
- 识别WAF的类型和厂商

### 8. 网站权重查询 (webweight)
- 查询域名的百度权重(PC端和移动端)
- 使用爱站网API进行查询
- 支持域名格式校验和提取

### 9. CMS识别 (whatcms)
- 识别网站使用的内容管理系统
- 帮助分析可能的漏洞和安全问题

## 依赖项

- Python 3.7+
- requests: 用于HTTP请求
- 各模块可能有额外的依赖，具体请参考各模块的实现文件

## 使用方法

### 导入单个插件

```python
# 示例：导入网站权重查询插件
from backend.plugins.webweight.webweight import get_web_weight

# 使用示例
domain = "https://www.baidu.com"
result = get_web_weight(domain)
print(result)
```

### 模块调用示例

#### 1. 网站权重查询

```python
from backend.plugins.webweight.webweight import get_web_weight

# 标准化返回格式
result = get_web_weight("https://jwt1399.top/")
print(f"查询结果: {result['result']}")
print(f"是否成功: {result['success']}")
print(f"详细信息: {result['message']}")

# 兼容原代码格式
from backend.plugins.webweight.webweight import get_web_weight_compat
result_compat = get_web_weight_compat("https://jwt1399.top/")
print(f"兼容格式结果: {result_compat}")
```

#### 2. IP地址定位

```python
from backend.plugins.iplocating.iplocating import get_ip_location

ip = "8.8.8.8"
location = get_ip_location(ip)
print(f"IP {ip} 的位置: {location}")
```

## 插件开发规范

### 新增插件的步骤

1. 在 `plugins` 目录下创建新的子目录，命名为插件名称
2. 在子目录中创建 `__init__.py` 文件（可以为空）
3. 创建插件的主要实现文件，命名为 `[插件名称].py`
4. 实现核心功能函数，并提供清晰的文档字符串
5. 添加必要的依赖项说明

### 代码规范

- 使用 UTF-8 编码
- 遵循 PEP 8 代码风格
- 提供详细的文档字符串
- 实现错误处理和异常捕获
- 考虑网络波动等情况，添加超时和重试机制

## 注意事项

1. **API密钥管理**：部分插件使用了第三方API（如爱站网API），请妥善保管API密钥
2. **网络请求**：插件会发起网络请求，请确保网络连接正常
3. **速率限制**：使用第三方API时，请注意API的速率限制，避免频繁请求导致被封禁
4. **法律合规**：使用插件进行检测时，请确保遵守相关法律法规，仅对授权的目标进行检测

## 版本历史

- **v1.0.0**：初始版本，包含基础插件模块
- **v1.1.0**：优化了部分插件的性能和稳定性
- **v1.2.0**：新增了部分插件模块，完善了文档

## 贡献指南

欢迎提交Issue和Pull Request，共同改进插件功能。提交代码时，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 联系信息

如有问题或建议，请联系项目维护者。

---

*本文档由 AI_WebSecurity 项目组维护*
*最后更新时间：2026-01-22*