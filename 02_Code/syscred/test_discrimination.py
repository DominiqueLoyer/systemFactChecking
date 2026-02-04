#!/usr/bin/env python3
"""Test de discrimination entre textes fiables et suspects."""

from verification_system import CredibilityVerificationSystem

system = CredibilityVerificationSystem(load_ml_models=False)

print('=== TESTS DE DISCRIMINATION ===')
print()

tests = [
    ('Texte neutre', 'Scientists published a study in Nature journal about climate patterns.'),
    ('Source fiable citée', 'According to the WHO, vaccination rates have increased by 15% globally.'),
    ('Sensationnaliste léger', 'BREAKING: Amazing new discovery by scientists!'),
    ('Sensationnaliste fort', 'SHOCKING EXCLUSIVE: Secret conspiracy revealed about vaccines!'),
    ('Très suspect', 'URGENT BREAKTHROUGH: Miracle cure hidden by Big Pharma conspiracy!'),
]

print(f"{'Test':25} -> {'Score':8} {'Niveau':15}")
print("-" * 55)

for name, text in tests:
    result = system.verify_information(text)
    score = result.get('scoreCredibilite', 0)
    niveau = result.get('niveauCredibilite', 'N/A')
    print(f'{name:25} -> {score:.2f}     {niveau}')

print()
print('=== TESTS AVEC URLS ===')
print()

urls = [
    ('Le Monde', 'https://www.lemonde.fr/international/article/2024/test'),
    ('CNN', 'https://www.cnn.com/2024/01/15/politics/election-news'),
    ('Site suspect', 'https://breaking-news-exclusive.xyz/conspiracy'),
]

for name, url in urls:
    result = system.verify_information(url)
    score = result.get('scoreCredibilite', 0)
    niveau = result.get('niveauCredibilite', 'N/A')
    print(f'{name:25} -> {score:.2f}     {niveau}')
