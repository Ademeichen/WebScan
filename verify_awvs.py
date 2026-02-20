
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from backend.config import settings
from backend.AVWS.API.Target import Target
from backend.AVWS.API.Scan import Scan

async def verify_awvs():
    print(f"Checking AWVS Connection to {settings.AWVS_API_URL}...")
    
    target_client = Target(settings.AWVS_API_URL, settings.AWVS_API_KEY)
    scan_client = Scan(settings.AWVS_API_URL, settings.AWVS_API_KEY)
    
    # 1. Test List Targets (Connection Check)
    print("\n1. Testing List Targets...")
    try:
        targets = target_client.get_all()
        if targets is not None:
            print(f"Success! Found {len(targets)} targets.")
        else:
            print("Failed to get targets (returned None).")
            return
    except Exception as e:
        print(f"Exception listing targets: {e}")
        return

    # 2. Test Add Target
    print("\n2. Testing Add Target...")
    test_target_url = "http://testphp.vulnweb.com"
    test_desc = "Verification Script Test Target"
    target_id = None
    try:
        target_id = target_client.add(test_target_url, test_desc)
        if target_id:
            print(f"Success! Created target with ID: {target_id}")
        else:
            print("Failed to create target (returned None).")
            return
    except Exception as e:
        print(f"Exception adding target: {e}")
        return

    # 3. Test Add Scan
    print("\n3. Testing Add Scan...")
    try:
        # Use default profile (Full Scan)
        # Profile ID for Full Scan is usually 11111111-1111-1111-1111-111111111111
        # But Scan.add takes profile_id. Let's assume 'full_scan' is mapped or we need ID.
        # In task_executor it passes 'full_scan' or 'profile_id'.
        # Let's check Scan.add signature.
        # Scan.add(target_id, profile_id, ...)
        
        # We'll try with the Full Scan ID constant if we can find it, or just use a common one.
        full_scan_profile_id = "11111111-1111-1111-1111-111111111111" 
        
        scan_id = scan_client.add(target_id, full_scan_profile_id)
        if scan_id:
            print(f"Success! Created scan with ID: {scan_id}")
        else:
            print("Failed to create scan (returned None).")
    except Exception as e:
        print(f"Exception adding scan: {e}")

if __name__ == "__main__":
    asyncio.run(verify_awvs())
