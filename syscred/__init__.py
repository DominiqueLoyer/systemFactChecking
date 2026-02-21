# -*- coding: utf-8 -*-
"""
SysCRED - Système Neuro-Symbolique de Vérification de Crédibilité
===================================================================

PhD Thesis Prototype - (c) Dominique S. Loyer
Citation Key: loyerModelingHybridSystem2025

Modules:
- api_clients: Web scraping, WHOIS, Fact Check APIs
- ir_engine: BM25, QLD, TF-IDF, PRF (from TREC)
- trec_retriever: Evidence retrieval for fact-checking (v2.3)
- trec_dataset: TREC AP88-90 data loader (v2.3)
- liar_dataset: LIAR benchmark dataset loader (v2.3)
- seo_analyzer: SEO analysis, PageRank estimation
- eval_metrics: MAP, NDCG, P@K, Recall, MRR
- ontology_manager: RDFLib integration
- verification_system: Main credibility pipeline
- graph_rag: GraphRAG for contextual memory (v2.3)
- ner_analyzer: Named Entity Recognition with spaCy (v2.4)
- eeat_calculator: Google E-E-A-T metrics (v2.4)
"""

__version__ = "2.4.0"
__author__ = "Dominique S. Loyer"
__citation__ = "loyerModelingHybridSystem2025"

# Core classes
from syscred.verification_system import CredibilityVerificationSystem
from syscred.api_clients import ExternalAPIClients
from syscred.ontology_manager import OntologyManager
from syscred.seo_analyzer import SEOAnalyzer
from syscred.ir_engine import IREngine
from syscred.eval_metrics import EvaluationMetrics
from syscred.graph_rag import GraphRAG

# NER and E-E-A-T (NEW - v2.4)
from syscred.ner_analyzer import NERAnalyzer
from syscred.eeat_calculator import EEATCalculator, EEATScore

# TREC Integration (v2.3)
from syscred.trec_retriever import TRECRetriever, Evidence, RetrievalResult
from syscred.trec_dataset import TRECDataset, TRECTopic

# LIAR Benchmark (v2.3)
from syscred.liar_dataset import LIARDataset, LiarStatement, LiarLabel

# Convenience alias
SysCRED = CredibilityVerificationSystem

__all__ = [
    # Core
    'CredibilityVerificationSystem',
    'SysCRED',
    'ExternalAPIClients',
    'OntologyManager',
    'SEOAnalyzer',
    'IREngine',
    'EvaluationMetrics',
    'GraphRAG',
    # NER & E-E-A-T (NEW v2.4)
    'NERAnalyzer',
    'EEATCalculator',
    'EEATScore',
    # TREC (v2.3)
    'TRECRetriever',
    'TRECDataset',
    'TRECTopic',
    'Evidence',
    'RetrievalResult',
    # LIAR Benchmark (v2.3)
    'LIARDataset',
    'LiarStatement',
    'LiarLabel',
]
