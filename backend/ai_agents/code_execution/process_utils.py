"""
进程工具模块

提供进程创建、等待和超时处理的公共工具函数
"""
import asyncio
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


async def execute_process(
    cmd: list,
    timeout: int,
    cwd: Optional[str] = None,
    encoding: str = "utf-8",
    errors: str = "replace"
) -> Tuple[bytes, bytes, int]:
    """
    执行进程并等待结果
    
    Args:
        cmd: 命令列表
        timeout: 超时时间(秒)
        cwd: 工作目录
        encoding: 编码格式
        errors: 错误处理方式
        
    Returns:
        Tuple[bytes, bytes, int]: 标准输出、错误输出和退出码
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        exit_code = process.returncode
        return stdout, stderr, exit_code
    except asyncio.TimeoutError:
        process.kill()
        return b"", f"执行超时({timeout}秒)".encode(encoding), -1


def decode_output(
    output: bytes,
    encoding: str = "utf-8",
    errors: str = "replace"
) -> str:
    """
    解码进程输出
    
    Args:
        output: 字节输出
        encoding: 编码格式
        errors: 错误处理方式
        
    Returns:
        str: 解码后的字符串
    """
    return output.decode(encoding, errors=errors)


def handle_process_error(
    error: Exception,
    operation: str
) -> str:
    """
    处理进程错误
    
    Args:
        error: 异常对象
        operation: 操作名称
        
    Returns:
        str: 错误消息
    """
    logger.error(f"{operation}失败: {str(error)}")
    return str(error)
