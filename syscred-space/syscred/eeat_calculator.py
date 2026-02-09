# -*- coding: utf-8 -*-
"""
E-E-A-T Calculator Module - SysCRED
====================================
Google Quality Rater Guidelines implementation.

E-E-A-T Scores:
- Experience: Domain age, content richness
- Expertise: Technical vocabulary, citations
- Authority: Estimated PageRank, backlinks
- Trust: HTTPS, unbiased sentiment

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import re
from typing import Dict, Optional
from urllib.parse import urlparse


class EEATCalculator:
    """
    Calculate E-E-A-T scores based on Google Quality Rater Guidelines.
    """
    
    # Technical terms that indicate expertise
    TECHNICAL_TERMS = {
        'research', 'study', 'analysis', 'data', 'evidence', 'methodology',
        'peer-reviewed', 'journal', 'university', 'professor', 'dr.', 'phd',
        'statistics', 'experiment', 'hypothesis', 'publication', 'citation',
        'algorithm', 'framework', 'systematic', 'empirical', 'quantitative'
    }
    
    # Trusted domains (simplified list)
    TRUSTED_DOMAINS = {
        '.edu', '.gov', '.org', 'reuters.com', 'apnews.com', 'bbc.com',
        'nature.com', 'science.org', 'who.int', 'un.org', 'wikipedia.org',
        'lemonde.fr', 'radio-canada.ca', 'uqam.ca', 'umontreal.ca'
    }
    
    def __init__(self):
        """Initialize E-E-A-T calculator."""
        pass
    
    def calculate(
        self,
        url: Optional[str] = None,
        text: Optional[str] = None,
        sentiment_score: float = 0.5,
        has_citations: bool = False,
        domain_age_years: int = 0
    ) -> Dict:
        """
        Calculate E-E-A-T scores.
        
        Args:
            url: Source URL
            text: Content text
            sentiment_score: 0-1 (0.5 = neutral is best for trust)
            has_citations: Whether content has citations
            domain_age_years: Estimated domain age
        
        Returns:
            {
                'experience': 0.75,
                'expertise': 0.80,
                'authority': 0.65,
                'trust': 0.90,
                'overall': 0.78,
                'details': {...}
            }
        """
        details = {}
        
        # --- EXPERIENCE ---
        experience = 0.5
        if domain_age_years >= 10:
            experience += 0.3
        elif domain_age_years >= 5:
            experience += 0.2
        elif domain_age_years >= 2:
            experience += 0.1
        
        if text:
            word_count = len(text.split())
            if word_count >= 1000:
                experience += 0.15
            elif word_count >= 500:
                experience += 0.1
        
        experience = min(experience, 1.0)
        details['experience_factors'] = {
            'domain_age_bonus': domain_age_years >= 2,
            'content_richness': len(text.split()) if text else 0
        }
        
        # --- EXPERTISE ---
        expertise = 0.4
        tech_count = 0
        
        if text:
            text_lower = text.lower()
            for term in self.TECHNICAL_TERMS:
                if term in text_lower:
                    tech_count += 1
            
            if tech_count >= 5:
                expertise += 0.35
            elif tech_count >= 3:
                expertise += 0.25
            elif tech_count >= 1:
                expertise += 0.15
        
        if has_citations:
            expertise += 0.2
        
        expertise = min(expertise, 1.0)
        details['expertise_factors'] = {
            'technical_terms_found': tech_count,
            'has_citations': has_citations
        }
        
        # --- AUTHORITY ---
        authority = 0.3
        
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for trusted in self.TRUSTED_DOMAINS:
                if trusted in domain:
                    authority += 0.4
                    break
            
            if parsed.scheme == 'https':
                authority += 0.1
        
        # Check for author indicators in text
        if text:
            author_patterns = [r'by\s+\w+\s+\w+', r'author:', r'written by', r'par\s+\w+']
            for pattern in author_patterns:
                if re.search(pattern, text.lower()):
                    authority += 0.15
                    break
        
        authority = min(authority, 1.0)
        details['authority_factors'] = {
            'trusted_domain': False,
            'https': url and urlparse(url).scheme == 'https' if url else False
        }
        
        # --- TRUST ---
        trust = 0.5
        
        # Neutral sentiment is best (0.5)
        sentiment_deviation = abs(sentiment_score - 0.5)
        if sentiment_deviation < 0.1:
            trust += 0.3  # Very neutral
        elif sentiment_deviation < 0.2:
            trust += 0.2
        elif sentiment_deviation < 0.3:
            trust += 0.1
        
        if url and urlparse(url).scheme == 'https':
            trust += 0.15
        
        trust = min(trust, 1.0)
        details['trust_factors'] = {
            'sentiment_neutrality': 1 - sentiment_deviation * 2,
            'secure_connection': url and 'https' in url if url else False
        }
        
        # --- OVERALL ---
        overall = (experience * 0.2 + expertise * 0.3 + 
                   authority * 0.25 + trust * 0.25)
        
        return {
            'experience': round(experience, 2),
            'expertise': round(expertise, 2),
            'authority': round(authority, 2),
            'trust': round(trust, 2),
            'overall': round(overall, 2),
            'details': details
        }
    
    def get_explanation(self, scores: Dict) -> str:
        """Generate human-readable explanation of E-E-A-T scores."""
        explanations = []
        
        exp = scores.get('experience', 0)
        if exp >= 0.7:
            explanations.append("✅ Expérience: Source établie avec contenu riche")
        elif exp >= 0.5:
            explanations.append("⚠️ Expérience: Source moyennement établie")
        else:
            explanations.append("❌ Expérience: Source nouvelle ou contenu limité")
        
        ext = scores.get('expertise', 0)
        if ext >= 0.7:
            explanations.append("✅ Expertise: Vocabulaire technique, citations présentes")
        elif ext >= 0.5:
            explanations.append("⚠️ Expertise: Niveau technique moyen")
        else:
            explanations.append("❌ Expertise: Manque de terminologie spécialisée")
        
        auth = scores.get('authority', 0)
        if auth >= 0.7:
            explanations.append("✅ Autorité: Domaine reconnu et fiable")
        elif auth >= 0.5:
            explanations.append("⚠️ Autorité: Niveau d'autorité moyen")
        else:
            explanations.append("❌ Autorité: Source non reconnue")
        
        tr = scores.get('trust', 0)
        if tr >= 0.7:
            explanations.append("✅ Confiance: Ton neutre, connexion sécurisée")
        elif tr >= 0.5:
            explanations.append("⚠️ Confiance: Niveau de confiance moyen")
        else:
            explanations.append("❌ Confiance: Ton biaisé ou connexion non sécurisée")
        
        return "\n".join(explanations)


# Singleton
_calculator = None

def get_calculator() -> EEATCalculator:
    """Get or create E-E-A-T calculator singleton."""
    global _calculator
    if _calculator is None:
        _calculator = EEATCalculator()
    return _calculator


# --- Testing ---
if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED E-E-A-T Calculator - Test")
    print("=" * 60)
    
    calc = EEATCalculator()
    
    test_url = "https://www.nature.com/articles/example"
    test_text = """
    A peer-reviewed study published in the journal Nature found evidence 
    that the new methodology significantly improves research outcomes.
    Dr. Smith from Harvard University presented the statistics at the conference.
    """
    
    result = calc.calculate(
        url=test_url,
        text=test_text,
        sentiment_score=0.5,
        has_citations=True,
        domain_age_years=15
    )
    
    print("\n--- E-E-A-T Scores ---")
    print(f"  Experience: {result['experience']:.0%}")
    print(f"  Expertise:  {result['expertise']:.0%}")
    print(f"  Authority:  {result['authority']:.0%}")
    print(f"  Trust:      {result['trust']:.0%}")
    print(f"  ─────────────────")
    print(f"  OVERALL:    {result['overall']:.0%}")
    
    print("\n--- Explanation ---")
    print(calc.get_explanation(result))
    
    print("\n" + "=" * 60)
