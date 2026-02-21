# -*- coding: utf-8 -*-
"""
SysCRED - Système Neuro-Symbolique de Vérification de Crédibilité
===================================================================

PhD Thesis Prototype - (c) Dominique S. Loyer
Citation Key: loyerModelingHybridSystem2025

Modules:
- api_clients: Web scraping, WHOIS, Fact Check APIs
- ir_engine: BM25, QLD, TF-IDF, PRF (from TREC)
- seo_analyzer: SEO analysis, PageRank estimation
- eval_metrics: MAP, NDCG, P@K, Recall, MRR
- ontology_manager: RDFLib integration
- verification_system: Main credibility pipeline
"""

__version__ = "2.0.0"
__author__ = "Dominique S. Loyer"
__citation__ = "loyerModelingHybridSystem2025"

# Core classes
from syscred.verification_system import CredibilityVerificationSystem
from syscred.api_clients import ExternalAPIClients
from syscred.ontology_manager import OntologyManager
from syscred.seo_analyzer import SEOAnalyzer
from syscred.ir_engine import IREngine
from syscred.eval_metrics import EvaluationMetrics

# Convenience alias
SysCRED = CredibilityVerificationSystem

__all__ = [
    'CredibilityVerificationSystem',
    'SysCRED',
    'ExternalAPIClients',
    'OntologyManager',
    'SEOAnalyzer',
    'IREngine',
    'EvaluationMetrics',
]
