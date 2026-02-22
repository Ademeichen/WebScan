"""
任务执行器 - 负责执行扫描任务并实时更新进度
"""
import asyncio
import logging
import multiprocessing
import signal
import time
from typing import Dict, Any, Set, Optional, Union
import json
from tortoise.expressions import Q
from backend.api.websocket import manager
from backend.config import settings
from backend.plugin_executor import run_plugin_process
from backend.ai_agents.poc_system.dynamic_engine import dynamic_engine

# Try to import Kafka
try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

logger = logging.getLogger(__name__)


from backend.utils.serializers import sanitize_json_data


class TaskExecutor:
    """
    任务执行器类
    
    功能:
    1. 任务队列管理 (串行执行)
    2. 幂等性检查 (防止重复提交)
    3. 全局超时控制
    4. 统一异常处理
    5. 多进程插件执行与管理
    """
    
    def __init__(self):
        # 任务队列 (串行执行)
        self.queue: asyncio.Queue = asyncio.Queue()
        # 记录在队列中的任务ID (用于幂等性检查)
        self.queued_task_ids: Set[int] = set()
        # 已取消的任务ID集合
        self.cancelled_task_ids: Set[int] = set()
        # 当前正在运行的任务ID
        self.running_task_id: Optional[int] = None
        # 当前正在执行的任务进程
        self.task_processes: Dict[int, multiprocessing.Process] = {}
        # 任务心跳时间 (task_id -> timestamp)
        self.task_heartbeats: Dict[int, float] = {}
        
        self.is_running = True
        self.worker_task = None
        
        self.kafka_producer = None
        self._init_kafka()

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
        
        # 1. 幂等性检查
        if task_id in self.queued_task_ids:
            logger.warning(f"[任务提交] 任务已在队列中,忽略重复提交 | 任务ID: {task_id}")
            return
            
        if task_id == self.running_task_id:
            logger.warning(f"[任务提交] 任务正在执行中,忽略重复提交 | 任务ID: {task_id}")
            return

        # 2. 提交到队列
        task_info = {
            'task_id': task_id,
            'target': target,
            'scan_config': scan_config or {}
        }
        
        self.queued_task_ids.add(task_id)
        await self.queue.put(task_info)
        logger.info(f"[任务提交] 任务已添加到队列 | 任务ID: {task_id} | 队列位置: {self.queue.qsize()}")
        
        # 广播任务入队消息
        await manager.broadcast({
            "type": "task_update",
            "payload": {
                "task_id": task_id,
                "status": "queued",
                "queue_position": self.queue.qsize()
            }
        })
        
        # 确保Worker在运行
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
                # 获取任务
                task_info = await self.queue.get()
                task_id = task_info['task_id']
                target = task_info.get('target', 'unknown')
                
                logger.info(f"[Worker] 获取到任务 | 任务ID: {task_id} | 目标: {target} | 队列剩余: {self.queue.qsize()}")
                
                # 检查是否已取消
                if task_id in self.cancelled_task_ids:
                    logger.info(f"[Worker] 任务已被取消,跳过执行 | 任务ID: {task_id}")
                    self.cancelled_task_ids.discard(task_id)
                    self.queued_task_ids.discard(task_id)
                    self.queue.task_done()
                    continue

                # 状态流转: Queued -> Running
                self.queued_task_ids.discard(task_id)
                self.running_task_id = task_id
                
                try:
                    logger.info(f"[Worker] 开始处理任务 | 任务ID: {task_id} | 目标: {target}")
                    
                    # 广播任务开始消息
                    await manager.broadcast({
                        "type": "task_update",
                        "payload": {
                            "task_id": task_id,
                            "status": "running",
                            "progress": 0
                        }
                    })
                    
                    # 获取全局超时配置 (默认使用 AGENT_MAX_EXECUTION_TIME)
                    timeout = task_info['scan_config'].get('global_timeout', settings.AGENT_MAX_EXECUTION_TIME)
                    
                    # 执行任务 (带超时控制)
                    # 创建Task对象以便可以被取消
                    self.current_execution_task = asyncio.create_task(self._execute_wrapper(task_info))
                    
                    await asyncio.wait_for(
                        self.current_execution_task,
                        timeout=timeout
                    )
                    
                except asyncio.TimeoutError:
                    logger.error(f"[Worker] 任务执行超时 | 任务ID: {task_id} | 超时限制: {timeout}s")
                    # 如果超时，也需要确保任务被取消
                    if self.current_execution_task and not self.current_execution_task.done():
                        self.current_execution_task.cancel()
                    await self._handle_task_failure(task_id, f"Task execution timed out after {timeout}s")
                except asyncio.CancelledError:
                    logger.warning(f"[Worker] 任务被取消 | 任务ID: {task_id}")
                    # 不需要抛出，因为这是预期的取消操作
                    # 但如果是Worker本身被取消，则需要抛出?
                    # 这里捕获的是 wait_for 抛出的 CancelledError，通常是因为 current_execution_task.cancel() 被调用
                    # 或者 wait_for 自身的 outer task 被取消
                    
                    # 检查是否是我们主动取消的任务
                    if task_id in self.cancelled_task_ids:
                        logger.info(f"[Worker] 确认任务已响应取消信号 | 任务ID: {task_id}")
                        self.cancelled_task_ids.discard(task_id)
                        # 更新数据库状态为已取消 (如果 _execute_wrapper 没来得及做)
                        try:
                            from backend.models import Task
                            task = await Task.get(id=task_id)
                            task.status = 'cancelled'
                            await task.save()
                        except:
                            pass
                    else:
                        # 可能是系统关闭导致的取消
                        raise
                        
                except Exception as e:
                    logger.error(f"[Worker] 任务执行发生未捕获异常 | 任务ID: {task_id} | 错误: {e}", exc_info=True)
                    await self._handle_task_failure(task_id, f"System Error: {str(e)}")
                finally:
                    # 状态清理
                    logger.info(f"[Worker] 任务处理完成,清理状态 | 任务ID: {task_id}")
                    self.running_task_id = None
                    self.current_execution_task = None
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info("Worker被取消,停止运行")
                break
            except Exception as e:
                logger.error(f"Worker循环异常: {e}", exc_info=True)
                await asyncio.sleep(1) # 防止死循环

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
                await self.execute_plugin_task(task_id, target, scan_config, task_type)
        except Exception as e:
            logger.error(f"任务分发失败: {e}")
            raise

    async def _handle_task_failure(self, task_id: int, error_msg: str):
        """统一失败处理"""
        try:
            from backend.models import Task
            task = await Task.get(id=task_id)
            task.status = 'failed'
            task.progress = 0
            
            # 尝试保留现有结果或更新错误信息
            try:
                current_result = json.loads(task.result) if task.result else {}
            except:
                current_result = {}
                
            current_result['error'] = error_msg
            task.result = json.dumps(current_result)
            
            await task.save()
            
            # 广播任务失败消息
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
                    
                    # ---------------------------------------------------------
                    # 自动触发 POC 验证 (集成 DynamicVerificationEngine)
                    # ---------------------------------------------------------
                    try:
                        # 重新加载任务获取最新配置
                        task = await Task.get(id=task_id)
                        current_config = json.loads(task.config) if task.config else {}
                        
                        # 检查是否开启自动验证 (默认开启或由 Agent 指定)
                        # 这里我们默认开启对高危漏洞的验证，除非明确禁用
                        auto_verify = current_config.get('auto_verify_poc', True)
                        
                        if auto_verify:
                            from backend.models import Vulnerability
                            
                            # 获取高危漏洞
                            high_risk_vulns = await Vulnerability.filter(
                                task_id=task_id,
                                severity__in=['Critical', 'High']
                            ).all()
                            
                            if high_risk_vulns:
                                logger.info(f"Task {task_id}: Found {len(high_risk_vulns)} high-risk vulnerabilities. Triggering POC verification...")
                                
                                vuln_list = []
                                for v in high_risk_vulns:
                                    vuln_list.append({
                                        "title": v.title,
                                        "description": v.description,
                                        "severity": v.severity,
                                        "url": v.url,
                                        "cve_id": None # AWVS 可能未提供 CVE，由动态引擎后续匹配
                                    })
                                
                                # 创建 POC 验证任务
                                new_task = await Task.create(
                                    task_name=f"Auto POC Verification for Task {task_id}",
                                    task_type="poc_scan",
                                    target=task.target,
                                    status="queued",
                                    progress=0,
                                    config=json.dumps({
                                        "vulnerabilities": vuln_list,
                                        "parent_task_id": task_id,
                                        "source": "auto_trigger_awvs",
                                        "timeout": 3600 # 1 hour timeout for batch verification
                                    })
                                )
                                
                                # 提交到执行队列
                                await self.start_task(new_task.id, task.target, {
                                    "vulnerabilities": vuln_list,
                                    "parent_task_id": task_id,
                                    "source": "auto_trigger_awvs",
                                    "timeout": 3600
                                })
                                logger.info(f"Successfully triggered POC Task {new_task.id}")
                            else:
                                logger.info(f"Task {task_id}: No high-risk vulnerabilities found for POC verification")
                        else:
                            logger.info(f"Task {task_id}: Auto POC verification disabled")
                            
                    except Exception as e:
                        logger.error(f"Failed to auto-trigger POC verification: {e}", exc_info=True)
                    # ---------------------------------------------------------

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
        """关闭任务执行器"""
        self.is_running = False
        
        # 取消Worker
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # 清理队列 (可选)
        logger.info("任务执行器已关闭")

task_executor = TaskExecutor()
