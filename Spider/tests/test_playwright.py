from playwright.sync_api import sync_playwright

def test_playwright():
    print('正在测试 Playwright 安装...')
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.baidu.com')
            title = page.title()
            print(f'✓ Playwright 安装成功！')
            print(f'✓ 浏览器正常工作')
            print(f'✓ 测试页面标题: {title}')
            browser.close()
        return True
    except Exception as e:
        print(f'✗ Playwright 测试失败: {e}')
        print('\n请确保已正确安装 Playwright 浏览器：')
        print('  playwright install chromium')
        print('\n如果遇到 SSL 错误，请查看 PLAYWRIGHT_INSTALL.md')
        return False

if __name__ == '__main__':
    success = test_playwright()
    exit(0 if success else 1)
