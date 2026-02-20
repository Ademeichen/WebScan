import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Tortoise ORM models before importing modules that use them
sys.modules['backend.models'] = MagicMock()
mock_models = sys.modules['backend.models']
mock_models.POCVerificationTask = MagicMock()
mock_models.POCVerificationResult = MagicMock()
mock_models.POCExecutionLog = MagicMock()
mock_models.POCExecutionLog.create = MagicMock(return_value=asyncio.Future())
mock_models.POCExecutionLog.create.return_value.set_result(None)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Demo")

async def run_demo():
    print("\n" + "="*80)
    print("🚀 STARTING DYNAMIC POC VERIFICATION FRAMEWORK DEMO")
    print("="*80 + "\n")

    # Import after mocking
    from backend.ai_agents.poc_system.dynamic_engine import dynamic_engine
    from backend.ai_agents.poc_system.poc_manager import poc_manager, POCMetadata
    from backend.Pocsuite3Agent.agent import POCResult

    # --- Setup Mocks ---
    
    # 1. Mock Seebug Sync (Simulate existing POCs in DB)
    async def mock_sync(*args, **kwargs):
        keyword = kwargs.get('keyword', '')
        if 'CVE-2014-0160' in keyword: # Heartbleed
            return [POCMetadata(
                poc_name="Heartbleed OpenSSL Extension",
                poc_id="ssvid-12345",
                # cve="CVE-2014-0160",  <-- Removed
                description="Heartbleed vulnerability in OpenSSL (CVE-2014-0160)",
                source="seebug"
            )]
        elif 'WebLogic' in keyword: # WebLogic
            return [POCMetadata(
                poc_name="Oracle WebLogic WLS-WSAT RCE",
                poc_id="ssvid-67890",
                description="Remote Code Execution in WebLogic WLS-WSAT",
                source="local"
            )]
        return []
    
    poc_manager.sync_from_seebug = mock_sync

    # 2. Mock Execution Engine (Simulate network scan results)
    async def mock_execute(config):
        # Create result with required fields
        result = POCResult(
            poc_name=str(config.poc_id),
            target=config.target,
            vulnerable=True,
            message="",
            output=""
        )
        result.execution_time = 0.5
        
        # Check logic based on what was passed
        if "Heartbleed" in config.poc_code or "Heartbleed" in str(config.poc_id):
            result.message = "Server returned heartbeat response with memory leak"
            result.output = "HEARTBEAT_RESPONSE... user:password ..."
        elif "WebLogic" in config.poc_code or "WebLogic" in str(config.poc_id):
             result.message = "Command executed successfully"
             result.output = "uid=0(root) gid=0(root)"
        elif "ThinkPHP" in config.poc_code or "Dynamic" in str(config.poc_id):
             result.message = "Keyword found in response"
             result.output = "PHP Version 7.x ... root:x:0:0:..."
        else:
            result.vulnerable = False
            
        return result

    # Patch the _execute_poc_with_retry method
    dynamic_engine.execution_engine._execute_poc_with_retry = mock_execute
    
    # Mock get_poc_code to return dummy code
    async def mock_get_poc_code(poc_id):
        if "ssvid-12345" in str(poc_id):
            return "def verify(url): return 'Heartbleed' in url" # Dummy code
        elif "ssvid-67890" in str(poc_id):
            return "def verify(url): return 'WebLogic' in url"
        return "def verify(url): return True"
        
    poc_manager.get_poc_code = mock_get_poc_code
    
    # Patch Task.save
    def mock_task_constructor(**kwargs):
        m = MagicMock()
        for k, v in kwargs.items():
            setattr(m, k, v)
        m.save = MagicMock(return_value=asyncio.Future())
        m.save.return_value.set_result(None)
        return m

    mock_models.POCVerificationTask.side_effect = mock_task_constructor
    
    mock_result = MagicMock()
    mock_models.POCVerificationResult.create = MagicMock(return_value=asyncio.Future())
    mock_models.POCVerificationResult.create.return_value.set_result(mock_result)

    # --- Scenario 1: Heartbleed (Perfect Match) ---
    print("\n🔸 Scenario 1: Heartbleed (Full Database Match)")
    print("-" * 50)
    vuln_info_1 = {
        "title": "OpenSSL Heartbleed Vulnerability",
        "cve_id": "CVE-2014-0160",
        "service": "openssl",
        "version": "1.0.1f",
        "description": "The TLS implementation in OpenSSL..."
    }
    
    result_1 = await dynamic_engine.verify_vulnerability("https://example.com", vuln_info_1)
    print(f"   MATCH STRATEGY: {result_1['poc_source'].upper()}")
    print(f"   POC ID:         {result_1['poc_id']}")
    print(f"   CONFIDENCE:     {result_1['confidence_score']}/100")
    print(f"   RESULT:         {'VULNERABLE' if result_1['vulnerable'] else 'SAFE'}")

    # --- Scenario 2: WebLogic (Partial/Fuzzy Match) ---
    print("\n🔸 Scenario 2: WebLogic Deserialization (Partial Field Match)")
    print("-" * 50)
    vuln_info_2 = {
        "title": "Oracle WebLogic Server Remote Command Execution",
        "cve_id": None, # Missing CVE
        "service": "weblogic",
        "version": "10.3.6.0",
        "description": "Vulnerability in the WLS-WSAT component of Oracle WebLogic Server."
    }
    
    result_2 = await dynamic_engine.verify_vulnerability("https://example.com:7001", vuln_info_2)
    print(f"   MATCH STRATEGY: {result_2['poc_source'].upper()}")
    print(f"   POC ID:         {result_2['poc_id']}")
    print(f"   CONFIDENCE:     {result_2['confidence_score']}/100")
    print(f"   RESULT:         {'VULNERABLE' if result_2['vulnerable'] else 'SAFE'}")

    # --- Scenario 3: ThinkPHP (No Match - Dynamic Generation) ---
    print("\n🔸 Scenario 3: ThinkPHP RCE (No Database Record - Dynamic Gen)")
    print("-" * 50)
    vuln_info_3 = {
        "title": "ThinkPHP 5.x Remote Code Execution",
        "cve_id": None,
        "service": "thinkphp",
        "version": "5.0.23",
        "description": "Remote code execution via invokable function",
        "vuln_type": "RCE",
        "path": "/index.php?s=index/think\\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id",
        "keyword": "uid="
    }
    
    result_3 = await dynamic_engine.verify_vulnerability("https://example.com/tp5", vuln_info_3)
    print(f"   MATCH STRATEGY: {result_3['poc_source'].upper()}")
    print(f"   POC ID:         {result_3['poc_id']}")
    print(f"   CONFIDENCE:     {result_3['confidence_score']}/100")
    print(f"   RESULT:         {'VULNERABLE' if result_3['vulnerable'] else 'SAFE'}")

    print("\n" + "="*80)
    print("✅ DEMO COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
