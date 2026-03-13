import json
from pathlib import Path


def normalize_path(path):
    normalized = path.rstrip('/')
    normalized = normalized.replace('{', '<').replace('}', '>')
    return normalized


def match_paths(backend_path, frontend_url):
    b_norm = normalize_path(backend_path)
    f_norm = normalize_path(frontend_url)
    
    if b_norm == f_norm:
        return True
    
    b_parts = b_norm.split('/')
    f_parts = f_norm.split('/')
    
    if len(b_parts) != len(f_parts):
        return False
    
    for b_part, f_part in zip(b_parts, f_parts):
        if b_part.startswith('<') and f_part.startswith('<'):
            continue
        if b_part != f_part:
            return False
    
    return True


def main():
    analysis_path = Path(r'd:\AI_WebSecurity\.trae\documents\api_analysis.json')
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    backend_apis = data['backend_apis']
    frontend_apis = data['frontend_apis']
    
    print("=" * 80)
    print("前后端 API 接口兼容性校验报告")
    print("=" * 80)
    
    matched_apis = []
    unmatched_backend = []
    unmatched_frontend = []
    
    for backend_api in backend_apis:
        matched = False
        for frontend_api in frontend_apis:
            if backend_api['method'] == frontend_api['method'] and match_paths(backend_api['path'], frontend_api['url']):
                matched_apis.append({
                    'backend': backend_api,
                    'frontend': frontend_api
                })
                matched = True
                break
        if not matched:
            unmatched_backend.append(backend_api)
    
    for frontend_api in frontend_apis:
        matched = False
        for backend_api in backend_apis:
            if frontend_api['method'] == backend_api['method'] and match_paths(backend_api['path'], frontend_api['url']):
                matched = True
                break
        if not matched:
            unmatched_frontend.append(frontend_api)
    
    print(f"\n1. 匹配成功的接口 ({len(matched_apis)} 个):")
    print("-" * 80)
    for match in matched_apis:
        b = match['backend']
        f = match['frontend']
        print(f"  ✓ {b['method']:7s} {b['path']:50s} 前端: {f['name']}")
    
    print(f"\n2. 后端有但前端没有实现的接口 ({len(unmatched_backend)} 个):")
    print("-" * 80)
    
    unmatched_by_prefix = {}
    for api in unmatched_backend:
        prefix = api['base_prefix'] if api['base_prefix'] else 'other'
        if prefix not in unmatched_by_prefix:
            unmatched_by_prefix[prefix] = []
        unmatched_by_prefix[prefix].append(api)
    
    for prefix, apis in sorted(unmatched_by_prefix.items()):
        print(f"\n--- {prefix} ---")
        for api in sorted(apis, key=lambda x: (x['method'], x['path'])):
            print(f"  ? {api['method']:7s} {api['path']:50s} [{api['file']}]")
    
    print(f"\n3. 前端有但后端不存在的接口 ({len(unmatched_frontend)} 个):")
    print("-" * 80)
    for api in unmatched_frontend:
        print(f"  ! {api['method']:7s} {api['url']:50s} {api['name']}")
    
    print("\n" + "=" * 80)
    print("统计摘要")
    print("=" * 80)
    print(f"后端接口总数: {len(backend_apis)}")
    print(f"前端接口总数: {len(frontend_apis)}")
    print(f"匹配成功: {len(matched_apis)}")
    print(f"后端未匹配: {len(unmatched_backend)}")
    print(f"前端未匹配: {len(unmatched_frontend)}")
    
    report_data = {
        'summary': {
            'total_backend': len(backend_apis),
            'total_frontend': len(frontend_apis),
            'matched': len(matched_apis),
            'unmatched_backend': len(unmatched_backend),
            'unmatched_frontend': len(unmatched_frontend)
        },
        'matched_apis': matched_apis,
        'unmatched_backend': unmatched_backend,
        'unmatched_frontend': unmatched_frontend
    }
    
    report_path = Path(r'd:\AI_WebSecurity\.trae\documents\api_compatibility_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_path}")
    
    return report_data


if __name__ == '__main__':
    main()
