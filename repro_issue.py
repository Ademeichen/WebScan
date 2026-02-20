
from string import Template
import logging

# Mock logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_POC_TEMPLATE = Template("""
class TestPOC:
    desc = '''
    $description
    '''
    name = '$poc_name'
""")

def generate_poc(vuln_info):
    try:
        description = vuln_info.get("description", "")
        title = vuln_info.get("title", "Dynamic POC")
        
        # This will fail if description contains $ and we use substitute
        poc_code = BASE_POC_TEMPLATE.substitute(
            poc_name=title,
            description=description
        )
        return poc_code
    except Exception as e:
        print(f"EXCEPTION: {e}")
        logger.error(f"Failed to generate POC: {e}")
        return None

# Test case with None description
vuln_info = {
    "title": "Test Vuln",
    "description": None
}

result = generate_poc(vuln_info)
if result:
    print(f"Success: {result[:50]}...")
else:
    print("Failed")
