"""
Seebug API客户端

提供Seebug漏洞查询功能，支持API和网页爬取两种模式。
"""
import requests
import json
import re
from typing import Optional, Dict, Any, List
from config import Config


class SeebugClient:
    """
    Seebug API客户端
    
    支持两种模式：
    1. API模式：使用Seebug官方API（需要API Key）
    2. 网页爬取模式：当API不可用时自动降级
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化Seebug客户端
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or Config()
        self.api_headers = {
            "User-Agent": "curl/7.80.0",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Token {self.config.SEEBUG_API_KEY}"
        }
        self.web_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.seebug.org/"
        }
        self.is_valid = False
        self.validate_key()

    def _send_request(self, path: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        发送API请求
        
        Args:
            path: API路径
            params: 请求参数
            
        Returns:
            解析后的JSON响应或None
        """
        url = f"{self.config.SEEBUG_BASE_URL}{path}"
        try:
            response = requests.get(
                url=url,
                headers=self.api_headers,
                params=params,
                timeout=self.config.SEEBUG_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return None
        except requests.exceptions.RequestException:
            return None
        except json.JSONDecodeError:
            return None

    def validate_key(self) -> Dict[str, Any]:
        """
        验证API Key
        
        Returns:
            验证结果
        """
        result = self._send_request(path="/user/poc_list", params={})
        
        if result is not None and isinstance(result, list):
            self.is_valid = True
            return {"status": "success", "msg": "Key valid"}
        else:
            self.is_valid = False
            return {"status": "error", "msg": "Key invalid or network error"}

    def _search_poc_web(self, keyword: str) -> Dict[str, Any]:
        """
        网页爬取模式搜索POC
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            搜索结果
        """
        web_search_url = "https://www.seebug.org/search/"
        params = {"keywords": keyword}
        
        try:
            response = requests.get(
                web_search_url,
                params=params,
                headers=self.web_headers,
                timeout=self.config.SEEBUG_TIMEOUT
            )
            if response.status_code == 200:
                html = response.text
                pattern = re.compile(
                    r'href="/vuldb/ssvid-(\d+)">SSV-\d+</a>.*?class="vul-title"\s+title="(.*?)"',
                    re.DOTALL
                )
                matches = pattern.findall(html)
                
                results = []
                for ssvid, title in matches:
                    results.append({
                        "id": ssvid,
                        "ssvid": ssvid,
                        "name": title.strip(),
                        "vul_name": title.strip(),
                        "type": "Web Vulnerability"
                    })
                
                if results:
                    return {
                        "status": "success",
                        "data": {
                            "list": results,
                            "total": len(results)
                        }
                    }
        except Exception:
            pass
            
        return {"status": "error", "msg": "Web search failed"}

    def _get_poc_detail_web(self, ssvid: str) -> Dict[str, Any]:
        """
        网页爬取模式获取POC详情
        
        Args:
            ssvid: POC的SSVID
            
        Returns:
            POC详情
        """
        ssvid_str = str(ssvid).replace('ssvid-', '')
        url = f"https://www.seebug.org/vuldb/ssvid-{ssvid_str}"
        
        try:
            response = requests.get(
                url,
                headers=self.web_headers,
                timeout=self.config.SEEBUG_TIMEOUT
            )
            if response.status_code == 200:
                html = response.text
                title_match = re.search(r'<title>(.*?) - Seebug 漏洞平台</title>', html)
                title = title_match.group(1) if title_match else f"SSVID-{ssvid_str}"
                
                return {
                    "status": "success",
                    "data": {
                        "name": title,
                        "vul_name": title,
                        "description": f"Details for {title} (SSVID-{ssvid_str}).",
                        "ssvid": ssvid_str,
                        "type": "Web Vulnerability",
                        "component": "Unknown"
                    }
                }
        except Exception:
            pass
            
        return {"status": "error", "msg": "Web detail scrape failed"}

    def search_poc(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索POC（优先API，失败则降级到网页爬取）
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        params = {"q": keyword}
        result = self._send_request(path="/user/poc_list", params=params)
        
        if result is not None and isinstance(result, list) and len(result) > 0:
            return {
                "status": "success", 
                "data": {
                    "list": result,
                    "total": len(result)
                }
            }
        
        return self._search_poc_web(keyword)

    def get_poc_detail(self, ssvid: str) -> Dict[str, Any]:
        """
        获取POC详情（优先API，失败则降级到网页爬取）
        
        Args:
            ssvid: POC的SSVID
            
        Returns:
            POC详情
        """
        ssvid_str = str(ssvid).replace('ssvid-', '')
        params = {"id": ssvid_str}
        result = self._send_request(path="/user/poc_detail", params=params)
        
        if result is not None and isinstance(result, dict):
            if 'status' in result and result['status'] is False:
                return self._get_poc_detail_web(ssvid_str)
            return {
                "status": "success", 
                "data": result
            }
            
        return self._get_poc_detail_web(ssvid_str)

    def download_poc(self, ssvid: str, save_path: str = "./") -> Dict[str, Any]:
        """
        下载POC代码
        
        Args:
            ssvid: POC的SSVID
            save_path: 保存路径
            
        Returns:
            下载结果
        """
        ssvid_str = str(ssvid).replace('ssvid-', '')
        detail_result = self.get_poc_detail(ssvid_str)
        
        if detail_result["status"] == "success":
            data = detail_result["data"]
            if "code" in data and data["code"]:
                poc_code = data["code"]
                file_name = f"seebug_{ssvid_str}.py"
                full_path = f"{save_path.rstrip('/')}/{file_name}"
                try:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(poc_code)
                    return {
                        "status": "success", 
                        "data": {
                            "save_path": full_path,
                            "poc": poc_code
                        }
                    }
                except IOError as e:
                    return {"status": "error", "msg": f"File write error: {e}"}
            else:
                return {"status": "error", "msg": "No POC code found in details"}
        
        return detail_result
