#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script: LIAR Dataset + GraphRAG
=====================================
Teste le benchmark LIAR et GraphRAG localement.
"""

import sys
import os

# Ajouter le chemin du module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '02_Code/syscred'))

print("=" * 60)
print("🧪 SysCRED - Test LIAR Dataset + GraphRAG")
print("=" * 60)

# ============================================
# 1. TEST LIAR DATASET
# ============================================
print("\n📊 1. Test LIAR Dataset")
print("-" * 40)

try:
    from liar_dataset import LIARDataset, LiarStatement, LiarLabel
    
    # Charger le dataset
    dataset_path = os.path.join(os.path.dirname(__file__), '02_Code/syscred/datasets/liar')
    ds = LIARDataset(dataset_path)
    
    # Charger les splits
    test_data = ds.load_split('test')
    train_data = ds.load_split('train')
    valid_data = ds.load_split('valid')
    
    print(f"✓ Train: {len(train_data)} statements")
    print(f"✓ Valid: {len(valid_data)} statements")
    print(f"✓ Test:  {len(test_data)} statements")
    print(f"✓ Total: {len(train_data) + len(valid_data) + len(test_data)} statements")
    
    # Afficher des exemples
    print("\n📋 Exemples du dataset LIAR:")
    for i, stmt in enumerate(test_data[:5]):
        label_emoji = "✅" if stmt.label.value >= 4 else "⚠️" if stmt.label.value >= 2 else "❌"
        print(f"\n{i+1}. {label_emoji} [{stmt.label.name}]")
        print(f"   Statement: {stmt.statement[:80]}...")
        print(f"   Speaker: {stmt.speaker} ({stmt.party or 'N/A'})")
        print(f"   Context: {stmt.context[:50]}..." if stmt.context else "   Context: N/A")
    
    # Distribution des labels
    print("\n📈 Distribution des labels (test set):")
    label_counts = {}
    for stmt in test_data:
        label_counts[stmt.label.name] = label_counts.get(stmt.label.name, 0) + 1
    
    for label, count in sorted(label_counts.items(), key=lambda x: LiarLabel[x[0]].value):
        pct = count / len(test_data) * 100
        bar = "█" * int(pct / 2)
        print(f"   {label:12s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    # Test conversion binaire
    print("\n🔄 Test conversion binaire:")
    fake_count = sum(1 for s in test_data if s.binary_label == "Fake")
    real_count = sum(1 for s in test_data if s.binary_label == "Real")
    print(f"   Fake: {fake_count} ({fake_count/len(test_data)*100:.1f}%)")
    print(f"   Real: {real_count} ({real_count/len(test_data)*100:.1f}%)")
    
    LIAR_OK = True
    
except Exception as e:
    print(f"❌ Erreur LIAR: {e}")
    import traceback
    traceback.print_exc()
    LIAR_OK = False

# ============================================
# 2. TEST GRAPHRAG
# ============================================
print("\n" + "=" * 60)
print("🧠 2. Test GraphRAG")
print("-" * 40)

try:
    from ontology_manager import OntologyManager
    from graph_rag import GraphRAG
    
    # Chercher le fichier ontologie
    onto_base = os.path.join(os.path.dirname(__file__), '02_Code', 'sysCRED_onto26avrtil.ttl')
    
    if os.path.exists(onto_base):
        print(f"✓ Ontologie trouvée: {onto_base}")
        om = OntologyManager(base_ontology_path=onto_base)
        graph_rag = GraphRAG(om)
        
        # Test get_context
        print("\n📍 Test get_context('lemonde.fr'):")
        context = graph_rag.get_context("lemonde.fr", keywords=["politique", "élection"])
        print(f"   Full text: {context.get('full_text', 'N/A')[:200]}...")
        
        # Test compute_context_score
        print("\n📍 Test compute_context_score('bbc.com'):")
        score_result = graph_rag.compute_context_score("bbc.com", keywords=["climate", "science"])
        print(f"   History score:  {score_result['history_score']:.2f}")
        print(f"   Pattern score:  {score_result['pattern_score']:.2f}")
        print(f"   Combined score: {score_result['combined_score']:.2f}")
        print(f"   Confidence:     {score_result['confidence']:.2f}")
        print(f"   Has history:    {score_result['has_history']}")
        
        # Test avec un domaine fictif douteux
        print("\n📍 Test compute_context_score('fake-news-site.com'):")
        score_result = graph_rag.compute_context_score("fake-news-site.com", keywords=["conspiracy"])
        print(f"   Combined score: {score_result['combined_score']:.2f} (devrait être 0.5 si pas d'historique)")
        print(f"   Confidence:     {score_result['confidence']:.2f}")
        
        GRAPHRAG_OK = True
    else:
        print(f"⚠️ Ontologie non trouvée à {onto_base}")
        print("   GraphRAG nécessite une ontologie de base")
        GRAPHRAG_OK = False
        
except Exception as e:
    print(f"❌ Erreur GraphRAG: {e}")
    import traceback
    traceback.print_exc()
    GRAPHRAG_OK = False

# ============================================
# RÉSUMÉ
# ============================================
print("\n" + "=" * 60)
print("📋 RÉSUMÉ")
print("=" * 60)
print(f"   LIAR Dataset: {'✅ OK' if LIAR_OK else '❌ ERREUR'}")
print(f"   GraphRAG:     {'✅ OK' if GRAPHRAG_OK else '❌ ERREUR'}")
print("=" * 60)
