"""
Seebug Agent - 独立POC生成模块

提供Seebug漏洞查询和AI生成POC的完整功能。
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from .client import SeebugClient
from .generator import POCGenerator
from .config import Config


class SeebugAgent:
    """
    Seebug Agent主类
    
    整合Seebug客户端和POC生成器，提供完整的POC生成流程。
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化Seebug Agent
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or Config()
        self.client = SeebugClient(self.config)
        self.generator = POCGenerator(self.config)

    def search_vulnerabilities(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索漏洞
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        return self.client.search_poc(keyword, page, page_size)

    def get_vulnerability_detail(self, ssvid: str) -> Dict[str, Any]:
        """
        获取漏洞详情
        
        Args:
            ssvid: 漏洞的SSVID
            
        Returns:
            漏洞详情
        """
        return self.client.get_poc_detail(ssvid)

    def generate_poc(self, vul_info: Dict[str, Any]) -> str:
        """
        生成POC代码
        
        Args:
            vul_info: 漏洞信息字典
            
        Returns:
            生成的POC代码
        """
        return self.generator.generate_poc(vul_info)

    def save_poc(self, poc_code: str, filename: str) -> str:
        """
        保存POC代码
        
        Args:
            poc_code: POC代码
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        output_path = Path(self.config.OUTPUT_DIR) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(poc_code)
            
        return str(output_path)

    def generate_and_save_poc(self, ssvid: str) -> Dict[str, Any]:
        """
        获取漏洞详情并生成保存POC
        
        Args:
            ssvid: 漏洞的SSVID
            
        Returns:
            包含POC路径和信息的字典
        """
        detail_result = self.get_vulnerability_detail(ssvid)
        
        if detail_result["status"] != "success":
            return {
                "success": False,
                "message": detail_result.get("msg", "Failed to get vulnerability detail")
            }
        
        vul_data = detail_result["data"]
        poc_code = self.generate_poc(vul_data)
        
        if not poc_code:
            return {
                "success": False,
                "message": "Failed to generate POC"
            }
        
        filename = f"poc_{ssvid}_ai.py"
        save_path = self.save_poc(poc_code, filename)
        
        return {
            "success": True,
            "poc_path": save_path,
            "vulnerability": vul_data
        }

    def search_and_generate(
        self,
        keyword: str,
        selection: int = 0
    ) -> Dict[str, Any]:
        """
        搜索漏洞并生成POC
        
        Args:
            keyword: 搜索关键词
            selection: 选择的结果索引
            
        Returns:
            包含POC路径和信息的字典
        """
        search_result = self.search_vulnerabilities(keyword)
        
        if search_result["status"] != "success":
            return {
                "success": False,
                "message": search_result.get("msg", "Search failed")
            }
        
        poc_list = search_result["data"]["list"]
        
        if not poc_list:
            return {
                "success": False,
                "message": "No vulnerabilities found"
            }
        
        if selection < 0 or selection >= len(poc_list):
            return {
                "success": False,
                "message": f"Invalid selection. Valid range: 0-{len(poc_list)-1}"
            }
        
        selected = poc_list[selection]
        ssvid = selected.get("ssvid")
        
        if not ssvid:
            return {
                "success": False,
                "message": "Selected vulnerability has no SSVID"
            }
        
        return self.generate_and_save_poc(ssvid)


def main():
    """命令行入口"""
    print("🚀 Starting Seebug POC Intelligent Agent...")
    
    agent = SeebugAgent()
    
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        print(f"🔍 Using keyword from arguments: {keyword}")
    else:
        keyword = input("🔍 Enter keyword to search for vulnerabilities (e.g., thinkphp, redis): ").strip()
        
    if not keyword:
        print("Keyword cannot be empty.")
        return

    print(f"Searching for '{keyword}'...")
    search_result = agent.search_vulnerabilities(keyword)
    
    if search_result.get("status") != "success":
        print(f"❌ Search failed: {search_result.get('msg', 'Unknown error')}")
        return

    poc_list = search_result["data"]["list"]
    if not poc_list:
        print(f"⚠️ No results found for '{keyword}'.")
        return

    total_count = search_result["data"].get("total", len(poc_list))
    print(f"\nFound {total_count} results. Showing top {len(poc_list)}:")
    
    for idx, poc in enumerate(poc_list):
        print(f"[{idx+1}] SSVID: {poc['ssvid']} | Name: {poc['name']} | Type: {poc.get('type', 'Unknown')}")

    try:
        if len(sys.argv) > 2:
            selection = int(sys.argv[2]) - 1
            print(f"\n👉 Using selection from arguments: {selection + 1}")
        else:
            selection = int(input(f"\n👉 Select a vulnerability to generate POC for (1-{len(poc_list)}): ")) - 1
            
        if selection < 0 or selection >= len(poc_list):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return

    result = agent.generate_and_save_poc(poc_list[selection]['ssvid'])
    
    if result["success"]:
        print(f"\n💾 POC saved to: {result['poc_path']}")
    else:
        print(f"\n❌ Failed: {result['message']}")


if __name__ == "__main__":
    main()
