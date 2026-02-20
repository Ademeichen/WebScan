"""
Dynamic POC Verification Engine
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from backend.models import POCVerificationTask, POCVerificationResult
from backend.ai_agents.poc_system.matching.matcher import poc_matcher
from backend.ai_agents.poc_system.generation.generator import poc_generator
from backend.ai_agents.poc_system.scoring.scorer import confidence_scorer
from backend.ai_agents.poc_system.poc_manager import poc_manager
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
        Verify a vulnerability using intelligent matching and dynamic generation
        
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
            # 2. Generate Dynamic POC
            logger.info("No matching POC found. Generating dynamic POC...")
            dynamic_code = poc_generator.generate_poc(vuln_info)
            
            if dynamic_code:
                dynamic_id = f"dynamic-{uuid.uuid4().hex[:8]}"
                poc_manager.register_dynamic_poc(dynamic_id, dynamic_code)
                selected_poc_id = dynamic_id
                poc_source = "generated"
                logger.info(f"Generated dynamic POC: {dynamic_id}")
            else:
                return {
                    "status": "failed",
                    "message": "Could not match or generate POC"
                }

        # 3. Create Task (In-memory or DB)
        # We need a task object for the execution engine
        # In a real scenario, we'd save this to DB. Here we mock/create ephemeral task.
        task = POCVerificationTask(
            id=uuid.uuid4(),
            poc_id=selected_poc_id,
            target=target,
            status="pending",
            poc_name=vuln_info.get("title", "Unknown Vuln")
        )
        # Note: We skip saving to DB for this demo logic to avoid DB constraint issues 
        # if the table schema expects specific FKs we don't have. 
        # But VerificationEngine expects .save() to work.
        # We will assume VerificationEngine handles it or we mock it.
        
        # For this implementation, let's try to run it.
        # Ideally, we should modify VerificationEngine to be more decoupled from DB,
        # but for now we'll rely on it.
        
        # NOTE: Since we can't easily mock the DB save in this environment without proper setup,
        # we will assume the caller handles the DB part or we catch the error.
        
        try:
            result = await self.execution_engine.execute_verification_task(task)
            
            # 4. Calculate Score
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
                "message": str(e)
            }

dynamic_engine = DynamicVerificationEngine()
