# -*- coding: utf-8 -*-
"""
TREC Retriever Module - SysCRED
================================
Information Retrieval component based on TREC AP88-90 methodology.

This module bridges the classic IR evaluation framework (TREC)
with the neuro-symbolic credibility verification system.

Features:
- BM25, TF-IDF, QLD scoring
- Pyserini/Lucene integration (optional)
- Evidence retrieval for fact-checking
- PRF (Pseudo-Relevance Feedback) query expansion

Based on: TREC_AP88-90_5juin2025.py
(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from syscred.ir_engine import IREngine, SearchResult, SearchResponse


@dataclass
class Evidence:
    """
    A piece of evidence retrieved for fact-checking.
    
    Represents a document or passage that can support or refute a claim.
    """
    doc_id: str
    text: str
    score: float
    rank: int
    source: str = ""
    retrieval_model: str = "bm25"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "score": round(self.score, 4),
            "rank": self.rank,
            "source": self.source,
            "model": self.retrieval_model
        }


@dataclass
class RetrievalResult:
    """Complete result from evidence retrieval."""
    query: str
    evidences: List[Evidence]
    total_retrieved: int
    search_time_ms: float
    model_used: str
    expanded_query: Optional[str] = None


class TRECRetriever:
    """
    TREC-style retriever for evidence gathering in fact-checking.
    
    This class wraps the IREngine to provide a fact-checking oriented
    interface for retrieving evidence documents.
    
    Usage:
        retriever = TRECRetriever(index_path="/path/to/lucene/index")
        result = retriever.retrieve_evidence("Climate change is caused by humans", k=10)
        for evidence in result.evidences:
            print(f"{evidence.rank}. [{evidence.score:.4f}] {evidence.text[:100]}...")
    """
    
    # Retrieval configuration
    DEFAULT_K = 10
    DEFAULT_MODEL = "bm25"
    
    # BM25 parameters (optimized on AP88-90)
    BM25_K1 = 0.9
    BM25_B = 0.4
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        corpus_path: Optional[str] = None,
        use_stemming: bool = True,
        enable_prf: bool = True,
        prf_top_docs: int = 3,
        prf_expansion_terms: int = 10
    ):
        """
        Initialize the TREC retriever.
        
        Args:
            index_path: Path to Lucene/Pyserini index (optional)
            corpus_path: Path to JSONL corpus for in-memory search
            use_stemming: Whether to apply Porter stemming
            enable_prf: Enable Pseudo-Relevance Feedback
            prf_top_docs: Number of top docs for PRF
            prf_expansion_terms: Number of expansion terms from PRF
        """
        self.index_path = index_path
        self.corpus_path = corpus_path
        self.enable_prf = enable_prf
        self.prf_top_docs = prf_top_docs
        self.prf_expansion_terms = prf_expansion_terms
        
        # Initialize IR engine
        self.ir_engine = IREngine(
            index_path=index_path,
            use_stemming=use_stemming
        )
        
        # In-memory corpus (for lightweight mode)
        self.corpus: Dict[str, Dict[str, str]] = {}
        if corpus_path and os.path.exists(corpus_path):
            self._load_corpus(corpus_path)
        
        # Statistics
        self.stats = {
            "queries_processed": 0,
            "total_search_time_ms": 0,
            "avg_results_per_query": 0
        }
        
        print(f"[TRECRetriever] Initialized with index={index_path}, stemming={use_stemming}")
    
    def _load_corpus(self, corpus_path: str):
        """Load JSONL corpus into memory for lightweight search."""
        print(f"[TRECRetriever] Loading corpus from {corpus_path}...")
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                for line in f:
                    doc = json.loads(line.strip())
                    self.corpus[doc['id']] = {
                        'text': doc.get('contents', doc.get('text', '')),
                        'title': doc.get('title', '')
                    }
            print(f"[TRECRetriever] Loaded {len(self.corpus)} documents")
        except Exception as e:
            print(f"[TRECRetriever] Failed to load corpus: {e}")
    
    def retrieve_evidence(
        self,
        claim: str,
        k: int = None,
        model: str = None,
        use_prf: bool = None
    ) -> RetrievalResult:
        """
        Retrieve evidence documents for a given claim.
        
        This is the main method for fact-checking integration.
        
        Args:
            claim: The claim or statement to verify
            k: Number of evidence documents to retrieve
            model: Retrieval model ('bm25', 'qld', 'tfidf')
            use_prf: Override PRF setting for this query
            
        Returns:
            RetrievalResult with list of Evidence objects
        """
        start_time = time.time()
        
        k = k or self.DEFAULT_K
        model = model or self.DEFAULT_MODEL
        use_prf = use_prf if use_prf is not None else self.enable_prf
        
        # Preprocess the claim
        processed_claim = self.ir_engine.preprocess(claim)
        
        # Try Pyserini first, fall back to in-memory
        if self.ir_engine.searcher:
            response = self._search_pyserini(processed_claim, model, k)
        else:
            response = self._search_in_memory(processed_claim, k)
        
        # Apply PRF if enabled
        expanded_query = None
        if use_prf and len(response.results) >= self.prf_top_docs:
            expanded_query = self._apply_prf(claim, response.results[:self.prf_top_docs])
            if expanded_query != claim:
                # Re-search with expanded query
                processed_expanded = self.ir_engine.preprocess(expanded_query)
                if self.ir_engine.searcher:
                    response = self._search_pyserini(processed_expanded, model, k)
                else:
                    response = self._search_in_memory(processed_expanded, k)
        
        # Convert to Evidence objects
        evidences = []
        for result in response.results:
            doc_text = self._get_document_text(result.doc_id)
            evidences.append(Evidence(
                doc_id=result.doc_id,
                text=doc_text,
                score=result.score,
                rank=result.rank,
                source="TREC-AP88-90" if "AP" in result.doc_id else "Unknown",
                retrieval_model=model
            ))
        
        search_time = (time.time() - start_time) * 1000
        
        # Update statistics
        self.stats["queries_processed"] += 1
        self.stats["total_search_time_ms"] += search_time
        
        return RetrievalResult(
            query=claim,
            evidences=evidences,
            total_retrieved=len(evidences),
            search_time_ms=search_time,
            model_used=model,
            expanded_query=expanded_query
        )
    
    def _search_pyserini(self, query: str, model: str, k: int) -> SearchResponse:
        """Search using Pyserini/Lucene."""
        return self.ir_engine.search_pyserini(
            query=query,
            model=model,
            k=k
        )
    
    def _search_in_memory(self, query: str, k: int) -> SearchResponse:
        """
        Lightweight in-memory BM25 search.
        
        Used when Pyserini is not available.
        """
        start_time = time.time()
        
        if not self.corpus:
            return SearchResponse(
                query_id="Q1",
                query_text=query,
                results=[],
                model="bm25_memory",
                total_hits=0,
                search_time_ms=0
            )
        
        query_terms = query.split()
        
        # Calculate document frequencies
        doc_freq = {}
        for term in query_terms:
            doc_freq[term] = sum(
                1 for doc in self.corpus.values() 
                if term in self.ir_engine.preprocess(doc['text'])
            )
        
        # Calculate average document length
        total_length = sum(
            len(self.ir_engine.preprocess(doc['text']).split())
            for doc in self.corpus.values()
        )
        avg_doc_length = total_length / len(self.corpus) if self.corpus else 1
        
        # Score all documents
        scores = []
        for doc_id, doc in self.corpus.items():
            doc_text = self.ir_engine.preprocess(doc['text'])
            doc_terms = doc_text.split()
            
            score = self.ir_engine.calculate_bm25_score(
                query_terms=query_terms,
                doc_terms=doc_terms,
                doc_length=len(doc_terms),
                avg_doc_length=avg_doc_length,
                doc_freq=doc_freq,
                corpus_size=len(self.corpus)
            )
            
            if score > 0:
                scores.append((doc_id, score))
        
        # Sort and take top k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_k = scores[:k]
        
        results = [
            SearchResult(doc_id=doc_id, score=score, rank=i+1)
            for i, (doc_id, score) in enumerate(top_k)
        ]
        
        return SearchResponse(
            query_id="Q1",
            query_text=query,
            results=results,
            model="bm25_memory",
            total_hits=len(results),
            search_time_ms=(time.time() - start_time) * 1000
        )
    
    def _apply_prf(self, original_query: str, top_results: List[SearchResult]) -> str:
        """Apply Pseudo-Relevance Feedback."""
        top_docs_texts = [
            self._get_document_text(r.doc_id)
            for r in top_results
        ]
        
        return self.ir_engine.pseudo_relevance_feedback(
            query=original_query,
            top_docs_texts=top_docs_texts,
            num_expansion_terms=self.prf_expansion_terms
        )
    
    def _get_document_text(self, doc_id: str) -> str:
        """Get document text from corpus or index."""
        if doc_id in self.corpus:
            return self.corpus[doc_id]['text']
        
        # Try Pyserini doc lookup
        if self.ir_engine.searcher:
            try:
                doc = self.ir_engine.searcher.doc(doc_id)
                if doc:
                    return doc.raw()
            except:
                pass
        
        return f"[Document {doc_id} text not available]"
    
    def batch_retrieve(
        self,
        claims: List[str],
        k: int = None,
        model: str = None
    ) -> List[RetrievalResult]:
        """
        Retrieve evidence for multiple claims.
        
        Useful for benchmark evaluation.
        """
        results = []
        for claim in claims:
            result = self.retrieve_evidence(claim, k=k, model=model)
            results.append(result)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        avg_time = 0
        if self.stats["queries_processed"] > 0:
            avg_time = self.stats["total_search_time_ms"] / self.stats["queries_processed"]
        
        return {
            "queries_processed": self.stats["queries_processed"],
            "total_search_time_ms": round(self.stats["total_search_time_ms"], 2),
            "avg_search_time_ms": round(avg_time, 2),
            "corpus_size": len(self.corpus),
            "has_pyserini_index": self.ir_engine.searcher is not None
        }


# --- Integration with VerificationSystem ---

def create_retriever_for_syscred(
    config: Optional[Any] = None
) -> TRECRetriever:
    """
    Factory function to create a TRECRetriever for SysCRED integration.
    
    Uses configuration from syscred.config if available.
    """
    index_path = None
    corpus_path = None
    
    if config:
        index_path = getattr(config, 'TREC_INDEX_PATH', None)
        corpus_path = getattr(config, 'TREC_CORPUS_PATH', None)
    
    # Try default paths
    default_corpus = Path(__file__).parent.parent / "benchmarks" / "ap_corpus.jsonl"
    if default_corpus.exists():
        corpus_path = str(default_corpus)
    
    return TRECRetriever(
        index_path=index_path,
        corpus_path=corpus_path,
        use_stemming=True,
        enable_prf=True
    )


# --- Testing ---

if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED TREC Retriever - Test Suite")
    print("=" * 60)
    
    # Initialize without index (in-memory mode)
    retriever = TRECRetriever(use_stemming=True, enable_prf=False)
    
    # Add some test documents to corpus
    retriever.corpus = {
        "DOC001": {"text": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels.", "title": "Climate Science"},
        "DOC002": {"text": "The Earth's temperature has risen significantly over the past century due to greenhouse gas emissions.", "title": "Global Warming"},
        "DOC003": {"text": "Natural climate variations have occurred throughout Earth's history.", "title": "Climate History"},
        "DOC004": {"text": "Renewable energy sources like solar and wind can help reduce carbon emissions.", "title": "Green Energy"},
        "DOC005": {"text": "Scientific consensus supports anthropogenic climate change theory.", "title": "IPCC Report"},
    }
    
    print("\n1. Testing evidence retrieval...")
    result = retriever.retrieve_evidence(
        claim="Climate change is caused by human activities",
        k=3
    )
    
    print(f"\n   Query: {result.query}")
    print(f"   Model: {result.model_used}")
    print(f"   Search time: {result.search_time_ms:.2f} ms")
    print(f"   Results found: {result.total_retrieved}")
    
    for evidence in result.evidences:
        print(f"\n   Rank {evidence.rank} [{evidence.score:.4f}]:")
        print(f"   {evidence.text[:100]}...")
    
    print("\n2. Testing batch retrieval...")
    claims = [
        "Climate change is real",
        "Renewable energy reduces emissions"
    ]
    batch_results = retriever.batch_retrieve(claims, k=2)
    print(f"   Processed {len(batch_results)} claims")
    
    print("\n3. Statistics:")
    stats = retriever.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
