# -*- coding: utf-8 -*-
"""
IR Engine Module - SysCRED
===========================
Information Retrieval engine extracted from TREC AP88-90 project.

Features:
- TF-IDF calculation (custom and via Pyserini)
- BM25 scoring (via Lucene/Pyserini)
- Query Likelihood Dirichlet (QLD)
- Pseudo-Relevance Feedback (PRF)
- Porter Stemming integration

Based on: TREC_AP88-90_5juin2025.py
(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter

# Check for optional dependencies
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    from nltk.tokenize import word_tokenize
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

try:
    from pyserini.search.lucene import LuceneSearcher
    HAS_PYSERINI = True
except ImportError:
    HAS_PYSERINI = False


# --- Data Classes ---

@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    score: float
    rank: int
    snippet: Optional[str] = None


@dataclass
class SearchResponse:
    """Complete search response."""
    query_id: str
    query_text: str
    results: List[SearchResult]
    model: str  # 'bm25', 'qld', 'tfidf'
    total_hits: int
    search_time_ms: float


class IREngine:
    """
    Information Retrieval engine with multiple scoring methods.
    
    Supports:
    - Built-in TF-IDF/BM25 (no dependencies)
    - Pyserini/Lucene BM25 and QLD (if pyserini installed)
    - Query expansion with Pseudo-Relevance Feedback
    """
    
    # BM25 default parameters
    BM25_K1 = 0.9
    BM25_B = 0.4
    
    def __init__(self, index_path: str = None, use_stemming: bool = True):
        """
        Initialize the IR engine.
        
        Args:
            index_path: Path to Lucene/Pyserini index (optional)
            use_stemming: Whether to apply Porter stemming
        """
        self.index_path = index_path
        self.use_stemming = use_stemming
        self.searcher = None
        
        # Initialize NLTK components
        if HAS_NLTK:
            try:
                self.stopwords = set(stopwords.words('english'))
                self.stemmer = PorterStemmer() if use_stemming else None
            except LookupError:
                print("[IREngine] Downloading NLTK resources...")
                nltk.download('stopwords', quiet=True)
                nltk.download('punkt', quiet=True)
                nltk.download('punkt_tab', quiet=True)
                self.stopwords = set(stopwords.words('english'))
                self.stemmer = PorterStemmer() if use_stemming else None
        else:
            # Fallback stopwords
            self.stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
                'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does',
                'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'must', 'shall', 'can', 'need', 'this', 'that', 'these',
                'those', 'it', 'its', 'they', 'them', 'he', 'she', 'him',
                'her', 'his', 'we', 'you', 'i', 'my', 'your', 'our', 'their'
            }
            self.stemmer = None
        
        # Initialize Pyserini searcher if available
        if HAS_PYSERINI and index_path:
            try:
                self.searcher = LuceneSearcher(index_path)
                print(f"[IREngine] Pyserini searcher initialized with index: {index_path}")
            except Exception as e:
                print(f"[IREngine] Failed to initialize Pyserini: {e}")
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess text with tokenization, stopword removal, and optional stemming.
        
        This matches the TREC preprocessing pipeline.
        """
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        
        if HAS_NLTK:
            try:
                tokens = word_tokenize(text)
            except LookupError:
                # Fallback tokenization
                tokens = re.findall(r'\b[a-z]+\b', text)
        else:
            tokens = re.findall(r'\b[a-z]+\b', text)
        
        # Filter stopwords and non-alpha
        filtered = [t for t in tokens if t.isalpha() and t not in self.stopwords]
        
        # Apply stemming if enabled
        if self.stemmer:
            filtered = [self.stemmer.stem(t) for t in filtered]
        
        return ' '.join(filtered)
    
    def calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Calculate term frequency."""
        if not tokens:
            return {}
        counts = Counter(tokens)
        total = len(tokens)
        return {term: count / total for term, count in counts.items()}
    
    def calculate_bm25_score(
        self,
        query_terms: List[str],
        doc_terms: List[str],
        doc_length: int,
        avg_doc_length: float,
        doc_freq: Dict[str, int],
        corpus_size: int
    ) -> float:
        """
        Calculate BM25 score for a document.
        
        BM25(D, Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) / (f(qi,D) + k1 × (1 - b + b × |D|/avgdl))
        """
        doc_term_counts = Counter(doc_terms)
        score = 0.0
        
        for term in query_terms:
            if term not in doc_term_counts:
                continue
            
            tf = doc_term_counts[term]
            df = doc_freq.get(term, 1)
            idf = math.log((corpus_size - df + 0.5) / (df + 0.5) + 1)
            
            numerator = tf * (self.BM25_K1 + 1)
            denominator = tf + self.BM25_K1 * (1 - self.BM25_B + self.BM25_B * doc_length / avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search_pyserini(
        self,
        query: str,
        model: str = 'bm25',
        k: int = 100,
        query_id: str = "Q1"
    ) -> SearchResponse:
        """
        Search using Pyserini/Lucene.
        
        Args:
            query: Query text
            model: 'bm25' or 'qld'
            k: Number of results
            query_id: Query identifier
        """
        import time
        start = time.time()
        
        if not self.searcher:
            raise RuntimeError("Pyserini searcher not initialized. Provide index_path.")
        
        # Configure similarity
        if model == 'bm25':
            self.searcher.set_bm25(k1=self.BM25_K1, b=self.BM25_B)
        elif model == 'qld':
            self.searcher.set_qld()
        else:
            self.searcher.set_bm25()
        
        # Preprocess query
        processed_query = self.preprocess(query)
        
        # Search
        hits = self.searcher.search(processed_query, k=k)
        
        results = []
        for i, hit in enumerate(hits):
            results.append(SearchResult(
                doc_id=hit.docid,
                score=hit.score,
                rank=i + 1
            ))
        
        elapsed = (time.time() - start) * 1000
        
        return SearchResponse(
            query_id=query_id,
            query_text=query,
            results=results,
            model=model,
            total_hits=len(results),
            search_time_ms=elapsed
        )
    
    def pseudo_relevance_feedback(
        self,
        query: str,
        top_docs_texts: List[str],
        num_expansion_terms: int = 10
    ) -> str:
        """
        Expand query using Pseudo-Relevance Feedback (PRF).
        
        Uses top-k retrieved documents to find expansion terms.
        """
        query_tokens = self.preprocess(query).split()
        
        # Collect terms from top documents
        expansion_candidates = Counter()
        for doc_text in top_docs_texts:
            doc_tokens = self.preprocess(doc_text).split()
            # Count terms not in original query
            for token in doc_tokens:
                if token not in query_tokens:
                    expansion_candidates[token] += 1
        
        # Get top expansion terms
        expansion_terms = [term for term, _ in expansion_candidates.most_common(num_expansion_terms)]
        
        # Create expanded query
        expanded_query = query + ' ' + ' '.join(expansion_terms)
        
        return expanded_query
    
    def format_trec_run(
        self,
        responses: List[SearchResponse],
        run_tag: str
    ) -> str:
        """
        Format results in TREC run file format.
        
        Format: query_id Q0 doc_id rank score run_tag
        """
        lines = []
        for response in responses:
            for result in response.results:
                lines.append(
                    f"{response.query_id} Q0 {result.doc_id} "
                    f"{result.rank} {result.score:.6f} {run_tag}"
                )
        return '\n'.join(lines)


# --- Kaggle/Colab Utilities ---

def setup_kaggle_environment():
    """Setup environment for Kaggle notebooks."""
    import subprocess
    import sys
    
    print("=" * 60)
    print("SysCRED - Kaggle Environment Setup")
    print("=" * 60)
    
    # Check for GPU/TPU
    import torch
    if torch.cuda.is_available():
        print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
    else:
        print("✗ No GPU detected")
    
    # Install required packages
    packages = [
        'pyserini',
        'transformers',
        'pytrec_eval',
        'nltk',
        'rdflib'
    ]
    
    print("\nInstalling packages...")
    for pkg in packages:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q', pkg],
                check=True,
                capture_output=True
            )
            print(f"  ✓ {pkg}")
        except:
            print(f"  ✗ {pkg} - install failed")
    
    # Download NLTK resources
    import nltk
    for resource in ['stopwords', 'punkt', 'punkt_tab', 'wordnet']:
        try:
            nltk.download(resource, quiet=True)
        except:
            pass
    
    print("\n✓ Environment setup complete")


def load_kaggle_dataset(dataset_path: str) -> str:
    """
    Load a Kaggle dataset.
    
    Args:
        dataset_path: Path like '/kaggle/input/trec-ap88-90'
    """
    import os
    
    if os.path.exists(dataset_path):
        print(f"✓ Dataset found: {dataset_path}")
        return dataset_path
    else:
        print(f"✗ Dataset not found: {dataset_path}")
        print("Make sure to add the dataset to your Kaggle notebook.")
        return None


# --- Testing ---
if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED IR Engine - Tests")
    print("=" * 60)
    
    engine = IREngine(use_stemming=True)
    
    # Test preprocessing
    print("\n1. Testing preprocessing...")
    sample = "Information Retrieval systems help users find relevant documents."
    processed = engine.preprocess(sample)
    print(f"   Original: {sample}")
    print(f"   Processed: {processed}")
    
    # Test BM25
    print("\n2. Testing BM25 calculation...")
    query_terms = engine.preprocess("information retrieval").split()
    doc_terms = engine.preprocess(sample).split()
    
    score = engine.calculate_bm25_score(
        query_terms=query_terms,
        doc_terms=doc_terms,
        doc_length=len(doc_terms),
        avg_doc_length=10,
        doc_freq={'inform': 5, 'retriev': 3},
        corpus_size=100
    )
    print(f"   BM25 Score: {score:.4f}")
    
    # Test PRF
    print("\n3. Testing Pseudo-Relevance Feedback...")
    expanded = engine.pseudo_relevance_feedback(
        query="information retrieval",
        top_docs_texts=[
            "Information retrieval is finding relevant documents in a collection.",
            "Search engines use retrieval models like BM25 and TF-IDF.",
            "Query expansion improves retrieval effectiveness."
        ]
    )
    print(f"   Original query: information retrieval")
    print(f"   Expanded query: {expanded}")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
