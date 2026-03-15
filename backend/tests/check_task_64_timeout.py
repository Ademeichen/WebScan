"""
检查任务 64 的超时配置
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
import json
from backend.database import init_db, close_db
from backend.models import Task


async def check_task_64():
    await init_db()
    
    try:
        print("=" * 60)
        print("检查任务 64 的超时配置")
        print("=" * 60)
        
        task = await Task.get_or_none(id=64)
        
        if task:
            print(f"\n✓ 找到任务 64")
            print(f"  任务类型: {task.task_type}")
            print(f"  任务名称: {task.task_name}")
            print(f"  目标: {task.target}")
            print(f"  状态: {task.status}")
            
            if task.config:
                try:
                    config = json.loads(task.config)
                    print(f"\n  任务配置:")
                    print(f"    timeout: {config.get('timeout')}")
                    print(f"    global_timeout: {config.get('global_timeout')}")
                    print(f"    完整配置: {json.dumps(config, indent=6, ensure_ascii=False)}")
                    
                    if config.get('timeout') == 120:
                        print(f"\n⚠️  发现问题: 任务配置了 timeout=120 秒，这太短了！")
                        print(f"   建议: 将 timeout 增加到至少 3600 秒 (60分钟) 或删除自定义配置使用默认值")
                except json.JSONDecodeError:
                    print(f"\n  配置解析失败: {task.config}")
            else:
                print(f"\n  没有配置信息")
        else:
            print(f"\n✗ 未找到任务 64")
            
        print("\n" + "=" * 60)
        print("当前 TASK_TIMEOUT_CONFIG:")
        print("=" * 60)
        
        from backend.task_executor import TASK_TIMEOUT_CONFIG
        
        for key, value in TASK_TIMEOUT_CONFIG.items():
            print(f"  {key}: {value}秒 ({value/60:.2f}分钟)")
            
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(check_task_64())
