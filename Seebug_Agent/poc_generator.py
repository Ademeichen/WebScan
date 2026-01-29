from openai import OpenAI
import time

class POCGenerator:
    """
    POC Intelligent Agent Generator
    Uses ModelScope's GLM-4.7-Flash model to generate Pocsuite3 compatible POC scripts
    """
    
    # ModelScope Configuration
    BASE_URL = 'https://api-inference.modelscope.cn/v1'
    # API Key provided by user
    API_KEY = 'ms-5c9c1aaf-f843-4648-8e24-8e0a9e4f2118'
    MODEL_ID = 'ZhipuAI/GLM-4.7-Flash'

    def __init__(self):
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.API_KEY,
        )

    def generate_poc(self, vul_info: dict) -> str:
        """
        Generate POC script based on vulnerability information
        :param vul_info: Dictionary containing vulnerability details (name, description, etc.)
        :return: Generated Python code string
        """
        
        # Construct the prompt
        system_prompt = """You are a senior security researcher and POC developer. 
Your task is to write a high-quality, executable POC (Proof of Concept) script based on the provided vulnerability information.
The POC MUST be written using the **Pocsuite3** framework.

**Pocsuite3 POC Structure Requirements:**
1. Must import necessary modules: `from pocsuite3.api import Output, POCBase, register_poc, requests, logger`
2. Define a class inheriting from `POCBase`.
3. Include required metadata fields: `vulID`, `version`, `author`, `vulDate`, `createDate`, `updateDate`, `references`, `name`, `appPowerLink`, `appName`, `appVersion`, `vulType`, `desc`, `samples`, `install_requires`.
4. Implement `_verify(self)` method for vulnerability verification (non-destructive).
5. Implement `_attack(self)` method (can call `_verify` if attack is same as verify).
6. Implement `parse_output(self, result)` to handle results.
7. Use `register_poc(YourClass)` at the end.
8. Use `requests` (from pocsuite3.api) for HTTP requests.
9. Handle exceptions gracefully.

**Input Vulnerability Info:**
"""
        
        user_content = f"""
Vulnerability Name: {vul_info.get('name', 'Unknown')}
Vulnerability Type: {vul_info.get('type', 'Unknown')}
Description: {vul_info.get('description', 'No description provided.')}
Affected Component: {vul_info.get('component', 'Unknown')}
Resolution/Fix: {vul_info.get('solution', 'Unknown')}

Please generate a complete Python POC script for this vulnerability. 
If specific payload details are missing in the description, infer a standard safe check based on the vulnerability type (e.g., for SQLi use a time-based check or simple boolean check; for RCE try `whoami` or `id`).
Output ONLY the code, inside a python code block.
"""

        print(f"🤖 Generating POC for: {vul_info.get('name')}...")
        
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL_ID,
                    messages=[
                        {
                            'role': 'system',
                            'content': system_prompt
                        },
                        {
                            'role': 'user',
                            'content': user_content
                        }
                    ],
                    stream=True 
                )

                full_content = ""
                print("⏳ Receiving generated code...", end="", flush=True)
                
                for chunk in response:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                
                print("\n✅ Generation complete.")
                
                # Extract code from markdown blocks if present
                if "```python" in full_content:
                    code = full_content.split("```python")[1].split("```")[0].strip()
                elif "```" in full_content:
                    code = full_content.split("```")[1].split("```")[0].strip()
                else:
                    code = full_content.strip()
                    
                return code

            except Exception as e:
                error_msg = str(e)
                print(f"\n⚠️ Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
                if "429" in error_msg and attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"⏳ Rate limited. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # Retry on other errors too, but maybe with less aggressive backoff or same
                    wait_time = 2
                    print(f"⏳ Error occurred. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ AI Generation failed after {max_retries} attempts.")
                    return ""
        return ""

if __name__ == "__main__":
    # Test
    generator = POCGenerator()
    test_info = {
        "name": "Test Vulnerability",
        "type": "SQL Injection",
        "description": "A SQL injection vulnerability exists in the login page parameter 'id'.",
        "component": "TestApp",
        "solution": "Filter inputs"
    }
    code = generator.generate_poc(test_info)
    print(code)
