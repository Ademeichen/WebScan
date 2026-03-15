#!/usr/bin/env python
"""
数据库管理命令行工具

用法:
    python -m backend.scripts.db init    - 初始化数据库
    python -m backend.scripts.db reset   - 重置数据库（清空所有数据）
"""
import sys
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_cli")


async def run_init():
    from backend.database import init_database, close_db
    
    try:
        logger.info("正在初始化数据库...")
        await init_database()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise
    finally:
        await close_db()


async def run_reset():
    from backend.database import reset_database, close_db
    
    try:
        logger.warning("⚠️  警告：此操作将删除所有数据，不可恢复！")
        confirm = input("确认重置数据库？(yes/no): ")
        if confirm.lower() != "yes":
            logger.info("已取消操作")
            return
        
        await reset_database()
        logger.info("✅ 数据库重置完成")
    except Exception as e:
        logger.error(f"❌ 重置失败: {e}")
        raise
    finally:
        await close_db()


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python -m backend.scripts.db init    - 初始化数据库")
        print("  python -m backend.scripts.db reset   - 重置数据库（清空所有数据）")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        asyncio.run(run_init())
    elif command == "reset":
        asyncio.run(run_reset())
    else:
        logger.error(f"未知命令: {command}")
        print("可用命令: init, reset")
        sys.exit(1)


if __name__ == "__main__":
    main()
