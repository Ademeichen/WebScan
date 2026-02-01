"""
依赖安装工具

提供 Python 包依赖安装功能。
"""
import subprocess
import sys
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def install_dependencies(packages: List[str], upgrade: bool = False) -> Dict[str, Any]:
    """
    安装 Python 包依赖
    
    Args:
        packages: 要安装的包列表
        upgrade: 是否升级已安装的包
        
    Returns:
        Dict: 安装结果
    """
    try:
        logger.info(f"🔧 开始安装依赖包: {packages}")
        
        # 构建安装命令
        cmd = [sys.executable, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        
        cmd.extend(packages)
        
        # 执行安装
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 解析输出
        output = result.stdout
        error = result.stderr
        
        # 检查是否成功
        success = result.returncode == 0
        
        # 提取安装的包信息
        installed_packages = []
        if success:
            for line in output.split('\n'):
                if 'Successfully installed' in line:
                    packages_str = line.replace('Successfully installed', '').strip()
                    installed_packages = packages_str.split()
        
        logger.info(f"✅ 依赖包安装完成: {len(installed_packages)} 个包")
        
        return {
            "status": "success" if success else "failed",
            "packages": packages,
            "installed_packages": installed_packages,
            "output": output,
            "error": error,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ 依赖包安装超时")
        return {
            "status": "timeout",
            "packages": packages,
            "installed_packages": [],
            "error": "安装超时",
            "return_code": -1
        }
    except Exception as e:
        logger.error(f"❌ 依赖包安装失败: {str(e)}")
        return {
            "status": "failed",
            "packages": packages,
            "installed_packages": [],
            "error": str(e),
            "return_code": -1
        }


def check_package_installed(package: str) -> bool:
    """
    检查包是否已安装
    
    Args:
        package: 包名
        
    Returns:
        bool: 是否已安装
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def get_installed_packages() -> Dict[str, str]:
    """
    获取已安装的包列表
    
    Returns:
        Dict: 包名到版本的映射
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
            return {pkg["name"]: pkg["version"] for pkg in packages}
        else:
            return {}
    except:
        return {}


def install_requirements(requirements_file: str, upgrade: bool = False) -> Dict[str, Any]:
    """
    从 requirements 文件安装依赖
    
    Args:
        requirements_file: requirements 文件路径
        upgrade: 是否升级已安装的包
        
    Returns:
        Dict: 安装结果
    """
    try:
        logger.info(f"🔧 从文件安装依赖: {requirements_file}")
        
        # 构建安装命令
        cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        
        if upgrade:
            cmd.append("--upgrade")
        
        # 执行安装
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 解析输出
        output = result.stdout
        error = result.stderr
        
        # 检查是否成功
        success = result.returncode == 0
        
        logger.info(f"✅ 依赖安装完成: {requirements_file}")
        
        return {
            "status": "success" if success else "failed",
            "requirements_file": requirements_file,
            "output": output,
            "error": error,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ 依赖安装超时: {requirements_file}")
        return {
            "status": "timeout",
            "requirements_file": requirements_file,
            "error": "安装超时",
            "return_code": -1
        }
    except Exception as e:
        logger.error(f"❌ 依赖安装失败: {str(e)}")
        return {
            "status": "failed",
            "requirements_file": requirements_file,
            "error": str(e),
            "return_code": -1
        }
