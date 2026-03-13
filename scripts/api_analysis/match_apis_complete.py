#!/usr/bin/env python3
"""
完整的API匹配脚本 - 确保前端所有API都与后端匹配
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(r"d:\AI_WebSecurity\backend")
FRONTEND_DIR = Path(r"d:\AI_WebSecurity\front\src")

def extract_backend_apis():
    """从后端提取所有API接口"""
    apis = []
    
    # 查找所有API路由文件
    api_files = []
    for ext in ['*.py']:
        api_files.extend(BACKEND_DIR.rglob(ext))
    
    for file_path in api_files:
        if 'test' in str(file_path).lower() or '__pycache__' in str(file_path):
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 查找FastAPI路由装饰器
            patterns = [
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    # 查找该文件中定义的router prefix
                    prefix = ''
                    prefix_match = re.search(r'router\s*=\s*APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)["\']', content)
                    if prefix_match:
                        prefix = prefix_match.group(1)
                    
                    # 从api/__init__.py中查找prefix
                    full_path = prefix + path if prefix else path
                    
                    apis.append({
                        'method': method,
                        'path': full_path,
                        'file': str(file_path.relative_to(BACKEND_DIR))
                    })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # 从api/__init__.py获取正确的prefix
    api_init = BACKEND_DIR / "api" / "__init__.py"
    if api_init.exists():
        content = api_init.read_text(encoding='utf-8')
        # 解析include_router获取正确的prefix
        router_prefix_map = {}
        # 简化解析，手动映射已知的prefix
        router_prefix_map = {
            'scan': '/scan',
            'tasks': '/tasks',
            'reports': '/reports',
            'awvs': '/awvs',
            'settings': '/settings',
            'ai': '/ai',
            'kb': '/kb',
            'user': '/user',
            'notifications': '/notifications',
            'poc': '/poc',
            'poc_verification': '/poc/verification',
            'poc_files': '/poc/files',
            'seebug_agent': '/seebug',
        }
        
        # 更新apis的path
        updated_apis = []
        for api in apis:
            file_name = Path(api['file']).stem
            prefix = router_prefix_map.get(file_name, '')
            if prefix and not api['path'].startswith(prefix):
                api['path'] = prefix + api['path']
            updated_apis.append(api)
        apis = updated_apis
    
    return apis

def extract_frontend_apis():
    """从前端api.js提取所有API调用"""
    api_file = FRONTEND_DIR / "utils" / "api.js"
    
    if not api_file.exists():
        return []
    
    content = api_file.read_text(encoding='utf-8')
    
    apis = []
    
    # 查找各个API模块
    module_pattern = r'export\s+const\s+(\w+Api)\s*=\s*\{([^}]+)\}'
    module_matches = re.finditer(module_pattern, content, re.DOTALL)
    
    for module_match in module_matches:
        module_name = module_match.group(1)
        module_content = module_match.group(2)
        
        # 查找模块中的方法
        method_pattern = r'(\w+)\s*:\s*async\s*\([^)]*\)\s*=>\s*\{[^}]*url:\s*["\']([^"\']+)["\'][^}]*method:\s*["\'](\w+)["\']'
        method_matches = re.finditer(method_pattern, module_content, re.DOTALL)
        
        for method_match in method_matches:
            method_name = method_match.group(1)
            url = method_match.group(2)
            http_method = method_match.group(3).upper()
            
            apis.append({
                'module': module_name,
                'method_name': method_name,
                'method': http_method,
                'path': url,
                'full_name': f"{module_name}.{method_name}"
            })
    
    return apis

def normalize_path(path):
    """标准化路径用于比较"""
    # 移除尾部斜杠
    path = path.rstrip('/')
    # 替换路径参数为通用格式 {param}
    path = re.sub(r'\{[^}]+\}', '{param}', path)
    path = re.sub(r':\w+', '{param}', path)
    return path

def match_apis(backend_apis, frontend_apis):
    """匹配前后端API"""
    matched = []
    unmatched_backend = []
    unmatched_frontend = []
    
    # 创建后端API索引
    backend_index = defaultdict(list)
    for api in backend_apis:
        key = (api['method'], normalize_path(api['path']))
        backend_index[key].append(api)
    
    # 匹配前端API
    for frontend_api in frontend_apis:
        key = (frontend_api['method'], normalize_path(frontend_api['path']))
        if key in backend_index:
            matched.append({
                'frontend': frontend_api,
                'backend': backend_index[key][0]
            })
        else:
            unmatched_frontend.append(frontend_api)
    
    # 找出未匹配的后端API
    matched_backend_paths = set((m['backend']['method'], m['backend']['path']) for m in matched)
    for backend_api in backend_apis:
        if (backend_api['method'], backend_api['path']) not in matched_backend_paths:
            unmatched_backend.append(backend_api)
    
    return matched, unmatched_backend, unmatched_frontend

def main():
    print("="*80)
    print("完整API匹配分析")
    print("="*80)
    
    # 提取API
    print("\n1. 提取后端API...")
    backend_apis = extract_backend_apis()
    print(f"   后端API总数: {len(backend_apis)}")
    
    print("\n2. 提取前端API...")
    frontend_apis = extract_frontend_apis()
    print(f"   前端API总数: {len(frontend_apis)}")
    
    # 匹配API
    print("\n3. 匹配API...")
    matched, unmatched_backend, unmatched_frontend = match_apis(backend_apis, frontend_apis)
    print(f"   匹配成功: {len(matched)}")
    print(f"   后端未匹配: {len(unmatched_backend)}")
    print(f"   前端未匹配: {len(unmatched_frontend)}")
    
    # 输出匹配成功的
    print("\n" + "="*80)
    print("匹配成功的API:")
    print("="*80)
    for m in matched:
        print(f"  ✓ {m['frontend']['method']:7s} {m['frontend']['path']:50s} -> {m['frontend']['full_name']}")
    
    # 输出前端未匹配的（需要修复）
    print("\n" + "="*80)
    print("前端未匹配的API（需要修复）:")
    print("="*80)
    for api in unmatched_frontend:
        print(f"  ! {api['method']:7s} {api['path']:50s} -> {api['full_name']}")
    
    # 保存结果
    result = {
        'backend_apis': backend_apis,
        'frontend_apis': frontend_apis,
        'matched': matched,
        'unmatched_backend': unmatched_backend,
        'unmatched_frontend': unmatched_frontend
    }
    
    output_file = Path(r"d:\AI_WebSecurity\.trae\documents\complete_api_match.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"\n详细结果已保存到: {output_file}")
    
    return result

if __name__ == "__main__":
    main()
