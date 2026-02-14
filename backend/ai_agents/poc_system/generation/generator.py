"""
Dynamic POC Generator
"""
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from backend.ai_agents.poc_system.generation.templates import BASE_POC_TEMPLATE, LOGIC_GET_KEYWORD, LOGIC_POST_KEYWORD

logger = logging.getLogger(__name__)

class AdaptivePOCGenerator:
    """
    Generates POC scripts based on vulnerability features
    """
    
    def generate_poc(self, vuln_info: Dict[str, Any]) -> Optional[str]:
        """
        Generate a python POC script
        """
        try:
            # Extract features with safety checks
            vuln_type = str(vuln_info.get("vuln_type") or "Unknown")
            description = str(vuln_info.get("description") or "")
            title = str(vuln_info.get("title") or "Dynamic POC")
            service = str(vuln_info.get("service") or "Unknown")
            version = str(vuln_info.get("version") or "Unknown")
            
            # Extract path from URL if not provided
            path = vuln_info.get("path")
            if not path and "url" in vuln_info:
                try:
                    parsed = urlparse(vuln_info["url"])
                    if parsed.path:
                        path = parsed.path
                        if parsed.query:
                            path += "?" + parsed.query
                except:
                    pass
            
            if not path:
                path = "/"
            
            # Determine logic
            verify_logic = ""
            
            # Keyword for verification
            keyword = vuln_info.get("keyword")
            if not keyword:
                # If no keyword provided, use a generic one based on context or default
                keyword = "<html" # Default to checking for HTML response
            
            status_code = vuln_info.get("status_code", 200)

            # Case 1: POST data provided
            if "post_data" in vuln_info:
                 verify_logic = LOGIC_POST_KEYWORD.format(
                    path=path,
                    data=vuln_info.get("post_data", ""),
                    headers=vuln_info.get("headers", {}),
                    status_code=status_code,
                    keyword=keyword
                 )
            # Case 2: GET (Default)
            else:
                verify_logic = LOGIC_GET_KEYWORD.format(
                    path=path,
                    status_code=status_code,
                    keyword=keyword
                )
                
            # Fill template
            # Use safe_substitute to avoid errors if description contains $ or other issues
            poc_code = BASE_POC_TEMPLATE.safe_substitute(
                poc_name=title,
                app_name=service,
                app_version=version,
                vuln_type=vuln_type,
                description=description,
                verify_logic=verify_logic
            )
            
            return poc_code
            
        except Exception as e:
            logger.error(f"Failed to generate POC: {e}", exc_info=True)
            return None

poc_generator = AdaptivePOCGenerator()
