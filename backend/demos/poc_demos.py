import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.ai_agents.poc_system.dynamic_engine import dynamic_engine
from backend.ai_agents.poc_system.poc_manager import poc_manager
from backend.models import POCVerificationResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("POC_Demos")

async def run_demos():
    print("="*50)
    print("Running POC Verification Demos")
    print("="*50)
    
    # Mock the execution engine to avoid real network requests
    # We want to verify that the flow works (Match -> Generate -> Execute -> Score)
    dynamic_engine.execution_engine.execute_verification_task = AsyncMock(return_value=POCVerificationResult(
        task_id="demo-task",
        vulnerable=True,
        output="[+] Vulnerability found!",
        error=None,
        execution_time=0.5
    ))

    # Scenario 1: Heartbleed (Matching Existing POC)
    # We simulate that a Heartbleed POC exists in the system
    print("\n[Scenario 1] Heartbleed - OpenSSL Information Disclosure")
    print("-" * 30)
    
    # Manually register a dummy POC for Heartbleed to simulate it being found in Seebug/Cache
    # We need to ensure the matcher finds it. The matcher uses poc_manager.sync_from_seebug
    # So we mock sync_from_seebug to return our dummy POC.
    
    from backend.ai_agents.poc_system.poc_manager import POCMetadata
    heartbleed_poc = POCMetadata(
        poc_name="OpenSSL Heartbleed",
        poc_id="SSVID-2014-0160",
        source="seebug",
        description="Heartbleed POC",
        tags=["heartbleed", "cve-2014-0160"]
    )
    
    # Mock the matcher's dependency on poc_manager
    # We'll just insert it into the registry and cache so matcher finds it if it looks there
    poc_manager.poc_registry["SSVID-2014-0160"] = heartbleed_poc
    
    # But matcher calls `match_pocs`. Let's see how matcher works.
    # It calls `poc_manager.sync_from_seebug(keyword=...)`.
    # We'll mock that.
    poc_manager.sync_from_seebug = AsyncMock(return_value=[heartbleed_poc])
    
    vuln_info_heartbleed = {
        "title": "OpenSSL Heartbleed Vulnerability",
        "description": "The Heartbleed bug allows anyone on the Internet to read the memory of the systems protected by the vulnerable versions of the OpenSSL software.",
        "severity": "Critical",
        "cve_id": "CVE-2014-0160",
        "url": "https://example.com"
    }
    
    result = await dynamic_engine.verify_vulnerability("https://example.com", vuln_info_heartbleed)
    print(f"Result: {result['status']}")
    print(f"Source: {result['poc_source']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Selected POC: {result['poc_id']}")

    # Scenario 2: WebLogic (Dynamic Generation from Path/Keyword)
    print("\n[Scenario 2] WebLogic - XMLDecoder RCE")
    print("-" * 30)
    
    # Reset matcher mock to return nothing so we trigger generation
    poc_manager.sync_from_seebug = AsyncMock(return_value=[])
    
    vuln_info_weblogic = {
        "title": "WebLogic XMLDecoder RCE",
        "description": "Vulnerability in WebLogic Server component of Oracle Fusion Middleware. Supported versions that are affected are 10.3.6.0.0, 12.1.3.0.0, 12.2.1.1.0 and 12.2.1.2.0.",
        "severity": "Critical",
        "url": "http://example.com/wls-wsat/CoordinatorPortType",
        "post_data": "<soapenv:Envelope>...</soapenv:Envelope>",
        "keyword": "weblogic",
        "service": "WebLogic",
        "vuln_type": "RCE"
    }
    
    result = await dynamic_engine.verify_vulnerability("http://example.com", vuln_info_weblogic)
    print(f"Result: {result['status']}")
    print(f"Source: {result['poc_source']}")
    if result['poc_source'] == 'generated':
        print("Generated POC logic successfully.")
        # We can check the generated code if we want
        poc_id = result['poc_id']
        code = await poc_manager.get_poc_code(poc_id)
        if code:
             print(f"Generated Code Snippet: {code[:100].replace(chr(10), ' ')}...")

    # Scenario 3: ThinkPHP (Dynamic Generation from URL)
    print("\n[Scenario 3] ThinkPHP - RCE via URL Manipulation")
    print("-" * 30)
    
    vuln_info_thinkphp = {
        "title": "ThinkPHP 5.x Remote Code Execution",
        "description": "ThinkPHP 5.x has a remote code execution vulnerability due to insufficient parameter filtering.",
        "severity": "High",
        "url": "http://example.com/index.php?s=index/think\\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=whoami",
        "keyword": "root", # Expected keyword in response
        "service": "ThinkPHP"
    }
    
    result = await dynamic_engine.verify_vulnerability("http://example.com", vuln_info_thinkphp)
    print(f"Result: {result['status']}")
    print(f"Source: {result['poc_source']}")
    if result['poc_source'] == 'generated':
         print("Generated POC logic successfully from URL.")
         poc_id = result['poc_id']
         code = await poc_manager.get_poc_code(poc_id)
         if code:
             # Check if URL params were preserved
             if "invokefunction" in code:
                 print("Confirmed: URL parameters preserved in POC.")

if __name__ == "__main__":
    asyncio.run(run_demos())
