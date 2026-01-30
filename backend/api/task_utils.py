"""
任务工具模块

提供任务创建、执行和管理的公共工具函数
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def create_scan_task(
    task_name: str,
    task_type: str,
    target: str,
    config: Dict[str, Any] = None,
    status: str = "pending"
) -> Any:
    """
    创建扫描任务
    
    Args:
        task_name: 任务名称
        task_type: 任务类型
        target: 扫描目标
        config: 任务配置
        status: 任务状态
        
    Returns:
        Task: 创建的任务对象
    """
    from models import Task
    
    if config is None:
        config = {}
    
    return await Task.create(
        task_name=task_name,
        task_type=task_type,
        target=target,
        status=status,
        progress=0,
        config=json.dumps(config),
        result=None
    )


async def start_task_execution(
    task_id: int,
    target: str,
    scan_config: Dict[str, Any] = None
):
    """
    启动任务执行
    
    Args:
        task_id: 任务ID
        target: 扫描目标
        scan_config: 扫描配置
    """
    from task_executor import task_executor
    
    if scan_config is None:
        scan_config = {}
    
    asyncio.create_task(task_executor.start_task(
        task_id=task_id,
        target=target,
        scan_config=scan_config
    ))


def handle_task_error(
    error: Exception,
    task_name: str
) -> str:
    """
    处理任务错误
    
    Args:
        error: 异常对象
        task_name: 任务名称
        
    Returns:
        str: 错误消息
    """
    logger.error(f"{task_name}失败: {str(error)}")
    return str(error)


def get_task_response(
    task_id: int,
    message: str
) -> Dict[str, Any]:
    """
    获取任务响应
    
    Args:
        task_id: 任务ID
        message: 响应消息
        
    Returns:
        Dict: 任务响应
    """
    return {
        "task_id": task_id,
        "message": message
    }
