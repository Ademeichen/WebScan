import requests

def test_seebug_search_scrape(keyword):
    url = "https://www.seebug.org/search/"
    params = {"keywords": keyword}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.seebug.org/"
    }
    
    print(f"Testing HTML scrape for: {url} with keyword: {keyword}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        if response.status_code == 200:
            # Find where 'ssvid' appears
            idx = response.text.find('ssvid')
            if idx != -1:
                print(f"Found 'ssvid' at index {idx}")
                print("--- Context around ssvid ---")
                # Print 500 chars before and 1000 after
                start = max(0, idx - 500)
                end = min(len(response.text), idx + 1000)
                print(response.text[start:end])
            else:
                print("'ssvid' not found in response.")
                print("--- First 1000 chars ---")
                print(response.text[:1000])
        else:
            print("❌ Request failed.")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_seebug_detail_scrape(ssvid):
    url = f"https://www.seebug.org/vuldb/ssvid-{ssvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    print(f"\nTesting Detail Scrape for: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            # Look for specific classes
            if 'class="md"' in response.text:
                print("Found class='md'")
                idx = response.text.find('class="md"')
                print(response.text[idx:idx+1000])
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    # test_seebug_search_scrape("thinkphp")
    test_seebug_detail_scrape("99617")
