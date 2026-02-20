import os
import requests
from pathlib import Path
import sys
import traceback

# Paths
BASE_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = BASE_DIR / 'backend'
DATABASE_DIR = BACKEND_DIR / 'database'
LOG_FILE = BASE_DIR / 'download.log'

# URLs
APPS_JSON_URL = "https://raw.githubusercontent.com/wappalyzer/wappalyzer/master/src/technologies.json"
GEOIP_ASN_URL = "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-ASN.mmdb"

def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg)

def download_file(url, dest_path):
    log(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log(f"Successfully downloaded {dest_path}")
        return True
    except Exception as e:
        log(f"Failed to download {url}: {e}")
        log(traceback.format_exc())
        return False

def main():
    try:
        if not DATABASE_DIR.exists():
            log(f"Creating directory {DATABASE_DIR}")
            DATABASE_DIR.mkdir(parents=True, exist_ok=True)

        success_apps = download_file(APPS_JSON_URL, DATABASE_DIR / 'apps.json')
        success_geo = download_file(GEOIP_ASN_URL, DATABASE_DIR / 'GeoLite2-ASN.mmdb')
        
        apps_txt = DATABASE_DIR / 'apps.txt'
        if not apps_txt.exists():
            apps_txt.touch()
            log(f"Created empty {apps_txt}")

        if success_apps and success_geo:
            log("All database files downloaded successfully!")
        else:
            log("Some downloads failed.")
            
    except Exception as e:
        log(f"Script failed: {e}")
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
