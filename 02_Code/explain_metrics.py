#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to explain the IR metrics shown in the TREC Demo interface.
"""

from syscred.eval_metrics import EvaluationMetrics

print("=" * 60)
print("EXPLICATION DES METRIQUES IR - SysCRED TREC Demo")
print("=" * 60)
print()

# The demo shows these values:
# P@3 = 0.67, MAP = 0.81, MRR = 1.00

# This is the example used in the demo:
retrieved = ['AP880101-0001', 'AP890215-0001', 'AP880101-0002']
relevant = {'AP880101-0001', 'AP880101-0002', 'AP880102-0001'}

print("📋 Scenario de test:")
print(f"   Documents récupérés (top 3):")
print(f"     1. AP880101-0001 (Climate Science Report)")
print(f"     2. AP890215-0001 (Election Coverage) - NON pertinent")
print(f"     3. AP880101-0002 (Global Warming Study)")
print()
print(f"   Documents pertinents (ground truth):")
print(f"     - AP880101-0001 (Climate Science Report)")
print(f"     - AP880101-0002 (Global Warming Study)")
print(f"     - AP880102-0001 (Sea Level Warning)")
print()
print("-" * 60)

m = EvaluationMetrics()

# P@3
p3 = m.precision_at_k(retrieved, relevant, 3)
print(f"📊 P@3 (Precision at 3) = {p3:.4f}")
print(f"   → Sur les 3 documents récupérés, 2 sont pertinents")
print(f"   → P@3 = 2/3 = 0.6667")
print()

# MAP
ap = m.average_precision(retrieved, relevant)
print(f"📊 MAP (Mean Average Precision) = {ap:.4f}")
print(f"   → Rang 1 (AP880101-0001): pertinent → P@1 = 1/1 = 1.00")
print(f"   → Rang 2 (AP890215-0001): non pertinent → ignoré")
print(f"   → Rang 3 (AP880101-0002): pertinent → P@3 = 2/3 = 0.67")
print(f"   → AP = (1.00 + 0.67) / 2 = 0.8333")
print()

# MRR (using reciprocal_rank)
mrr = m.reciprocal_rank(retrieved, relevant)
print(f"📊 MRR (Mean Reciprocal Rank) = {mrr:.4f}")
print(f"   → Premier document pertinent au rang 1")
print(f"   → MRR = 1/1 = 1.00")
print()

# Recall
r3 = m.recall_at_k(retrieved, relevant, 3)
print(f"📊 R@3 (Recall at 3) = {r3:.4f}")
print(f"   → 2 documents pertinents trouvés sur 3 total pertinents")
print(f"   → R@3 = 2/3 = 0.6667")
print()

print("=" * 60)
print("✅ Ces métriques montrent que le système de recherche")
print("   fonctionne bien: le premier résultat est pertinent (MRR=1)")
print("   et 2/3 des résultats sont corrects (P@3=0.67)")
print("=" * 60)
