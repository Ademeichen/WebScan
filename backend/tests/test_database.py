#!/usr/bin/env python3
"""
测试database.py功能
"""
import asyncio
import sys
from pathlib import Path

current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backend.database import init_db, init_database, health_check


async def test_init_db():
    """测试数据库初始化"""
    print("=" * 50)
    print("测试 1: init_db()")
    print("=" * 50)
    try:
        await init_db()
        print("✅ init_db() 测试通过")
        return True
    except Exception as e:
        print(f"❌ init_db() 测试失败: {e}")
        return False


async def test_health_check():
    """测试健康检查"""
    print("\n" + "=" * 50)
    print("测试 2: health_check()")
    print("=" * 50)
    try:
        result = await health_check()
        if result:
            print("✅ health_check() 测试通过")
            return True
        else:
            print("❌ health_check() 返回 False")
            return False
    except Exception as e:
        print(f"❌ health_check() 测试失败: {e}")
        return False


async def test_init_database():
    """测试完整数据库初始化（包括管理员账户）"""
    print("\n" + "=" * 50)
    print("测试 3: init_database()")
    print("=" * 50)
    try:
        await init_database()
        print("✅ init_database() 测试通过")
        return True
    except Exception as e:
        print(f"❌ init_database() 测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("开始测试 database.py 功能\n")
    
    results = []
    
    results.append(await test_init_db())
    results.append(await test_health_check())
    results.append(await test_init_database())
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
