import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, Tag

sys.path.insert(0, str(Path(__file__).parent))
from config import TARGET_URL, OUTPUT_DIR, CRAWLER_CONFIG, OUTPUT_CONFIG, FILTERS, ensure_output_dir


class AcunetixAPICrawler:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.api_data: List[Dict] = []
        self.all_links: List[Dict] = []
        self.base_url = FILTERS['base_url']
        self.api_pattern = re.compile(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\/api\/v1\/[^\s"\'<>]+)', re.IGNORECASE)
        self.endpoint_pattern = re.compile(r'(\/api\/v1\/[^\s"\'<>]+)', re.IGNORECASE)
        self.status_code_pattern = re.compile(r'\b(200|201|202|204|400|401|403|404|500)\b')
        
    async def crawl(self):
        ensure_output_dir()
        
        async with async_playwright() as p:
            print('正在启动浏览器...')
            browser = await p.chromium.launch(
                headless=CRAWLER_CONFIG['headless'],
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security', '--disable-features=VizDisplayCompositor']
            )
            
            print('正在创建浏览器上下文...')
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True,
                java_script_enabled=True
            )
            
            page = await context.new_page()
            
            print(f'=== Acunetix API Crawler ===')
            print(f'Target URL: {TARGET_URL}')
            print(f'Output directory: {OUTPUT_DIR}')
            print(f'Headless mode: {CRAWLER_CONFIG["headless"]}\n')
            
            try:
                print('开始爬取主页面...')
                await self._crawl_page(page, TARGET_URL)
                
            except Exception as e:
                print(f'\n爬取过程中发生错误: {e}')
                import traceback
                traceback.print_exc()
            finally:
                print('\n正在关闭浏览器...')
                await browser.close()
                print('浏览器已关闭')
        
        self._save_results()
    
    async def _crawl_page(self, page, url: str):
        if url in self.visited_urls:
            print(f'  跳过已访问: {url}')
            return
        
        self.visited_urls.add(url)
        print(f'\n正在访问: {url}')
        
        try:
            print(f'  正在加载页面...')
            await page.goto(url, wait_until='domcontentloaded', timeout=CRAWLER_CONFIG['timeout'])
            
            print(f'  等待页面稳定...')
            await asyncio.sleep(2)
            
            print(f'  获取页面内容...')
            content = await page.content()
            
            if not content or len(content) < 100:
                print(f'  ⚠ 页面内容为空或过短')
                return
            
            print(f'  解析页面...')
            soup = BeautifulSoup(content, 'lxml')
            
            page_api_data = self._extract_api_data(soup, url)
            if page_api_data:
                self.api_data.extend(page_api_data)
                print(f'  ✓ 提取了 {len(page_api_data)} 个 API 部分')
            else:
                print(f'  ⚠ 未找到 API 数据')
            
            page_links = self._extract_links(soup, url)
            self.all_links.extend(page_links)
            print(f'  ✓ 找到 {len(page_links)} 个链接')
            
        except asyncio.TimeoutError:
            print(f'  ✗ 超时错误: {url}')
        except Exception as e:
            print(f'  ✗ 处理错误 {url}: {type(e).__name__}: {e}')
    
    def _extract_api_data(self, soup: BeautifulSoup, current_url: str) -> List[Dict]:
        api_data = []
        processed_sections = set()
        
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headers:
            print('    未找到任何标题')
            return api_data
        
        print(f'    找到 {len(headers)} 个标题')
        
        for idx, header in enumerate(headers, 1):
            section_id = header.get('id', '') or header.get('name', '')
            section_title = header.get_text(strip=True)
            
            if section_id in processed_sections:
                continue
            processed_sections.add(section_id)
            
            section = self._extract_section_data(header, section_title, section_id)
            
            if section['endpoints'] or section['parameters']:
                api_data.append(section)
                print(f'    [{idx}] 添加部分: {section_title} (端点: {len(section["endpoints"])}, 参数: {len(section["parameters"])})')
        
        return api_data
    
    def _extract_section_data(self, header: Tag, section_title: str, section_id: str) -> Dict:
        section = {
            'sectionTitle': section_title,
            'sectionId': section_id,
            'methods': [],
            'endpoints': [],
            'description': '',
            'parameters': [],
            'examples': [],
            'responseFormat': '',
            'statusCode': '',
            'authentication': '',
            'requestHeaders': [],
            'responseHeaders': [],
            'url': '',
        }
        
        container = header.find_next_sibling() or header.parent
        section_content = container.find_parent(['section', 'div', 'article', 'main', 'body']) or container
        
        self._extract_endpoints_and_methods(section_content, section)
        self._extract_parameters(section_content, section)
        self._extract_description(section_content, section)
        self._extract_status_and_response(section_content, section)
        self._extract_authentication(section_content, section)
        self._extract_examples(section_content, section)
        
        return section
    
    def _extract_endpoints_and_methods(self, section_content: Tag, section: Dict):
        code_blocks = section_content.find_all(['code', 'pre'])
        
        for code in code_blocks:
            code_text = code.get_text(strip=True)
            
            match = self.api_pattern.search(code_text)
            if match:
                method = match.group(1).upper()
                endpoint = match.group(2)
                
                if method not in section['methods']:
                    section['methods'].append(method)
                if endpoint not in section['endpoints']:
                    section['endpoints'].append(endpoint)
            
            endpoint_matches = self.endpoint_pattern.findall(code_text)
            for endpoint in endpoint_matches:
                if endpoint not in section['endpoints']:
                    section['endpoints'].append(endpoint)
        
        for text in section_content.stripped_strings:
            match = self.api_pattern.search(str(text))
            if match:
                method = match.group(1).upper()
                endpoint = match.group(2)
                
                if method not in section['methods']:
                    section['methods'].append(method)
                if endpoint not in section['endpoints']:
                    section['endpoints'].append(endpoint)
    
    def _extract_parameters(self, section_content: Tag, section: Dict):
        tables = section_content.find_all('table')
        
        for table in tables:
            headers_text = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if cells:
                    param = {}
                    for i, header in enumerate(headers_text):
                        param[header] = cells[i].get_text(strip=True) if i < len(cells) else ''
                    
                    if param.get('name') or param.get('parameter') or param.get('field'):
                        param_name = param.get('name') or param.get('parameter') or param.get('field')
                        if not any(p.get('name') == param_name or p.get('parameter') == param_name or p.get('field') == param_name for p in section['parameters']):
                            section['parameters'].append(param)
    
    def _extract_description(self, section_content: Tag, section: Dict):
        description_elements = section_content.find_all(['p', 'div', 'span'])
        descriptions = []
        
        for elem in description_elements:
            text = elem.get_text(strip=True)
            if len(text) > 20 and text not in descriptions:
                descriptions.append(text)
        
        section['description'] = '\n'.join(descriptions[:5])
    
    def _extract_status_and_response(self, section_content: Tag, section: Dict):
        status_elements = section_content.find_all(class_=re.compile(r'status|response|code|http', re.IGNORECASE))
        
        for elem in status_elements:
            text = elem.get_text(strip=True)
            
            status_match = self.status_code_pattern.search(text)
            if status_match and not section['statusCode']:
                section['statusCode'] = status_match.group(1)
            
            if len(text) > 10 and len(text) < 500 and not section['responseFormat']:
                if '{' in text or '[' in text:
                    section['responseFormat'] = text
    
    def _extract_authentication(self, section_content: Tag, section: Dict):
        auth_keywords = ['authentication', 'authorization', 'api key', 'token', 'bearer', 'x-auth']
        
        for elem in section_content.find_all(['p', 'div', 'span', 'code']):
            if elem.parent and elem.parent.name not in ['script', 'style']:
                text = elem.get_text(strip=True).lower()
                
                if any(keyword in text for keyword in auth_keywords):
                    auth_text = elem.get_text(strip=True)
                    if len(auth_text) > 10 and len(auth_text) < 300 and not section['authentication']:
                        section['authentication'] = auth_text
    
    def _extract_examples(self, section_content: Tag, section: Dict):
        code_blocks = section_content.find_all(['code', 'pre'])
        
        for code in code_blocks:
            code_text = code.get_text(strip=True)
            
            if 20 < len(code_text) < 1000 and code_text not in section['examples']:
                if self.api_pattern.search(code_text) or self.endpoint_pattern.search(code_text):
                    section['examples'].append(code_text)
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[Dict]:
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if any(pattern in href for pattern in FILTERS['include_patterns']):
                absolute_url = urljoin(current_url, href)
                
                if absolute_url.startswith(self.base_url):
                    links.append({
                        'text': text,
                        'href': absolute_url,
                    })
        
        return links
    
    def _save_results(self):
        if not self.api_data:
            print('\n未找到 API 数据保存')
            return
        
        output_file = OUTPUT_DIR / OUTPUT_CONFIG['json_file']
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.api_data, f, ensure_ascii=False, indent=2)
        
        print(f'\n=== 爬取完成 ===')
        print(f'访问页面数: {len(self.visited_urls)}')
        print(f'找到 API 部分数: {len(self.api_data)}')
        print(f'数据保存到: {output_file}')
        
        unique_methods = list(set(m for item in self.api_data for m in item['methods']))
        unique_endpoints = list(set(e for item in self.api_data for e in item['endpoints']))
        
        summary = {
            'totalEndpoints': len(self.api_data),
            'uniqueMethods': unique_methods,
            'uniqueEndpoints': unique_endpoints,
            'totalParameters': sum(len(item['parameters']) for item in self.api_data),
            'totalExamples': sum(len(item['examples']) for item in self.api_data),
            'pagesVisited': len(self.visited_urls),
            'timestamp': datetime.now().isoformat(),
            'targetUrl': TARGET_URL,
        }
        
        summary_file = OUTPUT_DIR / OUTPUT_CONFIG['summary_file']
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f'摘要保存到: {summary_file}')
        print(f'\n=== 统计信息 ===')
        print(f'唯一方法: {", ".join(unique_methods) if unique_methods else "无"}')
        print(f'唯一端点数: {len(unique_endpoints)}')
        print(f'总参数数: {summary["totalParameters"]}')
        print(f'总示例数: {summary["totalExamples"]}')


async def main():
    crawler = AcunetixAPICrawler()
    await crawler.crawl()


if __name__ == '__main__':
    asyncio.run(main())
