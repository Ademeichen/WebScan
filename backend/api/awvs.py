"""
AWVS 漏洞扫描相关的 API 路由
整合 AVWS 工具包的功能
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

import logging
import json
import re
import asyncio

from functools import partial
from tortoise.functions import Count
from urllib.parse import urlparse
from backend.config import settings
from backend.models import Task, Vulnerability

# 导入 AWVS API 类



logger = logging.getLogger(__name__)

router = APIRouter()



async def run_sync(func, *args, **kwargs):
    """在线程池中运行同步阻塞函数"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


# 请求模型
class AWVSScanRequest(BaseModel):
    url: str
    scan_type: str = "full_scan"


class AWVSTargetRequest(BaseModel):
    address: str
    description: Optional[str] = None


# 响应模型
class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


def get_awvs_client():
    """获取AWVS客户端实例"""
    return {
        'api_url': settings.AWVS_API_URL,
        'api_key': settings.AWVS_API_KEY
    }

def map_severity(awvs_severity: int, vuln_title: str) -> str:
    """
    映射 AWVS 严重程度到系统 5 级分类
    AWVS: 3=High, 2=Medium, 1=Low, 0=Info
    System: Critical, High, Medium, Low, Info
    """
    try:
        s = int(awvs_severity)
    except:
        return "Info"
        
    if s >= 3:
        # 特殊规则:SQL注入、RCE 等提升为 Critical
        critical_keywords = ['SQL Injection', 'Remote Code Execution', 'RCE', 'Command Injection']
        if any(k.lower() in vuln_title.lower() for k in critical_keywords):
            return "Critical"
        return "High"
    elif s == 2:
        return "Medium"
    elif s == 1:
        return "Low"
    else:
        return "Info"

async def sync_vulnerabilities(scan_id: str, scan_session_id: str, task_id: int):
    """同步指定扫描的漏洞信息"""
    try:
        client = get_awvs_client()
        s = Scan(client['api_url'], client['api_key'])
        
        # 获取漏洞列表 (使用线程池避免阻塞)
        vulns = await run_sync(s.get_vulns, scan_id, scan_session_id)


        if not vulns:
            return

        for v in vulns:
            vuln_id = v.get('vuln_id')
            if not vuln_id:
                continue
                
            # 检查漏洞是否已存在
            existing_vuln = await Vulnerability.filter(source_id=vuln_id, task_id=task_id).first()
            
            # 映射严重程度
            severity = map_severity(v.get('severity', 0), v.get('vt_name', ''))
            
            # 获取详细信息 (仅对中高危漏洞或不存在的漏洞获取详情,以减少请求量)
            description = v.get('description', f"See AWVS for details. Target: {v.get('affects_url')}")
            remediation = v.get('recommendation', '')
            
            if severity in ['Critical', 'High', 'Medium'] or not existing_vuln:
                try:
                    detail = await run_sync(s.get_vuln_detail, scan_id, scan_session_id, vuln_id)
                    if detail:
                        description = detail.get('description', description)
                        remediation = detail.get('recommendation', remediation)
                        # 清理HTML标签 (简单处理)
                        description = re.sub(r'<[^>]+>', '', description)
                        remediation = re.sub(r'<[^>]+>', '', remediation)
                except Exception as e:
                    logger.warning(f"获取漏洞详情失败: {str(e)}")

            if existing_vuln:
                # 更新状态和严重程度
                existing_vuln.status = v.get('status', 'open')
                existing_vuln.severity = severity
                existing_vuln.description = description
                existing_vuln.remediation = remediation
                await existing_vuln.save()
            else:
                # 创建新漏洞
                await Vulnerability.create(
                    task_id=task_id,
                    vuln_type=v.get('vt_name', 'Unknown'),
                    severity=severity,
                    title=v.get('vt_name', 'Unknown'),
                    description=description,
                    remediation=remediation,
                    url=v.get('affects_url'),
                    status=v.get('status', 'open'),
                    source_id=vuln_id
                )
                
    except Exception as e:
        logger.error(f"同步漏洞失败 (ScanID: {scan_id}): {str(e)}")


async def sync_scans_from_awvs():
    """从AWVS同步扫描任务到数据库"""
    try:
        client = get_awvs_client()
        s = Scan(client['api_url'], client['api_key'])
        # 获取AWVS中所有扫描 (使用线程池)
        awvs_scans = await run_sync(s.get_all)


        # 获取数据库中所有AWVS任务
        # 注意:这里假设task_type='awvs_scan'
        db_tasks = await Task.filter(task_type='awvs_scan').all()
        db_task_map = {}
        for task in db_tasks:
            config = json.loads(task.config) if task.config else {}
            scan_id = config.get('scan_id')
            if scan_id:
                db_task_map[scan_id] = task

        # 同步更新
        for scan in awvs_scans:
            scan_id = scan.get('scan_id')
            target_id = scan.get('target_id')
            
            # 构建result JSON
            result_json = json.dumps(scan)
            
            current_session = scan.get('current_session', {})
            status = current_session.get('status', 'unknown')
            progress = current_session.get('progress', 0)
            scan_session_id = current_session.get('scan_session_id')
            
            target_task = None
            
            if scan_id in db_task_map:
                # 更新现有任务
                task = db_task_map[scan_id]
                task.status = status
                task.progress = progress
                task.result = result_json
                await task.save()
                target_task = task
            else:
                # 检查是否存在未关联scan_id的同目标任务
                # 优先通过 target_id 匹配 (更准确)
                existing_task = None
                
                # 获取所有未关联 scan_id 的活跃任务
                pending_tasks = await Task.filter(
                    task_type='awvs_scan',
                    status__in=['pending', 'submitted', 'processing']
                ).all()
                
                for p_task in pending_tasks:
                    p_config = json.loads(p_task.config) if p_task.config else {}
                    # 检查 scan_id 是否已存在 (如果已存在说明是其他任务)
                    if p_config.get('scan_id'):
                        continue
                        
                    # 匹配 target_id
                    if target_id and p_config.get('target_id') == target_id:
                        existing_task = p_task
                        break
                    
                    # 降级匹配: target URL (忽略末尾斜杠)
                    t1 = p_task.target.rstrip('/')
                    t2 = scan.get('target', {}).get('address', '').rstrip('/')
                    if t1 and t2 and t1 == t2:
                        existing_task = p_task
                        break
                
                if existing_task:
                    # 关联现有任务
                    existing_task.status = status
                    existing_task.progress = progress
                    existing_task.result = result_json
                    # 更新配置中的scan_id
                    config = json.loads(existing_task.config)
                    config['scan_id'] = scan_id
                    existing_task.config = json.dumps(config)
                    await existing_task.save()
                    # 更新映射防止重复处理
                    db_task_map[scan_id] = existing_task
                    target_task = existing_task
                else:
                    # 创建新任务(可能是直接在AWVS创建的)
                    target_address = scan.get('target', {}).get('address', 'Unknown Target')
                    new_task = await Task.create(
                        task_name=f"AWVS Scan: {target_address}",
                        task_type='awvs_scan',
                        target=target_address,
                        status=status,
                        progress=progress,
                        config=json.dumps({'scan_id': scan_id, 'target_id': target_id}),
                        result=result_json
                    )
                    db_task_map[scan_id] = new_task
                    target_task = new_task
            
            # 同步漏洞数据 (仅当任务处于处理中或已完成时)
            if target_task and scan_session_id and status in ['processing', 'completed', 'aborted']:
                 await sync_vulnerabilities(scan_id, scan_session_id, target_task.id)
                
    except Exception as e:
        logger.error(f"同步AWVS扫描任务失败: {str(e)}")


# ====== 获取所有扫描任务 ======
@router.get("/scans", response_model=APIResponse)
async def get_all_scans():
    """
    获取所有扫描任务列表 (从数据库获取,并尝试同步)
    """
    try:
        # 异步触发同步,不阻塞返回(或者可以阻塞以保证最新)
        # 为了保证显示最新状态,这里选择阻塞同步
        await sync_scans_from_awvs()
        
        # 从数据库读取
        tasks = await Task.filter(task_type='awvs_scan').order_by('-created_at').all()


        
        data = []
        for task in tasks:
            scan_data = {}
            if task.result:
                try:
                    scan_data = json.loads(task.result)
                except:
                    pass
            
            # 基础数据回退
            if not scan_data:
                scan_data = {
                    'target': {'address': task.target},
                    'profile_name': 'Unknown',
                    'current_session': {'status': task.status, 'severity_counts': {}, 'start_date': str(task.created_at)},
                    'target_id': json.loads(task.config).get('target_id') if task.config else None
                }
            
            # 使用数据库中的漏洞统计覆盖 AWVS 原始统计
            # 这样可以反映我们自定义的严重程度映射 (例如 SQLi -> Critical)
            db_counts = await Vulnerability.filter(task_id=task.id).group_by('severity').annotate(count=Count('id')).values('severity', 'count')
            
            severity_counts = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            }
            
            total_db_count = 0
            for item in db_counts:
                sev = str(item['severity']).lower()
                if sev in severity_counts:
                    severity_counts[sev] = item['count']
                    total_db_count += item['count']
            
            # 更新统计数据
            if 'current_session' not in scan_data:
                scan_data['current_session'] = {}
            
            # 仅当数据库有数据时才覆盖,或者如果原始数据中没有统计信息
            # 这样即使数据库同步失败,也能保留 AWVS 原始统计
            if total_db_count > 0 or not scan_data['current_session'].get('severity_counts'):
                scan_data['current_session']['severity_counts'] = severity_counts
            
            # 确保状态同步
            scan_data['current_session']['status'] = task.status
            
            # 确保 scan_id/target_id 存在
            if task.config:
                try:
                    config = json.loads(task.config)
                    if not scan_data.get('scan_id') and config.get('scan_id'):
                        scan_data['scan_id'] = config.get('scan_id')
                    if not scan_data.get('target_id') and config.get('target_id'):
                        scan_data['target_id'] = config.get('target_id')
                except:
                    pass
            
            data.append(scan_data)
        
        logger.info(f"获取扫描任务列表成功,共 {len(data)} 个任务")
        return APIResponse(code=200, message="获取成功", data=data)
    except Exception as e:
        logger.error(f"获取扫描任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 获取目标漏洞列表 ======
@router.get("/vulnerabilities/{target_id}", response_model=APIResponse)
async def get_target_vulnerabilities(target_id: str):
    """
    获取指定目标的漏洞列表
    """
    try:
        client = get_awvs_client()
        v = Vuln(client['api_url'], client['api_key'])


        
        # 搜索该目标的所有已打开的漏洞
        # search 方法返回的是 JSON 字符串,需要解析
        result_text = v.search(
            severity=None,
            criticality=None,
            status='open',
            target_id=target_id
        )


        
        data = []
        if result_text:
            try:
                result_json = json.loads(result_text)
                vulnerabilities = result_json.get('vulnerabilities', [])
                
                # Severity mapping
                severity_map = {
                    3: 'High',
                    2: 'Medium',
                    1: 'Low',
                    0: 'Info'
                }


                
                for val in vulnerabilities:
                    # Handle severity if it's an integer
                    severity_val = val.get('severity')
                    if isinstance(severity_val, int):
                        severity = severity_map.get(severity_val, 'Info')
                    else:
                        severity = str(severity_val) if severity_val is not None else 'Info'
                        
                    data.append({
                        'vuln_id': val.get('vuln_id'),
                        'severity': severity,
                        'vuln_name': val.get('vt_name'),
                        'target': val.get('affects_url'),
                        'time': val.get('last_seen', '').replace('T', ' ').split('.')[0] if val.get('last_seen') else ''
                    })
            except json.JSONDecodeError:
                logger.error(f"解析漏洞数据失败: {result_text}")
                
        return APIResponse(code=200, message="获取漏洞列表成功", data=data)
    except Exception as e:
        logger.error(f"获取漏洞列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 获取漏洞详情 ======
@router.get("/vulnerability/{vuln_id}", response_model=APIResponse)
async def get_vulnerability_detail(vuln_id: str):
    """
    获取漏洞详情
    """
    try:
        client = get_awvs_client()
        v = Vuln(client['api_url'], client['api_key'])
        
        vuln_data = v.get(vuln_id)


        if vuln_data:
            return APIResponse(code=200, message="获取漏洞详情成功", data=vuln_data)
        else:
            return APIResponse(code=404, message="未找到漏洞信息", data=None)
            
    except Exception as e:
        logger.error(f"获取漏洞详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 创建新的扫描任务 ======
@router.post("/scan", response_model=APIResponse)
async def create_scan(request: AWVSScanRequest):
    """
    创建新的扫描任务
    """
    try:
        client = get_awvs_client()
        
        # 1. 在数据库创建 Pending 任务
        task = await Task.create(
            task_name=f"AWVS Scan: {request.url}",
            task_type='awvs_scan',
            target=request.url,
            status='pending',
            progress=0,
            config=json.dumps({'scan_type': request.scan_type})
        )
        
        # 2. 先添加目标
        t = Target(client['api_url'], client['api_key'])
        target_id = t.add(request.url)
        
        if target_id is None:
            task.status = 'failed'
            task.error_message = "Failed to add target to AWVS"
            await task.save()
            return APIResponse(code=400, message="添加目标失败", data=None)
        
        # 更新任务配置
        config = json.loads(task.config)
        config['target_id'] = target_id
        task.config = json.dumps(config)
        await task.save()
        
        # 3. 创建扫描任务
        s = Scan(client['api_url'], client['api_key'])
        status_code = s.add(target_id, request.scan_type)
        
        if status_code == 200:
            logger.info(f"创建扫描任务成功: {request.url}")
            task.status = 'submitted'
            await task.save()
            
            # 尝试立即同步一次以获取 scan_id
            # 但AWVS可能需要一点时间生成scan_id,所以这里可能获取不到
            # 下次 list scans 时会自动同步
            
            return APIResponse(code=200, message="扫描任务创建成功", data={"target_id": target_id})
        else:
            task.status = 'failed'
            task.error_message = "Failed to start scan in AWVS"
            await task.save()
            return APIResponse(code=400, message="创建扫描任务失败", data=None)
            
    except Exception as e:
        logger.error(f"创建扫描任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




# ====== 获取漏洞排名 ======
@router.get("/vulnerabilities/rank", response_model=APIResponse)
async def get_vulnerability_rank():
    """
    获取漏洞排名(前5名)
    """
    try:
        client = get_awvs_client()
        d = Dashboard(client['api_url'], client['api_key'])
        data = json.loads(d.stats())["top_vulnerabilities"]
        
        vuln_rank = []
        for i in range(min(5, len(data))):
            tem = {
                'name': data[i]['name'],
                'value': data[i]['count']
            }
            vuln_rank.append(tem)
        
        logger.info("获取漏洞排名成功")
        return APIResponse(code=200, message="获取成功", data=vuln_rank)
    except Exception as e:
        logger.error(f"获取漏洞排名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 获取漏洞统计 ======
@router.get("/vulnerabilities/stats", response_model=APIResponse)
async def get_vulnerability_stats():
    """
    获取漏洞统计信息
    """
    try:
        client = get_awvs_client()
        d = Dashboard(client['api_url'], client['api_key'])
        data = json.loads(d.stats())["vuln_count_by_criticality"]
        
        result = {}
        if data.get('high') is not None:
            vuln_high_count = [i for i in data['high'].values()]
            result['high'] = vuln_high_count
        if data.get('normal') is not None:
            vuln_normal_count = [i for i in data['normal'].values()]
            result['normal'] = vuln_normal_count
        
        logger.info("获取漏洞统计成功")
        return APIResponse(code=200, message="获取成功", data=result)
    except Exception as e:
        logger.error(f"获取漏洞统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 获取所有目标 ======
@router.get("/targets", response_model=APIResponse)
async def get_all_targets():
    """
    获取所有目标列表
    """
    try:
        client = get_awvs_client()
        t = Target(client['api_url'], client['api_key'])
        data = t.get_all()
        
        logger.info(f"获取目标列表成功,共 {len(data) if data else 0} 个目标")
        return APIResponse(code=200, message="获取成功", data=data)
    except Exception as e:
        logger.error(f"获取目标列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 添加目标 ======
@router.post("/target", response_model=APIResponse)
async def add_target(request: AWVSTargetRequest):
    """
    添加新的扫描目标
    """
    try:
        client = get_awvs_client()
        t = Target(client['api_url'], client['api_key'])
        
        target_id = t.add(request.address, request.description)
        
        if target_id:
            logger.info(f"添加目标成功: {request.address}")
            return APIResponse(code=200, message="添加成功", data={"target_id": target_id})
        else:
            return APIResponse(code=400, message="添加目标失败", data=None)
            
    except Exception as e:
        logger.error(f"添加目标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ====== 健康检查 ======
@router.get("/health", response_model=APIResponse)
async def awvs_health_check():
    """
    检查AWVS服务连接状态
    """
    try:
        client = get_awvs_client()
        d = Dashboard(client['api_url'], client['api_key'])
        stats = d.stats()
        
        if stats:
            return APIResponse(code=200, message="AWVS服务连接正常", data={"status": "connected"})
        else:
            return APIResponse(code=503, message="AWVS服务连接失败", data={"status": "disconnected"})
    except Exception as e:
        logger.error(f"AWVS健康检查失败: {str(e)}")
        return APIResponse(code=503, message="AWVS服务连接失败", data={"status": "disconnected", "error": str(e)})



# ====== 中间件POC扫描相关 ======

class MiddlewareScanRequest(BaseModel):
    url: str
    cve_id: str


class MiddlewareScanStartRequest(BaseModel):
    url: str
    cve_id: str


def POC_Check(url: str, CVE_id: str) -> tuple:
    """
    执行POC检查
    :param url: 目标URL
    :param CVE_id: CVE ID
    :return: (是否漏洞, 消息)
    """
    try:
        parsed = urlparse(url)
        ip = parsed.hostname or parsed.netloc.split(':')[0]
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        CVE_id_clean = CVE_id.replace('-', "_")
        
        # Weblogic
        if CVE_id_clean == "CVE_2020_2551":
            result = cve_2020_2551_poc.poc(url)
        elif CVE_id_clean == "CVE_2018_2628":
            result = cve_2018_2628_poc.poc(ip, port, 0)
        elif CVE_id_clean == "CVE_2018_2894":
            result = cve_2018_2894_poc.poc(url, "weblogic")
        elif CVE_id_clean == "CVE_2020_14756":
            result = cve_2020_14756_poc(url)
        elif CVE_id_clean == "CVE_2023_21839":
            result = cve_2023_21839_poc(url)
        # Drupal
        elif CVE_id_clean == "CVE_2018_7600":
            result = cve_2018_7600_poc.poc(url)
        # Tomcat
        elif CVE_id_clean == "CVE_2017_12615":
            result = cve_2017_12615_poc.poc(url)
        elif CVE_id_clean == "CVE_2022_22965":
            result = cve_2022_22965_poc(url)
        elif CVE_id_clean == "CVE_2022_47986":
            result = cve_2022_47986_poc(url)
        # JBoss
        elif CVE_id_clean == "CVE_2017_12149":
            result = cve_2017_12149_poc.poc(url)
        # Nexus
        elif CVE_id_clean == "CVE_2020_10199":
            result = cve_2020_10199_poc.poc(ip, port, "admin")
        # Struts2
        elif CVE_id_clean == "Struts2_009":
            result = struts2_009_poc.poc(url)
        elif CVE_id_clean == "Struts2_032":
            result = struts2_032_poc.poc(url)
        else:
            return False, f"未知的CVE ID: {CVE_id}"
        
        if isinstance(result, tuple):
            return result
        else:
            return result, f"{CVE_id}: 扫描完成"
    except Exception as e:
        logger.error(f"POC检查失败: {str(e)}")
        return False, f"{CVE_id}: 扫描失败 - {str(e)}"


@router.post("/middleware/scan", response_model=APIResponse)
async def middleware_scan(request: MiddlewareScanRequest):
    """
    创建中间件POC扫描任务(插入数据库)
    """
    global middleware_scan_time
    
    try:
        url = request.url
        CVE_id = request.cve_id.replace('-', "_")
        middleware_scan_time = time.time()
        
        # 创建任务记录
        task = await Task.create(
            task_name=f"Middleware POC Scan: {CVE_id}",
            task_type='middleware_poc_scan',
            target=url,
            status='running',
            progress=0,
            config=json.dumps({
                'cve_id': CVE_id,
                'scan_time': middleware_scan_time
            })
        )
        
        logger.info(f"创建中间件扫描任务成功: {url} - {CVE_id}")
        return APIResponse(code=200, message="创建扫描任务成功", data={"task_id": task.id})
    except Exception as e:
        logger.error(f"创建中间件扫描任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/middleware/scan/start", response_model=APIResponse)
async def start_middleware_scan(request: MiddlewareScanStartRequest, background_tasks: BackgroundTasks):
    """
    启动中间件POC扫描(后台任务)
    """
    try:
        url = request.url
        CVE_id = request.cve_id.replace('-', "_")
        
        # 在后台执行扫描
        async def run_middleware_scan():
            try:
                # 等待数据插入成功
                await asyncio.sleep(2)
                
                # 查找运行中的任务
                tasks = await Task.filter(
                    task_type='middleware_poc_scan',
                    target=url,
                    status='running'
                ).all()
                
                for task in tasks:
                    config = json.loads(task.config) if task.config else {}
                    if config.get('cve_id') == CVE_id:
                        # 执行POC检查
                        result, message = await asyncio.to_thread(POC_Check, url, CVE_id)
                        
                        # 更新任务状态
                        task.status = 'completed'
                        task.progress = 100
                        task.result = json.dumps({
                            'vulnerable': result,
                            'message': message
                        })
                        
                        # 如果存在漏洞,创建漏洞记录
                        if result:
                            await Vulnerability.create(
                                task_id=task.id,
                                vuln_type=CVE_id,
                                severity='high',
                                title=f"{CVE_id} 漏洞检测",
                                description=message,
                                url=url,
                                status='open'
                            )
                        
                        await task.save()
                        logger.info(f"中间件扫描完成: {url} - {CVE_id} - 结果: {result}")
                        
            except Exception as e:
                logger.error(f"中间件扫描执行失败: {str(e)}")
        
        background_tasks.add_task(run_middleware_scan)
        
        logger.info(f"启动中间件扫描: {url} - {CVE_id}")
        return APIResponse(code=200, message="扫描任务已启动", data=None)
    except Exception as e:
        logger.error(f"启动中间件扫描失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/middleware/scans", response_model=APIResponse)
async def get_middleware_scans():
    """
    获取所有中间件POC扫描任务
    """
    try:
        tasks = await Task.filter(task_type='middleware_poc_scan').order_by('-created_at').all()
        
        data = []
        for task in tasks:
            scan_data = {
                'id': task.id,
                'task_name': task.task_name,
                'target': task.target,
                'status': task.status,
                'progress': task.progress,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
            
            if task.config:
                try:
                    config = json.loads(task.config)
                    scan_data['cve_id'] = config.get('cve_id')
                except:
                    pass
            
            if task.result:
                try:
                    result = json.loads(task.result)
                    scan_data['vulnerable'] = result.get('vulnerable', False)
                    scan_data['message'] = result.get('message', '')
                except:
                    pass
            
            data.append(scan_data)
        
        logger.info(f"获取中间件扫描列表成功,共 {len(data)} 个任务")
        return APIResponse(code=200, message="获取成功", data=data)
    except Exception as e:
        logger.error(f"获取中间件扫描列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/middleware/poc-list", response_model=APIResponse)
async def get_middleware_poc_list():
    """
    获取支持的中间件POC列表
    """
    try:
        poc_list = [
            {
                'cve_id': 'CVE-2020-2551',
                'name': 'WebLogic CVE-2020-2551',
                'description': 'WebLogic Server 反序列化漏洞',
                'severity': '高危',
                'middleware': 'WebLogic'
            },
            {
                'cve_id': 'CVE-2018-2628',
                'name': 'WebLogic CVE-2018-2628',
                'description': 'WebLogic Server 反序列化漏洞',
                'severity': '高危',
                'middleware': 'WebLogic'
            },
            {
                'cve_id': 'CVE-2018-2894',
                'name': 'WebLogic CVE-2018-2894',
                'description': 'WebLogic Server 任意文件上传漏洞',
                'severity': '高危',
                'middleware': 'WebLogic'
            },
            {
                'cve_id': 'CVE-2018-7600',
                'name': 'Drupal CVE-2018-7600',
                'description': 'Drupal 远程代码执行漏洞',
                'severity': '高危',
                'middleware': 'Drupal'
            },
            {
                'cve_id': 'CVE-2017-12615',
                'name': 'Tomcat CVE-2017-12615',
                'description': 'Tomcat 任意文件写入漏洞',
                'severity': '高危',
                'middleware': 'Tomcat'
            },
            {
                'cve_id': 'CVE-2017-12149',
                'name': 'JBoss CVE-2017-12149',
                'description': 'JBoss 反序列化漏洞',
                'severity': '高危',
                'middleware': 'JBoss'
            },
            {
                'cve_id': 'CVE-2020-10199',
                'name': 'Nexus CVE-2020-10199',
                'description': 'Nexus Repository Manager 远程代码执行漏洞',
                'severity': '高危',
                'middleware': 'Nexus'
            },
            {
                'cve_id': 'Struts2-009',
                'name': 'Struts2 S2-009',
                'description': 'Struts2 远程代码执行漏洞',
                'severity': '高危',
                'middleware': 'Struts2'
            },
            {
                'cve_id': 'Struts2-032',
                'name': 'Struts2 S2-032',
                'description': 'Struts2 远程代码执行漏洞',
                'severity': '高危',
                'middleware': 'Struts2'
            }
        ]
        
        logger.info("获取中间件POC列表成功")
        return APIResponse(code=200, message="获取成功", data=poc_list)
    except Exception as e:
        logger.error(f"获取中间件POC列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



