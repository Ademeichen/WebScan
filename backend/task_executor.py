"""
任务执行器 - 负责执行扫描任务并实时更新进度
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
import json
from tortoise.expressions import Q

# Import Plugins
from backend.plugins.portscan.portscan import ScanPort
from backend.plugins.infoleak.infoleak import get_infoleak
from backend.plugins.webside.webside import get_side_info
from backend.plugins.baseinfo.baseinfo import getbaseinfo
from backend.plugins.webweight.webweight import get_web_weight
from backend.plugins.iplocating.iplocating import get_locating
from backend.plugins.cdnexist.cdnexist import iscdn
from backend.plugins.waf.waf import getwaf
from backend.plugins.whatcms.whatcms import getwhatcms
from backend.plugins.subdomain.subdomain import get_subdomain
from backend.plugins.loginfo.loginfo import LogHandler
from backend.plugins.randheader.randheader import get_random_headers
try:
    from dirsearcch.dir_scanner import DirScanner
except ImportError:
    DirScanner = None

# Import POCs
from backend.poc import (
    cve_2020_2551_poc, cve_2018_2628_poc, cve_2018_2894_poc,
    struts2_009_poc, struts2_032_poc, cve_2017_12615_poc,
    cve_2017_12149_poc, cve_2020_10199_poc, cve_2018_7600_poc,
    cve_2022_22965_poc, cve_2022_47986_poc, cve_2020_14756_poc, cve_2023_21839_poc
)

logger = logging.getLogger(__name__)

POC_FUNCTIONS = {
    "weblogic_cve_2020_2551": cve_2020_2551_poc,
    "weblogic_cve_2018_2628": cve_2018_2628_poc,
    "weblogic_cve_2018_2894": cve_2018_2894_poc,
    "weblogic_cve_2020_14756": cve_2020_14756_poc,
    "weblogic_cve_2023_21839": cve_2023_21839_poc,
    "struts2_009": struts2_009_poc,
    "struts2_032": struts2_032_poc,
    "tomcat_cve_2017_12615": cve_2017_12615_poc,
    "tomcat_cve_2022_22965": cve_2022_22965_poc,
    "tomcat_cve_2022_47986": cve_2022_47986_poc,
    "jboss_cve_2017_12149": cve_2017_12149_poc,
    "nexus_cve_2020_10199": cve_2020_10199_poc,
    "drupal_cve_2018_7600": cve_2018_7600_poc,
}

class TaskExecutor:
    """任务执行器类"""
    
    def __init__(self):
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.is_running = True

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
            from models import Task
            from AVWS.API.Target import Target
            from AVWS.API.Scan import Scan
            from config import settings
            
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
            target_data = {
                "address": target,
                "description": f"Task {task_id}: {task.task_name}"
            }
            target_response = target_client.add(target_data)
            
            if not target_response or 'target_id' not in target_response:
                error_detail = f"Response: {target_response}" if target_response else "No response"
                task.status = 'failed'
                task.progress = 0
                task.error_message = f"Failed to create AWVS target. {error_detail}"
                await task.save()
                logger.error(f"任务 {task_id} 创建目标失败. {error_detail}")
                return
            
            target_id = target_response['target_id']
            logger.info(f"任务 {task_id} 创建AWVS目标成功: {target_id}")
            
            # 更新任务配置，保存target_id
            current_config = json.loads(task.config) if task.config else {}
            current_config['awvs_target_id'] = target_id
            task.config = json.dumps(current_config)
            
            task.progress = 10
            await task.save()
            
            # 启动扫描
            scan_profile = scan_config.get('profile', 'full_scan')
            scan_response = scan_client.add(target_id, scan_profile)
            
            if scan_response != 200:
                task.status = 'failed'
                task.progress = 0
                await task.save()
                logger.error(f"任务 {task_id} 启动扫描失败")
                return
            
            logger.info(f"任务 {task_id} 启动AWVS扫描成功")
            
            task.progress = 20
            await task.save()
            
            # 获取扫描ID
            scans = scan_client.get_all()
            scan_id = None
            for scan in scans:
                if scan.get('target_id') == target_id:
                    scan_id = scan.get('scan_id')
                    break
            
            if not scan_id:
                task.status = 'failed'
                task.progress = 0
                await task.save()
                logger.error(f"任务 {task_id} 获取扫描ID失败")
                return
            
            logger.info(f"任务 {task_id} 扫描ID: {scan_id}")

            # 更新任务配置，保存scan_id
            current_config['awvs_scan_id'] = scan_id
            task.config = json.dumps(current_config)
            await task.save()
            
            # 开始监控扫描进度
            await self._monitor_scan_progress(task_id, scan_id, scan_client)
            
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}", exc_info=True)
            try:
                from models import Task
                task = await Task.get(id=task_id)
                task.status = 'failed'
                task.progress = 0
                await task.save()
            except:
                pass
    
    async def _monitor_scan_progress(self, task_id: int, scan_id: str, scan_client):
        """监控扫描进度"""
        from models import Task
        
        last_progress = 20
        no_change_count = 0
        max_no_change = 30
        
        while self.is_running:
            try:
                scan_info = scan_client.get(scan_id)
                if not scan_info:
                    logger.error(f"任务 {task_id} 获取扫描状态失败")
                    break
                
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
                    break
                elif scan_status == 'failed':
                    task.status = 'failed'
                    task.progress = last_progress
                    await task.save()
                    logger.error(f"任务 {task_id} 扫描失败")
                    break
                elif scan_status == 'processing':
                    task.progress = progress
                    await task.save()
                    logger.info(f"任务 {task_id} 进度: {progress}%")
                elif scan_status == 'scheduled':
                    task.progress = 20
                    await task.save()
                    logger.info(f"任务 {task_id} 等待开始...")
                
                if no_change_count >= max_no_change:
                    task.status = 'completed'
                    task.progress = 100
                    await task.save()
                    logger.info(f"任务 {task_id} 扫描完成（无变化超时）")
                    await self._save_scan_results(task_id, scan_id, scan_client)
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
            from models import Task, Vulnerability
            from api.tasks import standardize_severity

            scan_info = scan_client.get(scan_id)
            if not scan_info:
                return
            
            vulnerabilities_summary = []
            scan_session_id = scan_info.get('current_session', {}).get('scan_session_id')
            
            if scan_session_id:
                vulns = scan_client.get_vulns(scan_id, scan_session_id)
                if vulns:
                    # 获取现有漏洞记录以避免重复 (根据 vuln_id)
                    existing_vulns = await Vulnerability.filter(task_id=task_id).values_list('title', flat=True) # 使用title作为简单去重，实际应存vuln_id
                    # 由于Vulnerability模型目前没有 awvs_vuln_id 字段，我们暂时用 title 和 url 组合判断，或者直接清空重建
                    # 为了安全起见，我们先删除该任务的所有旧漏洞记录，重新保存
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
        """执行POC扫描任务"""
        try:
            from models import Task, POCScanResult, VulnerabilityKB
            # Remove api.tasks import to avoid circular dependency
            # from api.tasks import standardize_severity 
            try:
                from api.poc_gen import poc_generator  # 导入 POC 生成器
            except ImportError:
                poc_generator = None
                logger.warning("Failed to import poc_generator")
            except Exception as e:
                poc_generator = None
                logger.error(f"Error importing poc_generator: {e}")

            task = await Task.get(id=task_id)
            task.status = 'running'
            task.progress = 0
            await task.save()
            
            # 构建待执行的 POC 列表
            pocs_to_run = []
            
            requested_pocs = scan_config.get('poc_types', [])
            use_all = not requested_pocs or 'all' in requested_pocs
            enable_ai = scan_config.get('enable_ai_generation', False)
            
            # 1. 内置 POC
            for name, func in POC_FUNCTIONS.items():
                if use_all or name in requested_pocs:
                    pocs_to_run.append({
                        'type': 'builtin',
                        'name': name,
                        'func': func
                    })
            
            # 2. 知识库 POC
            if use_all:
                kb_pocs = await VulnerabilityKB.filter(has_poc=True).all()
            else:
                # 按名称或CVE筛选
                kb_pocs = []
                for req in requested_pocs:
                    # 尝试精确匹配名称或CVE
                    items = await VulnerabilityKB.filter(has_poc=True).filter(Q(name=req) | Q(cve_id=req)).all()
                    kb_pocs.extend(items)
            
            for kb in kb_pocs:
                # 只有当有 POC 代码时才执行
                if kb.poc_code:
                    pocs_to_run.append({
                        'type': 'kb',
                        'name': kb.name,
                        'obj': kb
                    })

            # 3. AI 智能生成 POC (针对无 POC 的漏洞)
            if enable_ai and not use_all:
                # 仅对明确指定但没有 POC 的漏洞进行生成
                existing_names = {p['name'] for p in pocs_to_run}
                existing_cves = {p['obj'].cve_id for p in pocs_to_run if p['type'] == 'kb' and p['obj'].cve_id}
                
                for req in requested_pocs:
                    # 如果该请求未被满足 (既不是内置也不是已有KB POC)
                    if req not in existing_names and req not in existing_cves:
                         # 查找 KB 条目
                         kb_item = await VulnerabilityKB.filter(Q(name=req) | Q(cve_id=req)).first()
                         
                         if kb_item and not kb_item.has_poc:
                             logger.info(f"Adding AI generation task for: {kb_item.name}")
                             pocs_to_run.append({
                                 'type': 'ai_gen',
                                 'name': kb_item.name,
                                 'obj': kb_item
                             })

            total_pocs = len(pocs_to_run)
            if total_pocs == 0:
                logger.warning(f"任务 {task_id} 没有可执行的 POC")
                task.status = 'completed'
                task.result = json.dumps({'message': 'No POCs selected'})
                await task.save()
                return

            completed_pocs = 0
            vulnerable_count = 0
            results = []
            timeout = scan_config.get('timeout', 10)
            
            for poc_item in pocs_to_run:
                if not self.is_running:
                    break
                
                poc_name = poc_item['name']
                is_vulnerable = False
                message = ""
                severity = "High"
                cve_id = None
                
                try:
                    if poc_item['type'] == 'builtin':
                        # 执行内置 POC
                        poc_module = poc_item['func']
                        loop = asyncio.get_running_loop()
                        
                        # Ensure we are calling the poc function inside the module
                        if hasattr(poc_module, 'poc'):
                            poc_func = poc_module.poc
                        else:
                            # Fallback if it's already a function (unlikely based on analysis but safe)
                            poc_func = poc_module
                            
                        is_vulnerable, message = await loop.run_in_executor(
                            None, poc_func, target, timeout
                        )
                    elif poc_item['type'] == 'kb':
                        # 执行知识库 POC (Pocsuite3)
                        kb_obj = poc_item['obj']
                        cve_id = kb_obj.cve_id
                        severity = standardize_severity(kb_obj.severity) if kb_obj.severity else "High"
                        is_vulnerable, message = await self._run_kb_poc(kb_obj, target)
                    elif poc_item['type'] == 'ai_gen':
                        # 执行 AI 生成 POC
                        if not poc_generator:
                             is_vulnerable = False
                             message = "AI POC Generator not available"
                        else:
                            kb_obj = poc_item['obj']
                            cve_id = kb_obj.cve_id
                            severity = standardize_severity(kb_obj.severity) if kb_obj.severity else "High"
                            
                            # 1. 生成代码
                            logger.info(f"Generating POC for {poc_name}...")
                            poc_code = await poc_generator.generate_from_kb(kb_obj)
                            
                            # 2. 执行代码
                            logger.info(f"Executing generated POC for {poc_name}...")
                            exec_result = await poc_generator.execute_poc(poc_code, target)
                            
                            is_vulnerable = exec_result.get('vulnerable', False)
                            message = exec_result.get('message', '')
                            if exec_result.get('status') == 'error':
                                message = f"AI POC Error: {message}"
                    
                    if is_vulnerable:
                        vulnerable_count += 1
                        # 保存详细结果
                        await POCScanResult.create(
                            task=task,
                            poc_type=poc_name,
                            target=target,
                            vulnerable=True,
                            message=message,
                            severity=severity, 
                            cve_id=cve_id
                        )
                    
                    results.append({
                        'poc_type': poc_name,
                        'vulnerable': is_vulnerable,
                        'message': message,
                        'source': poc_item['type']
                    })
                    
                except Exception as e:
                    logger.error(f"POC {poc_name} 执行失败: {str(e)}")
                    results.append({
                        'poc_type': poc_name,
                        'vulnerable': False,
                        'message': f"执行出错: {str(e)}"
                    })
                
                completed_pocs += 1
                progress = int((completed_pocs / total_pocs) * 100)
                task.progress = progress
                await task.save()
            
            task.status = 'completed'
            task.progress = 100
            task.result = json.dumps({
                'total_scanned': total_pocs,
                'vulnerable_count': vulnerable_count,
                'details': results
            })
            await task.save()
            logger.info(f"POC任务 {task_id} 执行完成")
            
        except Exception as e:
            logger.error(f"POC任务 {task_id} 执行失败: {str(e)}", exc_info=True)
            try:
                from models import Task
                task = await Task.get(id=task_id)
                task.status = 'failed'
                task.progress = 0
                await task.save()
            except:
                pass

    async def _run_kb_poc(self, kb_item, target: str) -> (bool, str):
        """运行知识库中的 POC 代码 (基于 Pocsuite3)"""
        try:
            import tempfile
            import os
            
            # 检查 pocsuite3 是否可用
            try:
                import pocsuite3
            except ImportError:
                return False, "Pocsuite3 not installed"

            if not kb_item.poc_code:
                return False, "No POC code"

            # 写入临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(kb_item.poc_code)
                tmp_path = tmp.name
            
            try:
                # 使用 subprocess 调用 pocsuite3
                # 假设 pocsuite3 在 PATH 中，或者使用 python -m pocsuite3
                import subprocess
                import sys
                
                cmd = [sys.executable, "-m", "pocsuite3.cli", "-r", tmp_path, "-u", target, "--verify"]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                output = stdout.decode()
                
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

    async def execute_plugin_task(self, task_id: int, target: str, scan_config: Dict, task_type: str):
        """执行通用插件扫描任务"""
        try:
            from models import Task
            task = await Task.get(id=task_id)
            task.status = 'running'
            task.progress = 10
            await task.save()
            
            logger.info(f"插件任务 {task_id} ({task_type}) 开始执行: {target}")
            
            # 在线程池中执行插件，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._run_plugin, task_type, target, scan_config)
            
            task.result = json.dumps(result)
            task.status = 'completed'
            task.progress = 100
            await task.save()
            logger.info(f"插件任务 {task_id} 执行完成")
            
        except Exception as e:
            logger.error(f"插件任务 {task_id} 执行失败: {str(e)}", exc_info=True)
            try:
                from models import Task
                task = await Task.get(id=task_id)
                task.status = 'failed'
                task.result = json.dumps({'error': str(e)})
                await task.save()
            except:
                pass

    def _run_plugin(self, task_type: str, target: str, scan_config: Dict) -> Any:
        """运行具体的插件逻辑"""
        if task_type == 'scan_port':
            # scan_config might contain ports
            scanner = ScanPort(target)
            if scanner.run_scan():
                return scanner.get_results()
            return []
        elif task_type == 'scan_infoleak':
            return get_infoleak(target)
        elif task_type == 'scan_webside':
            return get_side_info(target)
        elif task_type == 'scan_baseinfo':
            return getbaseinfo(target)
        elif task_type == 'scan_webweight':
            return get_web_weight(target)
        elif task_type == 'scan_iplocating':
            return get_locating(target)
        elif task_type == 'scan_cdn':
             res = iscdn(target)
             return "存在CDN" if res else "无CDN"
        elif task_type == 'scan_waf':
            return getwaf(target)
        elif task_type == 'scan_cms':
            return getwhatcms(target)
        elif task_type == 'scan_subdomain':
            return get_subdomain(target)
        elif task_type == 'scan_dir':
            if DirScanner:
                scanner = DirScanner(target)
                return scanner.scan()
            else:
                return {"error": "DirScanner module is missing"}
        elif task_type == 'scan_comprehensive':
            results = {}
            try:
                results['baseinfo'] = getbaseinfo(target)
            except Exception as e: results['baseinfo'] = str(e)
            try:
                results['cms'] = getwhatcms(target)
            except Exception as e: results['cms'] = str(e)
            try:
                results['cdn'] = "存在CDN" if iscdn(target) else "无CDN"
            except Exception as e: results['cdn'] = str(e)
            try:
                results['waf'] = getwaf(target)
            except Exception as e: results['waf'] = str(e)
            return results
        return None

    async def start_task(self, task_id: int, target: str, scan_config: Dict):
        """启动任务"""
        if task_id in self.running_tasks:
            logger.warning(f"任务 {task_id} 已经在运行中")
            return
            
        try:
            from models import Task
            task = await Task.get(id=task_id)
            task_type = task.task_type
            
            if task_type == 'poc_scan':
                coro = self.execute_poc_task(task_id, target, scan_config)
            elif task_type == 'awvs_scan':
                coro = self.execute_scan_task(task_id, target, scan_config)
            else:
                # 默认为插件任务
                coro = self.execute_plugin_task(task_id, target, scan_config, task_type)
                
            async_task = asyncio.create_task(coro)
            self.running_tasks[task_id] = async_task
            logger.info(f"任务 {task_id} ({task_type}) 已启动")
            
        except Exception as e:
            logger.error(f"启动任务失败: {str(e)}")

    async def cancel_task(self, task_id: int):
        """取消任务"""
        if task_id not in self.running_tasks:
            return
        
        task = self.running_tasks[task_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.running_tasks[task_id]
        logger.info(f"任务 {task_id} 已取消")
    
    async def shutdown(self):
        """关闭任务执行器"""
        self.is_running = False
        for task_id, task in self.running_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.running_tasks.clear()
        logger.info("任务执行器已关闭")

task_executor = TaskExecutor()
