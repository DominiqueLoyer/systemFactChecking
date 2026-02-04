#!/usr/bin/env python3
"""Demo test for sysCRED light version (no PyTorch)."""

from verification_system import CredibilityVerificationSystem
from graph_rag import GraphRAG, OntologyManager

print('=== TEST VERSION LIGHT (sans PyTorch) ===')
print()

# Test 1: Vérifier URL connue
system = CredibilityVerificationSystem(load_ml_models=False)

print('\n--- Test 1: URL fiable (lemonde.fr) ---')
result = system.verify_information('https://www.lemonde.fr/sciences/article/2024/01/15/climate-research.html')
print(f"Score: {result.get('scoreCredibilite', 0):.2f}")
print(f"Niveau: {result.get('niveauCredibilite', 'N/A')}")

print('\n--- Test 2: Texte factuel avec source ---')
result = system.verify_information('According to NASA scientists, global temperatures have risen 1.2C since pre-industrial era.')
print(f"Score: {result.get('scoreCredibilite', 0):.2f}")
print(f"Niveau: {result.get('niveauCredibilite', 'N/A')}")

print('\n--- Test 3: Texte douteux ---')
result = system.verify_information('EXCLUSIVE: Scientists hide the truth about vaccines causing autism!!!')
print(f"Score: {result.get('scoreCredibilite', 0):.2f}")
print(f"Niveau: {result.get('niveauCredibilite', 'N/A')}")

print('\n✅ Version light fonctionne!')
