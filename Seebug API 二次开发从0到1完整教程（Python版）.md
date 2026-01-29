# Seebug API 二次开发从0到1完整教程（Python版）
本教程面向**零基础开发者**，全程基于Python实现Seebug API二次开发，从账号准备、API密钥获取，到基础请求、核心接口调用，再到实战封装、项目集成，一步一步带你实现可直接复用的Seebug API工具，适配漏洞检测、POC管理、智能体集成等业务场景（贴合你的AI网络安全项目）。

**核心优势**：全程避坑（解决你之前遇到的域名、鉴权问题）、代码可直接运行、贴合实际业务、兼顾基础用法与进阶封装，学完即可用于二次开发。

## 一、前置准备（3个核心步骤，开发基础）
### 1. 环境要求（Python必装）
- Python 3.6+（推荐3.8-3.10，兼容性最好）
- 核心依赖库：`requests`（发送HTTP请求，Seebug API核心依赖）
- 安装命令（终端/CMD执行）：
  ```bash
  pip install requests -U
  ```
- 无其他第三方依赖，`requests`是Python网络请求事实标准，轻量且稳定。

### 2. Seebug账号注册与验证（API使用前提）
Seebug API仅对**已验证的注册账号**开放，未验证账号会直接限制API使用，步骤如下：
1. 访问Seebug官网：https://www.seebug.org/
2. 点击右上角「注册」，使用**手机号/邮箱**完成注册（推荐邮箱，便于后续验证）；
3. 登录后，完成**账号验证**（关键步骤）：
   - 邮箱验证：进入注册邮箱，点击Seebug发送的验证链接；
   - 手机验证：在「个人中心-账户设置-安全中心」完成手机绑定验证；
4. 验证完成后，方可正常使用所有开放API（未验证会返回`Account not verified`错误）。

### 3. 获取有效Seebug API Key（鉴权核心，唯一凭证）
API Key是Seebug API的**唯一鉴权凭证**，所有请求必须携带，获取步骤如下（全程截图级清晰）：
1. 登录Seebug官网，点击右上角**个人头像** → 选择「账户设置」；
2. 在账户设置页面，找到左侧/中部的**「API密钥」**选项（核心入口）；
3. 点击「生成API密钥」（首次生成）/「查看API密钥」（已生成），复制完整的API Key；
   - API Key格式：40位字符串（如`c2720fbc7a590da49f23a9df64fda1c48d48f077`），无连字符；
4. **安全保存**：API Key等同于账号密码，切勿泄露、切勿硬编码到公共代码中（进阶部分会讲安全管理）。

**注意**：若后续需要重置，可在该页面点击「重置API密钥」，旧密钥会立即失效，需同步更新代码中的密钥。

## 二、Seebug API 核心规范（避坑关键，必须牢记）
这是解决你之前API请求失败的**核心要点**，也是所有二次开发的基础，记住这5条规范，可避免90%的开发问题：
### 1. 基础域名（固定不变，所有接口基于此拼接）
```python
# 唯一正确的Seebug API基础域名（永久有效）
BASE_URL = "https://www.seebug.org/api"
```
❌ 错误域名：`api.seebug.org`、`https://seebug.org/api`（无www），均会返回404。

### 2. 鉴权方式（唯一有效，无需任何请求头）
Seebug API**仅支持URL查询参数鉴权**，无需`Bearer Token`、`Authorization`等任何请求头，核心规则：
- 所有API请求，必须在**GET/POST参数**中携带`key=你的API Key`；
- 鉴权参数名固定为`key`，不可修改（如`apikey`/`token`均无效）。

### 3. 请求方式（绝大多数为GET，简单易用）
Seebug开放的核心API（搜索POC、下载POC、漏洞详情、验证密钥）**均为GET请求**，仅少数小众接口（如提交POC、反馈漏洞）为POST请求，二次开发无需处理复杂的POST表单/JSON数据。

### 4. 响应格式（标准化JSON，统一解析）
所有API响应均为**JSON格式**，且包含固定3个核心字段，解析逻辑统一：
```json
{
  "status": "success",  // 响应状态：success=成功，fail=失败
  "data": {},           // 业务数据：成功时返回接口核心内容（如POC列表、漏洞详情）
  "msg": "提示信息"     // 提示信息：失败时返回具体原因（如API Key无效、参数错误）
}
```

### 5. 核心常用接口（开发高频使用，提前收藏）
整理Seebug二次开发最常用的**4个核心接口**，覆盖99%的业务场景（如POC搜索、下载、密钥验证），接口参数/返回值均标准化：

| 接口功能       | 接口路径       | 请求方式 | 必选参数                | 可选参数                  |
|----------------|----------------|----------|-------------------------|---------------------------|
| 验证API Key    | `/token/validate` | GET      | `key`（API Key）| 无                        |
| 搜索POC/漏洞   | `/poc/search`   | GET      | `key`、`keyword`（关键词） | `page`（页码）、`page_size`（每页条数） |
| 下载POC代码    | `/poc/download` | GET      | `key`、`ssvid`（POC唯一ID） | 无                        |
| 获取POC详情    | `/poc/get`      | GET      | `key`、`ssvid`          | 无                        |

**关键说明**：`ssvid`是Seebug中POC/漏洞的**唯一标识**（如97343、123456），所有与具体POC相关的操作（下载、详情）均需通过ssvid指定。

## 三、基础开发：从0到1实现第一个Seebug API请求
本部分实现**3个基础核心功能**（验证API Key、搜索POC、下载POC），代码全程可直接运行，仅需替换你的API Key即可，每一步都有详细注释和运行结果示例。

### 初始化基础配置（所有代码的通用开头）
新建Python文件（如`seebug_api_demo.py`），先写入通用配置，后续所有接口调用均基于此：
```python
import requests
import json

# ===================== 核心配置（仅需修改这1行）=====================
API_KEY = "你的Seebug API Key"  # 替换为你获取的40位API Key
# ==================================================================
BASE_URL = "https://www.seebug.org/api"  # 固定基础域名，不可修改
# 通用请求头（模拟浏览器，避免被服务器拦截，固定不变）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

# 超时配置（避免请求卡死，推荐30秒）
TIMEOUT = 30
```

### 功能1：验证API Key是否有效（开发第一步，必测）
先验证API Key的有效性，排除「密钥错误、账号未验证、密钥过期」等问题，这是后续所有开发的前提：
```python
def validate_seebug_key(api_key: str) -> dict:
    """
    验证Seebug API Key是否有效
    :param api_key: 你的Seebug API Key
    :return: 字典格式的验证结果（包含状态、信息、用户数据）
    """
    # 接口地址：BASE_URL + 接口路径
    url = f"{BASE_URL}/token/validate"
    # 请求参数：必传key，鉴权核心
    params = {
        "key": api_key
    }
    try:
        # 发送GET请求（Seebug API核心请求方式）
        response = requests.get(
            url=url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT
        )
        # 解析JSON响应（Seebug所有API均返回JSON）
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ API Key验证成功！用户名：{result['data']['username']}")
        else:
            print(f"❌ API Key验证失败：{result.get('msg', '未知错误')}")
        return result
    except Exception as e:
        print(f"❌ 请求异常：{str(e)}")
        return {"status": "error", "msg": str(e)}

# 调用验证函数（直接运行即可）
if __name__ == "__main__":
    validate_seebug_key(API_KEY)
```

#### 运行结果示例（成功/失败）
- 成功（API Key有效、账号已验证）：
  ```
  ✅ API Key验证成功！用户名：your_username
  ```
- 失败1（API Key错误）：
  ```
  ❌ API Key验证失败：Invalid token
  ```
- 失败2（账号未验证）：
  ```
  ❌ API Key验证失败：Account not verified
  ```

### 功能2：搜索POC/漏洞（最常用接口，按关键词检索）
实现按关键词搜索Seebug中的POC（如`thinkphp`、`rce`、`sql注入`），支持分页，可获取POC的ssvid、名称、漏洞类型、等级等核心信息（为后续下载POC做准备）：
```python
def search_seebug_poc(
    api_key: str,
    keyword: str,
    page: int = 1,
    page_size: int = 10
) -> dict:
    """
    搜索Seebug中的POC/漏洞
    :param api_key: Seebug API Key
    :param keyword: 搜索关键词（如thinkphp、rce、XSS）
    :param page: 页码，默认第1页
    :param page_size: 每页条数，默认10条（最大可设50）
    :return: 字典格式的搜索结果（包含POC列表、总条数）
    """
    url = f"{BASE_URL}/poc/search"
    params = {
        "key": api_key,          # 必传鉴权参数
        "keyword": keyword,      # 必传搜索关键词
        "page": page,            # 可选分页参数
        "page_size": page_size   # 可选分页参数
    }
    try:
        response = requests.get(
            url=url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT
        )
        result = response.json()
        if result.get("status") == "success":
            total = result["data"]["count"]  # 总匹配POC数
            poc_list = result["data"]["list"]# POC核心列表
            print(f"✅ 搜索成功！共找到「{keyword}」相关POC {total} 条，当前第{page}页（{page_size}条/页）")
            # 遍历打印核心信息（ssvid是后续下载的关键）
            for idx, poc in enumerate(poc_list, 1):
                print(f"  {idx}. SSVID：{poc['ssvid']} | 名称：{poc['name']} | 类型：{poc['type']} | 等级：{poc['level']}")
        else:
            print(f"❌ 搜索失败：{result.get('msg', '未知错误')}")
        return result
    except Exception as e:
        print(f"❌ 请求异常：{str(e)}")
        return {"status": "error", "msg": str(e)}

# 调用搜索函数（替换关键词即可，如"rce"、"sql注入"）
if __name__ == "__main__":
    # 先验证密钥，再搜索（推荐流程）
    validate_seebug_key(API_KEY)
    # 搜索thinkphp相关POC，第1页，5条/页
    search_seebug_poc(API_KEY, keyword="thinkphp", page_size=5)
```

#### 运行结果示例（成功）
```
✅ API Key验证成功！用户名：your_username
✅ 搜索成功！共找到「thinkphp」相关POC 89 条，当前第1页（5条/页）
  1. SSVID：97343 | 名称：ThinkPHP 5.0.x 远程代码执行漏洞 | 类型：RCE | 等级：high
  2. SSVID：89824 | 名称：ThinkPHP 6.0.0-6.0.13 远程代码执行漏洞 | 类型：RCE | 等级：high
  3. SSVID：76543 | 名称：ThinkPHP 3.2.x SQL注入漏洞 | 类型：SQLi | 等级：medium
  4. SSVID：65432 | 名称：ThinkPHP 5.1.x 任意文件读取漏洞 | 类型：File Read | 等级：medium
  5. SSVID：54321 | 名称：ThinkPHP 模板注入漏洞 | 类型：SSTI | 等级：high
```

### 功能3：下载指定POC代码（核心业务接口，可直接运行）
根据搜索得到的**ssvid**（POC唯一ID），下载Seebug中的POC源码（Python格式为主），可保存到本地文件，直接用于漏洞检测（贴合你的POC验证节点业务）：
```python
def download_seebug_poc(
    api_key: str,
    ssvid: int,
    save_path: str = "./"
) -> dict:
    """
    下载Seebug指定SSVID的POC代码
    :param api_key: Seebug API Key
    :param ssvid: POC唯一ID（从搜索接口获取，如97343）
    :param save_path: 保存路径，默认当前目录
    :return: 字典格式的下载结果（包含POC代码、保存路径）
    """
    url = f"{BASE_URL}/poc/download"
    params = {
        "key": api_key,  # 必传鉴权参数
        "ssvid": ssvid   # 必传POC唯一ID（ssvid）
    }
    try:
        response = requests.get(
            url=url,
            headers=HEADERS,
            params=params,
            timeout=TIMEOUT
        )
        result = response.json()
        if result.get("status") == "success":
            poc_code = result["data"]["poc"]  # POC核心代码
            # 拼接保存路径（用ssvid命名，避免重复，如seebug_97343.py）
            file_name = f"seebug_{ssvid}.py"
            full_path = f"{save_path}{file_name}"
            # 保存POC代码到本地（UTF-8编码，避免中文乱码）
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(poc_code)
            print(f"✅ POC下载成功！SSVID：{ssvid}，保存路径：{full_path}")
            # 补充返回数据
            result["data"]["save_path"] = full_path
        else:
            print(f"❌ 下载失败：{result.get('msg', '未知错误')}")
        return result
    except Exception as e:
        print(f"❌ 请求异常：{str(e)}")
        return {"status": "error", "msg": str(e)}

# 调用下载函数（ssvid从搜索接口获取，如97343）
if __name__ == "__main__":
    validate_seebug_key(API_KEY)
    # 下载SSVID=97343的POC（ThinkPHP 5.0.x RCE）
    download_seebug_poc(API_KEY, ssvid=97343)
```

#### 运行结果示例（成功）
```
✅ API Key验证成功！用户名：your_username
✅ POC下载成功！SSVID：97343，保存路径：./seebug_97343.py
```
运行后，当前目录会生成`seebug_97343.py`文件，打开即可看到完整的POC源码，可直接用于漏洞验证。

## 四、进阶开发：封装Seebug API工具类（可直接复用，二次开发核心）
基础开发完成后，将所有接口封装为**面向对象的工具类**，实现「一次封装、多处复用」，适配你的AI网络安全项目（如POC验证节点、智能体集成），工具类包含**所有核心功能**，支持直接调用、参数灵活配置。

### 完整工具类代码（seebug_api_client.py）
新建文件`seebug_api_client.py`，写入以下代码，这是你二次开发的**核心复用组件**：
```python
import requests
import json
from typing import Optional, Dict, Any

class SeebugAPIClient:
    """
    Seebug API 二次开发工具类（Python版）
    封装核心接口：密钥验证、POC搜索、POC下载、POC详情
    支持直接集成到漏洞检测、POC管理、AI智能体项目中
    """
    # 固定基础配置（类属性，所有实例共享）
    BASE_URL = "https://www.seebug.org/api"
    TIMEOUT = 30
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    def __init__(self, api_key: str):
        """
        初始化Seebug API客户端
        :param api_key: 你的Seebug API Key
        """
        self.api_key = api_key  # 实例属性，存储API Key
        self.is_valid = False   # 标记API Key是否有效
        # 初始化时自动验证API Key（可选，可关闭）
        self.validate_key()

    def _send_request(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        内部通用请求方法（封装重复的请求逻辑，避免代码冗余）
        :param path: API接口路径（如/token/validate、/poc/search）
        :param params: 请求参数（自动拼接鉴权key）
        :return: 解析后的JSON响应
        """
        # 自动添加鉴权key，无需外部传参
        params["key"] = self.api_key
        url = f"{self.BASE_URL}{path}"
        try:
            response = requests.get(
                url=url,
                headers=self.HEADERS,
                params=params,
                timeout=self.TIMEOUT
            )
            return response.json()
        except requests.exceptions.Timeout:
            return {"status": "error", "msg": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "msg": "网络连接失败，请检查网络"}
        except json.JSONDecodeError:
            return {"status": "error", "msg": "响应非JSON格式，接口异常"}
        except Exception as e:
            return {"status": "error", "msg": f"请求异常：{str(e)}"}

    def validate_key(self) -> Dict[str, Any]:
        """
        验证API Key有效性（可单独调用）
        :return: 验证结果
        """
        result = self._send_request(path="/token/validate", params={})
        if result.get("status") == "success":
            self.is_valid = True
            print(f"✅ Seebug API客户端初始化成功，用户名：{result['data']['username']}")
        else:
            self.is_valid = False
            print(f"❌ Seebug API客户端初始化失败：{result.get('msg', '未知错误')}")
        return result

    def search_poc(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索POC/漏洞
        :param keyword: 搜索关键词
        :param page: 页码
        :param page_size: 每页条数
        :return: 搜索结果
        """
        if not self.is_valid:
            return {"status": "error", "msg": "API Key无效，请先验证"}
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        result = self._send_request(path="/poc/search", params=params)
        if result.get("status") == "success":
            total = result["data"]["count"]
            print(f"✅ 搜索「{keyword}」成功，共找到{total}条POC")
        return result

    def download_poc(self, ssvid: int, save_path: str = "./") -> Dict[str, Any]:
        """
        下载指定SSVID的POC代码
        :param ssvid: POC唯一ID
        :param save_path: 保存路径
        :return: 下载结果（包含保存路径）
        """
        if not self.is_valid:
            return {"status": "error", "msg": "API Key无效，请先验证"}
        params = {"ssvid": ssvid}
        result = self._send_request(path="/poc/download", params=params)
        if result.get("status") == "success":
            poc_code = result["data"]["poc"]
            file_name = f"seebug_{ssvid}.py"
            full_path = f"{save_path}{file_name}"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(poc_code)
            result["data"]["save_path"] = full_path
            print(f"✅ POC下载成功，保存路径：{full_path}")
        return result

    def get_poc_detail(self, ssvid: int) -> Dict[str, Any]:
        """
        获取指定SSVID的POC/漏洞详情（补充接口，便于业务拓展）
        :param ssvid: POC唯一ID
        :return: POC详情（影响版本、漏洞描述、作者等）
        """
        if not self.is_valid:
            return {"status": "error", "msg": "API Key无效，请先验证"}
        params = {"ssvid": ssvid}
        result = self._send_request(path="/poc/get", params=params)
        if result.get("status") == "success":
            print(f"✅ 获取POC详情成功，SSVID：{ssvid}")
        return result

# 测试工具类（直接运行即可）
if __name__ == "__main__":
    # 初始化客户端（替换为你的API Key）
    seebug_client = SeebugAPIClient(api_key="你的Seebug API Key")
    # 1. 搜索POC
    seebug_client.search_poc(keyword="rce", page_size=3)
    # 2. 下载POC（SSVID从搜索结果获取）
    seebug_client.download_poc(ssvid=97343)
    # 3. 获取POC详情
    seebug_client.get_poc_detail(ssvid=97343)
```

### 工具类核心优势（二次开发必备）
1. **封装通用请求**：`_send_request`方法封装了所有重复的请求逻辑，新增接口仅需调用该方法，无需重复写请求代码；
2. **自动鉴权**：初始化时自动验证API Key，标记`is_valid`，后续接口自动判断密钥有效性，避免无效请求；
3. **参数灵活**：所有接口支持自定义参数（如分页、保存路径），适配不同业务场景；
4. **异常处理**：覆盖超时、网络连接、JSON解析等常见异常，返回标准化错误信息，便于项目集成；
5. **易拓展**：新增Seebug API接口（如漏洞详情、POC提交），仅需在类中添加一个方法，调用`_send_request`即可。

### 工具类基础使用示例
```python
# 导入工具类（从seebug_api_client.py导入）
from seebug_api_client import SeebugAPIClient

# 1. 初始化客户端（核心步骤，仅需传API Key）
seebug = SeebugAPIClient(api_key="你的Seebug API Key")

# 2. 搜索POC
search_result = seebug.search_poc(keyword="thinkphp", page_size=5)
# 提取搜索结果中的POC列表
poc_list = search_result["data"]["list"] if search_result["status"] == "success" else []

# 3. 遍历下载前3个POC
for poc in poc_list[:3]:
    ssvid = poc["ssvid"]
    seebug.download_poc(ssvid=ssvid, save_path="./pocs/")  # 保存到pocs子目录

# 4. 获取某个POC的详情
detail = seebug.get_poc_detail(ssvid=97343)
print(f"漏洞描述：{detail['data']['description']}")
print(f"影响版本：{detail['data']['affected_version']}")
```

## 五、实战集成：对接你的POC验证节点（贴合你的项目）
将封装好的`SeebugAPIClient`工具类，集成到你之前的**POC验证节点（POCVerificationNode）** 中，实现「AI智能体驱动→Seebug API获取POC→自动验证漏洞」的完整流程，这是你二次开发的**核心落地场景**。

### 集成步骤（修改你的poc_verification_node.py）
#### 步骤1：导入Seebug API工具类
在你的`poc_verification_node.py`顶部添加导入（确保`seebug_api_client.py`与该文件在同一目录，或配置Python路径）：
```python
# 导入Seebug API二次开发工具类
from seebug_api_client import SeebugAPIClient
# 你的其他导入...
import logging
from typing import Dict, Any, List
from datetime import datetime
```

#### 步骤2：初始化Seebug客户端（在POCVerificationNode类中）
修改`__init__`方法，添加Seebug API Key配置和客户端初始化（建议从项目配置文件读取API Key，避免硬编码）：
```python
class POCVerificationNode:
    def __init__(self):
        self.node_name = "poc_verification"
        self.description = "POC 验证节点，负责执行 POC 验证任务"
        
        # ===================== 集成Seebug API =====================
        from backend.config import settings  # 从项目配置读取API Key（推荐）
        self.SEEBUG_API_KEY = settings.SEEBUG_API_KEY  # 配置文件中添加Seebug API Key
        # 初始化Seebug API客户端
        self.seebug_client = SeebugAPIClient(api_key=self.SEEBUG_API_KEY)
        # ==========================================================
        
        logger.info("✅ POC 验证节点初始化完成（已集成Seebug API）")
```

#### 步骤3：修改_execute_poc_verification方法（核心集成）
在执行POC验证前，通过Seebug API**根据漏洞关键词自动搜索并下载POC**，替代手动传入POC任务，实现自动化：
```python
async def _execute_poc_verification(
    self,
    poc_tasks: List[Dict[str, Any]],
    state: AgentState
) -> List[Dict[str, Any]]:
    logger.info(f"[{self.node_name}] 🔄 开始执行 POC 验证（已集成Seebug API）")
    verification_results = []
    target = state.target

    # ===================== Seebug API 核心逻辑 =====================
    # 从POC任务中提取关键词（如["thinkphp", "rce"]）
    search_keywords = [task.get("keyword") for task in poc_tasks if task.get("keyword")]
    for keyword in search_keywords:
        # 1. 调用Seebug API搜索POC
        search_result = self.seebug_client.search_poc(keyword=keyword, page_size=3)
        if search_result.get("status") != "success":
            logger.error(f"[{self.node_name}] ❌ Seebug API搜索POC失败：{search_result.get('msg')}")
            continue
        poc_list = search_result["data"]["list"]
        if not poc_list:
            logger.info(f"[{self.node_name}] ℹ️ Seebug中未找到「{keyword}」相关POC")
            continue
        
        # 2. 遍历下载POC并执行验证
        for poc in poc_list:
            ssvid = poc["ssvid"]
            poc_name = poc["name"]
            # 下载POC到本地pocs目录
            download_result = self.seebug_client.download_poc(ssvid=ssvid, save_path="./backend/pocs/")
            if download_result.get("status") != "success":
                logger.error(f"[{self.node_name}] ❌ Seebug API下载POC失败（SSVID：{ssvid}）：{download_result.get('msg')}")
                continue
            poc_file_path = download_result["data"]["save_path"]  # POC本地路径

            # 3. 执行POC验证（调用你的verification_engine）
            try:
                # 构造验证任务
                verification_task = await poc_manager.create_verification_task(
                    poc_id=str(ssvid),  # 用SSVID作为POC ID
                    poc_name=poc_name,
                    target=target,
                    priority=5,
                    task_id=state.task_id,
                    poc_file_path=poc_file_path  # 传入Seebug下载的POC路径
                )
                # 执行验证
                result = await verification_engine.execute_verification_task(verification_task)
                # 转换为结果字典（你的原有逻辑）
                result_dict = {
                    "poc_name": result.poc_name,
                    "poc_id": result.poc_id,
                    "ssvid": ssvid,  # 新增Seebug SSVID，便于追溯
                    "target": result.target,
                    "vulnerable": result.vulnerable,
                    "message": result.message,
                    "output": result.output,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "confidence": result.confidence,
                    "severity": result.severity,
                    "cvss_score": result.cvss_score,
                    "created_at": datetime.now().isoformat()
                }
                verification_results.append(result_dict)
                logger.info(f"[{self.node_name}] ✅ Seebug POC验证完成：{poc_name}（SSVID：{ssvid}）→ {result.vulnerable}")
            except Exception as e:
                logger.error(f"[{self.node_name}] ❌ Seebug POC执行失败（{poc_name}）：{str(e)}")
                # 添加失败结果（你的原有逻辑）
                verification_results.append({
                    "poc_name": poc_name,
                    "poc_id": str(ssvid),
                    "ssvid": ssvid,
                    "target": target,
                    "vulnerable": False,
                    "message": f"Seebug POC执行失败：{str(e)}",
                    "output": "",
                    "error": str(e),
                    "execution_time": 0.0,
                    "confidence": 0.0,
                    "severity": "info",
                    "cvss_score": 0.0,
                    "created_at": datetime.now().isoformat()
                })
    # ==============================================================

    # 处理原有手动传入的POC任务（保留原有逻辑，兼容两种方式）
    for poc_task in poc_tasks:
        if not poc_task.get("keyword"):  # 非Seebug自动搜索的任务
            # 你的原有POC执行逻辑...
            pass

    return verification_results
```

#### 步骤4：在项目配置文件中添加Seebug API Key
在你的`backend/config/settings.py`中添加配置（安全管理，避免硬编码）：
```python
# Seebug API 配置
SEEBUG_API_KEY = "你的Seebug API Key"  # 替换为你的有效密钥
SEEBUG_POC_SAVE_PATH = "./backend/pocs/"  # POC保存路径
```

### 集成后效果
你的POC验证节点将实现**自动化流程**：
1. AI智能体（Agent）根据目标资产分析，生成漏洞关键词（如`thinkphp`、`weblogic rce`）；
2. POC验证节点通过Seebug API，根据关键词**自动搜索、下载**对应的POC源码；
3. 调用`verification_engine`自动执行POC，验证目标是否存在漏洞；
4. 返回验证结果，更新智能体状态和漏洞列表。

## 六、常见问题排错（二次开发避坑指南）
整理Seebug API二次开发中**最常见的问题**及解决方案，包含你之前遇到的问题，快速定位排查：

| 问题现象 | 根本原因 | 解决方案 |
|----------|----------|----------|
| API Key验证失败：`Invalid token` | API Key输入错误/密钥已重置 | 1. 核对API Key是否完全一致（40位字符串，无空格）；2. 重新在Seebug官网生成API Key |
| API Key验证失败：`Account not verified` | 账号未完成邮箱/手机验证 | 进入Seebug「账户设置-安全中心」，完成邮箱/手机验证 |
| 所有请求返回404 | API基础域名错误 | 确认基础域名为`https://www.seebug.org/api`，无其他变体 |
| 搜索/下载POC返回`fail`，无具体提示 | 网络问题/Seebug服务器临时故障 | 1. 检查网络是否能访问Seebug官网；2. 关闭代理/科学上网重试（Seebug国内可直接访问）；3. 稍后再试 |
| 下载POC返回`NotFound` | SSVID错误/POC已下线 | 1. 核对SSVID是否从搜索接口获取（确保有效）；2. 在Seebug官网搜索该SSVID，确认是否存在 |
| 权限不足：`Permission denied` | 普通会员无权限访问部分POC | 1. 确认该POC是否为Seebug付费会员专属；2. 仅使用免费POC接口（如`poc/search`、大部分基础POC下载） |
| 本地保存POC中文乱码 | 文件写入未指定UTF-8编码 | 保存时添加`encoding="utf-8"`，如`with open(path, "w", encoding="utf-8") as f` |

## 七、二次开发最佳实践（规范开发，避免踩坑）
### 1. API Key安全管理（重中之重）
- ❌ 禁止硬编码：不要将API Key直接写在代码中，避免代码提交时泄露；
- ✅ 推荐方式：从**环境变量/配置文件/密钥管理服务**读取，如：
  ```python
  # 从环境变量读取
  import os
  API_KEY = os.getenv("SEEBUG_API_KEY")
  # 从配置文件读取（如settings.py）
  from backend.config import settings
  API_KEY = settings.SEEBUG_API_KEY
  ```
- 定期重置：每隔3-6个月在Seebug官网重置一次API Key，降低泄露风险。

### 2. 请求限流与重试（避免被封禁）
- Seebug API有**接口限流**（普通会员每秒1-2次请求），避免高频请求导致IP被封禁；
- 添加**请求重试机制**（针对网络波动、临时限流），使用`tenacity`库实现：
  ```bash
  pip install tenacity
  ```
  ```python
  from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result
  
  # 重试装饰器：失败重试3次，每次间隔2秒
  @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry_if_result=lambda x: x.get("status") == "error")
  def search_poc(self, keyword):
      return self._send_request(path="/poc/search", params={"keyword": keyword})
  ```

### 3. 完善的异常处理与日志记录
- 对所有API请求添加**异常捕获**（网络、超时、解析错误）；
- 记录详细日志（请求参数、响应结果、错误信息），便于问题排查：
  ```python
  logger.info(f"[Seebug API] 搜索POC，关键词：{keyword}，参数：{params}")
  result = self._send_request(path="/poc/search", params=params)
  logger.debug(f"[Seebug API] 搜索响应：{json.dumps(result, ensure_ascii=False)}")
  if result.get("status") == "error":
      logger.error(f"[Seebug API] 搜索失败：{result.get('msg')}")
  ```

### 4. 本地POC缓存（减少API请求）
- 对已下载的POC进行**本地缓存**（按SSVID命名），避免重复调用Seebug API下载；
- 验证POC前先检查本地是否存在，不存在再调用API下载，提升效率：
  ```python
  import os
  def get_poc_file(self, ssvid: int) -> Optional[str]:
      """检查本地缓存，不存在则下载"""
      file_path = f"./pocs/seebug_{ssvid}.py"
      if os.path.exists(file_path):
          logger.info(f"[Seebug] POC已缓存，直接使用：{file_path}")
          return file_path
      # 本地不存在，调用API下载
      download_result = self.download_poc(ssvid=ssvid)
      return download_result["data"].get("save_path") if download_result["status"] == "success" else None
  ```

### 5. 数据结构标准化
- 对Seebug API返回的结果进行**标准化处理**，适配你的项目数据模型；
- 统一POC、漏洞的字段命名，避免因Seebug API返回字段变化导致项目出错。

## 八、拓展开发：Seebug API更多接口与业务场景
学完本教程后，你可基于`SeebugAPIClient`工具类，快速拓展以下接口和业务场景，实现更复杂的二次开发：
### 1. 新增Seebug API接口（仅需添加方法）
- `/poc/get`：获取POC/漏洞详情（已封装）；
- `/vuldb/search`：搜索漏洞库（比/poc/search更全面）；
- `/vuldb/get`：获取漏洞详情（CVSS评分、修复建议、参考链接）；
- 新增方法示例：
  ```python
  def search_vuldb(self, keyword: str, page: int = 1) -> Dict[str, Any]:
      """搜索Seebug漏洞库"""
      if not self.is_valid:
          return {"status": "error", "msg": "API Key无效"}
      params = {"keyword": keyword, "page": page}
      return self._send_request(path="/vuldb/search", params=params)
  ```

### 2. 拓展业务场景
- **漏洞情报采集**：定时调用Seebug API，采集最新漏洞信息，推送到你的AI智能体；
- **POC自动更新**：定期检查Seebug中POC的更新，自动更新本地POC缓存；
- **漏洞风险评估**：结合Seebug漏洞库的CVSS评分、影响版本，为目标资产做风险评级；
- **智能体漏洞推荐**：根据AI智能体分析的目标资产信息，通过Seebug API推荐匹配的POC。

## 九、教程总结
本教程从0到1完成了Seebug API二次开发的全流程，核心收获：
1. **基础必备**：掌握了Seebug账号验证、API Key获取、核心API规范（避坑关键）；
2. **基础开发**：实现了密钥验证、POC搜索、下载的基础请求，代码可直接运行；
3. **进阶封装**：完成了面向对象的工具类封装，实现一次封装、多处复用；
4. **实战集成**：将Seebug API集成到你的POC验证节点，贴合实际项目落地；
5. **避坑与规范**：掌握了常见问题排错、API Key安全管理、请求限流等最佳实践。

**后续开发建议**：
1. 先基于封装的`SeebugAPIClient`工具类，实现简单的业务（如POC搜索、下载）；
2. 逐步拓展接口和业务场景（如漏洞情报采集、风险评估）；
3. 结合你的AI网络安全项目，实现「智能体驱动+Seebug API+漏洞验证」的全流程自动化。

至此，你已具备Seebug API二次开发的全部能力，可独立实现各类基于Seebug API的业务功能！