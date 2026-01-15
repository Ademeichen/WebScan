#!/usr/bin/env python3
"""
Sandbox 执行层 - 主执行脚本
运行此脚本执行决策层配置的任务
"""
import sys
import os
import json
from pathlib import Path
import logging
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_executor import CodeExecutor

# 配置日志
current_dir = Path(__file__).parent
# 配置日志，日志文件放到 services 目录下
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(current_dir / 'sandbox_execution.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def load_decision_config(decision_dir: str = "../decision") -> dict:
    """
    加载决策层配置文件
    
    Args:
        decision_dir: 决策层目录路径
        
    Returns:
        配置字典
    """
    try:
        # 构建配置文件路径
        current_dir = Path(__file__).parent
        decision_path = current_dir / decision_dir
        
        # 查找所有 JSON 配置文件
        json_files = list(decision_path.glob("*.json"))
        
        if not json_files:
            logger.warning(f"在 {decision_path} 中未找到 JSON 配置文件")
            
            # 创建默认配置文件
            default_config = {
                "name": "默认测试任务",
                "description": "自动化测试任务",
                "settings": {
                    "timeout": 30,
                    "stop_on_error": False,
                    "log_level": "INFO"
                },
                "actions": [
                    {
                        "type": "write_code",
                        "name": "创建测试脚本",
                        "filename": "test_script",
                        "language": "python",
                        "code": "#!/usr/bin/env python3\nprint('Hello from Sandbox!')\nprint(f'运行时间: {__import__(\"datetime\").datetime.now()}')\n"
                    },
                    {
                        "type": "execute_code",
                        "name": "执行测试脚本",
                        "filepath": "test_script.py",
                        "language": "python"
                    },
                    {
                        "type": "command",
                        "name": "系统信息",
                        "command": "echo %DATE% %TIME% && ver",
                        "shell": "cmd",
                        "timeout": 10
                    }
                ]
            }
            
            # 保存默认配置
            default_file = decision_path / "default_task.json"
            decision_path.mkdir(exist_ok=True, parents=True)
            
            with open(default_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已创建默认配置文件: {default_file}")
            return default_config
        
        # 使用第一个找到的配置文件
        config_file = json_files[0]
        logger.info(f"找到配置文件: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"成功加载配置文件: {config.get('name', '未命名任务')}")
        return config
        
    except Exception as e:
        logger.error(f"加载决策配置失败: {e}")
        return {}


def print_results_summary(results: list) -> None:
    """打印执行结果摘要"""
    print("\n" + "="*60)
    print("执行结果摘要")
    print("="*60)
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    
    print(f"总动作数: {total}")
    print(f"成功: {successful}")
    print(f"失败: {total - successful}")
    print("-"*60)
    
    for i, result in enumerate(results):
        status = "✓" if result.get("success", False) else "✗"
        action_name = result.get("action_name", f"动作_{i+1}")
        action_type = result.get("action_type", "unknown")
        
        print(f"{i+1:2d}. [{status}] {action_name} ({action_type})")
        
        if not result.get("success"):
            error_msg = result.get("error", "未知错误")
            stderr = result.get("stderr", "")
            
            if stderr:
                error_msg = f"{error_msg} | {stderr[:100]}"
            
            print(f"     错误: {error_msg[:150]}{'...' if len(error_msg) > 150 else ''}")


def save_execution_report(executor: CodeExecutor, config: dict, results: list) -> str:
    """保存执行报告"""
    try:
        # 创建报告目录
        report_dir = executor.workspace / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"execution_report_{timestamp}.json"
        
        report = {
            "execution_info": {
                "timestamp": datetime.now().isoformat(),
                "workflow_name": config.get("name", "未命名任务"),
                "workflow_description": config.get("description", ""),
                "sandbox_version": "1.0.0"
            },
            "summary": {
                "total_actions": len(results),
                "successful": sum(1 for r in results if r.get("success", False)),
                "failed": sum(1 for r in results if not r.get('success', False)),
                "success_rate": f"{(sum(1 for r in results if r.get('success', False)) / len(results) * 100):.1f}%" if results else "0%"
            },
            "detailed_results": results
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"执行报告已保存: {report_file}")
        return str(report_file)
        
    except Exception as e:
        logger.error(f"保存执行报告失败: {e}")
        return ""


def main():
    """主函数"""
    print("="*60)
    print("Sandbox 核心业务执行层")
    print("="*60)
    
    try:
        # 1. 加载决策层配置
        print("\n[1/4] 加载决策层配置...")
        config = load_decision_config("../decision")
        
        if not config:
            print("错误: 无法加载决策配置")
            return 1
        
        print(f"任务名称: {config.get('name', '未命名任务')}")
        print(f"任务描述: {config.get('description', '无描述')}")
        print(f"动作数量: {len(config.get('actions', []))}")
        
        # 2. 初始化执行器
        print("\n[2/4] 初始化执行器...")
        executor = CodeExecutor()
        print(f"工作空间: {executor.workspace}")
        
        # 3. 执行动作（通过 CodeExecutor.execute_actions 统一执行）
        print("\n[3/4] 执行动作...")
        print("-"*40)

        results = executor.execute_actions(config)

        # 打印每个动作的简要输出/错误
        for i, result in enumerate(results):
            action_name = result.get('action_name', f'动作_{i+1}')
            action_type = result.get('action_type', 'unknown')
            print(f"执行 {i+1}/{len(results)}: {action_name}")

            if result.get('success'):
                if action_type in ['execute_code', 'command']:
                    stdout = result.get('stdout', '').strip()
                    if stdout:
                        print(f"  输出: {stdout[:100]}{'...' if len(stdout) > 100 else ''}")
            else:
                error_msg = result.get('error', '')
                stderr = result.get('stderr', '')
                if stderr:
                    error_msg = f"{error_msg} | {stderr[:100]}"
                print(f"  错误: {error_msg[:150]}{'...' if len(error_msg) > 150 else ''}")
        
        # 4. 输出结果和报告
        print("\n[4/4] 生成报告...")
        
        # 打印摘要
        print_results_summary(results)
        
        # 保存报告
        report_file = save_execution_report(executor, config, results)
        if report_file:
            print(f"\n详细报告已保存: {report_file}")
        
        # 检查是否全部成功
        all_success = all(r.get('success', False) for r in results)
        
        print("\n" + "="*60)
        if all_success:
            print("✅ 所有动作执行成功!")
        else:
            print("⚠️  部分动作执行失败")
        print("="*60)
        
        return 0 if all_success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  执行被用户中断")
        return 130
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        print(f"\n❌ 执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)