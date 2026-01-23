"""
环境感知模块

提供环境信息收集和分析功能，使AI能够感知执行环境。
"""
import platform
import sys
import subprocess
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentAwareness:
    """
    环境感知类
    
    负责收集和分析执行环境信息，包括：
    - 操作系统检测
    - Python版本和依赖检查
    - 可用工具检测
    - 网络状态检测
    - 磁盘空间和内存状态
    """
    
    def __init__(self):
        self.os_info = self._detect_os()
        self.python_info = self._detect_python()
        self.available_tools = self._detect_tools()
        self.network_info = self._detect_network()
        self.system_resources = self._detect_resources()
        
        logger.info("✅ 环境感知模块初始化完成")
    
    def _detect_os(self) -> Dict[str, Any]:
        """
        检测操作系统信息
        
        Returns:
            Dict: 操作系统信息
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()
        }
    
    def _detect_python(self) -> Dict[str, Any]:
        """
        检测Python版本和依赖
        
        Returns:
            Dict: Python信息
        """
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        try:
            import langchain
            langchain_version = langchain.__version__
        except ImportError:
            langchain_version = None
        
        try:
            import langgraph
            langgraph_version = langgraph.__version__
        except ImportError:
            langgraph_version = None
        
        try:
            import tortoise
            tortoise_version = tortoise.__version__
        except ImportError:
            tortoise_version = None
        
        try:
            import fastapi
            fastapi_version = fastapi.__version__
        except ImportError:
            fastapi_version = None
        
        return {
            "version": python_version,
            "executable": sys.executable,
            "dependencies": {
                "langchain": langchain_version,
                "langgraph": langgraph_version,
                "tortoise": tortoise_version,
                "fastapi": fastapi_version
            }
        }
    
    def _detect_tools(self) -> Dict[str, Any]:
        """
        检测可用的安全工具
        
        Returns:
            Dict: 可用工具信息
        """
        tools = {
            "nmap": self._check_tool("nmap", "nmap --version"),
            "sqlmap": self._check_tool("sqlmap", "sqlmap --version"),
            "burpsuite": self._check_tool("burpsuite", "burpsuite --version"),
            "metasploit": self._check_tool("metasploit", "msfconsole --version"),
            "nikto": self._check_tool("nikto", "nikto --version"),
            "dirb": self._check_tool("dirb", "dirb --version"),
            "gobuster": self._check_tool("gobuster", "gobuster --version")
        }
        
        return tools
    
    def _check_tool(self, tool_name: str, version_cmd: str) -> Dict[str, Any]:
        """
        检查工具是否可用
        
        Args:
            tool_name: 工具名称
            version_cmd: 版本检查命令
            
        Returns:
            Dict: 工具信息
        """
        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            available = result.returncode == 0
            version = result.stdout.strip() if result.stdout else "unknown"
            
            return {
                "name": tool_name,
                "available": available,
                "version": version
            }
        except Exception as e:
            logger.warning(f"检测工具 {tool_name} 失败: {str(e)}")
            return {
                "name": tool_name,
                "available": False,
                "version": "unknown",
                "error": str(e)
            }
    
    def _detect_network(self) -> Dict[str, Any]:
        """
        检测网络状态
        
        Returns:
            Dict: 网络信息
        """
        try:
            import socket
            hostname = socket.gethostname()
            
            return {
                "hostname": hostname,
                "proxy_detected": self._check_proxy(),
                "firewall_detected": self._check_firewall(),
                "internet_available": self._check_internet()
            }
        except Exception as e:
            logger.error(f"网络检测失败: {str(e)}")
            return {
                "hostname": "unknown",
                "proxy_detected": False,
                "firewall_detected": False,
                "internet_available": False,
                "error": str(e)
            }
    
    def _check_proxy(self) -> bool:
        """
        检查是否配置了代理
        
        Returns:
            bool: 是否配置代理
        """
        proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "NO_PROXY"]
        return any(var in os.environ for var in proxy_vars)
    
    def _check_firewall(self) -> bool:
        """
        检查是否启用了防火墙
        
        Returns:
            bool: 是否启用防火墙
        """
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return "enabled" in result.stdout.lower()
            except:
                return False
        else:
            try:
                result = subprocess.run(
                    ["sudo", "ufw", "status"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0
            except:
                return False
    
    def _check_internet(self) -> bool:
        """
        检查是否有网络连接
        
        Returns:
            bool: 是否有网络连接
        """
        try:
            import socket
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except:
            return False
    
    def _detect_resources(self) -> Dict[str, Any]:
        """
        检测系统资源
        
        Returns:
            Dict: 资源信息
        """
        try:
            import shutil
            disk_usage = shutil.disk_usage("/")
            
            total, used, free = disk_usage
            used_percent = (used / total) * 100
            
            return {
                "disk_total": total,
                "disk_used": used,
                "disk_free": free,
                "disk_used_percent": used_percent
            }
        except Exception as e:
            logger.error(f"磁盘检测失败: {str(e)}")
            return {
                "disk_total": 0,
                "disk_used": 0,
                "disk_free": 0,
                "disk_used_percent": 0,
                "error": str(e)
            }
    
    def get_environment_report(self) -> Dict[str, Any]:
        """
        获取完整的环境报告
        
        Returns:
            Dict: 环境报告
        """
        return {
            "os_info": self.os_info,
            "python_info": self.python_info,
            "available_tools": self.available_tools,
            "network_info": self.network_info,
            "system_resources": self.system_resources,
            "scan_recommendations": self._generate_scan_recommendations()
        }
    
    def _generate_scan_recommendations(self) -> List[str]:
        """
        生成扫描建议
        
        Returns:
            List[str]: 扫描建议列表
        """
        recommendations = []
        
        os_system = self.os_info.get("system", "").lower()
        available_tools = self.available_tools
        
        if os_system == "windows":
            recommendations.append("建议使用PowerShell进行脚本执行")
            if available_tools.get("nmap", {}).get("available"):
                recommendations.append("建议使用nmap进行端口扫描")
        else:
            recommendations.append("建议使用Bash进行脚本执行")
            if available_tools.get("nmap", {}).get("available"):
                recommendations.append("建议使用nmap进行端口扫描")
        
        if self.python_info.get("dependencies", {}).get("langchain"):
            recommendations.append("建议启用LLM增强任务规划")
        
        if self.system_resources.get("disk_used_percent", 0) > 80:
            recommendations.append("磁盘空间不足，建议清理临时文件")
        
        return recommendations
    
    def is_tool_available(self, tool_name: str) -> bool:
        """
        检查工具是否可用
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 工具是否可用
        """
        tool_info = self.available_tools.get(tool_name, {})
        return tool_info.get("available", False)
    
    def get_python_version(self) -> str:
        """
        获取Python版本
        
        Returns:
            str: Python版本
        """
        return self.python_info.get("version", "unknown")
