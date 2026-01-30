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
            
        # 2. Pattern Matching (Future V2)
        # patterns = self._find_similar_claims(keywords)
        # if patterns: context_parts.append(patterns)
        
        full_context = "\n\n".join(context_parts) if context_parts else "No prior knowledge found in the graph."
        
        return {
            "full_text": full_context,
            "source_history": source_history
        }

    def _get_source_history(self, domain: str) -> str:
        """
        Query the graph for all previous evaluations of this domain.
        """
        if not domain:
            return ""
            
        # We reuse the specific query logic but tailored for retrieval
        query = """
        PREFIX cred: <http://www.dic9335.uqam.ca/ontologies/credibility-verification#>
        
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
