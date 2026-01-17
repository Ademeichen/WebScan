import asyncio
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from models import Task

# Mock the AWVS API modules
sys.modules['AVWS.API.Scan'] = MagicMock()
sys.modules['AVWS.API.Target'] = MagicMock()
sys.modules['AVWS.API.Vuln'] = MagicMock()
sys.modules['AVWS.API.Dashboard'] = MagicMock()
sys.modules['AVWS.API.Base'] = MagicMock()

from api.awvs import sync_scans_from_awvs

async def run_test():
    print("Initializing DB...")
    await Tortoise.init(
        db_url='sqlite://:memory:',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()
    print("DB Initialized.")

    try:
        # Mock AWVS Scan.get_all
        mock_scan_instance = MagicMock()
        mock_scan_instance.get_all.return_value = [
            {
                'scan_id': 'scan_123',
                'target_id': 'target_123',
                'target': {'address': 'http://test.com'},
                'current_session': {'status': 'completed', 'progress': 100}
            }
        ]
        
        print("Testing Sync Logic...")
        with patch('api.awvs.Scan', return_value=mock_scan_instance):
            await sync_scans_from_awvs()
            
            # Check if task is created in DB
            tasks = await Task.all()
            if len(tasks) != 1:
                print(f"FAILED: Expected 1 task, got {len(tasks)}")
                return
            
            if tasks[0].target != 'http://test.com':
                print(f"FAILED: Expected target http://test.com, got {tasks[0].target}")
                return
                
            if tasks[0].status != 'completed':
                print(f"FAILED: Expected status completed, got {tasks[0].status}")
                return
            
            print("Initial sync passed.")
            
            # Mock update
            mock_scan_instance.get_all.return_value = [
                {
                    'scan_id': 'scan_123',
                    'target_id': 'target_123',
                    'target': {'address': 'http://test.com'},
                    'current_session': {'status': 'processing', 'progress': 50}
                }
            ]
            
            await sync_scans_from_awvs()
            
            task = await Task.get(target='http://test.com')
            if task.status != 'processing':
                print(f"FAILED: Expected status processing, got {task.status}")
                return
            
            if task.progress != 50:
                print(f"FAILED: Expected progress 50, got {task.progress}")
                return
                
            print("Update sync passed.")

    finally:
        await Tortoise.close_connections()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test())
