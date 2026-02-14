import sys
import os
import socket
import requests
from urllib.parse import urlparse

# Hardcoded from .env for diagnostic purposes
AWVS_API_URL = "https://127.0.0.1:3443"
AWVS_API_KEY = "1986ad8c0a5b3df4d7028d5f3c06e936c74deac5b05e4406bb3630cb247b0d2d3"

def run_diagnostics():
    print("=== Starting AWVS Diagnostic Tool (Standalone) ===")
    
    url = AWVS_API_URL
    api_key = AWVS_API_KEY
    
    print(f"Target URL: {url}")
    print(f"API Key: {'*' * max(0, len(api_key)-4)}{api_key[-4:] if api_key else ''}")
    
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    
    print(f"\n--- Layer 1: DNS Resolution ---")
    ip = None
    try:
        ip = socket.gethostbyname(hostname)
        print(f"[PASS] DNS Resolution: {hostname} -> {ip}")
    except Exception as e:
        print(f"[FAIL] DNS Resolution: {hostname} - {e}")
        if hostname == 'localhost':
            ip = '127.0.0.1'
            print(f"[INFO] Using fallback IP for localhost: {ip}")

    if ip:
        print(f"\n--- Layer 2: TCP Connectivity ---")
        try:
            sock = socket.create_connection((ip, port), timeout=5)
            print(f"[PASS] TCP Connection: {ip}:{port} connected successfully")
            sock.close()
        except Exception as e:
            print(f"[FAIL] TCP Connection: {ip}:{port} - {e}")
    
    print(f"\n--- Layer 3 & 4: HTTP/Auth Check ---")
    headers = {"X-Auth": api_key, "Content-Type": "application/json"}
    try:
        requests.packages.urllib3.disable_warnings()
        print(f"Sending GET request to {url}/api/v1/me")
        # Added print to confirm execution flow
        sys.stdout.flush()
        
        resp = requests.get(f"{url}/api/v1/me", headers=headers, verify=False, timeout=10)
        print(f"[INFO] HTTP Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"[PASS] API Authentication Successful")
            try:
                data = resp.json()
                print(f"[INFO] User Info: {data.get('email', 'unknown')}")
            except:
                pass
        else:
            print(f"[FAIL] Auth Failed or Unexpected. Code: {resp.status_code}")
            print(f"[INFO] Body: {resp.text[:200]}")
            
    except Exception as e:
        print(f"[FAIL] HTTP Request Exception: {e}")

if __name__ == "__main__":
    run_diagnostics()
