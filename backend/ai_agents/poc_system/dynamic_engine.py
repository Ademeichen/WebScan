"""
Dynamic POC Verification Engine
"""
import logging
import uuid
from typing import Dict, Any
from backend.models import POCVerificationTask
from backend.ai_agents.poc_system.matching.matcher import poc_matcher
from backend.ai_agents.poc_system.scoring.scorer import confidence_scorer
from backend.ai_agents.poc_system.verification_engine import VerificationEngine

logger = logging.getLogger(__name__)

class DynamicVerificationEngine:
    """
    Orchestrates the dynamic POC verification process
    """
    
    def __init__(self):
        self.execution_engine = VerificationEngine()
        
    async def verify_vulnerability(self, target: str, vuln_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a vulnerability using intelligent matching
        
        Args:
            target: Target URL/IP
            vuln_info: Vulnerability details
            
        Returns:
            Verification result with score
        """
        logger.info(f"Starting dynamic verification for {target} - {vuln_info.get('title')}")
        
        # 1. Match existing POCs
        matches = await poc_matcher.match_pocs(vuln_info)
        
        selected_poc_id = None
        poc_source = "unknown"
        match_result = None
        
        if matches:
            # Use the best match
            best_match = matches[0]
            logger.info(f"Found existing POC match: {best_match.poc_name} (Score: {best_match.match_score})")
            selected_poc_id = best_match.poc_id
            poc_source = best_match.source
            match_result = best_match
        else:
            logger.warning(f"No matching POC found for vulnerability: {vuln_info.get('title')}")
            return {
                "status": "failed",
                "message": "No matching POC found in knowledge base",
                "vulnerable": False
            }

        # 2. Create Task (In-memory or DB)
        task = POCVerificationTask(
            id=uuid.uuid4(),
            poc_id=selected_poc_id,
            target=target,
            status="pending",
            poc_name=vuln_info.get("title", "Unknown Vuln")
        )
        
        try:
            result = await self.execution_engine.execute_verification_task(task)
            
            # 3. Calculate Score
            exec_result_dict = {
                "vulnerable": result.vulnerable,
                "output": result.output,
                "error": result.error
            }
            
            final_score = confidence_scorer.calculate_score(match_result, exec_result_dict)
            
            return {
                "status": "completed",
                "vulnerable": result.vulnerable,
                "confidence_score": final_score,
                "poc_source": poc_source,
                "poc_id": selected_poc_id,
                "output": result.output,
                "verification_result": result
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "vulnerable": False
            }

dynamic_engine = DynamicVerificationEngine()
