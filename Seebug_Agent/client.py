"""
Seebug API客户端

提供Seebug漏洞查询功能，支持API和网页爬取两种模式。
"""
import requests
import json
import re
from typing import Optional, Dict, Any, List
from config import Config

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


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

    def _search_poc_web(self, keyword: str, page: int = 1) -> Dict[str, Any]:
        """
        网页爬取模式搜索POC
        
        Args:
            keyword: 搜索关键词
            page: 页码 (默认为1)
            
        Returns:
            搜索结果
        """
        web_search_url = "https://www.seebug.org/search/"
        # 如果关键词为空，使用漏洞列表页（支持分页）
        if not keyword:
            web_search_url = "https://www.seebug.org/vuldb/vulnerabilities"
            
        params = {"keywords": keyword, "page": page}
        if not keyword:
            params = {"page": page}
        
        try:
            response = requests.get(
                web_search_url,
                params=params,
                headers=self.web_headers,
                timeout=self.config.SEEBUG_TIMEOUT
            )
            if response.status_code == 200:
                html = response.text
                results = []
                
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(html, 'html.parser')
                    # Find all links that match SSVID pattern AND have class 'vul-title'
                    # This ensures we get the link with the real title, not the SSV-ID link
                    links = soup.find_all('a', href=re.compile(r'/vuldb/ssvid-\d+'), class_='vul-title')
                    seen_ssvids = set()
                    
                    for link in links:
                        href = link.get('href')
                        match = re.search(r'ssvid-(\d+)', href)
                        if not match:
                            continue
                            
                        ssvid = match.group(1)
                        if ssvid in seen_ssvids:
                            continue
                        seen_ssvids.add(ssvid)
                        
                        title = link.get('title') or link.text.strip()
                        if not title:
                            continue
                            
                        # Try to extract level/date if they are in parent/siblings
                        # Usually Seebug list has structure: <tr><td><a ...>SSV-ID</a></td><td>Date</td><td>Level</td>...<td>Title</td></tr>
                        # Since we are now at Title (4th column usually), we need to look back or find parent row
                        level = "Unknown"
                        submit_time = ""
                        
                        try:
                            row = link.find_parent('tr')
                            if row:
                                cols = row.find_all('td')
                                # Structure: [SSV-ID, Date, Level, Title, CVE/POC]
                                if len(cols) >= 3:
                                    # Date is usually 2nd column (index 1)
                                    submit_time = cols[1].text.strip()
                                    # Level is usually 3rd column (index 2)
                                    level = cols[2].text.strip()
                        except:
                            pass

                        results.append({
                            "id": ssvid,
                            "ssvid": ssvid,
                            "name": title,
                            "vul_name": title,
                            "submit_time": submit_time,
                            "level": level,
                            "type": "Web Vulnerability"
                        })
                else:
                    # Fallback to regex if BS4 not available
                    pattern = re.compile(
                        r'href="/vuldb/ssvid-(\d+)">SSV-\d+</a>.*?class="vul-title"\s+title="(.*?)"',
                        re.DOTALL
                    )
                    matches = pattern.findall(html)
                    
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
                
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract Title
                    title_tag = soup.find('h1', class_='vul-title')
                    if title_tag:
                        # Remove any child tags like small (SSV-ID)
                        for child in title_tag.find_all('small'):
                            child.decompose()
                        title = title_tag.text.strip()
                    else:
                        title_match = re.search(r'<title>(.*?) - Seebug 漏洞平台</title>', html)
                        title = title_match.group(1) if title_match else f"SSVID-{ssvid_str}"

                    data = {
                        "name": title,
                        "vul_name": title,
                        "ssvid": ssvid_str,
                        "type": "Web Vulnerability",
                        "component": "Unknown",
                        "description": "",
                        "solution": "",
                        "cve_id": "",
                        "cnvd_id": "",
                        "cvss_score": 0.0,
                        "level": "Unknown",
                        "submit_time": ""
                    }
                    
                    # Extract Info Fields from dl-horizontal or similar list
                    # Seebug typically uses <dl class="dl-horizontal"> or similar
                    for dt in soup.find_all('dt'):
                        key = dt.text.strip()
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            val = dd.text.strip()
                            # Clean up value (remove extra spaces/newlines)
                            val = re.sub(r'\s+', ' ', val).strip()
                            
                            if 'CNVD' in key:
                                data['cnvd_id'] = val
                            elif 'CVE' in key:
                                data['cve_id'] = val
                            elif '发布时间' in key or 'Time' in key:
                                data['submit_time'] = val
                            elif '危害级别' in key or 'Level' in key:
                                data['level'] = val
                            elif 'CVSS' in key:
                                try:
                                    # Extract number from string like "9.8 (High)"
                                    score_match = re.search(r'(\d+(\.\d+)?)', val)
                                    if score_match:
                                        data['cvss_score'] = float(score_match.group(1))
                                except:
                                    pass
                            elif '组件' in key or 'Component' in key:
                                data['product'] = val
                                data['component'] = val

                    # Extract Description and Solution
                    # Look for section headers
                    for header in soup.find_all(['h3', 'h4', 'div']):
                        header_text = header.text.strip()
                        if header.name in ['h3', 'h4'] or (header.name == 'div' and 'header' in header.get('class', [])):
                            if '漏洞概要' in header_text or '漏洞详情' in header_text or 'Summary' in header_text:
                                content_div = header.find_next_sibling('div')
                                if content_div:
                                    data['description'] = content_div.text.strip()
                            elif '解决方案' in header_text or 'Solution' in header_text:
                                content_div = header.find_next_sibling('div')
                                if content_div:
                                    data['solution'] = content_div.text.strip()
                    
                    # If description is still empty, try to find meta description
                    if not data['description']:
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc:
                            data['description'] = meta_desc.get('content', '')

                    return {
                        "status": "success",
                        "data": data
                    }

                else:
                    # Fallback to regex
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
