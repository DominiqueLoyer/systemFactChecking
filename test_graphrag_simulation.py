#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphRAG avec données simulées
====================================
Ajoute des évaluations au Knowledge Graph et teste GraphRAG.

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import sys
import os
import tempfile

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '02_Code/syscred'))

from ontology_manager import OntologyManager
from graph_rag import GraphRAG

print("=" * 60)
print("🧠 Test GraphRAG avec Données Simulées")
print("=" * 60)

# ============================================
# 1. CRÉER UNE ONTOLOGIE TEMPORAIRE AVEC DONNÉES
# ============================================

# Ontologie de base avec quelques évaluations simulées
TEST_ONTOLOGY = """
@prefix cred: <https://github.com/DominiqueLoyer/systemFactChecking#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# === SOURCES ===
cred:LeMonde a cred:Source ;
    cred:sourceURL "https://www.lemonde.fr" ;
    cred:sourceName "Le Monde" ;
    cred:sourceType cred:QualityJournalism .

cred:BBC a cred:Source ;
    cred:sourceURL "https://www.bbc.com" ;
    cred:sourceName "BBC" ;
    cred:sourceType cred:QualityJournalism .

cred:Infowars a cred:Source ;
    cred:sourceURL "https://www.infowars.com" ;
    cred:sourceName "Infowars" ;
    cred:sourceType cred:ConspiracySite .

# === ÉVALUATIONS PASSÉES ===

# Le Monde - 3 évaluations positives
cred:Info1 a cred:Information ;
    cred:informationURL "https://www.lemonde.fr/article1" ;
    cred:informationContent "Les élections présidentielles de 2022 ont vu une participation record." .

cred:Request1 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info1 .

cred:Report1 a cred:CredibilityReport ;
    cred:isReportOf cred:Request1 ;
    cred:credibilityScoreValue "0.85"^^xsd:float ;
    cred:assignsCredibilityLevel cred:HighCredibility ;
    cred:completionTimestamp "2025-12-01T10:00:00"^^xsd:dateTime .

cred:Info2 a cred:Information ;
    cred:informationURL "https://www.lemonde.fr/article2" ;
    cred:informationContent "Le changement climatique s'accélère selon les scientifiques." .

cred:Request2 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info2 .

cred:Report2 a cred:CredibilityReport ;
    cred:isReportOf cred:Request2 ;
    cred:credibilityScoreValue "0.90"^^xsd:float ;
    cred:assignsCredibilityLevel cred:HighCredibility ;
    cred:completionTimestamp "2025-12-15T14:30:00"^^xsd:dateTime .

cred:Info3 a cred:Information ;
    cred:informationURL "https://www.lemonde.fr/article3" ;
    cred:informationContent "La réforme des retraites suscite des manifestations." .

cred:Request3 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info3 .

cred:Report3 a cred:CredibilityReport ;
    cred:isReportOf cred:Request3 ;
    cred:credibilityScoreValue "0.82"^^xsd:float ;
    cred:assignsCredibilityLevel cred:HighCredibility ;
    cred:completionTimestamp "2026-01-10T09:00:00"^^xsd:dateTime .

# Infowars - 2 évaluations négatives
cred:Info4 a cred:Information ;
    cred:informationURL "https://www.infowars.com/article1" ;
    cred:informationContent "Conspiracy about government control through vaccines." .

cred:Request4 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info4 .

cred:Report4 a cred:CredibilityReport ;
    cred:isReportOf cred:Request4 ;
    cred:credibilityScoreValue "0.15"^^xsd:float ;
    cred:assignsCredibilityLevel cred:LowCredibility ;
    cred:completionTimestamp "2025-11-20T16:00:00"^^xsd:dateTime .

cred:Info5 a cred:Information ;
    cred:informationURL "https://www.infowars.com/article2" ;
    cred:informationContent "Secret plot to control the weather exposed." .

cred:Request5 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info5 .

cred:Report5 a cred:CredibilityReport ;
    cred:isReportOf cred:Request5 ;
    cred:credibilityScoreValue "0.10"^^xsd:float ;
    cred:assignsCredibilityLevel cred:LowCredibility ;
    cred:completionTimestamp "2025-12-05T11:00:00"^^xsd:dateTime .

# === CLAIMS SIMILAIRES (pour pattern matching) ===
cred:Info6 a cred:Information ;
    cred:informationURL "https://factcheck.org/climate" ;
    cred:informationContent "Climate change fake hoax conspiracy scientists lie." .

cred:Request6 a cred:VerificationRequest ;
    cred:concernsInformation cred:Info6 .

cred:Report6 a cred:CredibilityReport ;
    cred:isReportOf cred:Request6 ;
    cred:credibilityScoreValue "0.20"^^xsd:float ;
    cred:assignsCredibilityLevel cred:LowCredibility ;
    cred:completionTimestamp "2025-10-01T08:00:00"^^xsd:dateTime .
"""

# Sauvegarder dans un fichier temporaire
with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
    f.write(TEST_ONTOLOGY)
    temp_onto_path = f.name

print(f"\n✓ Ontologie créée: {temp_onto_path}")

# ============================================
# 2. INITIALISER GRAPHRAG
# ============================================

try:
    om = OntologyManager(base_ontology_path=temp_onto_path)
    graph_rag = GraphRAG(om)
    print(f"✓ GraphRAG initialisé avec {len(om.base_graph)} triples")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

# ============================================
# 3. TESTS GRAPHRAG
# ============================================

print("\n" + "=" * 60)
print("📊 Tests GraphRAG")
print("=" * 60)

# Test 1: Source avec historique positif (Le Monde)
print("\n🧪 Test 1: lemonde.fr (source fiable avec historique)")
print("-" * 40)
context = graph_rag.get_context("lemonde.fr", keywords=["élection", "politique"])
print(f"   Context:\n{context.get('full_text', 'N/A')}")

score = graph_rag.compute_context_score("lemonde.fr", keywords=["élection"])
print(f"\n   Scores:")
print(f"   - History score:  {score['history_score']:.2f} (attendu: ~0.85)")
print(f"   - Combined score: {score['combined_score']:.2f}")
print(f"   - Confidence:     {score['confidence']:.2f}")
print(f"   - History count:  {score['history_count']}")

# Test 2: Source avec historique négatif (Infowars)
print("\n🧪 Test 2: infowars.com (source non fiable)")
print("-" * 40)
context = graph_rag.get_context("infowars.com", keywords=["conspiracy"])
print(f"   Context:\n{context.get('full_text', 'N/A')}")

score = graph_rag.compute_context_score("infowars.com", keywords=["conspiracy", "hoax"])
print(f"\n   Scores:")
print(f"   - History score:  {score['history_score']:.2f} (attendu: ~0.12)")
print(f"   - Combined score: {score['combined_score']:.2f}")
print(f"   - Confidence:     {score['confidence']:.2f}")
print(f"   - Has history:    {score['has_history']}")

# Test 3: Source inconnue
print("\n🧪 Test 3: unknown-site.com (pas d'historique)")
print("-" * 40)
score = graph_rag.compute_context_score("unknown-site.com", keywords=["random"])
print(f"   Combined score: {score['combined_score']:.2f} (attendu: 0.50 neutre)")
print(f"   Confidence:     {score['confidence']:.2f} (attendu: 0.00)")
print(f"   Has history:    {score['has_history']}")

# Test 4: Pattern matching avec keywords "climate" et "hoax"
print("\n🧪 Test 4: Pattern matching (keywords: 'climate', 'hoax')")
print("-" * 40)
context = graph_rag.get_context("any-site.com", keywords=["climate", "hoax", "conspiracy"])
print(f"   Context:\n{context.get('full_text', 'N/A')}")

score = graph_rag.compute_context_score("any-site.com", keywords=["climate", "hoax"])
print(f"\n   Scores (basé sur patterns similaires):")
print(f"   - Pattern score:  {score['pattern_score']:.2f}")
print(f"   - Similar count:  {score['similar_count']}")

# ============================================
# 4. SIMULATION D'INTÉGRATION
# ============================================

print("\n" + "=" * 60)
print("🔗 Simulation d'Intégration dans le Score Final")
print("=" * 60)

# Pondérations v2.3.1
weights = {
    'source_reputation': 0.22,
    'domain_age': 0.08,
    'sentiment_neutrality': 0.13,
    'entity_presence': 0.13,
    'coherence': 0.12,
    'fact_check': 0.17,
    'graph_context': 0.15  # NOUVEAU
}

def simulate_score(domain, other_scores, keywords=[]):
    """Simule le calcul du score final avec GraphRAG."""
    
    # Obtenir le score GraphRAG
    graph_score = graph_rag.compute_context_score(domain, keywords)
    
    # Calculer le score pondéré
    weighted_score = (
        other_scores.get('source_reputation', 0.5) * weights['source_reputation'] +
        other_scores.get('domain_age', 0.5) * weights['domain_age'] +
        other_scores.get('sentiment_neutrality', 0.5) * weights['sentiment_neutrality'] +
        other_scores.get('entity_presence', 0.5) * weights['entity_presence'] +
        other_scores.get('coherence', 0.5) * weights['coherence'] +
        other_scores.get('fact_check', 0.5) * weights['fact_check'] +
        graph_score['combined_score'] * weights['graph_context']
    )
    
    return {
        'final_score': weighted_score,
        'graph_contribution': graph_score['combined_score'] * weights['graph_context'],
        'graph_raw': graph_score['combined_score']
    }

# Simulation 1: Article Le Monde
print("\n📰 Simulation: Article du Monde")
result = simulate_score(
    "lemonde.fr",
    {
        'source_reputation': 0.8,
        'domain_age': 0.9,
        'sentiment_neutrality': 0.6,
        'entity_presence': 0.7,
        'coherence': 0.8,
        'fact_check': 0.5
    },
    keywords=["politique"]
)
print(f"   Score final:      {result['final_score']:.3f}")
print(f"   GraphRAG brut:    {result['graph_raw']:.2f}")
print(f"   Contribution GR:  +{result['graph_contribution']:.3f} (15% du total)")

# Simulation 2: Article Infowars
print("\n📰 Simulation: Article Infowars")
result = simulate_score(
    "infowars.com",
    {
        'source_reputation': 0.2,
        'domain_age': 0.7,
        'sentiment_neutrality': 0.3,
        'entity_presence': 0.4,
        'coherence': 0.3,
        'fact_check': 0.1
    },
    keywords=["conspiracy"]
)
print(f"   Score final:      {result['final_score']:.3f}")
print(f"   GraphRAG brut:    {result['graph_raw']:.2f}")
print(f"   Contribution GR:  +{result['graph_contribution']:.3f} (pénalité)")

print("\n" + "=" * 60)
print("✅ Tests GraphRAG terminés!")
print("=" * 60)

# Cleanup
os.unlink(temp_onto_path)
