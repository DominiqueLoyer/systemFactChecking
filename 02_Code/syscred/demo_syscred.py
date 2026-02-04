#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SysCRED v2.3 - Script de Démonstration
========================================
Ce script montre les capacités du système de vérification de crédibilité.

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import sys
import os

# Add paths for imports (support both syscred package and local imports)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

def main():
    print("=" * 70)
    print("         SysCRED v2.3 - DÉMONSTRATION DU SYSTÈME")
    print("=" * 70)
    
    # Test 1: Afficher les composants disponibles
    print()
    print("📦 COMPOSANTS DU SYSTÈME:")
    print("-" * 40)
    
    try:
        # Try syscred package first, then local imports
        try:
            import syscred
            version = syscred.__version__
            author = syscred.__author__
            citation = syscred.__citation__
            all_modules = syscred.__all__
        except ImportError:
            # Local imports
            from __init__ import __version__, __author__, __citation__, __all__
            version = __version__
            author = __author__
            citation = __citation__
            all_modules = __all__
        
        print(f"   Version: {version}")
        print(f"   Auteur: {author}")
        print(f"   Citation: {citation}")
        print(f"   Modules exportés:")
        for m in all_modules:
            print(f"      - {m}")
    except Exception as e:
        print(f"   Erreur: {e}")
        print("   (Utilisation des imports locaux)")
    
    # Test 2: Initialiser le système (mode léger sans ML)
    print()
    print("🔧 INITIALISATION (mode léger sans ML):")
    print("-" * 40)
    
    try:
        try:
            from syscred import CredibilityVerificationSystem
        except ImportError:
            from verification_system import CredibilityVerificationSystem
        system = CredibilityVerificationSystem(load_ml_models=False)
        print("   ✓ Système initialisé avec succès!")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        system = None
    
    # Test 3: Test de prétraitement de texte
    if system:
        print()
        print("📝 TEST DE PRÉTRAITEMENT:")
        print("-" * 40)
        samples = [
            "COVID-19 vaccine is 95% effective according to WHO!",
            "BREAKING: Scientists discover SHOCKING truth about climate!",
            "According to Reuters, the study was peer-reviewed."
        ]
        for sample in samples:
            processed = system.preprocess(sample)
            print(f"   Original: {sample[:50]}...")
            print(f"   Traité:   {processed[:50]}...")
            print()
    
    # Test 4: Test du TREC Retriever
    print()
    print("🔍 TEST TREC RETRIEVER (Evidence Retrieval):")
    print("-" * 40)
    
    try:
        try:
            from syscred import TRECRetriever
        except ImportError:
            from trec_retriever import TRECRetriever
        retriever = TRECRetriever(use_stemming=True, enable_prf=False)
        
        # Ajouter un corpus de test
        retriever.corpus = {
            "DOC001": {"text": "Climate change is caused by human activities and greenhouse gas emissions.", "title": "Climate Science"},
            "DOC002": {"text": "The Earth temperature has risen significantly due to industrial pollution.", "title": "Global Warming"},
            "DOC003": {"text": "Vaccination is the most effective way to prevent infectious diseases.", "title": "Health Report"},
            "DOC004": {"text": "Scientists confirm that carbon dioxide levels are at record highs.", "title": "CO2 Report"},
            "DOC005": {"text": "The Paris Agreement aims to limit global warming to 1.5 degrees Celsius.", "title": "Paris Agreement"},
        }
        
        # Test de recherche
        query = "Climate change human activity"
        result = retriever.retrieve_evidence(query, k=3)
        
        print(f"   Query: '{query}'")
        print(f"   Modèle: {result.model_used}")
        print(f"   Résultats trouvés: {result.total_retrieved}")
        print(f"   Temps de recherche: {result.search_time_ms:.2f} ms")
        print()
        print("   📄 Évidences récupérées:")
        for e in result.evidences:
            print(f"      Rank {e.rank}: [{e.score:.4f}] {e.text[:60]}...")
        
        print()
        print("   ✓ TREC Retriever fonctionne correctement!")
        
    except Exception as e:
        print(f"   ✗ Erreur TREC: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Test des métriques d'évaluation
    print()
    print("📊 TEST DES MÉTRIQUES D'ÉVALUATION (IR):")
    print("-" * 40)
    
    try:
        try:
            from syscred import EvaluationMetrics
        except ImportError:
            from eval_metrics import EvaluationMetrics
        metrics = EvaluationMetrics()
        
        # Données de test
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc5"}
        
        p5 = metrics.precision_at_k(retrieved, relevant, 5)
        r5 = metrics.recall_at_k(retrieved, relevant, 5)
        ap = metrics.average_precision(retrieved, relevant)
        rr = metrics.reciprocal_rank(retrieved, relevant)
        
        print(f"   Documents récupérés: {retrieved}")
        print(f"   Documents pertinents: {relevant}")
        print()
        print(f"   P@5:  {p5:.4f} (Précision à 5)")
        print(f"   R@5:  {r5:.4f} (Rappel à 5)")
        print(f"   AP:   {ap:.4f} (Average Precision)")
        print(f"   MRR:  {rr:.4f} (Mean Reciprocal Rank)")
        print()
        print("   ✓ Métriques calculées correctement!")
        
    except Exception as e:
        print(f"   ✗ Erreur Métriques: {e}")
    
    # Test 6: Test du TRECDataset
    print()
    print("📚 TEST TREC DATASET (Loader):")
    print("-" * 40)
    
    try:
        try:
            from syscred import TRECDataset, TRECTopic
            from syscred.trec_dataset import SAMPLE_TOPICS
        except ImportError:
            from trec_dataset import TRECDataset, TRECTopic, SAMPLE_TOPICS
        dataset = TRECDataset()
        
        # Utiliser les topics exemples
        dataset.topics = SAMPLE_TOPICS.copy()
        
        print(f"   Topics chargés: {len(dataset.topics)}")
        print()
        print("   📋 Exemples de topics:")
        for tid, topic in list(dataset.topics.items())[:3]:
            print(f"      Topic {tid}: {topic.title}")
            print(f"         Desc: {topic.description[:50]}...")
        
        print()
        print("   ✓ TRECDataset fonctionne correctement!")
        
    except Exception as e:
        print(f"   ✗ Erreur Dataset: {e}")
    
    # Résumé final
    print()
    print("=" * 70)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 70)
    print()
    print("🏗️  ARCHITECTURE SysCRED v2.3:")
    print()
    print("   ┌─────────────────────────────────────────────────────┐")
    print("   │              SysCRED - Fact Checking                │")
    print("   ├─────────────────────────────────────────────────────┤")
    print("   │                                                     │")
    print("   │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │")
    print("   │  │ Neural    │  │ Symbolic  │  │ TREC IR       │   │")
    print("   │  │ (BERT)    │  │ (Ontology)│  │ (BM25/QLD)    │   │")
    print("   │  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘   │")
    print("   │        │              │                │           │")
    print("   │        └──────────────┼────────────────┘           │")
    print("   │                       ▼                            │")
    print("   │             ┌─────────────────┐                    │")
    print("   │             │ Credibility     │                    │")
    print("   │             │ Score (0-1)     │                    │")
    print("   │             └─────────────────┘                    │")
    print("   │                                                     │")
    print("   └─────────────────────────────────────────────────────┘")
    print()


if __name__ == "__main__":
    main()
