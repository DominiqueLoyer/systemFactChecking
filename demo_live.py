#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration Live SysCRED
"""

import sys
sys.path.insert(0, '02_Code/syscred')

from ontology_manager import OntologyManager
from graph_rag import GraphRAG

print('=' * 60)
print('🎯 DÉMONSTRATION LIVE - SysCRED avec GraphRAG')
print('=' * 60)

# Initialiser GraphRAG avec l'ontologie réelle
onto_path = '02_Code/sysCRED_onto26avrtil.ttl'
om = OntologyManager(onto_path)
rag = GraphRAG(om)

# === TEST 1: Source Connue ===
print('\n📰 Test 1: Analyse d\'une URL du Monde')
print('-' * 40)
context1 = rag.get_context('lemonde.fr')
print(f'Contexte GraphRAG: {str(context1)[:100]}...')

# === TEST 2: Source Inconnue ===
print('\n📰 Test 2: Analyse d\'une source inconnue')
print('-' * 40)
context2 = rag.get_context('site-inconnu.xyz')
print(f'Contexte (pas d\'historique): {str(context2)[:100]}...')

# === TEST 3: Patterns de Fake News ===
print('\n📰 Test 3: Détection patterns fake news')
print('-' * 40)
keywords = ['climate', 'hoax', 'conspiracy']
context3 = rag.get_context('example.com', keywords)
print(f'Contexte avec keywords: {str(context3)[:100]}...')

# === DEMO LIAR ===
print('\n' + '=' * 60)
print('📊 DÉMONSTRATION LIAR DATASET')
print('=' * 60)

from liar_dataset import LIARDataset, LiarLabel

dataset = LIARDataset()
test_data = dataset.load_split('test')

# Prendre 5 exemples variés
samples = [test_data[i] for i in [0, 100, 200, 300, 400]]

for stmt in samples:
    label = '✅' if stmt.binary_label == 'real' else '❌'
    print(f'\n{label} [{stmt.label.name}] {stmt.speaker}')
    print(f'   "{stmt.statement[:70]}..."')

print('\n' + '=' * 60)
print('✅ DÉMONSTRATION TERMINÉE')
print('=' * 60)
