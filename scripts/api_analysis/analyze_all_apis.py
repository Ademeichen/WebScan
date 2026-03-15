#!/usr/bin/env python3
"""
完整的API分析脚本 - 分析前后端所有API
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
    
    # 手动整理已知的后端API
    # 从api/__init__.py我们知道各个模块的prefix
    modules = [
        ('scan', '/scan'),
        ('tasks', '/tasks'),
        ('reports', '/reports'),
        ('awvs', '/awvs'),
        ('settings', '/settings'),
        ('ai', '/ai'),
        ('kb', '/kb'),
        ('user', '/user'),
        ('notifications', '/notifications'),
        ('poc', '/poc'),
        ('poc_verification', '/poc/verification'),
        ('poc_files', '/poc/files'),
        ('seebug_agent', '/seebug'),
    ]
    
    for module_name, prefix in modules:
        file_path = BACKEND_DIR / "api" / f"{module_name}.py"
        if not file_path.exists():
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 查找FastAPI路由装饰器
            patterns = [
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    full_path = prefix + path
                    
                    apis.append({
                        'method': method,
                        'path': full_path,
                        'module': module_name,
                        'file': str(file_path.relative_to(BACKEND_DIR))
                    })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # 添加ai_agents的API
    ai_agents_file = BACKEND_DIR / "ai_agents" / "api" / "routes.py"
    if ai_agents_file.exists():
        try:
            content = ai_agents_file.read_text(encoding='utf-8')
            patterns = [
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    full_path = '/ai_agents' + path
                    
                    apis.append({
                        'method': method,
                        'path': full_path,
                        'module': 'ai_agents',
                        'file': str(ai_agents_file.relative_to(BACKEND_DIR))
                    })
        except Exception as e:
            print(f"Error reading ai_agents routes: {e}")
    
    return apis

def extract_frontend_apis():
    """从前端api.js提取所有API调用"""
    api_file = FRONTEND_DIR / "utils" / "api.js"
    
    if not api_file.exists():
        return []
    
    content = api_file.read_text(encoding='utf-8')
    
    apis = []
    
    # 查找各个API模块
    lines = content.split('\n')
    current_module = None
    in_module = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 查找模块开始
        if line.startswith('export const') and 'Api = {' in line:
            match = re.search(r'export\s+const\s+(\w+Api)', line)
            if match:
                current_module = match.group(1)
                in_module = True
            continue
        
        # 查找模块结束
        if in_module and line == '}':
            current_module = None
            in_module = False
            continue
        
        # 查找方法定义
        if in_module and ':' in line and not line.startswith('//') and 'async' in line:
            # 提取方法名
            method_match = re.match(r'(\w+)\s*:', line)
            if method_match:
                method_name = method_match.group(1)
                
                # 查找url和method，需要看后续几行
                url = None
                http_method = None
                
                # 查找后续行的url和method
                for j in range(i, min(i+20, len(lines))):
                    next_line = lines[j].strip()
                    
                    if 'url:' in next_line:
                        url_match = re.search(r'url:\s*["\']([^"\']+)["\']', next_line)
                        if url_match:
                            url = url_match.group(1)
                    
                    if 'method:' in next_line:
                        method_match_http = re.search(r'method:\s*["\'](\w+)["\']', next_line)
                        if method_match_http:
                            http_method = method_match_http.group(1).upper()
                    
                    if url and http_method:
                        break
                
                if url and http_method:
                    apis.append({
                        'module': current_module,
                        'method_name': method_name,
                        'method': http_method,
                        'path': url,
                        'full_name': f"{current_module}.{method_name}"
                    })
    
    return apis

def normalize_path(path):
    """标准化路径用于比较"""
    path = path.rstrip('/')
    path = re.sub(r'\{[^}]+\}', '{param}', path)
    path = re.sub(r':\w+', '{param}', path)
    return path

def match_apis(backend_apis, frontend_apis):
    """匹配前后端API"""
    matched = []
    unmatched_backend = []
    unmatched_frontend = []
    
    backend_index = defaultdict(list)
    for api in backend_apis:
        key = (api['method'], normalize_path(api['path']))
        backend_index[key].append(api)
    
    for frontend_api in frontend_apis:
        key = (frontend_api['method'], normalize_path(frontend_api['path']))
        if key in backend_index:
            matched.append({
                'frontend': frontend_api,
                'backend': backend_index[key][0]
            })
        else:
            unmatched_frontend.append(frontend_api)
    
    matched_backend_paths = set((m['backend']['method'], m['backend']['path']) for m in matched)
    for backend_api in backend_apis:
        if (backend_api['method'], backend_api['path']) not in matched_backend_paths:
            unmatched_backend.append(backend_api)
    
    return matched, unmatched_backend, unmatched_frontend

def main():
    print("="*80)
    print("完整API分析")
    print("="*80)
    
    print("\n1. 提取后端API...")
    backend_apis = extract_backend_apis()
    print(f"   后端API总数: {len(backend_apis)}")
    
    print("\n2. 提取前端API...")
    frontend_apis = extract_frontend_apis()
    print(f"   前端API总数: {len(frontend_apis)}")
    
    print("\n3. 匹配API...")
    matched, unmatched_backend, unmatched_frontend = match_apis(backend_apis, frontend_apis)
    print(f"   匹配成功: {len(matched)}")
    print(f"   后端未匹配: {len(unmatched_backend)}")
    print(f"   前端未匹配: {len(unmatched_frontend)}")
    
    print("\n" + "="*80)
    print("匹配成功的API:")
    print("="*80)
    for m in matched:
        print(f"  ✓ {m['frontend']['method']:7s} {m['frontend']['path']:50s} -> {m['frontend']['full_name']}")
    
    print("\n" + "="*80)
    print("前端未匹配的API（需要修复）:")
    print("="*80)
    for api in unmatched_frontend:
        print(f"  ! {api['method']:7s} {api['path']:50s} -> {api['full_name']}")
    
    result = {
        'backend_apis': backend_apis,
        'frontend_apis': frontend_apis,
        'matched': matched,
        'unmatched_backend': unmatched_backend,
        'unmatched_frontend': unmatched_frontend
    }
    
    output_file = Path(r"d:\AI_WebSecurity\.trae\documents\all_apis_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"\n详细结果已保存到: {output_file}")
    
    return result

if __name__ == "__main__":
    main()
