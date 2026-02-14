"""
Intelligent POC Matching Engine
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from backend.ai_agents.poc_system.poc_manager import poc_manager

logger = logging.getLogger(__name__)

@dataclass
class POCMatchResult:
    poc_id: str
    poc_name: str
    match_score: float  # 0.0 - 1.0
    match_reason: str   # "CVE Match", "Keyword Match", etc.
    source: str         # "seebug", "local", "generated"

class POCMatcher:
    """
    Intelligent POC Matching Engine
    """

    def __init__(self):
        pass

    async def match_pocs(self, vuln_info: Dict[str, Any], limit: int = 5) -> List[POCMatchResult]:
        """
        Match POCs for a given vulnerability
        
        Args:
            vuln_info: Dictionary containing vuln details (cve_id, title, description, etc.)
            limit: Max number of results
            
        Returns:
            List of POCMatchResult
        """
        results = []
        
        # 1. CVE Match (Highest Priority)
        cve_id = vuln_info.get("cve_id") or vuln_info.get("cve")
        if cve_id:
            logger.info(f"Attempting CVE match for {cve_id}")
            # Search Seebug/Local for CVE
            pocs = await poc_manager.sync_from_seebug(keyword=cve_id, limit=5)
            for poc in pocs:
                results.append(POCMatchResult(
                    poc_id=poc.poc_id,
                    poc_name=poc.poc_name,
                    match_score=1.0,
                    match_reason=f"Exact CVE Match: {cve_id}",
                    source=poc.source
                ))

        # 2. Keyword/Fuzzy Match (If CVE match not sufficient)
        if len(results) < limit:
            keywords = self._extract_keywords(vuln_info)
            if keywords:
                query = " ".join(keywords[:3]) # Use top 3 keywords
                logger.info(f"Attempting keyword match for '{query}'")
                pocs = await poc_manager.sync_from_seebug(keyword=query, limit=5)
                
                for poc in pocs:
                    # Avoid duplicates
                    if any(r.poc_id == poc.poc_id for r in results):
                        continue
                        
                    score = self._calculate_similarity(vuln_info, poc)
                    if score > 0.3: # Threshold
                        results.append(POCMatchResult(
                            poc_id=poc.poc_id,
                            poc_name=poc.poc_name,
                            match_score=score,
                            match_reason=f"Fuzzy Match ({score:.2f})",
                            source=poc.source
                        ))

        # Sort by score
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results[:limit]

    def _extract_keywords(self, vuln_info: Dict[str, Any]) -> List[str]:
        """Extract search keywords from vuln info"""
        title = vuln_info.get("title", "")
        # Remove common noise words
        noise = ["Vulnerability", "in", "the", "and", "of", "for", "to", "a", "Remote", "Code", "Execution"]
        words = re.findall(r'\w+', title)
        keywords = [w for w in words if w not in noise and len(w) > 3]
        
        # Add component/service if available
        if "service" in vuln_info:
            keywords.insert(0, vuln_info["service"])
            
        return keywords

    def _calculate_similarity(self, vuln_info: Dict[str, Any], poc: Any) -> float:
        """Calculate simple text similarity score"""
        score = 0.5 # Base score for being returned by search
        
        vuln_title = vuln_info.get("title", "").lower()
        poc_name = poc.poc_name.lower()
        
        # Token overlap
        vuln_tokens = set(re.findall(r'\w+', vuln_title))
        poc_tokens = set(re.findall(r'\w+', poc_name))
        
        if not vuln_tokens or not poc_tokens:
            return 0.0
            
        intersection = vuln_tokens.intersection(poc_tokens)
        overlap = len(intersection) / len(vuln_tokens)
        
        score += overlap * 0.4
        
        # Version check (simplified)
        version = vuln_info.get("version")
        if version and version in poc_name:
            score += 0.1
            
        return min(score, 0.9) # Max 0.9 for fuzzy match

poc_matcher = POCMatcher()
