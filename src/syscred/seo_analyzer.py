# -*- coding: utf-8 -*-
"""
SEO Analyzer Module - SysCRED
==============================
Provides SEO analysis and Information Retrieval metrics for credibility assessment.

Implements:
- TF-IDF calculation
- BM25 scoring
- PageRank estimation/explanation
- SEO meta tag analysis
- Backlink quality assessment

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerModelingHybridSystem2025

Note sur la scalabilité:
- Pour des corpus de grande taille, envisager Cython ou Rust pour TF-IDF/BM25
- Les calculs matriciels peuvent bénéficier de NumPy optimisé ou de bibliothèques C
"""

import math
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter
from urllib.parse import urlparse

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# --- Data Classes ---

@dataclass
class SEOAnalysis:
    """Results of SEO analysis for a webpage."""
    url: str
    title_length: int
    title_has_keywords: bool
    meta_description_length: int
    has_meta_keywords: bool
    heading_structure: Dict[str, int]  # h1, h2, h3 counts
    word_count: int
    keyword_density: Dict[str, float]
    readability_score: float
    seo_score: float  # Overall 0-1 score


@dataclass
class PageRankExplanation:
    """Explainable PageRank estimation."""
    url: str
    estimated_pr: float
    factors: List[Dict[str, Any]]
    explanation_text: str
    confidence: float


@dataclass
class IRMetrics:
    """Information Retrieval metrics for a document."""
    tf_idf_scores: Dict[str, float]
    bm25_score: float
    top_terms: List[Tuple[str, float]]
    document_length: int
    avg_term_frequency: float


class SEOAnalyzer:
    """
    Analyze SEO factors and compute IR metrics for credibility assessment.
    
    This module helps explain WHY a URL might rank well (or poorly) in search engines,
    which is a factor in its credibility assessment.
    """
    
    # BM25 parameters (classic values)
    BM25_K1 = 1.5  # Term frequency saturation
    BM25_B = 0.75   # Length normalization
    
    # Stopwords (expandable)
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
        'he', 'she', 'him', 'her', 'his', 'my', 'your', 'our', 'their',
        'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
        # French stopwords
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
        'mais', 'donc', 'car', 'ni', 'que', 'qui', 'quoi', 'dont', 'où',
        'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
        'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs',
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'on',
        'est', 'sont', 'être', 'avoir', 'fait', 'faire', 'dit', 'dire',
        'plus', 'moins', 'très', 'bien', 'tout', 'tous', 'toute', 'toutes',
        'pour', 'par', 'sur', 'sous', 'avec', 'sans', 'dans', 'en', 'au', 'aux'
    }
    
    def __init__(self):
        """Initialize the SEO analyzer."""
        # Reference corpus statistics (can be updated with real data)
        self.avg_doc_length = 500  # Average document length in words
        self.corpus_size = 1000     # Number of documents in reference corpus
        # IDF values for common terms (placeholder - would be computed from real corpus)
        self.idf_cache = {}
    
    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            remove_stopwords: Whether to remove stopwords
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', text)
        
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.STOPWORDS]
        
        return tokens
    
    def calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """
        Calculate Term Frequency for each token.
        
        TF(t) = (count of t in document) / (total terms in document)
        """
        if not tokens:
            return {}
        
        term_counts = Counter(tokens)
        total_terms = len(tokens)
        
        return {term: count / total_terms for term, count in term_counts.items()}
    
    def calculate_idf(self, term: str, doc_frequency: int = None) -> float:
        """
        Calculate Inverse Document Frequency.
        
        IDF(t) = log(N / (1 + df(t)))
        
        Args:
            term: The term to calculate IDF for
            doc_frequency: Number of documents containing the term
                          (if None, use heuristic based on term length)
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        if doc_frequency is None:
            # Heuristic: shorter common words appear in more documents
            if len(term) <= 3:
                doc_frequency = self.corpus_size * 0.5
            elif len(term) <= 5:
                doc_frequency = self.corpus_size * 0.3
            elif len(term) <= 8:
                doc_frequency = self.corpus_size * 0.1
            else:
                doc_frequency = self.corpus_size * 0.05
        
        idf = math.log(self.corpus_size / (1 + doc_frequency))
        self.idf_cache[term] = idf
        return idf
    
    def calculate_tf_idf(self, text: str) -> Dict[str, float]:
        """
        Calculate TF-IDF scores for all terms in a document.
        
        TF-IDF(t,d) = TF(t,d) × IDF(t)
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of term -> TF-IDF score
        """
        tokens = self.tokenize(text)
        tf_scores = self.calculate_tf(tokens)
        
        tf_idf = {}
        for term, tf in tf_scores.items():
            idf = self.calculate_idf(term)
            tf_idf[term] = tf * idf
        
        return tf_idf
    
    def calculate_bm25(
        self, 
        query: str, 
        document: str,
        k1: float = None,
        b: float = None
    ) -> float:
        """
        Calculate BM25 relevance score between query and document.
        
        BM25(D, Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) / (f(qi,D) + k1 × (1 - b + b × |D|/avgdl))
        
        Args:
            query: Query string
            document: Document text
            k1: Term frequency saturation parameter
            b: Length normalization parameter
            
        Returns:
            BM25 score
        """
        k1 = k1 or self.BM25_K1
        b = b or self.BM25_B
        
        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(document, remove_stopwords=False)
        
        if not query_tokens or not doc_tokens:
            return 0.0
        
        doc_length = len(doc_tokens)
        doc_term_counts = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in doc_term_counts:
                continue
            
            tf = doc_term_counts[term]
            idf = self.calculate_idf(term)
            
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_length / self.avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def analyze_seo(
        self, 
        url: str,
        title: Optional[str],
        meta_description: Optional[str],
        text_content: str,
        headings: Dict[str, List[str]] = None
    ) -> SEOAnalysis:
        """
        Perform comprehensive SEO analysis.
        
        Args:
            url: Page URL
            title: Page title
            meta_description: Meta description
            text_content: Main text content
            headings: Dictionary of heading levels (h1, h2, etc.) and their texts
            
        Returns:
            SEOAnalysis with all metrics
        """
        tokens = self.tokenize(text_content)
        word_count = len(tokens)
        
        # Title analysis
        title_length = len(title) if title else 0
        title_tokens = self.tokenize(title) if title else []
        
        # Check if title contains main keywords from content
        content_top_terms = Counter(tokens).most_common(10)
        title_has_keywords = any(
            term in title_tokens 
            for term, _ in content_top_terms[:5]
        ) if title_tokens else False
        
        # Meta description analysis
        meta_length = len(meta_description) if meta_description else 0
        
        # Heading structure
        headings = headings or {}
        heading_structure = {
            'h1': len(headings.get('h1', [])),
            'h2': len(headings.get('h2', [])),
            'h3': len(headings.get('h3', []))
        }
        
        # Keyword density (top 5 terms)
        keyword_density = {}
        for term, count in Counter(tokens).most_common(5):
            keyword_density[term] = count / word_count if word_count > 0 else 0
        
        # Readability score (simple metric based on average word/sentence length)
        sentences = re.split(r'[.!?]+', text_content)
        avg_sentence_length = word_count / len(sentences) if sentences else 0
        
        # Convert to readability score (0-1, where 1 is optimal ~15-20 words/sentence)
        if 15 <= avg_sentence_length <= 20:
            readability_score = 1.0
        elif 10 <= avg_sentence_length <= 25:
            readability_score = 0.8
        elif 5 <= avg_sentence_length <= 30:
            readability_score = 0.6
        else:
            readability_score = 0.4
        
        # Overall SEO score
        seo_factors = []
        
        # Title score (optimal: 50-60 chars)
        if 50 <= title_length <= 60:
            seo_factors.append(1.0)
        elif 30 <= title_length <= 70:
            seo_factors.append(0.7)
        else:
            seo_factors.append(0.3)
        
        # Meta description (optimal: 150-160 chars)
        if 150 <= meta_length <= 160:
            seo_factors.append(1.0)
        elif 100 <= meta_length <= 200:
            seo_factors.append(0.7)
        else:
            seo_factors.append(0.3)
        
        # Has exactly one H1
        seo_factors.append(1.0 if heading_structure['h1'] == 1 else 0.5)
        
        # Content length (optimal: 300+ words)
        if word_count >= 1000:
            seo_factors.append(1.0)
        elif word_count >= 500:
            seo_factors.append(0.8)
        elif word_count >= 300:
            seo_factors.append(0.6)
        else:
            seo_factors.append(0.3)
        
        seo_score = sum(seo_factors) / len(seo_factors) if seo_factors else 0.5
        
        return SEOAnalysis(
            url=url,
            title_length=title_length,
            title_has_keywords=title_has_keywords,
            meta_description_length=meta_length,
            has_meta_keywords=bool(keyword_density),
            heading_structure=heading_structure,
            word_count=word_count,
            keyword_density=keyword_density,
            readability_score=readability_score,
            seo_score=seo_score
        )
    
    def estimate_pagerank(
        self,
        url: str,
        backlinks: List[Dict[str, Any]] = None,
        domain_age_days: int = None,
        source_reputation: str = None
    ) -> PageRankExplanation:
        """
        Estimate and explain PageRank-like score.
        
        This is NOT the actual Google PageRank, but an explainable approximation
        based on available factors that contribute to search ranking.
        
        PageRank Formula (simplified):
        PR(A) = (1-d) + d × Σ (PR(Ti) / C(Ti))
        
        Where:
        - d = damping factor (0.85)
        - Ti = pages pointing to A
        - C(Ti) = number of outgoing links from Ti
        
        Args:
            url: Target URL
            backlinks: List of backlink information
            domain_age_days: Age of the domain in days
            source_reputation: Known reputation level
            
        Returns:
            PageRankExplanation with estimated score and factors
        """
        d = 0.85  # Damping factor
        base_pr = (1 - d)  # Starting PageRank
        
        factors = []
        pr_contributions = []
        
        # Factor 1: Domain Age
        if domain_age_days is not None:
            if domain_age_days > 365 * 5:  # > 5 years
                age_contribution = 0.3
                age_description = "Domaine ancien (5+ ans) - forte confiance"
            elif domain_age_days > 365 * 2:  # > 2 years
                age_contribution = 0.2
                age_description = "Domaine établi (2-5 ans) - bonne confiance"
            elif domain_age_days > 365:  # > 1 year
                age_contribution = 0.1
                age_description = "Domaine récent (1-2 ans) - confiance modérée"
            else:
                age_contribution = 0.0
                age_description = "Domaine très récent (<1 an) - confiance faible"
            
            factors.append({
                'name': 'Domain Age',
                'value': f"{domain_age_days} days ({domain_age_days/365:.1f} years)",
                'contribution': age_contribution,
                'description': age_description
            })
            pr_contributions.append(age_contribution)
        
        # Factor 2: Source Reputation
        if source_reputation:
            if source_reputation == 'High':
                rep_contribution = 0.3
                rep_description = "Source réputée - équivalent à beaucoup de backlinks de qualité"
            elif source_reputation == 'Medium':
                rep_contribution = 0.15
                rep_description = "Source connue - équivalent à quelques backlinks de qualité"
            else:
                rep_contribution = 0.0
                rep_description = "Source inconnue ou peu fiable - pas de boost de réputation"
            
            factors.append({
                'name': 'Source Reputation',
                'value': source_reputation,
                'contribution': rep_contribution,
                'description': rep_description
            })
            pr_contributions.append(rep_contribution)
        
        # Factor 3: Backlinks (if available)
        backlinks = backlinks or []
        if backlinks:
            # Estimate backlink contribution
            high_quality_count = sum(1 for bl in backlinks if bl.get('quality', 'low') == 'high')
            medium_quality_count = sum(1 for bl in backlinks if bl.get('quality', 'low') == 'medium')
            
            # Each high-quality backlink contributes more
            backlink_contribution = min(0.3, high_quality_count * 0.05 + medium_quality_count * 0.02)
            
            factors.append({
                'name': 'Backlinks',
                'value': f"{len(backlinks)} total ({high_quality_count} high quality)",
                'contribution': backlink_contribution,
                'description': f"Liens entrants détectés - contribution au classement"
            })
            pr_contributions.append(backlink_contribution)
        
        # Factor 4: Domain type (TLD)
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain.endswith('.edu') or domain.endswith('.gov'):
            tld_contribution = 0.2
            tld_description = "Domaine .edu/.gov - haute autorité institutionnelle"
        elif domain.endswith('.ac.uk') or domain.endswith('.gouv.fr'):
            tld_contribution = 0.15
            tld_description = "Domaine académique/gouvernemental - bonne autorité"
        elif domain.endswith('.org'):
            tld_contribution = 0.05
            tld_description = "Domaine .org - légère autorité"
        else:
            tld_contribution = 0.0
            tld_description = "Domaine commercial standard"
        
        factors.append({
            'name': 'Domain Type (TLD)',
            'value': domain,
            'contribution': tld_contribution,
            'description': tld_description
        })
        pr_contributions.append(tld_contribution)
        
        # Calculate final estimated PageRank
        total_contribution = sum(pr_contributions)
        estimated_pr = base_pr + d * total_contribution
        estimated_pr = min(1.0, max(0.0, estimated_pr))  # Clamp to [0, 1]
        
        # Generate explanation
        explanation_parts = [
            f"PageRank estimé: {estimated_pr:.3f}",
            f"",
            f"Formule: PR = (1-d) + d × Σ(contributions)",
            f"        PR = {base_pr:.2f} + {d:.2f} × {total_contribution:.2f}",
            f"",
            f"Facteurs contributifs:"
        ]
        
        for factor in factors:
            explanation_parts.append(
                f"  • {factor['name']}: +{factor['contribution']:.2f} - {factor['description']}"
            )
        
        # Confidence based on how many factors we have data for
        confidence = min(1.0, len([f for f in factors if f['contribution'] > 0]) / 4)
        
        return PageRankExplanation(
            url=url,
            estimated_pr=estimated_pr,
            factors=factors,
            explanation_text="\n".join(explanation_parts),
            confidence=confidence
        )
    
    def get_ir_metrics(self, text: str, query: str = None) -> IRMetrics:
        """
        Get comprehensive IR metrics for a document.
        
        Args:
            text: Document text
            query: Optional query for BM25 calculation
            
        Returns:
            IRMetrics with TF-IDF, BM25, and other metrics
        """
        tokens = self.tokenize(text)
        tf_idf = self.calculate_tf_idf(text)
        
        # Top terms by TF-IDF
        top_terms = sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # BM25 score (if query provided)
        bm25_score = 0.0
        if query:
            bm25_score = self.calculate_bm25(query, text)
        
        # Average term frequency
        tf = self.calculate_tf(tokens)
        avg_tf = sum(tf.values()) / len(tf) if tf else 0
        
        return IRMetrics(
            tf_idf_scores=tf_idf,
            bm25_score=bm25_score,
            top_terms=top_terms,
            document_length=len(tokens),
            avg_term_frequency=avg_tf
        )


# --- Testing ---
if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED SEO Analyzer - Tests")
    print("=" * 60 + "\n")
    
    analyzer = SEOAnalyzer()
    
    # Test 1: TF-IDF
    print("1. Testing TF-IDF calculation...")
    sample_text = """
    The credibility of online information is crucial in today's digital age.
    Fact-checking organizations help verify claims and identify misinformation.
    Source reputation and domain age are important credibility factors.
    """
    tf_idf = analyzer.calculate_tf_idf(sample_text)
    top_5 = sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:5]
    print("   Top 5 TF-IDF terms:")
    for term, score in top_5:
        print(f"     {term}: {score:.4f}")
    print()
    
    # Test 2: BM25
    print("2. Testing BM25 scoring...")
    query = "credibility verification"
    bm25_score = analyzer.calculate_bm25(query, sample_text)
    print(f"   Query: '{query}'")
    print(f"   BM25 Score: {bm25_score:.4f}")
    print()
    
    # Test 3: SEO Analysis
    print("3. Testing SEO analysis...")
    seo = analyzer.analyze_seo(
        url="https://example.com/article",
        title="Understanding Online Credibility - A Complete Guide",
        meta_description="Learn about the key factors that determine the credibility of online information sources.",
        text_content=sample_text
    )
    print(f"   Title length: {seo.title_length} chars")
    print(f"   Meta description length: {seo.meta_description_length} chars")
    print(f"   Word count: {seo.word_count}")
    print(f"   SEO Score: {seo.seo_score:.2f}")
    print()
    
    # Test 4: PageRank Estimation
    print("4. Testing PageRank estimation...")
    pr = analyzer.estimate_pagerank(
        url="https://www.lemonde.fr/article",
        domain_age_days=9125,  # ~25 years
        source_reputation="High"
    )
    print(f"   Estimated PageRank: {pr.estimated_pr:.3f}")
    print(f"   Confidence: {pr.confidence:.2f}")
    print("\n   Explanation:")
    print("   " + pr.explanation_text.replace("\n", "\n   "))
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
