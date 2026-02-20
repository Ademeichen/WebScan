"""
POC Confidence Scoring System
"""
from typing import Dict, Any

class ConfidenceScorer:
    """
    Calculates confidence scores for POC verification results
    """
    
    @staticmethod
    def calculate_score(match_result: Any, execution_result: Dict[str, Any]) -> float:
        """
        Calculate final confidence score (0-100)
        
        Args:
            match_result: Result from POCMatcher (has initial match_score)
            execution_result: Result from execution engine (vulnerable, output, etc.)
        """
        base_score = 0.0
        
        # 1. Start with match quality
        # match_score is 0.0-1.0
        if hasattr(match_result, 'match_score'):
            base_score = match_result.match_score * 50  # Max 50 points from matching
        else:
            base_score = 50.0 # Default if no match info
            
        # 2. Add points for execution success
        if execution_result.get("vulnerable"):
            base_score += 40
            
            # Bonus for strong evidence
            output = execution_result.get("output", "")
            if "uid=0(root)" in output or "nt authority" in output.lower():
                base_score += 10 # High certainty evidence
            elif "syntax error" in output.lower():
                base_score += 5  # Medium certainty
        else:
            # Penalty for failure, but keep some score if match was high (false negative potential)
            base_score -= 20
            
        # Clamp 0-100
        return max(0.0, min(100.0, base_score))

confidence_scorer = ConfidenceScorer()
