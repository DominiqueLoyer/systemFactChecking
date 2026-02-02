#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔬 SysCRED TREC DEMONSTRATION
==============================
Démonstration des capacités TREC intégrées dans SysCRED.
"""

import sys
import time

def main():
    print("=" * 70)
    print("🔬 SysCRED TREC DEMONSTRATION - Localhost")
    print("=" * 70)
    print()

    # 1. Import des modules TREC (direct, sans charger les modèles ML)
    print("📦 1. Chargement des modules TREC...")
    import sys
    sys.path.insert(0, '.')
    
    # Import direct pour éviter le chargement des modèles ML
    from syscred.trec_retriever import TRECRetriever, Evidence
    from syscred.trec_dataset import TRECDataset, TRECTopic
    from syscred.eval_metrics import EvaluationMetrics
    from syscred.ir_engine import IREngine
    
    # Sample topics définis localement
    SAMPLE_TOPICS = {
        "51": TRECTopic(
            topic_id="51",
            title="Airbus Subsidies",
            description="How much government money has been used to support Airbus?",
            narrative="A relevant document discusses subsidies to Airbus."
        ),
        "52": TRECTopic(
            topic_id="52", 
            title="Smoking bans",
            description="What are the effects of smoking bans in public places?",
            narrative="Relevant documents discuss smoking restrictions."
        ),
        "53": TRECTopic(
            topic_id="53",
            title="Endangered species",
            description="What species are currently endangered?",
            narrative="Documents about endangered wildlife."
        ),
    }
    
    print("   ✅ Tous les modules chargés avec succès!")
    print()

    # 2. Initialisation du retriever
    print("🔧 2. Initialisation du TRECRetriever...")
    retriever = TRECRetriever(use_stemming=True, enable_prf=False)
    print("   ✅ Retriever initialisé (mode in-memory, stemming=True)")
    print()

    # 3. Ajout d'un corpus de démonstration
    print("📚 3. Création d'un corpus de démonstration (style AP88-90)...")
    retriever.corpus = {
        "AP880101-0001": {
            "text": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels which release greenhouse gases into the atmosphere.",
            "title": "Climate Science Report"
        },
        "AP880101-0002": {
            "text": "The Earth's temperature has risen significantly over the past century due to greenhouse gas emissions from industrial activities and deforestation.",
            "title": "Global Warming Study"
        },
        "AP880102-0001": {
            "text": "Scientists warn that sea levels could rise dramatically if current warming trends continue, threatening coastal cities worldwide.",
            "title": "Sea Level Warning"
        },
        "AP890215-0001": {
            "text": "The presidential election campaign focused on economic policies, healthcare reform, and national security issues.",
            "title": "Election Coverage"
        },
        "AP890216-0001": {
            "text": "Stock markets rose sharply after positive economic indicators were released by the Federal Reserve, signaling economic recovery.",
            "title": "Financial News"
        },
    }
    print(f"   ✅ Corpus chargé: {len(retriever.corpus)} documents")
    for doc_id, doc in retriever.corpus.items():
        print(f"      - {doc_id}: {doc['title']}")
    print()

    # 4. Démonstration de récupération d'évidences
    print("=" * 70)
    print("🔍 4. DÉMONSTRATION: Récupération d'évidences pour un claim")
    print("=" * 70)
    print()
    
    claims = [
        "Climate change is caused by human activities",
        "The stock market is influenced by economic indicators",
        "Sea levels are rising due to global warming"
    ]
    
    for i, claim in enumerate(claims, 1):
        print(f"   📝 Claim #{i}: \"{claim}\"")
        print()
        
        result = retriever.retrieve_evidence(claim=claim, k=3)
        
        print(f"   ⏱️  Temps de recherche: {result.search_time_ms:.2f} ms")
        print(f"   📊 Résultats trouvés: {result.total_retrieved}")
        print()
        
        for evidence in result.evidences:
            print(f"      Rank {evidence.rank} | Score: {evidence.score:.4f}")
            print(f"      📄 Doc: {evidence.doc_id}")
            print(f"      📝 {evidence.text[:80]}...")
            print()
        
        print("-" * 70)
        print()

    # 5. Démonstration des métriques IR
    print("=" * 70)
    print("📊 5. DÉMONSTRATION: Métriques d'évaluation IR")
    print("=" * 70)
    print()
    
    metrics = EvaluationMetrics()
    
    # Simulation d'un run TREC
    retrieved = ["AP880101-0001", "AP890215-0001", "AP880101-0002", "AP880102-0001", "AP890216-0001"]
    relevant = {"AP880101-0001", "AP880101-0002", "AP880102-0001"}  # Documents sur le climat
    
    print("   📋 Simulation d'évaluation TREC:")
    print(f"      Documents récupérés: {retrieved}")
    print(f"      Documents pertinents: {relevant}")
    print()
    
    p_at_3 = metrics.precision_at_k(retrieved, relevant, k=3)
    p_at_5 = metrics.precision_at_k(retrieved, relevant, k=5)
    r_at_5 = metrics.recall_at_k(retrieved, relevant, k=5)
    ap = metrics.average_precision(retrieved, relevant)
    rr = metrics.reciprocal_rank(retrieved, relevant)
    
    print("   📈 Métriques calculées:")
    print(f"      • P@3 (Precision at 3):     {p_at_3:.4f}")
    print(f"      • P@5 (Precision at 5):     {p_at_5:.4f}")
    print(f"      • R@5 (Recall at 5):        {r_at_5:.4f}")
    print(f"      • AP (Average Precision):  {ap:.4f}")
    print(f"      • RR (Reciprocal Rank):    {rr:.4f}")
    print()

    # 6. Démonstration des topics TREC
    print("=" * 70)
    print("📋 6. DÉMONSTRATION: Topics TREC (AP88-90 samples)")
    print("=" * 70)
    print()
    
    print(f"   📚 {len(SAMPLE_TOPICS)} topics échantillons disponibles:")
    print()
    for topic_id, topic in list(SAMPLE_TOPICS.items())[:3]:
        print(f"   Topic {topic_id}:")
        print(f"      Title: {topic.title}")
        print(f"      Description: {topic.description[:60]}...")
        print()

    # 7. Démonstration du préprocesseur IR
    print("=" * 70)
    print("🔤 7. DÉMONSTRATION: Préprocesseur IR (stemming + stopwords)")
    print("=" * 70)
    print()
    
    engine = IREngine(use_stemming=True)
    
    test_texts = [
        "The quick brown fox jumps over the lazy dog",
        "Climate change is affecting global temperatures",
        "Information Retrieval systems are important"
    ]
    
    for text in test_texts:
        processed = engine.preprocess(text)
        print(f"   Original:  \"{text}\"")
        print(f"   Processed: \"{processed}\"")
        print()

    # 8. Statistiques finales
    print("=" * 70)
    print("📊 8. Statistiques du retriever")
    print("=" * 70)
    print()
    
    stats = retriever.get_statistics()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    print()

    print("=" * 70)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 70)
    print()
    print("Les modules TREC sont prêts pour l'intégration fact-checking!")
    print("Lancez le serveur avec: python -m syscred.backend_app")
    print()


if __name__ == "__main__":
    main()
