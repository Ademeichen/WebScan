"""
任务管理相关的 API 路由
已迁移至数据库存储（Tortoise-ORM）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from tortoise import connections
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 辅助函数 ====================
def standardize_severity(severity_val) -> str:
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

def standardize_title(title: str) -> str:
    """标准化漏洞标题 (添加前缀)"""
    if not title: return "Unknown Vulnerability"
    if 'SQL Injection' in title and not title.startswith('[SQL'):
        return f"[SQL Injection] {title}"
    if 'XSS' in title and not title.startswith('[XSS'):
         return f"[XSS] {title}"
    return title

def validate_vulnerability_consistency(vuln_data: dict) -> List[str]:
    """
    验证漏洞数据一致性
    返回错误信息列表
    """
    errors = []
    if not vuln_data.get('vuln_id'):
        errors.append("Missing vuln_id")
    
    # 验证严重程度
    severity = vuln_data.get('severity')
    if severity is not None:
        if isinstance(severity, int) and not (0 <= severity <= 4):
            errors.append(f"Invalid severity value (int): {severity}")
        elif isinstance(severity, str) and severity.lower() not in ['critical', 'high', 'medium', 'low', 'info']:
             # 仅记录警告，不视为严重错误
             pass
    
    if not vuln_data.get('vt_name'):
        errors.append("Missing vt_name (title)")
        
    # 检查关键字段是否存在
    if 'affects_url' not in vuln_data:
        errors.append("Missing affects_url")
        
    return errors

# 请求模型
class CreateTaskRequest(BaseModel):
    task_name: str
    target: str
    task_type: str  # awvs_scan, poc_scan, scan_dir, scan_webside, etc.
    config: Dict[str, Any] = {}

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    result: Optional[Any] = None

class APIResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# ==================== 任务管理接口 ====================

@router.post("/create", response_model=APIResponse)
async def create_task(request: CreateTaskRequest):
    """
    统一任务创建接口
    """
    try:
        from models import Task
        from task_executor import task_executor
        import json
        
        # 1. 验证任务类型
        # valid_types = ['awvs_scan', 'poc_scan', 'scan_dir', 'scan_webside', 'scan_port', 'scan_cms', 'scan_comprehensive']
        # if request.task_type not in valid_types:
        #     # 暂时不强制验证，允许插件扩展
        #     pass

        # 2. 创建 Task 记录
        task = await Task.create(
            task_name=request.task_name,
            task_type=request.task_type,
            target=request.target,
            status='pending',
            progress=0,
            config=json.dumps(request.config)
        )
        
        logger.info(f"创建任务: {request.task_name} (ID: {task.id}, Type: {request.task_type})")
        
        # 3. 启动异步任务执行
        asyncio.create_task(task_executor.start_task(
            task_id=task.id,
            target=request.target,
            scan_config=request.config
        ))
            
        return APIResponse(code=200, message="任务创建成功", data={"task_id": task.id})
        
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=APIResponse)
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000
):
    """
    获取任务列表（使用数据库）
    支持按状态、类型、时间范围、关键词过滤
    """
    try:
        from models import Task
        from tortoise.expressions import Q
        
        # 构建查询条件
        query = Task.all()
        
        # 过滤条件
        if status:
            query = query.filter(status=status)
        if task_type:
            query = query.filter(task_type=task_type)
        if search:
            query = query.filter(Q(task_name__icontains=search) | Q(target__icontains=search))
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(created_at__gte=start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # 加一天以包含结束日期当天
                from datetime import timedelta
                end_dt = end_dt + timedelta(days=1)
                query = query.filter(created_at__lt=end_dt)
            except ValueError:
                pass
        
        # 排序（最新的在前）
        query = query.order_by('-created_at')
        
        # 获取总数
        total = await query.count()
        
        # 分页查询
        tasks = await query.offset(skip).limit(limit)
        
        # 转换为字典格式
        task_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "target": task.target,
                "status": task.status,
                "progress": task.progress,
                "config": json.loads(task.config) if task.config else {},
                "result": json.loads(task.result) if task.result else None,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            task_list.append(task_dict)
        
        return APIResponse(
            code=200,
            message="获取成功",
            data={
                "tasks": task_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=APIResponse)
async def get_task(task_id: int):
    """
    获取任务详情（使用数据库）
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 转换为字典格式
        task_dict = {
            "id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "target": task.target,
            "status": task.status,
            "progress": task.progress,
            "config": json.loads(task.config) if task.config else {},
            "result": json.loads(task.result) if task.result else None,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return APIResponse(code=200, message="获取成功", data=task_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}", response_model=APIResponse)
async def update_task(task_id: int, task_update: TaskUpdate):
    """
    更新任务状态
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
            
        if task_update.status:
            task.status = task_update.status
        if task_update.progress is not None:
            task.progress = task_update.progress
        if task_update.result:
            task.result = json.dumps(task_update.result)
            
        await task.save()
        
        return APIResponse(code=200, message="更新成功")
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(task_id: int):
    """
    删除任务
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
            
        await task.delete()
        
        return APIResponse(code=200, message="删除成功")
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/results", response_model=APIResponse)
async def get_task_results(task_id: int):
    """
    获取任务的详细结果（智能聚合）
    """
    try:
        from models import Task, POCScanResult, Vulnerability
        from AVWS.API.Vuln import Vuln
        from config import settings
        
        task = await Task.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
            
        response_data = {
            "task_info": {
                "id": task.id,
                "name": task.task_name,
                "type": task.task_type,
                "target": task.target,
                "status": task.status,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            },
            "vulnerabilities": [],
            "basic_info": [],
            "poc_results": []
        }
        
        # 1. 获取 POC 结果
        poc_results = await POCScanResult.filter(task=task).all()
        for poc in poc_results:
            response_data["poc_results"].append({
                "id": poc.id,
                "poc_type": poc.poc_type,
                "target": poc.target,
                "vulnerable": poc.vulnerable,
                "message": poc.message,
                "severity": standardize_severity(poc.severity),  # 强制标准化
                "cve_id": poc.cve_id,
                "created_at": poc.created_at,
                "source": "poc"
            })
            
        # 2. 获取 AWVS 漏洞
        # 优先从数据库获取
        db_vulns = await Vulnerability.filter(task=task).all()
        if db_vulns:
            for v in db_vulns:
                 response_data["vulnerabilities"].append({
                    "id": v.source_id or str(v.id), # 优先使用 source_id (AWVS GUID), 否则使用 DB ID
                    "title": v.title,
                    "severity": standardize_severity(v.severity),
                    "status": v.status,
                    "cvss_score": None, # 数据库暂未存储
                    "discovered_at": str(v.created_at),
                    "description": f"Found on {v.url}", 
                    "type": v.vuln_type,
                    "target": v.url,
                    "source": "awvs"
                })
        # 如果数据库没有且是 AWVS 任务，尝试从 API 获取 (并同步到数据库)
        elif task.task_type == 'awvs_scan':
            config = json.loads(task.config) if task.config else {}
            target_id = config.get('target_id')
            
            # 尝试从 AWVS API 获取最新漏洞
            if target_id and settings.AWVS_API_KEY:
                try:
                    client = {'api_url': settings.AWVS_API_URL, 'api_key': settings.AWVS_API_KEY}
                    v_api = Vuln(client['api_url'], client['api_key'])
                    result_text = v_api.search(status='open', target_id=target_id)
                    if result_text:
                        result_json = json.loads(result_text)
                        vulns = result_json.get('vulnerabilities', [])
                        
                        for val in vulns:
                            # 数据一致性检查与清洗
                            severity_val = val.get('severity')
                            severity_str = standardize_severity(severity_val)
                            
                            vt_name = val.get('vt_name', 'Unknown Vulnerability')
                            title = standardize_title(vt_name)

                            # 数据一致性检查机制
                            validation_errors = validate_vulnerability_consistency(val)
                            if validation_errors:
                                logger.warning(f"Task {task_id} Vulnerability Consistency Warning: {validation_errors} - Data: {val.get('vuln_id', 'Unknown')}")
                                if "Missing vuln_id" in validation_errors:
                                     continue # Skip items without ID
                            
                            # 保存到数据库 (Sync)
                            try:
                                await Vulnerability.create(
                                    task=task,
                                    vuln_type=val.get('vt_name'),
                                    severity=severity_str,
                                    title=title,
                                    description=val.get('description', ''),
                                    url=val.get('affects_url', ''),
                                    status=val.get('status', 'open'),
                                    source_id=val.get('vuln_id')
                                )
                            except Exception as db_e:
                                logger.error(f"Sync vulnerability to DB failed: {db_e}")

                            response_data["vulnerabilities"].append({
                                "id": val.get('vuln_id'),
                                "title": title,
                                "severity": severity_str,
                                "status": val.get('status'),
                                "cvss_score": val.get('cvss_score'),
                                "discovered_at": val.get('last_seen'),
                                "description": f"Found on {val.get('affects_url')}", 
                                "type": val.get('vt_name'),
                                "target": val.get('affects_url'),
                                "source": "awvs",
                                "consistency_errors": validation_errors # 返回一致性检查结果
                            })
                except Exception as e:
                    logger.warning(f"从 AWVS 获取漏洞失败: {e}")
            
        # 3. 获取插件扫描结果 (非 AWVS/POC 任务，或者混合任务)
        # 始终尝试提取 basic_info，无论任务类型如何
        if task.result:
            try:
                res = json.loads(task.result)
                # 尝试提取结构化基础信息
                if isinstance(res, dict):
                    # 如果是 AWVS 任务，result 主要是统计信息，基础信息可能在 details 里
                    # 但如果是插件任务，result 本身就是信息
                    
                    # 排除掉已知的大字段
                    ignored_keys = ['vulnerabilities', 'scan_id', 'target_id', 'scan_status', 'start_time', 'end_time', 'requests_count', 'vulnerabilities_count']
                    
                    for k, v in res.items():
                        if k not in ignored_keys:
                            # 格式化 value
                            val_str = str(v)
                            if isinstance(v, (dict, list)):
                                try:
                                    val_str = json.dumps(v, ensure_ascii=False)
                                except:
                                    pass
                            response_data["basic_info"].append({
                                "key": k, 
                                "value": val_str,
                                "source": "plugin",
                                "timestamp": str(task.updated_at)
                            })
                            
                elif isinstance(res, list):
                     for item in res:
                         if isinstance(item, dict) and 'key' in item and 'value' in item:
                             response_data["basic_info"].append({
                                 "key": item['key'],
                                 "value": str(item['value']),
                                 "source": item.get('source', 'plugin'),
                                 "timestamp": item.get('timestamp', str(task.updated_at))
                             })
                         elif isinstance(item, dict):
                             for k, v in item.items():
                                 response_data["basic_info"].append({
                                     "key": k, 
                                     "value": str(v),
                                     "source": "plugin",
                                     "timestamp": str(task.updated_at)
                                 })
                         else:
                             response_data["basic_info"].append({
                                 "key": "Result", 
                                 "value": str(item),
                                 "source": "plugin",
                                 "timestamp": str(task.updated_at)
                             })
            except Exception as e:
                logger.warning(f"Error parsing task result for basic info: {e}")

        # 智能结果展示逻辑
        # 如果是 AWVS 任务，确保 basic_info 包含目标信息
        if task.task_type == 'awvs_scan' and not response_data["basic_info"]:
             response_data["basic_info"].append({
                 "key": "Target",
                 "value": task.target,
                 "source": "task_config",
                 "timestamp": str(task.created_at)
             })

        return APIResponse(code=200, message="获取成功", data=response_data)
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_task(task_id: int, task_update: TaskUpdate):
    """
    更新任务状态（使用数据库）
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 构建更新数据
        update_data = {}
        if task_update.status:
            update_data['status'] = task_update.status
        if task_update.result is not None:
            update_data['result'] = json.dumps(task_update.result)
        if task_update.progress is not None:
            update_data['progress'] = task_update.progress
        
        # 更新任务
        if update_data:
            for key, value in update_data.items():
                setattr(task, key, value)
            await task.save()
        
        # 重新获取更新后的任务
        task = await Task.get(id=task_id)
        
        logger.info(f"更新任务: {task_id}")
        
        # 转换为字典格式
        task_dict = {
            "id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "target": task.target,
            "status": task.status,
            "progress": task.progress,
            "config": json.loads(task.config) if task.config else {},
            "result": json.loads(task.result) if task.result else None,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return APIResponse(code=200, message="更新成功", data=task_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(task_id: int):
    """
    删除任务（使用数据库）
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_name = task.task_name
        
        # 删除任务
        await task.delete()
        
        logger.info(f"删除任务: {task_name} (ID: {task_id})")
        return APIResponse(code=200, message="删除成功", data=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel", response_model=APIResponse)
async def cancel_task(task_id: int):
    """
    取消任务（使用数据库）
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status in ['completed', 'failed', 'cancelled']:
            return APIResponse(code=400, message=f"任务已{task.status}，无法取消", data=None)
        
        # 更新任务状态为已取消
        for key, value in {'status': 'cancelled'}.items():
            setattr(task, key, value)
        await task.save()
        
        # 停止正在执行的任务
        from task_executor import task_executor
        await task_executor.cancel_task(task_id)
        
        logger.info(f"取消任务: {task_id}")
        
        # 重新获取更新后的任务
        task = await Task.get(id=task_id)
        
        # 转换为字典格式
        task_dict = {
            "id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "target": task.target,
            "status": task.status,
            "progress": task.progress,
            "config": json.loads(task.config) if task.config else {},
            "result": json.loads(task.result) if task.result else None,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return APIResponse(code=200, message="任务已取消", data=task_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/progress", response_model=APIResponse)
async def get_task_progress(task_id: int):
    """
    获取任务进度（实时显示功能）
    """
    try:
        from models import Task
        
        task = await Task.get_or_none(id=task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 返回进度信息
        progress_info = {
            "task_id": task.id,
            "task_name": task.task_name,
            "status": task.status,
            "progress": task.progress,
            "target": task.target,
            "updated_at": task.updated_at
        }
        
        return APIResponse(code=200, message="获取成功", data=progress_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 获取任务漏洞列表 ====================
@router.get("/{task_id}/vulnerabilities", response_model=APIResponse)
async def get_task_vulnerabilities(task_id: int):
    """
    获取任务的漏洞列表（统一接口）
    """
    try:
        from models import Task, POCScanResult
        from config import settings
        from AVWS.API.Vuln import Vuln
        
        task = await Task.get_or_none(id=task_id)
        if not task:
            return APIResponse(code=404, message="任务不存在")
            
        vulnerabilities = []
        
        # 根据任务类型获取漏洞
        if task.task_type == 'awvs_scan':
            # 获取 AWVS 漏洞
            config = json.loads(task.config) if task.config else {}
            target_id = config.get('awvs_target_id') or config.get('target_id')
            
            if target_id:
                client = {
                    'api_url': settings.AWVS_API_URL,
                    'api_key': settings.AWVS_API_KEY
                }
                d = Vuln(client['api_url'], client['api_key'])
                
                # 搜索该目标的漏洞
                try:
                    vuln_details_json = d.search(None, None, "open", target_id=target_id)
                    vuln_details = json.loads(vuln_details_json)
                    
                    if 'vulnerabilities' in vuln_details:
                        for item in vuln_details['vulnerabilities']:
                            severity_val = item.get('severity')
                            severity = standardize_severity(severity_val)
                            
                            vt_name = item.get('vt_name', 'Unknown Vulnerability')
                            title = standardize_title(vt_name)
                            
                            vulnerabilities.append({
                                'id': item.get('vuln_id'),
                                'title': title,
                                'type': item.get('vt_name'), 
                                'severity': severity,
                                'cvssScore': item.get('cvss_score'),
                                'location': item.get('affects_url'),
                                'discoveredAt': item.get('last_seen', '').replace('T', ' ').split('.')[0],
                                'status': item.get('status', 'open'),
                                'target': item.get('affects_url'),
                                'source': 'awvs'
                            })
                except Exception as e:
                    logger.error(f"Fetch AWVS vulns failed: {e}")
                    
        elif task.task_type == 'poc_scan':
            # 获取 POC 漏洞
            poc_results = await POCScanResult.filter(task=task, vulnerable=True).all()
            for res in poc_results:
                vulnerabilities.append({
                    'id': str(res.id),
                    'title': standardize_title(f"{res.poc_type} 漏洞"),
                    'type': res.poc_type,
                    'severity': standardize_severity(res.severity or 'high'),
                    'cvssScore': 0, 
                    'location': res.target,
                    'discoveredAt': res.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'open',
                    'target': res.target,
                    'source': 'poc'
                })
        
        return APIResponse(code=200, message="获取成功", data=vulnerabilities)
        
    except Exception as e:
        logger.error(f"获取任务漏洞失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 获取漏洞详情 ====================
@router.get("/vulnerabilities/{vuln_id}", response_model=APIResponse)
async def get_vulnerability_detail(vuln_id: str, source: Optional[str] = 'awvs'):
    """
    获取漏洞详情（统一接口）
    """
    try:
        from models import Task, POCScanResult
        from config import settings
        from AVWS.API.Vuln import Vuln
        
        data = {}
        
        if source == 'awvs':
            client = {
                'api_url': settings.AWVS_API_URL,
                'api_key': settings.AWVS_API_KEY
            }
            v = Vuln(client['api_url'], client['api_key'])
            vuln_data = v.get(vuln_id)
            
            if vuln_data:
                        severity_val = vuln_data.get('severity')
                        severity = standardize_severity(severity_val)
                        
                        vt_name = vuln_data.get('vt_name', '')
                        title = standardize_title(vt_name)

                        data = {
                            'vuln_id': vuln_data.get('vuln_id'),
                            'vt_name': title,  # Use prefixed title for display
                            'severity': severity,
                            'cvss_score': vuln_data.get('cvss_score'),
                            'affects_url': vuln_data.get('affects_url'),
                            'last_seen': vuln_data.get('last_seen', '').replace('T', ' ').split('.')[0],
                            'impact': vuln_data.get('impact', ''),
                            'description': vuln_data.get('description', ''),
                            'details': vuln_data.get('details', ''),
                            'recommendation': vuln_data.get('recommendation', ''),
                            'request': vuln_data.get('request', ''),
                            'response': vuln_data.get('response', ''),
                            'status': vuln_data.get('status', 'open'),
                            'source': 'awvs'
                        }
                
        elif source == 'poc':
            try:
                res = await POCScanResult.get_or_none(id=int(vuln_id))
                if res:
                    data = {
                        'vuln_id': str(res.id),
                        'vt_name': f"{res.poc_type} 漏洞",
                        'severity': res.severity.title() if res.severity else 'High',
                        'cvss_score': 0,
                        'affects_url': res.target,
                        'last_seen': res.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        'impact': 'Potential RCE or Information Leak',
                        'description': res.message,
                        'details': f"CVE ID: {res.cve_id}" if res.cve_id else "",
                        'recommendation': 'Please update to the latest version.',
                        'request': '',
                        'response': '',
                        'status': 'open',
                        'source': 'poc'
                    }
            except ValueError:
                pass

        if data:
            return APIResponse(code=200, message="获取成功", data=data)
        else:
            return APIResponse(code=404, message="未找到漏洞信息")
            
    except Exception as e:
        logger.error(f"获取漏洞详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
