import re
import os
import json
from pathlib import Path


class APIController:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.apis = []
        
    def extract_apis_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        relative_path = file_path.relative_to(self.base_path)
        prefix = str(relative_path.parent).replace('\\', '/')
        
        router_pattern = r'router\s*=\s*APIRouter\([^)]*prefix=["\']([^"\']+)["\'][^)]*\)'
        router_match = re.search(router_pattern, content)
        base_prefix = router_match.group(1) if router_match else ''
        
        pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'][^)]*\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            full_path = f"{base_prefix}{path}"
            
            api_info = {
                'file': str(relative_path),
                'method': method,
                'path': full_path,
                'base_prefix': base_prefix,
                'endpoint': path
            }
            self.apis.append(api_info)
            
    def analyze_all_api_files(self):
        api_dir = self.base_path / 'api'
        ai_agents_api_dir = self.base_path / 'ai_agents' / 'api'
        
        if api_dir.exists():
            for file_path in api_dir.glob('*.py'):
                if file_path.is_file():
                    self.extract_apis_from_file(file_path)
        
        if ai_agents_api_dir.exists():
            for file_path in ai_agents_api_dir.glob('*.py'):
                if file_path.is_file():
                    self.extract_apis_from_file(file_path)
        
        return self.apis


class FrontendAPIController:
    def __init__(self, api_js_path):
        self.api_js_path = Path(api_js_path)
        self.apis = []
        
    def extract_apis(self):
        with open(self.api_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'(\w+):\s*async\s*\([^)]*\)\s*=>\s*\{[\s\S]*?url:\s*["\']([^"\']+)["\'][\s\S]*?method:\s*["\']([^"\']+)["\']'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            name = match.group(1)
            url = match.group(2)
            method = match.group(3).upper()
            
            self.apis.append({
                'name': name,
                'method': method,
                'url': url
            })
        
        return self.apis


def main():
    backend_path = r'd:\AI_WebSecurity\backend'
    api_js_path = r'd:\AI_WebSecurity\front\src\utils\api.js'
    
    print("=== 分析后端 FastAPI 接口 ===\n")
    
    backend_analyzer = APIController(backend_path)
    backend_apis = backend_analyzer.analyze_all_api_files()
    
    backend_apis_sorted = sorted(backend_apis, key=lambda x: (x['base_prefix'], x['method'], x['path']))
    
    print(f"共找到 {len(backend_apis_sorted)} 个后端接口：\n")
    
    current_prefix = None
    for api in backend_apis_sorted:
        if api['base_prefix'] != current_prefix:
            current_prefix = api['base_prefix']
            print(f"\n--- {current_prefix} ---")
        print(f"  {api['method']:7s} {api['path']}")
    
    print("\n\n=== 分析前端 API 调用 ===\n")
    
    frontend_analyzer = FrontendAPIController(api_js_path)
    frontend_apis = frontend_analyzer.extract_apis()
    
    print(f"共找到 {len(frontend_apis)} 个前端 API 调用：\n")
    
    for api in sorted(frontend_apis, key=lambda x: (x['method'], x['url'])):
        print(f"  {api['method']:7s} {api['url']:50s} {api['name']}")
    
    output_data = {
        'backend_apis': backend_apis_sorted,
        'frontend_apis': frontend_apis
    }
    
    output_path = Path(r'd:\AI_WebSecurity\.trae\documents\api_analysis.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n分析结果已保存到: {output_path}")
    
    return output_data


if __name__ == '__main__':
    main()
