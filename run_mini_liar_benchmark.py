#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Benchmark LIAR (Mode Light)
=================================
Teste SysCRED sur un échantillon du dataset LIAR sans ML.
Utilise uniquement les heuristiques et règles symboliques.

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import sys
import os
import time
import random
from collections import Counter

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '02_Code/syscred'))

from liar_dataset import LIARDataset, LiarStatement, LiarLabel

# ============================================
# HEURISTIQUES SIMPLES (Sans ML)
# ============================================

# Mots indicateurs de désinformation
FAKE_INDICATORS = [
    "hoax", "fake", "conspiracy", "unbelievable", "shocking",
    "they don't want you to know", "secret", "cover up", "scam",
    "miracle", "cure", "100%", "guaranteed", "never before",
    "breaking:", "exposed", "bombshell"
]

# Mots indicateurs de sources fiables
CREDIBLE_INDICATORS = [
    "according to", "research shows", "study found", "data indicates",
    "scientists say", "experts", "report", "analysis", "percent",
    "university", "institute", "published"
]

# Sources connues fiables
CREDIBLE_SPEAKERS = [
    "barack-obama", "hillary-clinton", "john-boehner", "nancy-pelosi"
]

# Sources à faible crédibilité historique
LOW_CRED_SOURCES = [
    "chain-email", "bloggers", "viral-image", "facebook-posts"
]


def analyze_statement_heuristic(stmt: LiarStatement) -> dict:
    """
    Analyse une déclaration avec des heuristiques simples.
    Retourne un score de 0.0 à 1.0.
    """
    text = stmt.statement.lower()
    
    # Scores partiels
    fake_score = 0.0
    cred_score = 0.0
    
    # 1. Détecter les indicateurs de fake news
    for indicator in FAKE_INDICATORS:
        if indicator in text:
            fake_score += 0.15
    
    # 2. Détecter les indicateurs de crédibilité
    for indicator in CREDIBLE_INDICATORS:
        if indicator in text:
            cred_score += 0.1
    
    # 3. Analyser le speaker
    speaker = stmt.speaker.lower() if stmt.speaker else ""
    if speaker in LOW_CRED_SOURCES:
        fake_score += 0.3
    elif speaker in CREDIBLE_SPEAKERS:
        cred_score += 0.15
    
    # 4. Présence de nombres (signe de factualité)
    import re
    if re.search(r'\d+\.?\d*%?', text):
        cred_score += 0.1
    
    # 5. Longueur (les vrais énoncés sont souvent plus détaillés)
    if len(text) > 150:
        cred_score += 0.05
    
    # 6. Ponctuation excessive (indicateur de sensationnalisme)
    if text.count('!') > 1 or text.count('?') > 2:
        fake_score += 0.1
    
    # Calcul du score final (0.5 = neutre)
    base_score = 0.5
    final_score = base_score + cred_score - fake_score
    final_score = max(0.0, min(1.0, final_score))
    
    return {
        'score': final_score,
        'fake_indicators': fake_score,
        'cred_indicators': cred_score,
        'predicted_binary': 'Real' if final_score >= 0.5 else 'Fake'
    }


def run_mini_benchmark(sample_size: int = 100):
    """Exécute un mini-benchmark sur un échantillon."""
    
    print("=" * 60)
    print("🧪 SysCRED - Mini Benchmark LIAR (Mode Light)")
    print("=" * 60)
    
    # Charger le dataset
    dataset_path = os.path.join(os.path.dirname(__file__), '02_Code/syscred/datasets/liar')
    ds = LIARDataset(dataset_path)
    test_data = ds.load_split('test')
    
    # Échantillon aléatoire
    sample = random.sample(test_data, min(sample_size, len(test_data)))
    print(f"\n📊 Benchmark sur {len(sample)} déclarations\n")
    
    # Résultats
    results = []
    correct_binary = 0
    
    start_time = time.time()
    
    for i, stmt in enumerate(sample):
        analysis = analyze_statement_heuristic(stmt)
        
        is_correct = analysis['predicted_binary'] == stmt.binary_label
        if is_correct:
            correct_binary += 1
        
        results.append({
            'id': stmt.id,
            'statement': stmt.statement[:60],
            'ground_truth': stmt.binary_label,
            'predicted': analysis['predicted_binary'],
            'score': analysis['score'],
            'correct': is_correct
        })
        
        # Afficher quelques exemples
        if i < 5:
            emoji = "✅" if is_correct else "❌"
            print(f"{emoji} [{stmt.binary_label:4s}→{analysis['predicted_binary']:4s}] {stmt.statement[:50]}...")
            print(f"   Score: {analysis['score']:.2f}")
    
    elapsed = time.time() - start_time
    
    # Calcul des métriques
    accuracy = correct_binary / len(sample) * 100
    
    # Métriques par classe
    true_positives = sum(1 for r in results if r['ground_truth'] == 'Fake' and r['predicted'] == 'Fake')
    false_positives = sum(1 for r in results if r['ground_truth'] == 'Real' and r['predicted'] == 'Fake')
    false_negatives = sum(1 for r in results if r['ground_truth'] == 'Fake' and r['predicted'] == 'Real')
    true_negatives = sum(1 for r in results if r['ground_truth'] == 'Real' and r['predicted'] == 'Real')
    
    precision_fake = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall_fake = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_fake = 2 * precision_fake * recall_fake / (precision_fake + recall_fake) if (precision_fake + recall_fake) > 0 else 0
    
    # Afficher les résultats
    print("\n" + "=" * 60)
    print("📈 RÉSULTATS DU BENCHMARK")
    print("=" * 60)
    
    print(f"\n📊 Métriques globales:")
    print(f"   Accuracy:     {accuracy:.1f}%")
    print(f"   Correct:      {correct_binary}/{len(sample)}")
    print(f"   Temps total:  {elapsed:.2f}s")
    print(f"   Temps/stmt:   {elapsed/len(sample)*1000:.1f}ms")
    
    print(f"\n📊 Métriques pour classe 'Fake':")
    print(f"   Precision:    {precision_fake:.2f}")
    print(f"   Recall:       {recall_fake:.2f}")
    print(f"   F1-Score:     {f1_fake:.2f}")
    
    print(f"\n📊 Matrice de confusion:")
    print(f"                  Prédit")
    print(f"                  Fake    Real")
    print(f"   Réel  Fake     {true_positives:4d}    {false_negatives:4d}")
    print(f"         Real     {false_positives:4d}    {true_negatives:4d}")
    
    # Analyse des erreurs
    print(f"\n📊 Analyse des erreurs:")
    errors = [r for r in results if not r['correct']]
    print(f"   Total erreurs: {len(errors)}")
    
    if errors:
        print("\n   Exemples d'erreurs:")
        for err in errors[:5]:
            print(f"   - [{err['ground_truth']}→{err['predicted']}] {err['statement']}")
    
    # Baseline comparaison
    print(f"\n📊 Comparaison avec baseline:")
    print(f"   Random guess:  50.0%")
    print(f"   Majority vote: {max(sum(1 for s in sample if s.binary_label=='Real'), sum(1 for s in sample if s.binary_label=='Fake'))/len(sample)*100:.1f}%")
    print(f"   SysCRED (light): {accuracy:.1f}%")
    
    improvement = accuracy - 50.0
    print(f"\n   ⭐ Amélioration vs random: +{improvement:.1f}%")
    
    return {
        'accuracy': accuracy,
        'precision_fake': precision_fake,
        'recall_fake': recall_fake,
        'f1_fake': f1_fake,
        'sample_size': len(sample)
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=200, help='Taille de l\'échantillon')
    args = parser.parse_args()
    
    run_mini_benchmark(args.sample)
