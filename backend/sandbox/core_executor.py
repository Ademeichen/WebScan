"""
核心业务执行层 - 模块化版本

提供 CodeExecutor 类供其他模块导入使用。
支持多种编程语言的代码执行和工作流配置文件。
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
# TODO: 集成该功能到 LangChain 工作流中，作为工具调用节点

class CodeExecutor:
    """
    代码执行器核心类 - 模块化版本
    
    支持多种编程语言的代码执行，包括 Python、JavaScript、Shell、PowerShell、Batch。
    支持从配置文件执行工作流。
    """
    
    def __init__(self, workspace: Optional[str] = None):
        """
        初始化代码执行器
        
        Args:
            workspace: 工作空间路径，默认为 executor_workspace
        """
        current_dir = Path(__file__).parent
        if workspace:
            self.workspace = Path(workspace)
        else:
            self.workspace = current_dir / "executor_workspace"
        
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        self.executors = {
            "python": {"ext": ".py", "cmd": [sys.executable, "{file_path}"]},
            "javascript": {"ext": ".js", "cmd": ["node", "{file_path}"]},
            "shell": {"ext": ".sh", "cmd": ["bash", "{file_path}"]},
            "powershell": {"ext": ".ps1", "cmd": ["powershell", "-File", "{file_path}"]},
            "batch": {"ext": ".bat", "cmd": ["cmd", "/c", "{file_path}"]}
        }
        
        logger.info(f"✅ 代码执行器初始化完成，工作空间: {self.workspace}")
    
    def load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，可以是相对路径
            
        Returns:
            Dict: 配置数据字典
        """
        try:
            path = Path(config_path)
            if not path.is_absolute():
                path = Path(__file__).parent.parent / config_path
            
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            return {}
    
    def execute_from_config(self, config_path: str) -> List[Dict]:
        """
        根据配置文件执行所有动作
        
        Args:
            config_path: 配置文件路径，可以是相对路径
            
        Returns:
            List[Dict]: 执行结果列表
        """
        config = self.load_config(config_path)
        if not config:
            return [{"success": False, "error": "配置加载失败"}]
        
        return self.execute_actions(config)
    
    def execute_actions(self, config_data: Dict) -> List[Dict]:
        """
        执行配置中的所有动作
        
        Args:
            config_data: 配置数据字典
            
        Returns:
            List[Dict]: 执行结果列表
        """
        actions = config_data.get("actions", [])
        settings = config_data.get("settings", {})
        results = []
        
        for action in actions:
            result = self._process_action(action)
            results.append(result)
            
            if not result.get("success") and settings.get("stop_on_error", False):
                logger.warning(f"⚠️ 执行停止，遇到错误: {result.get('error')}")
                break
        
        return results
    
    def _process_action(self, action: Dict) -> Dict:
        """
        处理单个动作（内部方法）
        
        Args:
            action: 动作字典
            
        Returns:
            Dict: 执行结果
        """
        action_type = action.get("type")
        action_name = action.get("name") or action.get("filename") or ""

        result = {"type": action_type, "success": False}

        try:
            if action_type == "write_code":
                result = self._write_code(action)
            elif action_type == "execute_code":
                result = self._execute_code(action)
            elif action_type == "command":
                result = self._execute_command(action)
            elif action_type == "read_code":
                result = self._read_code(action)
            else:
                result = {"success": False, "error": f"❌ 未知动作类型: {action_type}", "action": action_type}
        except Exception as e:
            result = {"success": False, "error": str(e), "action": action_type}

        result["action_type"] = action_type
        result["action_name"] = action_name
        result.setdefault("stdout", "")
        result.setdefault("stderr", "")
        result.setdefault("returncode", None)

        return result
    
    def _write_code(self, action: Dict) -> Dict:
        """
        写入代码文件
        
        Args:
            action: 包含 filename、code、language 的字典
            
        Returns:
            Dict: 执行结果
        """
        filename = action["filename"]
        code = action["code"]
        language = action.get("language", "python")
        
        if language in self.executors:
            if not filename.endswith(self.executors[language]["ext"]):
                filename += self.executors[language]["ext"]
        
        file_path = self.workspace / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"✅ 代码已写入: {file_path}")
        
        return {
            "success": True,
            "filepath": str(file_path),
            "action": "write_code",
            "stdout": "",
            "stderr": "",
            "returncode": 0
        }
    
    def _execute_code(self, action: Dict) -> Dict:
        """
        执行代码文件
        
        Args:
            action: 包含 filepath、language、args 的字典
            
        Returns:
            Dict: 执行结果
        """
        filepath = action["filepath"]
        language = action.get("language", "python")
        args = action.get("args", [])
        
        full_path = Path(filepath) if os.path.isabs(filepath) else self.workspace / filepath
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"❌ 文件不存在: {full_path}",
                "action": "execute_code"
            }
        
        if language not in self.executors:
            return {
                "success": False,
                "error": f"❌ 不支持的语言: {language}",
                "action": "execute_code"
            }
        
        try:
            cmd_template = self.executors[language]["cmd"]
            cmd = [part.format(file_path=str(full_path)) for part in cmd_template]
            cmd.extend(args)
            
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding=encoding,
                errors='replace'
            )

            if result.returncode == 0:
                logger.info(f"✅ 代码执行成功: {full_path}")
            else:
                logger.error(f"❌ 代码执行失败: {full_path}")

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "filepath": str(full_path),
                "action": "execute_code"
            }
        except Exception as e:
            logger.error(f"❌ 执行异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "action": "execute_code"
            }
    
    def _execute_command(self, action: Dict) -> Dict:
        """
        执行终端命令
        
        Args:
            action: 包含 command、shell、timeout 的字典
            
        Returns:
            Dict: 执行结果
        """
        command = action["command"]
        shell_type = action.get("shell", "cmd")
        timeout = action.get("timeout", 30)
        
        try:
            if shell_type.lower() == "powershell":
                full_cmd = ["powershell", "-Command", command]
            else:
                full_cmd = ["cmd", "/c", command]
            
            encoding = 'gbk' if sys.platform == 'win32' else 'utf-8'

            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding=encoding,
                errors='replace',
                shell=False
            )

            if result.returncode == 0:
                logger.info(f"✅ 命令执行成功: {command}")
            else:
                logger.error(f"❌ 命令执行失败: {command}")

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "command": command,
                "action": "command"
            }
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 执行超时: {command}")
            return {
                "success": False,
                "error": "执行超时",
                "command": command,
                "action": "command"
            }
        except Exception as e:
            logger.error(f"❌ 执行异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "action": "command"
            }
    
    def _read_code(self, action: Dict) -> Dict:
        """
        读取代码文件
        
        Args:
            action: 包含 filepath 的字典
            
        Returns:
            Dict: 执行结果
        """
        filepath = action["filepath"]
        full_path = Path(filepath) if os.path.isabs(filepath) else self.workspace / filepath
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"✅ 文件读取成功: {full_path}")

            return {
                "success": True,
                "content": content,
                "filepath": str(full_path),
                "action": "read_code",
                "stdout": "",
                "stderr": "",
                "returncode": 0
            }
        except Exception as e:
            logger.error(f"❌ 读取失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "action": "read_code"
            }
