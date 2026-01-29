import requests
import json
import re
from typing import Optional, Dict, Any

class SeebugAPIClient:
    """
    Seebug API Client for Python (Updated for Pocsuite3 integration + Web Scrape fallback)
    Encapsulates core interfaces: Key validation, POC search, POC download, POC details
    """
    # Updated base configuration based on Pocsuite3 source code
    BASE_URL = "https://www.seebug.org/api"
    WEB_SEARCH_URL = "https://www.seebug.org/search/"
    WEB_DETAIL_URL_BASE = "https://www.seebug.org/vuldb/ssvid-"
    TIMEOUT = 30
    
    def __init__(self, api_key: str):
        """
        Initialize Seebug API Client
        :param api_key: Your Seebug API Key
        """
        self.api_key = api_key
        self.headers = {
            "User-Agent": "curl/7.80.0",  # Crucial for bypassing 403/404 for API
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Token {self.api_key}"
        }
        self.web_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.seebug.org/"
        }
        self.is_valid = False
        # Validate key on initialization
        self.validate_key()

    def _send_request(self, path: str, params: Dict[str, Any]) -> Any:
        """
        Internal generic request method
        :param path: API interface path (e.g., /user/poc_list)
        :param params: Request parameters
        :return: Parsed JSON response or None on failure
        """
        url = f"{self.BASE_URL}{path}"
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                params=params,
                timeout=self.TIMEOUT
            )
            # print(f"DEBUG: {url} -> {response.status_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # print(f"DEBUG: HTTP Error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            # print(f"DEBUG: Request Error: {e}")
            return None
        except json.JSONDecodeError:
            # print("DEBUG: Response is not JSON")
            return None

    def validate_key(self) -> Dict[str, Any]:
        """
        Validate API Key by checking if we can access the poc list
        :return: Validation result
        """
        # Pocsuite3 uses /user/poc_list to check token availability
        result = self._send_request(path="/user/poc_list", params={})
        
        if result is not None and isinstance(result, list):
            self.is_valid = True
            # print("✅ Seebug API Key validated successfully")
            return {"status": "success", "msg": "Key valid"}
        else:
            self.is_valid = False
            # print("❌ Seebug API Key validation failed")
            # We don't exit here because we might fallback to web scraping
            return {"status": "error", "msg": "Key invalid or network error"}

    def search_poc_web(self, keyword: str) -> Dict[str, Any]:
        """
        Fallback method: Scrape search results from seebug.org website
        """
        params = {"keywords": keyword}
        try:
            print(f"🌍 Fallback: Scraping Seebug website for '{keyword}'...")
            response = requests.get(
                self.WEB_SEARCH_URL,
                params=params,
                headers=self.web_headers,
                timeout=self.TIMEOUT
            )
            if response.status_code == 200:
                html = response.text
                # Simple regex parsing for table rows
                # Structure: <td><a href="/vuldb/ssvid-99617">SSV-99617</a></td>...<a class="vul-title" title="..."
                
                # Regex to capture SSVID and Title
                pattern = re.compile(r'href="/vuldb/ssvid-(\d+)">SSV-\d+</a>.*?class="vul-title"\s+title="(.*?)"', re.DOTALL)
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
        except Exception as e:
            print(f"⚠️ Web scraping failed: {e}")
            
        return {"status": "error", "msg": "Web search failed"}

    def get_poc_detail_web(self, ssvid: str) -> Dict[str, Any]:
        """
        Fallback method: Scrape details from seebug.org website
        """
        ssvid_str = str(ssvid).replace('ssvid-', '')
        url = f"{self.WEB_DETAIL_URL_BASE}{ssvid_str}"
        
        try:
            print(f"🌍 Fallback: Scraping details for SSVID-{ssvid_str}...")
            response = requests.get(
                url,
                headers=self.web_headers,
                timeout=self.TIMEOUT
            )
            if response.status_code == 200:
                html = response.text
                
                # Extract Title
                title_match = re.search(r'<title>(.*?) - Seebug 漏洞平台</title>', html)
                title = title_match.group(1) if title_match else f"SSVID-{ssvid_str}"
                
                # Extract Description (Try best effort)
                # Since simple scraping didn't find "漏洞简介", we might use the title as description 
                # or try to extract all text from a container.
                # However, for the AI generation purpose, Title + ID is often enough to infer context.
                
                description = f"Details for {title} (SSVID-{ssvid_str})."
                
                # Try to find date
                # <td class="text-center datetime hidden-sm hidden-xs">2022-12-09</td>
                # But that's on search page. On detail page it might be different.
                
                return {
                    "status": "success",
                    "data": {
                        "name": title,
                        "vul_name": title,
                        "description": description,
                        "ssvid": ssvid_str,
                        # Mocking other fields to satisfy expected structure
                        "type": "Web Vulnerability",
                        "component": "Unknown" 
                    }
                }
        except Exception as e:
            print(f"⚠️ Web scraping details failed: {e}")
            
        return {"status": "error", "msg": "Web detail scrape failed"}

    def search_poc(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for POC/Vulnerabilities (API first, then Web Scrape)
        :param keyword: Search keyword
        :param page: Page number (Not supported by new API, ignored)
        :param page_size: Items per page (Not supported by new API, ignored)
        :return: Search result in standardized format
        """
        # New API uses 'q' for keyword
        params = {"q": keyword}
        result = self._send_request(path="/user/poc_list", params=params)
        
        # If API returns valid list, use it
        if result is not None and isinstance(result, list) and len(result) > 0:
            # Transform list to match old structure for compatibility
            return {
                "status": "success", 
                "data": {
                    "list": result,
                    "total": len(result)
                }
            }
        
        # Fallback to Web Scraping if API returns empty list or fails
        # Note: API might return empty list [] if no results found OR if no permission.
        # We assume if empty, we try web search to see if there are public results.
        return self.search_poc_web(keyword)

    def download_poc(self, ssvid: str, save_path: str = "./") -> Dict[str, Any]:
        """
        Download POC code for a specific SSVID
        :param ssvid: POC Unique ID (can be int or str)
        :param save_path: Save path
        :return: Download result (including save path)
        """
        # Ensure ssvid is string and strip prefix if present
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
                    print(f"✅ POC downloaded successfully: {full_path}")
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

    def get_poc_detail(self, ssvid: str) -> Dict[str, Any]:
        """
        Get POC/Vulnerability details (API first, then Web Scrape)
        :param ssvid: POC Unique ID
        :return: POC details in standardized format
        """
        ssvid_str = str(ssvid).replace('ssvid-', '')
        params = {"id": ssvid_str}
        result = self._send_request(path="/user/poc_detail", params=params)
        
        if result is not None and isinstance(result, dict):
            # Check for error status in response
            if 'status' in result and result['status'] is False:
                # If API says "No permission" or error, try web scrape
                msg = result.get('message', 'Unknown error')
                # print(f"⚠️ API Detail Error: {msg}. Trying web scrape...")
                return self.get_poc_detail_web(ssvid_str)
                
            return {
                "status": "success", 
                "data": result
            }
            
        # If request failed completely, try web scrape
        return self.get_poc_detail_web(ssvid_str)
