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
        
        # Escape domain to prevent SPARQL injection
        safe_domain = self._escape_sparql_string(domain)
            
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
        """ % safe_domain
        
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
            return {"text": "", "uris": [], "scores": []}
            
        # Build REGEX filter for keywords (OR logic)
        # e.g., (fake|hoax|conspiracy)
        clean_kws = [k for k in keywords if len(k) > 3] # Skip short words
        if not clean_kws:
            return {"text": "", "uris": [], "scores": []}
        
        # Escape each keyword for safe use in SPARQL REGEX
        safe_kws = [self._escape_sparql_string(k) for k in clean_kws]
        regex_pattern = "|".join(safe_kws)
        
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
            return {"text": "", "uris": [], "scores": []}
            
        if not results:
            return {"text": "", "uris": [], "scores": []}
            
        lines = [f"Found {len(results)} similar claims in history:"]
        for r in results:
            lines.append(f"- \"{r['content']}\" ({r['verdict']}, Score: {r['score']:.2f})")
            
        return {
            "text": "\n".join(lines),
            "uris": [r['uri'] for r in results],
            "scores": [r['score'] for r in results]
        }
    
    def compute_context_score(self, domain: str, keywords: List[str] = []) -> Dict[str, float]:
        """
        Compute numerical context scores for integration into credibility scoring.
        
        This transforms the GraphRAG context into actionable numerical scores
        that can be directly used in the calculate_overall_score() function.
        
        Args:
            domain: The domain being analyzed (e.g., 'lemonde.fr')
            keywords: List of keywords from the claim
            
        Returns:
            Dictionary with:
            - 'history_score': 0.0-1.0 based on past evaluations of this domain
            - 'pattern_score': 0.0-1.0 based on similar claims in the graph
            - 'combined_score': Weighted average (0.7 * history + 0.3 * pattern)
            - 'confidence': How confident we are (based on amount of data)
            - 'has_history': Boolean if domain has prior evaluations
        """
        result = {
            'history_score': 0.5,  # Neutral default
            'pattern_score': 0.5,
            'combined_score': 0.5,
            'confidence': 0.0,
            'has_history': False,
            'history_count': 0,
            'similar_count': 0
        }
        
        if not self.om:
            return result
        
        # 1. Get source history score
        history_data = self._get_source_history_data(domain)
        if history_data['count'] > 0:
            result['history_score'] = history_data['avg_score']
            result['has_history'] = True
            result['history_count'] = history_data['count']
            # Confidence increases with more data points (max at 5)
            history_confidence = min(1.0, history_data['count'] / 5)
        else:
            history_confidence = 0.0
        
        # 2. Get pattern score from similar claims
        if keywords:
            similar_result = self._find_similar_claims(keywords)
            scores = similar_result.get('scores', [])
            if scores:
                result['pattern_score'] = sum(scores) / len(scores)
                result['similar_count'] = len(scores)
                pattern_confidence = min(1.0, len(scores) / 3)
            else:
                pattern_confidence = 0.0
        else:
            pattern_confidence = 0.0
        
        # 3. Calculate combined score
        # Weight history more heavily than pattern matching
        if result['has_history'] and result['similar_count'] > 0:
            result['combined_score'] = 0.7 * result['history_score'] + 0.3 * result['pattern_score']
            result['confidence'] = 0.6 * history_confidence + 0.4 * pattern_confidence
        elif result['has_history']:
            result['combined_score'] = result['history_score']
            result['confidence'] = history_confidence * 0.8  # Reduce confidence without pattern
        elif result['similar_count'] > 0:
            result['combined_score'] = result['pattern_score']
            result['confidence'] = pattern_confidence * 0.5  # Lower confidence with only patterns
        else:
            # No data available - return neutral
            result['combined_score'] = 0.5
            result['confidence'] = 0.0
        
        return result
    
    def _escape_sparql_string(self, value: str) -> str:
        """
        Escape special characters in a string for safe use in SPARQL queries.
        Prevents SPARQL injection attacks.
        """
        if not value:
            return ""
        # Escape backslash first, then other special characters
        result = value.replace('\\', '\\\\')
        result = result.replace('"', '\\"')
        result = result.replace("'", "\\'")
        result = result.replace('\n', '\\n')
        result = result.replace('\r', '\\r')
        result = result.replace('\t', '\\t')
        return result
    
    def _get_source_history_data(self, domain: str) -> Dict[str, Any]:
        """
        Query the graph for evaluation statistics of this domain.
        
        Returns:
            Dictionary with 'count', 'avg_score', 'last_verdict', 'scores'
        """
        if not domain:
            return {'count': 0, 'avg_score': 0.5, 'scores': []}
        
        # Escape domain to prevent SPARQL injection
        safe_domain = self._escape_sparql_string(domain)
            
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
        LIMIT 10
        """ % safe_domain
        
        scores = []
        last_verdict = None
        
        try:
            combined = self.om.base_graph + self.om.data_graph
            for i, row in enumerate(combined.query(query)):
                scores.append(float(row.score))
                if i == 0:
                    last_verdict = str(row.level).split('#')[-1]
        except Exception as e:
            print(f"[GraphRAG] History data query error: {e}")
            return {'count': 0, 'avg_score': 0.5, 'scores': []}
        
        if not scores:
            return {'count': 0, 'avg_score': 0.5, 'scores': []}
        
        return {
            'count': len(scores),
            'avg_score': sum(scores) / len(scores),
            'last_verdict': last_verdict,
            'scores': scores
        }
