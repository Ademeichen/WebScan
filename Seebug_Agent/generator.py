"""
POC生成器

使用AI模型生成Pocsuite3兼容的POC脚本。
"""
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from config import Config


class POCGenerator:
    """
    POC智能生成器
    
    使用ModelScope的GLM-4.7-Flash模型生成Pocsuite3兼容的POC脚本。
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化POC生成器
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or Config()
        self.client = OpenAI(
            base_url=self.config.AI_BASE_URL,
            api_key=self.config.AI_API_KEY,
        )

    def generate_poc(self, vul_info: Dict[str, Any]) -> str:
        """
        生成POC脚本
        
        Args:
            vul_info: 漏洞信息字典
            
        Returns:
            生成的Python代码字符串
        """
        system_prompt = """You are a senior security researcher and POC developer. 
Your task is to write a high-quality, executable POC (Proof of Concept) script based on provided vulnerability information.
The POC MUST be written using **Pocsuite3** framework.

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
If specific payload details are missing in the description, infer a standard safe check based on vulnerability type (e.g., for SQLi use a time-based check or simple boolean check; for RCE try `whoami` or `id`).
Output ONLY the code, inside a python code block.
"""

        max_retries = self.config.MAX_RETRIES
        base_delay = self.config.BASE_DELAY
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.AI_MODEL_ID,
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
                
                for chunk in response:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                
                if "```python" in full_content:
                    code = full_content.split("```python")[1].split("```")[0].strip()
                elif "```" in full_content:
                    code = full_content.split("```")[1].split("```")[0].strip()
                else:
                    code = full_content.strip()
                    
                return code

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    wait_time = 2
                    time.sleep(wait_time)
                else:
                    return ""
        return ""
