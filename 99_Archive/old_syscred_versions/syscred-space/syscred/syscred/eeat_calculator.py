#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-E-A-T Metrics Calculator for SysCRED
========================================
Calculates Google-style E-E-A-T metrics (Experience, Expertise, Authority, Trust).

These metrics mirror modern Google ranking signals:
- Experience: Domain age, content freshness
- Expertise: Author identification, depth of content
- Authority: PageRank simulation, citations/backlinks
- Trust: HTTPS, fact-checks, low bias score
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class EEATScore:
    """E-E-A-T score container."""
    experience: float  # 0-1
    expertise: float   # 0-1
    authority: float   # 0-1
    trust: float       # 0-1
    
    @property
    def overall(self) -> float:
        """Weighted average of all E-E-A-T components."""
        # Weights based on Google's emphasis
        weights = {
            'experience': 0.15,
            'expertise': 0.25,
            'authority': 0.35,
            'trust': 0.25
        }
        return (
            self.experience * weights['experience'] +
            self.expertise * weights['expertise'] +
            self.authority * weights['authority'] +
            self.trust * weights['trust']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'experience': round(self.experience, 3),
            'expertise': round(self.expertise, 3),
            'authority': round(self.authority, 3),
            'trust': round(self.trust, 3),
            'overall': round(self.overall, 3),
            'experience_pct': f"{int(self.experience * 100)}%",
            'expertise_pct': f"{int(self.expertise * 100)}%",
            'authority_pct': f"{int(self.authority * 100)}%",
            'trust_pct': f"{int(self.trust * 100)}%",
            'overall_pct': f"{int(self.overall * 100)}%"
        }


class EEATCalculator:
    """
    Calculate E-E-A-T metrics from various signals.
    
    Mirrors Google's quality rater guidelines:
    - Experience: Has the author demonstrated real experience?
    - Expertise: Is the content expert-level?
    - Authority: Is the source recognized as authoritative?
    - Trust: Is the source trustworthy?
    """
    
    # Known authoritative domains
    AUTHORITATIVE_DOMAINS = {
        # News
        'lemonde.fr': 0.95,
        'lefigaro.fr': 0.90,
        'liberation.fr': 0.88,
        'nytimes.com': 0.95,
        'washingtonpost.com': 0.93,
        'theguardian.com': 0.92,
        'bbc.com': 0.94,
        'bbc.co.uk': 0.94,
        'reuters.com': 0.96,
        'apnews.com': 0.95,
        # Academic
        'nature.com': 0.98,
        'science.org': 0.98,
        'pubmed.ncbi.nlm.nih.gov': 0.97,
        'scholar.google.com': 0.85,
        # Government
        'gouv.fr': 0.90,
        'gov.uk': 0.90,
        'whitehouse.gov': 0.88,
        'europa.eu': 0.92,
        # Fact-checkers
        'snopes.com': 0.88,
        'factcheck.org': 0.90,
        'politifact.com': 0.88,
        'fullfact.org': 0.89,
        # Wikipedia (moderate authority)
        'wikipedia.org': 0.75,
        'fr.wikipedia.org': 0.75,
        'en.wikipedia.org': 0.75,
    }
    
    # Low-trust domains (misinformation sources)
    LOW_TRUST_DOMAINS = {
        'infowars.com': 0.1,
        'breitbart.com': 0.3,
        'naturalnews.com': 0.15,
        # Add more as needed
    }
    
    def __init__(self):
        """Initialize E-E-A-T calculator."""
        pass
    
    def calculate(
        self,
        url: str,
        text: str,
        nlp_analysis: Optional[Dict[str, Any]] = None,
        pagerank: Optional[float] = None,
        fact_checks: Optional[List[Dict]] = None,
        domain_age_years: Optional[float] = None,
        has_https: bool = True,
        author_identified: bool = False,
        seo_score: Optional[float] = None
    ) -> EEATScore:
        """
        Calculate E-E-A-T scores from available signals.
        
        Args:
            url: Source URL
            text: Article text content
            nlp_analysis: NLP analysis results (sentiment, coherence, bias)
            pagerank: Simulated PageRank score (0-1)
            fact_checks: List of fact-check results
            domain_age_years: Domain age in years (from WHOIS)
            has_https: Whether site uses HTTPS
            author_identified: Whether author is clearly identified
            seo_score: SEO/technical quality score
            
        Returns:
            EEATScore with all component scores
        """
        # Extract domain from URL
        domain = self._extract_domain(url)
        
        # Calculate each component
        experience = self._calculate_experience(
            domain_age_years, 
            text, 
            nlp_analysis
        )
        
        expertise = self._calculate_expertise(
            text, 
            author_identified, 
            nlp_analysis
        )
        
        authority = self._calculate_authority(
            domain, 
            pagerank, 
            seo_score
        )
        
        trust = self._calculate_trust(
            domain, 
            has_https, 
            fact_checks, 
            nlp_analysis
        )
        
        return EEATScore(
            experience=experience,
            expertise=expertise,
            authority=authority,
            trust=trust
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1).lower() if match else url.lower()
    
    def _calculate_experience(
        self,
        domain_age_years: Optional[float],
        text: str,
        nlp_analysis: Optional[Dict]
    ) -> float:
        """
        Calculate Experience score.
        
        Factors:
        - Domain age (longer = more experience)
        - Content freshness (recently updated)
        - First-hand experience indicators in text
        """
        score = 0.5  # Base score
        
        # Domain age contribution (max 0.3)
        if domain_age_years is not None:
            age_score = min(domain_age_years / 20, 1.0) * 0.3  # 20 years = max
            score += age_score
        else:
            score += 0.15  # Assume moderate age
        
        # Content depth contribution (max 0.2)
        word_count = len(text.split()) if text else 0
        if word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.15
        elif word_count > 200:
            score += 0.1
        
        # First-hand experience indicators (max 0.1)
        experience_indicators = [
            r'\b(j\'ai|je suis|nous avons|I have|we have|in my experience)\b',
            r'\b(interview|entretien|témoignage|witness|firsthand)\b',
            r'\b(sur place|on the ground|eyewitness)\b'
        ]
        for pattern in experience_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.03
        
        return min(score, 1.0)
    
    def _calculate_expertise(
        self,
        text: str,
        author_identified: bool,
        nlp_analysis: Optional[Dict]
    ) -> float:
        """
        Calculate Expertise score.
        
        Factors:
        - Author identification
        - Technical depth of content
        - Citation of sources
        - Coherence (from NLP)
        """
        score = 0.4  # Base score
        
        # Author identification (0.2)
        if author_identified:
            score += 0.2
        
        # Citation indicators (max 0.2)
        citation_patterns = [
            r'\b(selon|according to|d\'après|source:)\b',
            r'\b(étude|study|research|rapport|report)\b',
            r'\b(expert|spécialiste|chercheur|professor|Dr\.)\b',
            r'\[([\d]+)\]',  # [1] style citations
            r'https?://[^\s]+'  # Links
        ]
        citation_count = 0
        for pattern in citation_patterns:
            citation_count += len(re.findall(pattern, text, re.IGNORECASE))
        score += min(citation_count * 0.02, 0.2)
        
        # Coherence from NLP analysis (0.2)
        if nlp_analysis and 'coherence' in nlp_analysis:
            coherence = nlp_analysis['coherence']
            if isinstance(coherence, dict):
                coherence = coherence.get('score', 0.5)
            score += coherence * 0.2
        else:
            score += 0.1  # Assume moderate coherence
        
        return min(score, 1.0)
    
    def _calculate_authority(
        self,
        domain: str,
        pagerank: Optional[float],
        seo_score: Optional[float]
    ) -> float:
        """
        Calculate Authority score.
        
        Factors:
        - Known authoritative domain
        - PageRank simulation
        - SEO/technical quality
        """
        score = 0.3  # Base score
        
        # Known domain authority (max 0.5)
        for known_domain, authority in self.AUTHORITATIVE_DOMAINS.items():
            if known_domain in domain:
                score = max(score, authority * 0.5 + 0.3)
                break
        
        # Check low-trust domains
        for low_trust_domain, low_score in self.LOW_TRUST_DOMAINS.items():
            if low_trust_domain in domain:
                score = min(score, low_score)
                break
        
        # PageRank contribution (max 0.3)
        if pagerank is not None:
            score += pagerank * 0.3
        else:
            score += 0.15  # Assume moderate pagerank
        
        # SEO score contribution (max 0.2)
        if seo_score is not None:
            score += seo_score * 0.2
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_trust(
        self,
        domain: str,
        has_https: bool,
        fact_checks: Optional[List[Dict]],
        nlp_analysis: Optional[Dict]
    ) -> float:
        """
        Calculate Trust score.
        
        Factors:
        - HTTPS
        - Fact-check results
        - Bias score (low = better)
        - Known trustworthy domain
        """
        score = 0.4  # Base score
        
        # HTTPS (0.1)
        if has_https:
            score += 0.1
        
        # Fact-check results (max 0.3)
        if fact_checks:
            positive_checks = sum(1 for fc in fact_checks 
                                  if fc.get('rating', '').lower() in ['true', 'vrai', 'correct'])
            negative_checks = sum(1 for fc in fact_checks 
                                  if fc.get('rating', '').lower() in ['false', 'faux', 'incorrect', 'pants-fire'])
            
            if positive_checks > 0:
                score += 0.2
            if negative_checks > 0:
                score -= 0.3
        
        # Bias score (max 0.2, lower bias = higher trust)
        if nlp_analysis:
            bias_data = nlp_analysis.get('bias_analysis', {})
            if isinstance(bias_data, dict):
                bias_score = bias_data.get('score', 0.3)
            else:
                bias_score = 0.3
            # Invert: low bias = high trust contribution
            score += (1 - bias_score) * 0.2
        else:
            score += 0.1
        
        # Known trustworthy domain (0.1)
        for known_domain in self.AUTHORITATIVE_DOMAINS:
            if known_domain in domain:
                score += 0.1
                break
        
        # Known low-trust domain (penalty)
        for low_trust_domain in self.LOW_TRUST_DOMAINS:
            if low_trust_domain in domain:
                score -= 0.3
                break
        
        return max(min(score, 1.0), 0.0)
    
    def explain_score(self, eeat: EEATScore, url: str) -> str:
        """
        Generate human-readable explanation of E-E-A-T score.
        
        Args:
            eeat: EEATScore instance
            url: Source URL
            
        Returns:
            Formatted explanation string
        """
        domain = self._extract_domain(url)
        
        explanations = []
        
        # Experience
        if eeat.experience >= 0.8:
            explanations.append(f"✅ **Expérience élevée** ({eeat.experience_pct}): Source établie depuis longtemps")
        elif eeat.experience >= 0.5:
            explanations.append(f"🔶 **Expérience moyenne** ({eeat.experience_pct}): Source modérément établie")
        else:
            explanations.append(f"⚠️ **Expérience faible** ({eeat.experience_pct}): Source récente ou peu connue")
        
        # Expertise
        if eeat.expertise >= 0.8:
            explanations.append(f"✅ **Expertise élevée** ({eeat.expertise_pct}): Contenu approfondi avec citations")
        elif eeat.expertise >= 0.5:
            explanations.append(f"🔶 **Expertise moyenne** ({eeat.expertise_pct}): Contenu standard")
        else:
            explanations.append(f"⚠️ **Expertise faible** ({eeat.expertise_pct}): Manque de profondeur")
        
        # Authority
        if eeat.authority >= 0.8:
            explanations.append(f"✅ **Autorité élevée** ({eeat.authority_pct}): Source très citée et reconnue")
        elif eeat.authority >= 0.5:
            explanations.append(f"🔶 **Autorité moyenne** ({eeat.authority_pct}): Source modérément reconnue")
        else:
            explanations.append(f"⚠️ **Autorité faible** ({eeat.authority_pct}): Peu de citations externes")
        
        # Trust
        if eeat.trust >= 0.8:
            explanations.append(f"✅ **Confiance élevée** ({eeat.trust_pct}): Faits vérifiés, pas de biais")
        elif eeat.trust >= 0.5:
            explanations.append(f"🔶 **Confiance moyenne** ({eeat.trust_pct}): Quelques signaux de confiance")
        else:
            explanations.append(f"⚠️ **Confiance faible** ({eeat.trust_pct}): Prudence recommandée")
        
        return "\n".join(explanations)


# Test
if __name__ == "__main__":
    calc = EEATCalculator()
    
    test_url = "https://www.lemonde.fr/politique/article/2024/01/06/trump.html"
    test_text = """
    Selon une étude du chercheur Dr. Martin, l'insurrection du 6 janvier 2021 
    au Capitol a été un événement marquant. Notre reporter sur place a témoigné
    des événements. Les experts politiques analysent les conséquences.
    """
    
    nlp_analysis = {
        'coherence': {'score': 0.8},
        'bias_analysis': {'score': 0.2}
    }
    
    eeat = calc.calculate(
        url=test_url,
        text=test_text,
        nlp_analysis=nlp_analysis,
        pagerank=0.7,
        has_https=True,
        author_identified=True
    )
    
    print("=== E-E-A-T Scores ===")
    print(f"Experience: {eeat.experience_pct}")
    print(f"Expertise:  {eeat.expertise_pct}")
    print(f"Authority:  {eeat.authority_pct}")
    print(f"Trust:      {eeat.trust_pct}")
    print(f"Overall:    {eeat.overall_pct}")
    print("\n=== Explanation ===")
    print(calc.explain_score(eeat, test_url))
