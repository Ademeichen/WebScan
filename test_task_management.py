#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试任务管理、数据库存储和进度显示功能
使用SQLite数据库进行测试
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from tortoise import Tortoise


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()


async def test_task_creation():
    """测试任务创建"""
    print("\n" + "=" * 60)
    print("测试1: 创建任务")
    print("=" * 60)
    
    try:
        from models import Task
        
        # 创建测试任务
        task = await Task.create(
            task_name="测试扫描任务",
            task_type="scan",
            target="http://testphp.vulnweb.com",
            status="pending",
            progress=0,
            config='{"profile": "full_scan"}',
            result=None
        )
        
        print(f"✅ 任务创建成功")
        print(f"   任务ID: {task.id}")
        print(f"   任务名称: {task.task_name}")
        print(f"   目标: {task.target}")
        print(f"   状态: {task.status}")
        print(f"   进度: {task.progress}%")
        
        return task.id
    except Exception as e:
        print(f"❌ 任务创建失败: {str(e)}")
        return None


async def test_task_query(task_id):
    """测试任务查询"""
    print("\n" + "=" * 60)
    print("测试2: 查询任务")
    print("=" * 60)
    
    try:
        from models import Task
        
        # 查询任务
        task = await Task.get(id=task_id)
        
        print(f"✅ 任务查询成功")
        print(f"   任务ID: {task.id}")
        print(f"   任务名称: {task.task_name}")
        print(f"   状态: {task.status}")
        print(f"   进度: {task.progress}%")
        print(f"   创建时间: {task.created_at}")
        
    except Exception as e:
        print(f"❌ 任务查询失败: {str(e)}")


async def test_task_update(task_id):
    """测试任务更新"""
    print("\n" + "=" * 60)
    print("测试3: 更新任务进度")
    print("=" * 60)
    
    try:
        from models import Task
        
        # 更新任务进度
        task = await Task.get(id=task_id)
        for key, value in {'progress': 50, 'status': 'running'}.items():
            setattr(task, key, value)
        await task.save()
        
        print(f"✅ 任务更新成功")
        print(f"   任务ID: {task.id}")
        print(f"   新状态: {task.status}")
        print(f"   新进度: {task.progress}%")
        
    except Exception as e:
        print(f"❌ 任务更新失败: {str(e)}")


async def test_task_list():
    """测试任务列表查询"""
    print("\n" + "=" * 60)
    print("测试4: 查询任务列表")
    print("=" * 60)
    
    try:
        from models import Task
        
        # 查询任务列表
        tasks = await Task.all().order_by('-created_at').limit(10)
        
        print(f"✅ 任务列表查询成功")
        print(f"   任务总数: {len(tasks)}")
        
        for task in tasks:
            print(f"   - ID: {task.id}, 名称: {task.task_name}, 状态: {task.status}, 进度: {task.progress}%")
        
    except Exception as e:
        print(f"❌ 任务列表查询失败: {str(e)}")


async def test_report_creation(task_id):
    """测试报告创建"""
    print("\n" + "=" * 60)
    print("测试5: 创建报告")
    print("=" * 60)
    
    try:
        from models import Report
        
        # 创建测试报告
        report = await Report.create(
            task_id=task_id,
            report_name="测试扫描报告",
            report_type="html",
            content=None
        )
        
        print(f"✅ 报告创建成功")
        print(f"   报告ID: {report.id}")
        print(f"   报告名称: {report.report_name}")
        print(f"   关联任务ID: {report.task_id}")
        print(f"   报告类型: {report.report_type}")
        
        return report.id
    except Exception as e:
        print(f"❌ 报告创建失败: {str(e)}")
        return None


async def test_report_query(report_id):
    """测试报告查询"""
    print("\n" + "=" * 60)
    print("测试6: 查询报告")
    print("=" * 60)
    
    try:
        from models import Report
        
        # 查询报告
        report = await Report.get(id=report_id)
        
        print(f"✅ 报告查询成功")
        print(f"   报告ID: {report.id}")
        print(f"   报告名称: {report.report_name}")
        print(f"   关联任务ID: {report.task_id}")
        print(f"   创建时间: {report.created_at}")
        
    except Exception as e:
        print(f"❌ 报告查询失败: {str(e)}")


async def test_progress_tracking(task_id):
    """测试进度跟踪"""
    print("\n" + "=" * 60)
    print("测试7: 模拟进度更新")
    print("=" * 60)
    
    try:
        from models import Task
        
        # 模拟进度更新
        progress_values = [10, 25, 40, 55, 70, 85, 100]
        
        for progress in progress_values:
            await asyncio.sleep(0.5)  # 模拟扫描过程
            task = await Task.get(id=task_id)
            for key, value in {'progress': progress}.items():
                setattr(task, key, value)
            await task.save()
            print(f"   进度更新: {progress}%")
        
        # 更新状态为完成
        task = await Task.get(id=task_id)
        for key, value in {'status': 'completed'}.items():
            setattr(task, key, value)
        await task.save()
        
        print(f"✅ 进度跟踪测试完成")
        print(f"   最终状态: {task.status}")
        print(f"   最终进度: {task.progress}%")
        
    except Exception as e:
        print(f"❌ 进度跟踪测试失败: {str(e)}")


async def test_cleanup(task_id, report_id):
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    try:
        from models import Task, Report
        
        # 删除报告
        if report_id:
            report = await Report.get(id=report_id)
            await report.delete()
            print(f"✅ 删除报告: {report_id}")
        
        # 删除任务
        if task_id:
            task = await Task.get(id=task_id)
            await task.delete()
            print(f"✅ 删除任务: {task_id}")
        
    except Exception as e:
        print(f"❌ 清理失败: {str(e)}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始测试任务管理、数据库存储和进度显示功能")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    print("✅ 数据库连接成功")
    
    task_id = None
    report_id = None
    
    try:
        # 测试任务创建
        task_id = await test_task_creation()
        
        if task_id:
            # 测试任务查询
            await test_task_query(task_id)
            
            # 测试任务更新
            await test_task_update(task_id)
            
            # 测试任务列表查询
            await test_task_list()
            
            # 测试报告创建
            report_id = await test_report_creation(task_id)
            
            if report_id:
                # 测试报告查询
                await test_report_query(report_id)
            
            # 测试进度跟踪
            await test_progress_tracking(task_id)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
    
    finally:
        # 清理测试数据
        if task_id or report_id:
            await test_cleanup(task_id, report_id)
        
        # 关闭数据库连接
        await Tortoise.close_connections()
        print("\n✅ 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
