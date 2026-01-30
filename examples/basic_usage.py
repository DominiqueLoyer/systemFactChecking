#!/usr/bin/env python3
"""
Exemple d'utilisation basique de SysCRED
Système de Vérification de Crédibilité de l'Information

Auteur: Dominique S. Loyer
"""

from syscred import CredibilityVerificationSystem


def main():
    """Démonstration des fonctionnalités principales de SysCRED"""
    
    print("=" * 60)
    print("SysCRED - Système de Vérification de Crédibilité")
    print("=" * 60)
    
    # Initialiser le système
    print("\n📊 Initialisation du système...")
    system = CredibilityVerificationSystem()
    print("✅ Système initialisé avec succès!\n")
    
    # Exemple 1: Vérifier une URL
    print("=" * 60)
    print("Exemple 1: Vérification d'une URL")
    print("=" * 60)
    url = "https://www.bbc.com/news/world"
    print(f"URL à vérifier: {url}")
    
    result_url = system.verify_information(url)
    
    print(f"\n📈 Résultats:")
    print(f"  Score de crédibilité: {result_url['scoreCredibilite']:.2f}")
    print(f"  Niveau: {result_url['niveauCredibilite']}")
    
    if 'analysisDetails' in result_url:
        print(f"\n🔍 Détails de l'analyse:")
        details = result_url['analysisDetails']
        if 'sourceReputation' in details:
            print(f"  - Réputation de la source: {details['sourceReputation']}")
        if 'domainAge' in details:
            print(f"  - Âge du domaine: {details['domainAge']} jours")
        if 'sentiment' in details:
            print(f"  - Sentiment: {details['sentiment']['label']} ({details['sentiment']['score']:.2f})")
    
    # Exemple 2: Vérifier du texte
    print("\n" + "=" * 60)
    print("Exemple 2: Vérification de texte brut")
    print("=" * 60)
    
    text = (
        "According to a study published by Harvard researchers, "
        "the new methodology shows statistically significant results "
        "in improving information credibility assessment."
    )
    print(f"Texte à vérifier:\n{text}")
    
    result_text = system.verify_information(text)
    
    print(f"\n📈 Résultats:")
    print(f"  Score de crédibilité: {result_text['scoreCredibilite']:.2f}")
    print(f"  Niveau: {result_text['niveauCredibilite']}")
    
    if 'analysisDetails' in result_text:
        print(f"\n🔍 Détails de l'analyse:")
        details = result_text['analysisDetails']
        if 'entities' in details and details['entities']:
            print(f"  - Entités détectées: {len(details['entities'])}")
            for entity in details['entities'][:3]:  # Afficher max 3 entités
                print(f"    • {entity['word']} ({entity['entity_group']})")
    
    print("\n" + "=" * 60)
    print("✨ Démonstration terminée!")
    print("=" * 60)


if __name__ == "__main__":
    main()
