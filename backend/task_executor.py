"""
任务执行器 - 负责执行扫描任务并实时更新进度

功能:
1. 任务队列管理 (串行执行)
2. 幂等性检查 (防止重复提交)
3. 全局超时控制
4. 统一异常处理
5. 多进程插件执行与管理
6. 任务状态持久化
7. 任务恢复功能
8. 任务超时处理
"""
import asyncio
import logging
import multiprocessing
import signal
import time
import os
import json
from typing import Dict, Any, Set, Optional, Union, List
from datetime import datetime
from pathlib import Path
from tortoise.expressions import Q
from backend.api.websocket import manager
from backend.config import settings
from backend.plugin_executor import run_plugin_process
from backend.ai_agents.poc_system.dynamic_engine import dynamic_engine
from backend.utils.logging_utils import (
    task_state_logger, 
    get_request_id, 
    set_request_id,
    StructuredLogger
)

try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("task_executor")


from backend.utils.serializers import sanitize_json_data


TASK_STATE_FILE = "data/task_states.json"
TASK_TIMEOUT_CONFIG = {
    "port_scan": 15 * 60,
    "waf_check": 5 * 60,
    "awvs_scan": 5 * 60 * 60,
    "poc_scan": 60 * 60,
    "ai_agent_scan": 5 * 60 * 60,
    "default": 30 * 60,
}


class TaskExecutor:
    """
    任务执行器类
    
    功能:
    1. 任务队列管理 (串行执行)
    2. 幂等性检查 (防止重复提交)
    3. 全局超时控制
    4. 统一异常处理
    5. 多进程插件执行与管理
    6. 任务状态持久化
    7. 任务恢复功能
    8. 任务超时处理
    """
    
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.queued_task_ids: Set[int] = set()
        self.cancelled_task_ids: Set[int] = set()
        self.running_task_id: Optional[int] = None
        self.task_processes: Dict[int, multiprocessing.Process] = {}
        self.task_heartbeats: Dict[int, float] = {}
        self.task_start_times: Dict[int, float] = {}
        self.task_timeouts: Dict[int, int] = {}
        
        self.is_running = True
        self.is_shutting_down = False
        self.worker_task = None
        self.current_execution_task = None
        
        self.kafka_producer = None
        self._init_kafka()
        
        self._ensure_state_dir()
        self._persisted_tasks: Dict[int, Dict] = self._load_task_states()
        
        logger.info(f"TaskExecutor initialized with {len(self._persisted_tasks)} persisted task states")

    def _init_kafka(self):
        """初始化Kafka生产者"""
        try:
            if KafkaProducer:
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=[settings.KAFKA_BOOTSTRAP_SERVERS],
                    value_serializer=lambda x: json.dumps(x).encode('utf-8')
                )
                logger.info(f"Kafka Producer initialized: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.warning(f"Kafka setup failed: {e}")

    def _ensure_state_dir(self):
        """确保状态目录存在"""
        state_dir = Path(TASK_STATE_FILE).parent
        state_dir.mkdir(parents=True, exist_ok=True)

    def _load_task_states(self) -> Dict[int, Dict]:
        """从文件加载任务状态"""
        try:
            if os.path.exists(TASK_STATE_FILE):
                with open(TASK_STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load task states: {e}")
        return {}

    def _save_task_states(self):
        """保存任务状态到文件"""
        try:
            with open(TASK_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._persisted_tasks, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Failed to save task states: {e}")

    def _persist_task_state(self, task_id: int, state: Dict):
        """持久化单个任务状态"""
        self._persisted_tasks[task_id] = {
            **state,
            "updated_at": datetime.utcnow().isoformat()
        }
        self._save_task_states()

    def _remove_task_state(self, task_id: int):
        """移除任务状态"""
        if task_id in self._persisted_tasks:
            del self._persisted_tasks[task_id]
            self._save_task_states()

    def _get_task_timeout(self, task_type: str, scan_config: Dict = None) -> int:
        """获取任务超时时间"""
        if scan_config and 'timeout' in scan_config:
            return scan_config['timeout']
        if scan_config and 'global_timeout' in scan_config:
            return scan_config['global_timeout']
        return TASK_TIMEOUT_CONFIG.get(task_type, TASK_TIMEOUT_CONFIG['default'])

    async def reset_scan_data(self):
        """
        重置扫描数据 - 项目启动时清空所有扫描相关数据
        
        清空内容:
        - 所有任务记录
        - 所有扫描结果
        - 所有漏洞记录
        - 所有POC扫描结果
        - 所有报告记录
        """
        from backend.models import Task, ScanResult, Vulnerability, POCScanResult, Report
        
        logger.info("=" * 50)
        logger.info("开始重置扫描数据...")
        
        try:
            task_count = await Task.all().count()
            scan_result_count = await ScanResult.all().count()
            vuln_count = await Vulnerability.all().count()
            poc_count = await POCScanResult.all().count()
            report_count = await Report.all().count()
            
            logger.info(f"当前数据统计: 任务={task_count}, 扫描结果={scan_result_count}, 漏洞={vuln_count}, POC结果={poc_count}, 报告={report_count}")
            
            await POCScanResult.all().delete()
            logger.info("已清空 POC 扫描结果表")
            
            await Vulnerability.all().delete()
            logger.info("已清空漏洞表")
            
            await ScanResult.all().delete()
            logger.info("已清空扫描结果表")
            
            await Report.all().delete()
            logger.info("已清空报告表")
            
            await Task.all().delete()
            logger.info("已清空任务表")
            
            self.queued_task_ids.clear()
            self.cancelled_task_ids.clear()
            self.running_task_id = None
            self.task_processes.clear()
            self.task_heartbeats.clear()
            self.task_start_times.clear()
            self.task_timeouts.clear()
            self._persisted_tasks.clear()
            self._save_task_states()
            logger.info("已清空内存中的任务状态")
            
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            logger.info("已清空任务队列")
            
            logger.info("扫描数据重置完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"重置扫描数据失败: {e}", exc_info=True)
            raise

    async def recover_pending_tasks(self):
        """
        恢复未完成的任务
        
        应用重启后，检查数据库中处于 pending/running 状态的任务，
        将其重新加入执行队列。
        """
        from backend.models import Task
        
        logger.info("=" * 50)
        logger.info("开始恢复未完成任务...")
        
        try:
            pending_tasks = await Task.filter(
                status__in=['pending', 'running', 'queued']
            ).order_by('created_at')
            
            recovered_count = 0
            for task in pending_tasks:
                try:
                    scan_config = json.loads(task.config) if task.config else {}
                    
                    task_state_logger.log_task_recovery(
                        task_id=task.id,
                        task_type=task.task_type,
                        status=task.status
                    )
                    
                    if task.status == 'running':
                        task.status = 'pending'
                        task.progress = 0
                        task.error_message = "Task interrupted by system restart, retrying..."
                        await task.save()
                    
                    await self.start_task(task.id, task.target, scan_config)
                    recovered_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to recover task {task.id}: {e}")
                    structured_logger.error(
                        "Task recovery failed",
                        task_id=task.id,
                        exc=e
                    )
            
            logger.info(f"任务恢复完成，共恢复 {recovered_count} 个任务")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"任务恢复过程出错: {e}", exc_info=True)

    async def _publish_state_change(self, task_id: int, status: str, details: Dict = None):
        """
        发布状态变更消息 (MySQL + MQ + WebSocket)
        Requirement 3.3
        """
        # 1. MySQL is updated by caller usually, but we ensure consistency here if needed
        # (Caller handles DB save for now to avoid async race in critical paths)
        
        # 2. WebSocket
        payload = {
            "task_id": task_id,
            "status": status
        }
        if details:
            payload.update(details)
            
        await manager.broadcast({
            "type": "task_update",
            "payload": payload
        })
        
        # 3. MQ (agent.status.change)
        if self.kafka_producer:
            try:
                msg = {
                    "task_id": task_id,
                    "status": status,
                    "timestamp": time.time(),
                    "details": details or {}
                }
                self.kafka_producer.send("agent.status.change", msg)
            except Exception as e:
                logger.error(f"Failed to send to Kafka: {e}")

    def start_worker(self):
        """启动后台工作协程"""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("任务执行器Worker已启动")

    async def start_task(self, task_id: Union[int, str], target: str, scan_config: Dict):
        """
        提交任务到执行队列
        
        Args:
            task_id: 任务ID
            target: 目标地址
            scan_config: 扫描配置
        """
        logger.info(f"[任务提交] 开始处理 | 任务ID: {task_id} | 目标: {target} | 配置: {scan_config}")
        
        if task_id in self.queued_task_ids:
            logger.warning(f"[任务提交] 任务已在队列中,忽略重复提交 | 任务ID: {task_id}")
            return
            
        if task_id == self.running_task_id:
            logger.warning(f"[任务提交] 任务正在执行中,忽略重复提交 | 任务ID: {task_id}")
            return

        task_info = {
            'task_id': task_id,
            'target': target,
            'scan_config': scan_config or {}
        }
        
        self.queued_task_ids.add(task_id)
        await self.queue.put(task_info)
        
        self._persist_task_state(task_id, {
            "status": "queued",
            "target": target,
            "scan_config": scan_config or {}
        })
        
        task_state_logger.log_task_created(
            task_id=task_id,
            task_type=scan_config.get('task_type', 'unknown') if scan_config else 'unknown',
            target=target
        )
        
        logger.info(f"[任务提交] 任务已添加到队列 | 任务ID: {task_id} | 队列位置: {self.queue.qsize()}")
        
        await manager.broadcast({
            "type": "task_update",
            "payload": {
                "task_id": task_id,
                "status": "queued",
                "queue_position": self.queue.qsize()
            }
        })
        
        self.start_worker()

    async def cancel_task(self, task_id: Union[int, str]) -> bool:
        """
        取消任务 (已废弃，请使用 abort_task)
        """
        self.abort_task(task_id)
        return True

    async def _worker(self):
        """后台工作协程: 串行消费队列"""
        while self.is_running:
            try:
                task_info = await self.queue.get()
                task_id = task_info['task_id']
                target = task_info.get('target', 'unknown')
                scan_config = task_info.get('scan_config', {})
                
                logger.info(f"[Worker] 获取到任务 | 任务ID: {task_id} | 目标: {target} | 队列剩余: {self.queue.qsize()}")
                
                if task_id in self.cancelled_task_ids:
                    logger.info(f"[Worker] 任务已被取消,跳过执行 | 任务ID: {task_id}")
                    self.cancelled_task_ids.discard(task_id)
                    self.queued_task_ids.discard(task_id)
                    self._remove_task_state(task_id)
                    self.queue.task_done()
                    continue

                self.queued_task_ids.discard(task_id)
                self.running_task_id = task_id
                self.task_start_times[task_id] = time.time()
                
                try:
                    from backend.models import Task
                    task = await Task.get(id=task_id)
                    task_type = task.task_type
                    timeout = self._get_task_timeout(task_type, scan_config)
                    self.task_timeouts[task_id] = timeout
                except:
                    timeout = self._get_task_timeout('default', scan_config)
                    self.task_timeouts[task_id] = timeout
                    task_type = 'unknown'
                
                self._persist_task_state(task_id, {
                    "status": "running",
                    "target": target,
                    "task_type": task_type if 'task_type' in dir() else 'unknown',
                    "timeout": timeout,
                    "started_at": datetime.now(datetime.UTC).isoformat()
                })
                
                task_state_logger.log_task_started(
                    task_id=task_id,
                    task_type=task_type if 'task_type' in dir() else 'unknown',
                    target=target,
                    timeout=timeout
                )
                
                try:
                    logger.info(f"[Worker] 开始处理任务 | 任务ID: {task_id} | 目标: {target} | 超时: {timeout}s")
                    
                    await manager.broadcast({
                        "type": "task_update",
                        "payload": {
                            "task_id": task_id,
                            "status": "running",
                            "progress": 0,
                            "timeout": timeout
                        }
                    })
                    logger.info(f"[Worker] 任务开始执行 | 任务ID: {task_id} | 目标: {target} | 超时: {timeout}s")
                    self.current_execution_task = asyncio.create_task(self._execute_wrapper(task_info))
                    
                    await asyncio.wait_for(
                        self.current_execution_task,
                        timeout=timeout
                    )
                    
                    duration = time.time() - self.task_start_times.get(task_id, time.time())
                    logger.info(f"[Worker] 任务执行成功 | 任务ID: {task_id} | 目标: {target} | 耗时: {duration:.2f}s")
                    task_state_logger.log_task_completed(
                        task_id=task_id,
                        duration=duration
                    )
                    self._remove_task_state(task_id)
                    
                except asyncio.TimeoutError:
                    duration = time.time() - self.task_start_times.get(task_id, time.time())
                    logger.error(f"[Worker] 任务执行超时 | 任务ID: {task_id} | 超时限制: {timeout}s | 实际耗时: {duration:.2f}s")
                    
                    task_state_logger.log_task_timeout(
                        task_id=task_id,
                        timeout_seconds=timeout
                    )
                    
                    if self.current_execution_task and not self.current_execution_task.done():
                        self.current_execution_task.cancel()
                        try:
                            await asyncio.wait_for(self.current_execution_task, timeout=5)
                        except:
                            pass
                    
                    await self._handle_task_timeout(task_id, timeout)
                    
                except asyncio.CancelledError:
                    logger.warning(f"[Worker] 任务被取消 | 任务ID: {task_id}")
                    
                    if task_id in self.cancelled_task_ids:
                        logger.info(f"[Worker] 确认任务已响应取消信号 | 任务ID: {task_id}")
                        self.cancelled_task_ids.discard(task_id)
                        task_state_logger.log_task_cancelled(task_id=task_id, reason="User requested")
                        self._remove_task_state(task_id)
                        try:
                            from backend.models import Task
                            task = await Task.get(id=task_id)
                            task.status = 'cancelled'
                            await task.save()
                        except:
                            pass
                    else:
                        raise
                        
                except Exception as e:
                    logger.error(f"[Worker] 任务执行发生未捕获异常 | 任务ID: {task_id} | 错误: {e}", exc_info=True)
                    structured_logger.error(
                        "Task execution error",
                        task_id=task_id,
                        exc=e
                    )
                    await self._handle_task_failure(task_id, f"System Error: {str(e)}")
                    self._remove_task_state(task_id)
                finally:
                    logger.info(f"[Worker] 任务处理完成,清理状态 | 任务ID: {task_id}")
                    self.running_task_id = None
                    self.current_execution_task = None
                    if task_id in self.task_start_times:
                        del self.task_start_times[task_id]
                    if task_id in self.task_timeouts:
                        del self.task_timeouts[task_id]
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info("Worker被取消,停止运行")
                break
            except Exception as e:
                logger.error(f"Worker循环异常: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _handle_task_timeout(self, task_id: int, timeout_seconds: int):
        """处理任务超时"""
        try:
            from backend.models import Task
            task = await Task.get(id=task_id)
            task.status = 'failed'
            task.progress = task.progress or 0
            
            try:
                current_result = json.loads(task.result) if task.result else {}
            except:
                current_result = {}
                
            current_result['error'] = f"Task execution timed out after {timeout_seconds} seconds"
            current_result['timeout'] = True
            current_result['timeout_seconds'] = timeout_seconds
            task.result = json.dumps(current_result)
            
            await task.save()
            
            await manager.broadcast({
                "type": "task_completed",
                "payload": {
                    "task_id": task_id,
                    "status": "failed",
                    "error": f"Task timed out after {timeout_seconds}s",
                    "timeout": True
                }
            })
        except Exception as e:
            logger.error(f"更新任务 {task_id} 超时状态出错: {e}")

    async def _execute_wrapper(self, task_info: Dict):
        """任务执行分发包装器"""
        task_id = task_info['task_id']
        target = task_info['target']
        scan_config = task_info['scan_config']
        
        try:
            from backend.models import Task
            task = await Task.get(id=task_id)
            task_type = task.task_type
            
            if task_type == 'poc_scan':
                await self.execute_poc_task(task_id, target, scan_config)
            elif task_type == 'awvs_scan':
                await self.execute_scan_task(task_id, target, scan_config)
            elif task_type == 'ai_agent_scan':
                await self.execute_agent_task(task_id, target, scan_config)
            else:
                logger.warning(f"未知任务类型 {task_type}, 任务ID: {task_id}")
                # TODO：解决未知任务类型的问题
                await self.execute_plugin_task(task_id, target, scan_config, task_type)
        except Exception as e:
            logger.error(f"任务分发失败: {e}")
            raise

    async def _handle_task_failure(self, task_id: int, error_msg: str, exc: Exception = None):
        """统一失败处理"""
        try:
            from backend.models import Task
            task = await Task.get(id=task_id)
            task.status = 'failed'
            task.progress = task.progress or 0
            
            try:
                current_result = json.loads(task.result) if task.result else {}
            except:
                current_result = {}
                
            current_result['error'] = error_msg
            if exc:
                current_result['error_type'] = type(exc).__name__
            task.result = json.dumps(current_result)
            
            await task.save()
            
            task_state_logger.log_task_failed(
                task_id=task_id,
                error=error_msg,
                exc=exc
            )
            
            await manager.broadcast({
                "type": "task_completed",
                "payload": {
                    "task_id": task_id,
                    "status": "failed",
                    "error": error_msg
                }
            })
        except Exception as e:
            logger.error(f"更新任务 {task_id} 失败状态出错: {e}")

    async def execute_agent_task(self, task_id: int, target: str, scan_config: Dict):
        """
        执行AI Agent扫描任务
        """
        from backend.models import Task, Vulnerability, Report
        from backend.ai_agents.core.state import AgentState
        from backend.ai_agents.core.graph import ScanAgentGraph
        
        task = await Task.get(id=task_id)
        task.status = 'running'
        task.progress = 5
        await task.save()
        
        logger.info(f"AI Agent任务 {task_id} 开始执行: {target}")
        
        # 1. 初始化状态
        # 从 scan_config 中提取参数
        user_tools = scan_config.get('user_tools', [])
        user_requirement = scan_config.get('user_requirement', '')
        memory_info = scan_config.get('memory_info', '')
        
        initial_state = AgentState(
            target=target,
            task_id=str(task_id),  # 传递任务ID用于WebSocket广播
            target_context=scan_config or {},
            user_tools=user_tools,
            user_requirement=user_requirement,
            memory_info=memory_info
        )
        
        # 从配置中提取特定字段到状态属性
        if scan_config and "custom_tasks" in scan_config and scan_config["custom_tasks"]:
            initial_state.planned_tasks = scan_config["custom_tasks"]
        
        # 2. 构建并编译图
        agent_graph = ScanAgentGraph()
        app = agent_graph.graph.compile()
        
        # 3. 执行工作流
        # 使用 ainvoke 异步执行
        final_state = await app.ainvoke(initial_state)
        
        # 4. 处理结果
        task.status = 'completed'
        task.progress = 100
        
        # 提取结果（兼容对象和字典模式）
        def get_state_value(state, key, default):
            if state is None:
                return default
            if isinstance(state, dict):
                return state.get(key, default)
            return getattr(state, key, default)

        scan_summary = get_state_value(final_state, 'scan_summary', {})
        vulnerabilities = get_state_value(final_state, 'vulnerabilities', [])
        report_content = get_state_value(final_state, 'report', "")
        
        history_data = get_state_value(final_state, 'execution_history', [])
        execution_history = [
            {
                "node": h.get("node", "") if isinstance(h, dict) else getattr(h, "node", ""),
                "action": h.get("action", "") if isinstance(h, dict) else getattr(h, "action", ""),
                "result": sanitize_json_data(h.get("result", "") if isinstance(h, dict) else getattr(h, "result", "")),
                "timestamp": h.get("timestamp", "") if isinstance(h, dict) else getattr(h, "timestamp", "")
            } for h in history_data
        ]
        
        stage_status = get_state_value(final_state, 'stage_status', {})

        result_data = {
            "scan_summary": scan_summary,
            "vulnerabilities": vulnerabilities,
            "report": report_content,
            "execution_history": execution_history,
            "stages": stage_status
        }
        
        # Sanitize entire result data to ensure no circular references exist in any field
        result_data = sanitize_json_data(result_data)
        
        task.result = json.dumps(result_data, default=str)
        await task.save()
        
        # 5. 持久化漏洞信息
        for vuln in vulnerabilities:
            try:
                await Vulnerability.create(
                    task=task,
                    vuln_type=vuln.get('type', 'Unknown'),
                    severity=self.standardize_severity(vuln.get('severity', 'Info')),
                    title=vuln.get('title', 'Unknown Vulnerability'),
                    description=vuln.get('description', ''),
                    url=vuln.get('url', target),
                    payload=vuln.get('payload', ''),
                    evidence=vuln.get('evidence', ''),
                    remediation=vuln.get('remediation', ''),
                    source='ai_agent'
                )
            except Exception as e:
                logger.error(f"Failed to save vulnerability: {e}")

        # 6. 生成/保存报告
        if report_content:
            try:
                await Report.create(
                    task=task,
                    report_name=f"Scan Report - {target}",
                    report_type="markdown",
                    content=report_content
                )
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        
        logger.info(f"AI Agent任务 {task_id} 执行完成")
        
        # 广播任务完成
        await manager.broadcast({
            "type": "task_completed",
            "payload": {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "result": result_data
            }
        })

    def standardize_severity(self, severity_val) -> str:
        """标准化严重程度 (Title Case)"""
        if isinstance(severity_val, int):
            if severity_val >= 4: return 'Critical'
            if severity_val == 3: return 'High'
            if severity_val == 2: return 'Medium'
            if severity_val == 1: return 'Low'
            return 'Info'
        
        if isinstance(severity_val, str):
            s = severity_val.lower()
            if s == 'critical': return 'Critical'
            if s == 'high': return 'High'
            if s == 'medium': return 'Medium'
            if s == 'low': return 'Low'
            if s == 'info': return 'Info'
            return severity_val.capitalize()
        
        return 'Info'
    
    async def execute_scan_task(self, task_id: int, target: str, scan_config: Dict):
        """
        执行AWVS扫描任务并实时更新进度
        """
        try:
            from backend.models import Task
            from AVWS.API.Target import Target
            from AVWS.API.Scan import Scan
            from backend.config import settings
            
            # 获取任务
            task = await Task.get(id=task_id)
            
            # 初始化AWVS客户端
            target_client = Target(settings.AWVS_API_URL, settings.AWVS_API_KEY)
            scan_client = Scan(settings.AWVS_API_URL, settings.AWVS_API_KEY)
            
            # 更新任务状态为运行中
            task.status = 'running'
            task.progress = 5
            await task.save()
            logger.info(f"任务 {task_id} 开始执行: {target}")
            
            # 创建AWVS目标
            target_desc = f"Task {task_id}: {task.task_name}"
            target_id = target_client.add(target, target_desc)
            
            if not target_id:
                task.status = 'failed'
                task.progress = 0
                task.error_message = "Failed to create AWVS target"
                await task.save()
                logger.error(f"任务 {task_id} 创建目标失败")
                return
            
            logger.info(f"任务 {task_id} 创建AWVS目标成功: {target_id}")
            
            # 更新任务配置,保存target_id
            current_config = json.loads(task.config) if task.config else {}
            current_config['awvs_target_id'] = target_id
            task.config = json.dumps(current_config)
            
            task.progress = 10
            await task.save()
            
            # 启动扫描
            scan_profile = scan_config.get('profile', 'full_scan')
            scan_id = scan_client.add(target_id, scan_profile)
            
            if not scan_id:
                task.status = 'failed'
                task.progress = 0
                await task.save()
                logger.error(f"任务 {task_id} 启动扫描失败")
                return
            
            logger.info(f"任务 {task_id} 启动AWVS扫描成功, ID: {scan_id}")
            
            task.progress = 20
            
            # 更新任务配置,保存scan_id
            current_config['awvs_scan_id'] = scan_id
            task.config = json.dumps(current_config)
            await task.save()
            
            # 开始监控扫描进度
            await self._monitor_scan_progress(task_id, scan_id, scan_client)
            
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}", exc_info=True)
            try:
                from backend.models import Task
                task = await Task.get(id=task_id)
                task.status = 'failed'
                task.progress = 0
                await task.save()
            except:
                pass
    
    async def _monitor_scan_progress(self, task_id: int, scan_id: str, scan_client):
        """监控扫描进度"""
        from backend.models import Task
        
        last_progress = 20
        no_change_count = 0
        max_no_change = 360  # 30分钟无变化才超时 (360 * 5s = 1800s)
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_running:
            try:
                loop = asyncio.get_running_loop()
                # 使用 to_thread 避免阻塞事件循环
                scan_info = await loop.run_in_executor(None, scan_client.get, scan_id)
                
                if not scan_info:
                    consecutive_errors += 1
                    logger.warning(f"任务 {task_id} 获取扫描状态失败 ({consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"任务 {task_id} 获取扫描状态连续失败, 停止监控")
                        break
                    await asyncio.sleep(5)
                    continue
                
                # 重置错误计数
                consecutive_errors = 0
                
                progress = self._calculate_progress(scan_info)
                
                if progress == last_progress:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_progress = progress
                
                task = await Task.get(id=task_id)
                scan_status = scan_info.get('status', 'unknown')
                
                if scan_status == 'completed':
                    task.status = 'completed'
                    task.progress = 100
                    await task.save()
                    logger.info(f"任务 {task_id} 扫描完成")
                    await self._save_scan_results(task_id, scan_id, scan_client)

                    # 广播任务完成
                    await manager.broadcast({
                        "type": "task_completed",
                        "payload": {
                            "task_id": task_id,
                            "status": "completed",
                            "progress": 100,
                            "result": json.loads(task.result) if task.result else {}
                        }
                    })
                    break
                elif scan_status == 'failed':
                    task.status = 'failed'
                    task.progress = last_progress
                    await task.save()
                    logger.error(f"任务 {task_id} 扫描失败")
                    
                    # 广播任务失败
                    await manager.broadcast({
                        "type": "task_completed",
                        "payload": {
                            "task_id": task_id,
                            "status": "failed",
                            "error": "Scan failed in AWVS"
                        }
                    })
                    break
                elif scan_status == 'processing':
                    task.progress = progress
                    await task.save()
                    logger.info(f"任务 {task_id} 进度: {progress}%")
                    
                    # 广播进度更新
                    await manager.broadcast({
                        "type": "task_progress",
                        "payload": {
                            "task_id": task_id,
                            "progress": progress,
                            "status": "running"
                        }
                    })
                elif scan_status == 'scheduled':
                    task.progress = 20
                    await task.save()
                    logger.info(f"任务 {task_id} 等待开始...")
                
                if no_change_count >= max_no_change:
                    # AWVS 可能会在某个进度停留很久, 30分钟无变化再判定为超时
                    # 即使超时, 也尝试保存结果
                    task.status = 'completed' # 或者 failed? 视业务逻辑而定,这里保持原逻辑但增加日志
                    task.progress = 100
                    await task.save()
                    logger.warning(f"任务 {task_id} 扫描进度长时间({max_no_change*5}s)无变化, 强制完成")
                    await self._save_scan_results(task_id, scan_id, scan_client)
                    
                    await manager.broadcast({
                        "type": "task_completed",
                        "payload": {
                            "task_id": task_id,
                            "status": "completed",
                            "progress": 100,
                            "note": "completed_by_timeout",
                            "result": json.loads(task.result) if task.result else {}
                        }
                    })
                    break
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"任务 {task_id} 监控进度失败: {str(e)}", exc_info=True)
                await asyncio.sleep(5)

    def _calculate_progress(self, scan_info: Dict) -> int:
        status = scan_info.get('status', 'unknown')
        if status == 'scheduled':
            return 20
        elif status == 'processing':
            requests_count = scan_info.get('requests_count', 0)
            processed_requests = scan_info.get('processed_requests_count', 0)
            if requests_count > 0:
                progress = int((processed_requests / requests_count) * 80) + 20
                return min(progress, 95)
            else:
                return 30
        elif status == 'completed':
            return 100
        elif status == 'failed':
            return 0
        else:
            return 20

    # INSPECTION:检查扫描结果是否完整
    async def _save_scan_results(self, task_id: int, scan_id: str, scan_client):
        try:
            from backend.models import Task, Vulnerability
            from backend.api.tasks import standardize_severity

            scan_info = scan_client.get(scan_id)
            if not scan_info:
                return
            
            vulnerabilities_summary = []
            scan_session_id = scan_info.get('current_session', {}).get('scan_session_id')
            
            if scan_session_id:
                vulns = scan_client.get_vulns(scan_id, scan_session_id)
                if vulns:
                    # 获取现有漏洞记录以避免重复 (根据 vuln_id)
                    existing_vulns = await Vulnerability.filter(task_id=task_id).values_list('title', flat=True) # 使用title作为简单去重,实际应存vuln_id
                    # 由于Vulnerability模型目前没有 awvs_vuln_id 字段,我们暂时用 title 和 url 组合判断,或者直接清空重建
                    # 为了安全起见,我们先删除该任务的所有旧漏洞记录,重新保存
                    await Vulnerability.filter(task_id=task_id).delete()
                    
                    for vuln in vulns:
                        # 1. 保存到 vulnerabilities_summary 用于 task.result (保持兼容)
                        severity_val = vuln.get('severity')
                        severity_str = standardize_severity(severity_val)
                        
                        vulnerabilities_summary.append({
                            'severity': severity_str, # Use standardized severity string
                            'name': vuln.get('vt_name'),
                            'count': vuln.get('count', 0)
                        })
                        
                        # 2. 保存到 Vulnerability 表 (详细存储)
                        
                        # 处理标题前缀
                        vt_name = vuln.get('vt_name', 'Unknown')
                        if 'SQL Injection' in vt_name and not vt_name.startswith('[SQL'):
                            vt_name = f"[SQL Injection] {vt_name}"
                        elif 'XSS' in vt_name and not vt_name.startswith('[XSS'):
                            vt_name = f"[XSS] {vt_name}"
                        
                        # 确保 url 字段存在
                        affects_url = vuln.get('affects_url', '')
                        if not affects_url:
                            affects_url = task.target

                        await Vulnerability.create(
                            task_id=task_id,
                            vuln_type=vuln.get('vt_name'), # 原始类型
                            severity=severity_str,
                            title=vt_name,
                            description=vuln.get('description', ''),
                            url=affects_url,
                            status=vuln.get('status', 'open'),
                            source_id=vuln.get('vuln_id')
                        )

            result_data = {
                'scan_id': scan_id,
                'scan_status': scan_info.get('status'),
                'start_time': scan_info.get('start_time'),
                'end_time': scan_info.get('end_time'),
                'requests_count': scan_info.get('requests_count', 0),
                'vulnerabilities_count': scan_info.get('vulnerabilities_count', 0),
                'vulnerabilities': vulnerabilities_summary
            }
            
            task = await Task.get(id=task_id)
            task.result = json.dumps(result_data)
            await task.save()
            logger.info(f"任务 {task_id} 保存扫描结果成功 (包含详细漏洞记录)")
        except Exception as e:
            logger.error(f"任务 {task_id} 保存扫描结果失败: {str(e)}", exc_info=True)

    async def execute_poc_task(self, task_id: int, target: str, scan_config: Dict):
        """执行POC扫描任务 (Dynamic Engine Integrated)"""
        try:
            from backend.models import Task, POCScanResult, VulnerabilityKB
            from tortoise.expressions import Q
            
            task = await Task.get(id=task_id)
            task.status = 'running'
            task.progress = 5
            await task.save()
            
            logger.info(f"Starting POC verification task {task_id} for {target}")
            
            # 1. Determine vulnerabilities to verify
            vulns_to_verify = []
            
            # Case A: Explicit vulnerability list (from Agent or previous scan)
            if 'vulnerabilities' in scan_config:
                vulns_to_verify = scan_config['vulnerabilities']
                
            # Case B: POC types/names/CVEs (Legacy/Manual)
            elif 'poc_types' in scan_config:
                requested_pocs = scan_config['poc_types']
                use_all = not requested_pocs or 'all' in requested_pocs
                
                if use_all:
                    # Get all KB entries with POCs
                    kb_pocs = await VulnerabilityKB.filter(has_poc=True).all()
                else:
                    kb_pocs = []
                    for req in requested_pocs:
                        items = await VulnerabilityKB.filter(Q(name=req) | Q(cve_id=req)).all()
                        kb_pocs.extend(items)
                
                # Convert KB items to vuln_info dicts
                for kb in kb_pocs:
                    vulns_to_verify.append({
                        "title": kb.name,
                        "cve_id": kb.cve_id,
                        "description": kb.description,
                        "severity": kb.severity,
                        "poc_code": kb.poc_code 
                    })

            if not vulns_to_verify:
                logger.warning(f"Task {task_id}: No vulnerabilities to verify")
                task.status = 'completed'
                task.result = json.dumps({'message': 'No vulnerabilities selected'})
                await task.save()
                return

            # 2. Execute Dynamic Verification (Parallel)
            total_vulns = len(vulns_to_verify)
            completed_count = 0
            vulnerable_count = 0
            results_summary = []
            
            # Batch size to avoid overwhelming
            batch_size = 5
            
            for i in range(0, total_vulns, batch_size):
                if not self.is_running:
                    break

                batch = vulns_to_verify[i:i+batch_size]
                tasks = []
                for vuln in batch:
                    # Ensure vuln is a dict
                    if not isinstance(vuln, dict):
                        continue
                    tasks.append(dynamic_engine.verify_vulnerability(target, vuln))
                
                if not tasks:
                    continue

                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for res in batch_results:
                    if isinstance(res, Exception):
                        logger.error(f"Verification error in task {task_id}: {res}")
                        continue
                        
                    results_summary.append(res)
                    
                    if res.get('vulnerable'):
                        vulnerable_count += 1
                        # Create legacy POCScanResult for compatibility
                        try:
                            await POCScanResult.create(
                                task=task,
                                poc_type=res.get('poc_id', 'unknown'),
                                target=target,
                                vulnerable=True,
                                message=str(res.get('output', ''))[:500],
                                severity="High", 
                                cve_id=res.get('cve_id')
                            )
                        except Exception as e:
                            logger.error(f"Failed to save POCScanResult: {e}")

                completed_count += len(batch)
                task.progress = int((completed_count / total_vulns) * 100)
                await task.save()

            # 3. Finalize
            task.status = 'completed'
            task.result = json.dumps({
                'total': total_vulns,
                'vulnerable_count': vulnerable_count,
                'details': results_summary
            }, default=str)
            await task.save()
            logger.info(f"Task {task_id} POC verification completed")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            await self._handle_task_failure(task_id, str(e))

    async def _run_kb_poc(self, kb_obj, target):
        """执行知识库 POC (基于 Pocsuite3)"""
        import tempfile
        import os
        from pocsuite3.api import init_pocsuite
        from pocsuite3.lib.core.data import logger as poc_logger
        
        # 禁用 pocsuite3 的控制台日志
        poc_logger.setLevel(logging.ERROR)
        
        try:
            # 将 POC 代码写入临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(kb_obj.poc_code)
                tmp_path = tmp.name
            
            try:
                # 配置 Pocsuite3
                config = {
                    'url': target,
                    'poc': tmp_path,
                    'quiet': True
                }
                
                # 在线程中运行 Pocsuite3，因为它是阻塞的
                loop = asyncio.get_running_loop()
                
                def run_pocsuite():
                    # 捕获 stdout
                    import io
                    import sys
                    capture = io.StringIO()
                    old_stdout = sys.stdout
                    sys.stdout = capture
                    
                    try:
                        init_pocsuite(config)
                    except Exception as e:
                        print(f"Error: {e}")
                    finally:
                        sys.stdout = old_stdout
                        
                    return capture.getvalue()

                output = await loop.run_in_executor(None, run_pocsuite)
                
                # 分析输出判断是否成功
                # Pocsuite3 输出通常包含 "success" 或 "vulnerable"
                is_vulnerable = "success" in output.lower() or "vulnerable" in output.lower()
                
                # 尝试提取输出中的有用信息
                msg = "Vulnerable" if is_vulnerable else "Not Vulnerable"
                if len(output) > 200:
                    msg += f" (Output truncated: {output[:200]}...)"
                else:
                    msg += f" ({output.strip()})"
                    
                return is_vulnerable, msg
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"KB POC Execution Error: {e}")
            return False, str(e)

    def update_heartbeat(self, task_id: int):
        """更新任务心跳"""
        self.task_heartbeats[task_id] = time.time()

    async def execute_plugin_task(self, task_id: int, target: str, scan_config: Dict, task_type: str):
        """执行通用插件扫描任务 (多进程版)"""
        try:
            from backend.models import Task
            task = await Task.get(id=task_id)
            task.status = 'running'
            task.progress = 10
            await task.save()
            
            logger.info(f"插件任务 {task_id} ({task_type}) 开始执行: {target}")
            
            agent_url = f"http://{settings.HOST}:{settings.PORT}"
            
            # 初始化心跳
            self.task_heartbeats[task_id] = time.time()
            
            # 启动进程
            p = multiprocessing.Process(
                target=run_plugin_process,
                args=(task_id, task_type, target, scan_config, agent_url)
            )
            p.start()
            self.task_processes[task_id] = p
            self.running_task_id = task_id
            
            # 设置硬超时 (Requirement 4.1)
            # 端口扫描 ≤ 15 min, WAF 识别 ≤ 5 min, AWVS 扫描 ≤ 5 hours
            timeout_seconds = 300 # default 5 min
            if task_type == 'port_scan': timeout_seconds = 15 * 60
            elif task_type == 'waf_check': timeout_seconds = 5 * 60
            elif task_type == 'awvs_scan': timeout_seconds = 5 * 60 * 60
            
            start_time = time.time()
            
            # 等待进程结束或被取消
            try:
                while p.is_alive():
                    # 检查是否取消
                    if task_id in self.cancelled_task_ids:
                        logger.info(f"检测到任务 {task_id} 取消信号，终止进程")
                        self._kill_process(p, task_id)
                        task = await Task.get(id=task_id)
                        task.status = 'aborted'
                        await task.save()
                        break
                    
                    # 检查硬超时 (4.1)
                    if time.time() - start_time > timeout_seconds:
                        logger.warning(f"任务 {task_id} 超时 ({timeout_seconds}s)，强制终止")
                        self._kill_process(p, task_id)
                        task = await Task.get(id=task_id)
                        task.status = 'failed'
                        task.result = json.dumps({"error": "Task execution timed out"})
                        await task.save()
                        break
                    
                    # 检查心跳 (4.2)
                    # 累计 3 次未收到心跳 (30s * 3 = 90s)
                    last_hb = self.task_heartbeats.get(task_id, start_time)
                    if time.time() - last_hb > 90:
                        logger.warning(f"任务 {task_id} 心跳丢失 (>90s)，强制终止")
                        self._kill_process(p, task_id)
                        task = await Task.get(id=task_id)
                        task.status = 'aborted' # Or failed? Requirement says 'trigger abort'
                        task.result = json.dumps({"error": "Heartbeat lost"})
                        await task.save()
                        break

                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.warning(f"插件任务 {task_id} 协程被取消，正在终止进程...")
                if p.is_alive():
                    self._kill_process(p, task_id)
                raise
            
            # 进程结束后清理
            if task_id in self.task_processes:
                del self.task_processes[task_id]
            if task_id in self.task_heartbeats:
                del self.task_heartbeats[task_id]
            if self.running_task_id == task_id:
                self.running_task_id = None
            
            logger.info(f"插件任务 {task_id} 进程已退出 (ExitCode: {p.exitcode})")
            
            # 检查状态是否已由回调更新 (Requirement 3.2: 30s timeout)
            # 循环检查直到状态改变或超时
            wait_start = time.time()
            while time.time() - wait_start < 30:
                task = await Task.get(id=task_id)
                if task.status != 'running':
                    break
                await asyncio.sleep(1)
            
            task = await Task.get(id=task_id)
            if task.status == 'running':
                # 如果仍为running，说明回调失败或超时
                logger.warning(f"任务 {task_id} 进程退出后 30s 内未收到完成回调，标记为 FAILED")
                if p.exitcode == 0:
                     task.result = json.dumps({"error": "No result callback received (Timeout 30s)"})
                else:
                     task.result = json.dumps({"error": f"Process crashed with exit code {p.exitcode}"})
                task.status = 'failed'
                await task.save()

        except Exception as e:
            logger.error(f"插件任务 {task_id} 执行失败: {str(e)}", exc_info=True)
            try:
                from backend.models import Task
                task = await Task.get(id=task_id)
                task.status = 'failed'
                task.result = json.dumps({'error': str(e)})
                await task.save()
            except:
                pass

    async def _kill_process(self, p, task_id):
        """辅助方法：强制终止进程"""
        p.terminate()
        for _ in range(5):
            if not p.is_alive(): return
            await asyncio.sleep(1)
        if p.is_alive():
            logger.warning(f"任务 {task_id} 未响应 SIGTERM，发送 SIGKILL")
            p.kill()

    def abort_task(self, task_id: int):
        """强制中止任务"""
        logger.info(f"收到强制中止请求: {task_id}")
        self.cancelled_task_ids.add(task_id)
        
        # 如果任务在队列中，标记为取消 (Worker取到时会跳过)
        if task_id in self.queued_task_ids:
            logger.info(f"任务 {task_id} 在队列中，已标记为取消")
            
        # 如果任务正在运行，强制取消协程
        if self.running_task_id == task_id and self.current_execution_task and not self.current_execution_task.done():
            logger.info(f"任务 {task_id} 正在运行，发送取消信号给协程")
            self.current_execution_task.cancel()
        
    async def cancel_task(self, task_id: int):
        """取消任务 (兼容接口)"""
        self.abort_task(task_id)

    async def shutdown(self):
        """
        关闭任务执行器
        
        执行完整的清理流程:
        1. 标记关闭状态
        2. 停止接收新任务
        3. 取消当前运行的任务
        4. 终止所有子进程
        5. 关闭Kafka生产者
        6. 保存任务状态
        7. 清理资源
        """
        if self.is_shutting_down:
            logger.warning("关闭流程已在进行中，跳过重复调用")
            return
        
        self.is_shutting_down = True
        self.is_running = False
        
        logger.info("=" * 50)
        logger.info("开始关闭任务执行器...")
        logger.info(f"当前队列任务数: {self.queue.qsize()}")
        logger.info(f"当前运行任务ID: {self.running_task_id}")
        logger.info(f"当前活跃进程数: {len(self.task_processes)}")
        logger.info(f"持久化任务状态数: {len(self._persisted_tasks)}")
        logger.info("=" * 50)
        
        if self.worker_task and not self.worker_task.done():
            logger.info("[1/6] 正在取消Worker任务...")
            self.worker_task.cancel()
            try:
                await asyncio.wait_for(self.worker_task, timeout=5)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logger.warning("[1/6] Worker取消超时")
            logger.info("[1/6] Worker已取消")
        else:
            logger.info("[1/6] Worker未运行，跳过")
        
        if self.current_execution_task and not self.current_execution_task.done():
            logger.info("[2/6] 正在取消当前执行任务...")
            self.current_execution_task.cancel()
            try:
                await asyncio.wait_for(self.current_execution_task, timeout=5)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logger.warning("[2/6] 当前任务取消超时")
            logger.info("[2/6] 当前任务已取消")
        else:
            logger.info("[2/6] 无正在执行的任务，跳过")
        
        if self.task_processes:
            logger.info(f"[3/6] 正在终止 {len(self.task_processes)} 个子进程...")
            terminated_count = 0
            for task_id, process in list(self.task_processes.items()):
                if process.is_alive():
                    logger.info(f"  终止进程: Task {task_id} (PID: {process.pid})")
                    try:
                        process.terminate()
                        process.join(timeout=3)
                        if process.is_alive():
                            logger.warning(f"  进程 {process.pid} 未响应SIGTERM，发送SIGKILL")
                            process.kill()
                            process.join(timeout=2)
                            if process.is_alive():
                                logger.error(f"  进程 {process.pid} 仍然存活，强制关闭")
                                process.terminate()
                                process.join(timeout=1)
                        terminated_count += 1
                    except Exception as e:
                        logger.error(f"  终止进程 {process.pid} 时出错: {e}")
            self.task_processes.clear()
            logger.info(f"[3/6] 已终止 {terminated_count} 个子进程")
        else:
            logger.info("[3/6] 无活跃子进程，跳过")
        
        if self.kafka_producer:
            logger.info("[4/6] 正在关闭Kafka生产者...")
            try:
                self.kafka_producer.flush(timeout=5)
                self.kafka_producer.close(timeout=5)
                logger.info("[4/6] Kafka生产者已关闭")
            except Exception as e:
                logger.error(f"[4/6] 关闭Kafka生产者时发生错误: {e}")
            finally:
                self.kafka_producer = None
        else:
            logger.info("[4/6] Kafka生产者未初始化，跳过")
        
        logger.info("[5/6] 正在保存任务状态...")
        self._save_task_states()
        logger.info(f"[5/6] 已保存 {len(self._persisted_tasks)} 个任务状态")
        
        self.queued_task_ids.clear()
        self.cancelled_task_ids.clear()
        self.task_heartbeats.clear()
        self.task_start_times.clear()
        self.task_timeouts.clear()
        self.running_task_id = None
        
        logger.info("[6/6] 正在清空任务队列...")
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("[6/6] 任务队列已清空")
        
        logger.info("=" * 50)
        logger.info("任务执行器关闭完成")
        logger.info("=" * 50)

task_executor = TaskExecutor()
