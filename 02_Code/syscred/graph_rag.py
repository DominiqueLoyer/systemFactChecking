# -*- coding: utf-8 -*-
"""
GraphRAG Module - SysCRED
=========================
Retrieves context from the Knowledge Graph to enhance verification.
Transforms "Passive" Graph into "Active" Context.

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

from typing import List, Dict, Any, Optional
from syscred.ontology_manager import OntologyManager

class GraphRAG:
    """
    Retrieval Augmented Generation using the Semantic Knowledge Graph.
    """
    
    def __init__(self, ontology_manager: OntologyManager):
        self.om = ontology_manager
        
    def get_context(self, domain: str, keywords: List[str] = []) -> Dict[str, str]:
        """
        Retrieve context for a specific verification task.
        
        Args:
            domain: The domain being analyzed (e.g., 'lemonde.fr')
            keywords: List of keywords from the claim (not yet used in V1)
            
        Returns:
            Dictionary with natural language context strings.
        """
        if not self.om:
            return {"graph_context": "No ontology manager available."}
            
        context_parts = []
        
        # 1. Source History
        source_history = self._get_source_history(domain)
        if source_history:
            context_parts.append(source_history)
            
        # 2. Pattern Matching (Similar Claims)
        similar_uris = []
        if keywords:
            similar_result = self._find_similar_claims(keywords)
            if similar_result["text"]:
                context_parts.append(similar_result["text"])
                similar_uris = similar_result["uris"]
        
        full_context = "\n\n".join(context_parts) if context_parts else "No prior knowledge found in the graph."
        
        return {
            "full_text": full_context,
            "source_history": source_history,
            "similar_uris": similar_uris  # [NEW] Return URIs for linking
        }

    def _get_source_history(self, domain: str) -> str:
        """
        Query the graph for all previous evaluations of this domain.
        """
        if not domain:
            return ""
            
        # We reuse the specific query logic but tailored for retrieval
        query = """
        PREFIX cred: <https://github.com/DominiqueLoyer/systemFactChecking#>
        
        SELECT ?score ?level ?timestamp
        WHERE {
            ?info cred:informationURL ?url .
            ?request cred:concernsInformation ?info .
            ?report cred:isReportOf ?request .
            ?report cred:credibilityScoreValue ?score .
            ?report cred:assignsCredibilityLevel ?level .
            ?report cred:completionTimestamp ?timestamp .
            FILTER(CONTAINS(STR(?url), "%s"))
        }
        ORDER BY DESC(?timestamp)
        LIMIT 5
        """ % domain
        
        results = []
        try:
            combined = self.om.base_graph + self.om.data_graph
            for row in combined.query(query):
                results.append({
                    "score": float(row.score),
                    "level": str(row.level).split('#')[-1],
                    "date": str(row.timestamp).split('T')[0]
                })
        except Exception as e:
            print(f"[GraphRAG] Query error: {e}")
            return ""
            
        if not results:
            return f"The graph contains no previous evaluations for {domain}."
            
        # Summarize
        count = len(results)
        avg_score = sum(r['score'] for r in results) / count
        last_verdict = results[0]['level']
        
        summary = (
            f"Graph Memory for '{domain}':\n"
            f"- Analyzed {count} times previously.\n"
            f"- Average Credibility Score: {avg_score:.2f} / 1.0\n"
            f"- Most recent verdict ({results[0]['date']}): {last_verdict}.\n"
        )
        
        return summary

    def _find_similar_claims(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Find evaluation history for content containing specific keywords.
        Returns dict with 'text' (for LLM) and 'uris' (for Graph linking).
        """
        if not keywords:
            return {"text": "", "uris": []}
            
        # Build REGEX filter for keywords (OR logic)
        # e.g., (fake|hoax|conspiracy)
        clean_kws = [k for k in keywords if len(k) > 3] # Skip short words
        if not clean_kws:
            return {"text": "", "uris": []}
            
        regex_pattern = "|".join(clean_kws)
        
        query = """
        PREFIX cred: <https://github.com/DominiqueLoyer/systemFactChecking#>
        
        SELECT ?report ?content ?score ?level ?timestamp
        WHERE {
            ?info cred:informationContent ?content .
            ?request cred:concernsInformation ?info .
            ?report cred:isReportOf ?request .
            ?report cred:credibilityScoreValue ?score .
            ?report cred:assignsCredibilityLevel ?level .
            ?report cred:completionTimestamp ?timestamp .
            FILTER(REGEX(?content, "%s", "i"))
        }
        ORDER BY DESC(?timestamp)
        LIMIT 3
        """ % regex_pattern
        
        results = []
        try:
            combined = self.om.base_graph + self.om.data_graph
            for row in combined.query(query):
                results.append({
                    "uri": str(row.report),
                    "content": str(row.content)[:100] + "...",
                    "score": float(row.score),
                    "verdict": str(row.level).split('#')[-1]
                })
        except Exception as e:
            print(f"[GraphRAG] Similar claims error: {e}")
            return {"text": "", "uris": []}
            
        if not results:
            return {"text": "", "uris": []}
            
        lines = [f"Found {len(results)} similar claims in history:"]
        for r in results:
            lines.append(f"- \"{r['content']}\" ({r['verdict']}, Score: {r['score']:.2f})")
            
        return {
            "text": "\n".join(lines),
            "uris": [r['uri'] for r in results]
        }
