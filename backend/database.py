"""
数据库连接和会话管理 - 使用 Tortoise-ORM

提供数据库初始化、连接管理、健康检查、数据重置等功能。
支持异步操作,与 FastAPI 集成使用。
"""

import os
import sys
import asyncio
from tortoise import Tortoise, connections
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """
    初始化数据库连接
    
    创建数据库表结构,建立连接池。
    支持多种数据库:SQLite、MySQL、PostgreSQL。
    
    Raises:
        Exception: 数据库初始化失败时抛出异常
    """
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite://"):
            db_path = db_url.replace("sqlite://", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"✅ 创建数据库目录: {db_dir}")
            
            if not os.path.isabs(db_path):
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.normpath(os.path.join(backend_dir, db_path))
                db_url = f"sqlite:///{db_path.replace(os.sep, '/')}"
        
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["backend.models"]},
            _create_db=True,
            use_tz=False
        )
        await Tortoise.generate_schemas()
        logger.info(f"✅ 数据库初始化成功 - {db_url}")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise


async def init_database():
    """
    初始化数据库并创建管理员账户
    
    创建所有数据库表结构，并创建默认管理员账户。
    管理员账户信息：
    - 用户名: admin
    - 密码: admin123
    - 角色: admin
    
    Raises:
        Exception: 初始化失败时抛出异常
    """
    try:
        await init_db()
        
        from backend.models import User
        
        admin_exists = await User.filter(username="admin").exists()
        if not admin_exists:
            admin_user = await User.create(
                username="admin",
                password="admin123",
                role="admin",
                email="admin@example.com"
            )
            logger.info("✅ 默认管理员账户已创建")
            logger.info("   用户名: admin")
            logger.info("   密码: admin123")
            logger.info("   ⚠️  请在生产环境中修改默认密码！")
        else:
            logger.info("ℹ️  管理员账户已存在，跳过创建")
        
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise


async def reset_database():
    """
    重置数据库 - 清空所有数据
    
    ⚠️  警告：此操作将删除所有数据，不可恢复！
    
    清空内容:
    - 所有用户数据
    - 所有任务记录
    - 所有扫描结果
    - 所有漏洞记录
    - 所有POC扫描结果
    - 所有报告记录
    - 所有设置
    """
    try:
        await init_db()
        
        from backend.models import (
            User, Task, ScanResult, Vulnerability,
            POCScanResult, Report, Setting
        )
        
        logger.info("=" * 50)
        logger.info("⚠️  开始重置数据库...")
        logger.info("⚠️  此操作将删除所有数据，不可恢复！")
        
        task_count = await Task.all().count()
        scan_result_count = await ScanResult.all().count()
        vuln_count = await Vulnerability.all().count()
        poc_count = await POCScanResult.all().count()
        report_count = await Report.all().count()
        user_count = await User.all().count()
        setting_count = await Setting.all().count()
        
        logger.info(f"当前数据统计:")
        logger.info(f"  - 用户: {user_count}")
        logger.info(f"  - 任务: {task_count}")
        logger.info(f"  - 扫描结果: {scan_result_count}")
        logger.info(f"  - 漏洞: {vuln_count}")
        logger.info(f"  - POC结果: {poc_count}")
        logger.info(f"  - 报告: {report_count}")
        logger.info(f"  - 设置: {setting_count}")
        
        await POCScanResult.all().delete()
        logger.info("✅ 已清空 POC 扫描结果表")
        
        await Vulnerability.all().delete()
        logger.info("✅ 已清空漏洞表")
        
        await ScanResult.all().delete()
        logger.info("✅ 已清空扫描结果表")
        
        await Report.all().delete()
        logger.info("✅ 已清空报告表")
        
        await Task.all().delete()
        logger.info("✅ 已清空任务表")
        
        await Setting.all().delete()
        logger.info("✅ 已清空设置表")
        
        await User.all().delete()
        logger.info("✅ 已清空用户表")
        
        logger.info("=" * 50)
        logger.info("✅ 数据库重置完成")
        logger.info("ℹ️  请运行 'python -m backend.database init' 重新初始化数据库")
    except Exception as e:
        logger.error(f"❌ 数据库重置失败: {str(e)}")
        raise


async def close_db():
    """
    关闭数据库连接
    
    优雅关闭所有数据库连接,释放资源。
    
    Raises:
        Exception: 关闭连接失败时抛出异常
    """
    try:
        await Tortoise.close_connections()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {str(e)}")
        raise


async def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        Connection: 默认数据库连接对象
    """
    conn = connections.get("default")
    return conn


async def health_check():
    """
    数据库健康检查
    
    执行简单查询验证数据库连接是否正常。
    
    Returns:
        bool: True表示健康,False表示异常
    """
    try:
        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {str(e)}")
        return False


def main():
    """
    命令行接口
    
    用法:
        python -m backend.database init    - 初始化数据库
        python -m backend.database reset   - 重置数据库（清空所有数据）
    """
    if len(sys.argv) < 2:
        print("用法:")
        print("  python -m backend.database init    - 初始化数据库")
        print("  python -m backend.database reset   - 重置数据库（清空所有数据）")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        print("正在初始化数据库...")
        asyncio.run(init_database())
    elif command == "reset":
        print("⚠️  警告：此操作将删除所有数据，不可恢复！")
        confirm = input("确认重置数据库？(yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(reset_database())
        else:
            print("已取消操作")
    else:
        print(f"未知命令: {command}")
        print("可用命令: init, reset")
        sys.exit(1)


if __name__ == "__main__":
    main()
