# SysCRED : Système d'Évaluation de Crédibilité Neuro-Symbolique

**Version 2.1 (Prototype de Thèse DIC-9411)**

## 1. Vue d'ensemble

SysCRED (**Sys**tem for **Cr**edibility **E**valuation) est une architecture hybride qui combine la puissance des modèles de langage (LLM - Système 1) avec la rigueur des graphes de connaissances (Ontologie - Système 2) pour combattre la désinformation.

Contrairement aux solutions purement statistiques ("Black Box"), SysCRED offre une **explicabilité by design** et une approche **Zero Trust** (Confiance Zéro) : une information est présumée non fiable tant que des preuves explicites ne sont pas trouvées.

---

## 2. Architecture Technique

Le système fonctionne en "Sandwich Cognitif" à 4 couches :

1. **Perception (Système 1 - Neuronal)**
    * Analyse sémantique (BERT) pour le sentiment et la cohérence.
    * Extraction d'entités (NER) et de relations.
2. **Enrichissement (Preuves Externes)**
    * API Google FactCheck Tools.
    * Analyse technique du domaine (WHOIS, Âge du domaine).
3. **Audit Symbolique (Système 2 - Le Juge)**
    * Moteur d'inférence logique (Règles Veto).
    * *Exemple* : Si `Source` ∈ `Blacklist` alors `Crédibilité` = 0.
4. **Traçabilité (Ontologie)**
    * Stockage de la décision dans un Knowledge Graph (RDF/Turtle).
    * Lien immuable : `Rapport` $\rightarrow$ `Preuve` $\rightarrow$ `Source`.

---

## 3. Structure du Projet (Consolidé)

```
systemFactChecking/
├── SysCRED_v2.1_Update/       # Code source principal (Python)
│   ├── verification_system.py # Point d'entrée principal
│   ├── api_clients.py         # Connecteurs (Google, WHOIS, Web)
│   ├── ontology_manager.py    # Gestionnaire du Graphe RDF
│   ├── config.py              # Configuration et Liste Noire/Blanche
│   └── static/                # Assets Web (JS/CSS)
├── presentation_2026/         # Présentation de Thèse (LaTeX)
│   ├── syscred_presentation.tex
│   └── references.bib
├── projetFinal_sysCred_Onto_28avril.ttl # Ontologie de base
└── syscred_legacy/            # Anciennes versions archivées
```

---

## 4. Installation et Démarrage

### Pré-requis

* Python 3.9+
* Clé API Google FactCheck (Optionnel, mode simulation dispo)

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/DominiqueLoyer/systemFactChecking.git
cd systemFactChecking

# 2. Installer les dépendances
pip install -r SysCRED_v2.1_Update/requirements.txt
# (Inclut: transformers, torch, rdflib, flask, beautifulsoup4)
```

### Lancer une vérification

```bash
cd SysCRED_v2.1_Update
python verification_system.py
```

*Le script lancera une série de tests sur des URL (Le Monde, Infowars, etc.) et affichera les rapports de crédibilité dans la console.*

---

## 5. Présentation Doctorale (LaTeX)

Le code source de la présentation est situé dans `presentation_2026/`.
Il inclut désormais un diagramme d'ontologie généré dynamiquement en **TikZ**.

**Pour compiler :**
Ouvrez `syscred_presentation.tex` avec votre éditeur LaTeX local (TeXnicle, TeXShop) et compilez.

---

## 6. Prochaines Étapes (Roadmap 2026)

* [ ] **Février** : Finalisation de l'intégration GraphRAG.
* [ ] **Mars** : Benchmark étendu sur le dataset LIAR.
* [ ] **Avril** : Dépôt officiel de la proposition de thèse.

---
*(c) 2026 Dominique S. Loyer - UQAM*
