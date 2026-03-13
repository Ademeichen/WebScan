#!/usr/bin/env python3
"""
分析前端组件实际使用的API调用
"""
import os
import re
import json
from pathlib import Path

FRONTEND_DIR = Path(r"d:\AI_WebSecurity\front\src")

def find_api_usages():
    """查找前端组件中实际使用的API"""
    api_usages = {}
    
    # 先读取api.js中的所有API定义
    api_definitions = read_api_definitions()
    
    # 查找所有.vue和.js文件
    vue_files = list(FRONTEND_DIR.rglob("*.vue"))
    js_files = list(FRONTEND_DIR.rglob("*.js"))
    
    all_files = vue_files + js_files
    
    for file_path in all_files:
        if str(file_path).endswith("api.js") or str(file_path).endswith("aiAgents.js"):
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 查找各种API调用模式
            patterns = [
                r'(\w+Api)\.(\w+)\(',  # tasksApi.getTasks(
                r'api\.(\w+)\.(\w+)\(',  # api.tasks.getTasks(
                r'from.*utils\.api import.*',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if len(match.groups()) >= 2:
                        api_module = match.group(1)
                        api_method = match.group(2)
                        key = f"{api_module}.{api_method}"
                        
                        if key not in api_usages:
                            api_usages[key] = {
                                'module': api_module,
                                'method': api_method,
                                'files': []
                            }
                        
                        rel_path = str(file_path.relative_to(FRONTEND_DIR))
                        if rel_path not in api_usages[key]['files']:
                            api_usages[key]['files'].append(rel_path)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return api_usages, api_definitions

def read_api_definitions():
    """读取api.js中的API定义"""
    api_file = FRONTEND_DIR / "utils" / "api.js"
    
    if not api_file.exists():
        return {}
    
    content = api_file.read_text(encoding='utf-8')
    
    definitions = {}
    
    # 查找export const定义
    patterns = [
        r'export\s+const\s+(\w+Api)\s*=\s*\{',
    ]
    
    # 简单解析
    lines = content.split('\n')
    current_module = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('export const') and 'Api = {' in line:
            match = re.search(r'export\s+const\s+(\w+Api)', line)
            if match:
                current_module = match.group(1)
                definitions[current_module] = []
        
        elif current_module and line.startswith('}'):
            current_module = None
        
        elif current_module and ':' in line and not line.startswith('//'):
            # 查找方法名
            match = re.match(r'(\w+)\s*:', line)
            if match:
                method_name = match.group(1)
                definitions[current_module].append(method_name)
    
    return definitions

def main():
    print("=== 分析前端API使用情况 ===\n")
    
    api_usages, api_definitions = find_api_usages()
    
    print("1. 实际使用的API:")
    for key in sorted(api_usages.keys()):
        usage = api_usages[key]
        print(f"  ✓ {key}")
        for file in usage['files'][:3]:
            print(f"      - {file}")
        if len(usage['files']) > 3:
            print(f"      ... 还有 {len(usage['files']) - 3} 个文件")
    
    print("\n2. 定义但未使用的API:")
    unused_apis = []
    for module, methods in api_definitions.items():
        for method in methods:
            key = f"{module}.{method}"
            if key not in api_usages:
                unused_apis.append(key)
    
    for api in sorted(unused_apis):
        print(f"  ? {api}")
    
    # 保存结果
    result = {
        'used_apis': api_usages,
        'unused_apis': unused_apis,
        'definitions': api_definitions
    }
    
    output_file = Path(r"d:\AI_WebSecurity\.trae\documents\frontend_api_usage.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"\n分析结果已保存到: {output_file}")
    print(f"\n统计:")
    print(f"  定义的API总数: {sum(len(m) for m in api_definitions.values())}")
    print(f"  实际使用的API: {len(api_usages)}")
    print(f"  未使用的API: {len(unused_apis)}")

if __name__ == "__main__":
    main()
