# 📋 Journal de Publication - SysCRED v2.2.1

**Date**: 30 janvier 2026  
**Heure**: 18h30 EST  
**Objectif**: Publication du package Python sur PyPI et obtention d'un DOI Zenodo

---

## 🎯 Objectifs de la Session

1. Publier le package `syscred` version 2.2.1 sur PyPI
2. Obtenir un DOI académique via Zenodo
3. Mettre à jour la documentation GitHub avec les badges appropriés
4. Créer un release GitHub pour la traçabilité

---

## ✅ Actions Réalisées

### 1. Préparation du Package (17h00 - 17h15)

#### Configuration initiale
- **Fichier**: `pyproject.toml`
- **Action**: Mise à jour de la version de 2.2.0 à 2.2.1
- **Commande**: 
  ```bash
  sed -i '' 's/version = "2.2.0"/version = "2.2.1"/' pyproject.toml
  ```
- **Raison**: Incrémenter la version pour une nouvelle publication sur PyPI

#### Nettoyage des builds précédents
- **Commande**:
  ```bash
  rm -rf dist/ build/ *.egg-info
  ```
- **Raison**: Éliminer les artefacts de builds antérieurs pour éviter les conflits

---

### 2. Construction du Package (17h15 - 17h25)

#### Build avec Python Build
- **Commande**:
  ```bash
  python -m build
  ```
- **Résultat**: 
  - `syscred-2.2.1-py3-none-any.whl` (74.9 KB)
  - `syscred-2.2.1.tar.gz` (70.2 KB)
- **Raison**: Créer les distributions wheel et source pour PyPI

#### Warnings rencontrés
- **Warning**: License classifiers deprecation
- **Message**: "License :: OSI Approved :: MIT License" déprécié
- **Impact**: Aucun (avertissement seulement)
- **Action future**: Considérer l'utilisation d'expressions de licence SPDX

---

### 3. Publication sur PyPI (17h25 - 17h35)

#### Upload avec Twine
- **Commande**:
  ```bash
  python -m twine upload dist/*
  ```
- **Résultat**: ✅ Succès
  - URL: https://pypi.org/project/syscred/2.2.1/
  - Upload speed: ~70 MB/s pour le wheel, ~54 MB/s pour le tarball
- **Raison**: Rendre le package installable via `pip install syscred==2.2.1`

#### Vérification
- **Package disponible**: ✅
- **Installation testée**: `pip install syscred==2.2.1` fonctionne
- **Métadonnées**: Correctes sur la page PyPI

---

### 4. Création du Git Tag et Release GitHub (17h35 - 17h50)

#### Création du tag Git
- **Commande**:
  ```bash
  git tag -a v2.2.1 -m "Release v2.2.1: PyPI publication with updated README and badges"
  git push origin v2.2.1
  ```
- **Statut**: Le tag existait déjà (créé précédemment)
- **Raison**: Marquer cette version spécifique dans l'historique Git

#### Création du Release GitHub
- **URL**: https://github.com/DominiqueLoyer/systemFactChecking/releases/tag/v2.2.1
- **Titre**: "v2.2.1 - PyPI Publication"
- **Description**: Détails des nouvelles fonctionnalités et instructions d'installation
- **Raison**: Documenter officiellement cette version et déclencher Zenodo

---

### 5. Obtention du DOI Zenodo (17h50 - 18h10)

#### Activation de l'intégration GitHub-Zenodo
- **Plateforme**: https://zenodo.org/
- **Action**: Connexion avec GitHub et activation du repo `systemFactChecking`
- **Raison**: Permettre l'archivage automatique et l'attribution de DOI

#### DOI attribué
- **DOI**: 10.5281/zenodo.18436691
- **URL**: https://doi.org/10.5281/zenodo.18436691
- **Date d'attribution**: 30 janvier 2026
- **Raison**: Citation académique du logiciel dans les publications

---

### 6. Mise à jour du README (18h10 - 18h30)

#### Ajout du badge DOI Zenodo
- **Badge ajouté**:
  ```markdown
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18436691.svg)](https://doi.org/10.5281/zenodo.18436691)
  ```
- **Position**: Ligne 4 du README, après le badge PyPI
- **Raison**: Afficher le DOI pour faciliter la citation académique

#### Suppression de l'ancien DOI
- **DOI supprimé**: 10.5281/zenodo.17943226
- **Commande**:
  ```bash
  sed -i '' '/10.5281\/zenodo.17943226/d' README.md
  ```
- **Raison**: Éviter la confusion et garder uniquement le DOI le plus récent

#### Commit et push final
- **Commandes**:
  ```bash
  git add README.md
  git commit -m "docs: Remove old Zenodo DOI, keep only latest"
  git push origin master
  ```
- **Hash du commit**: 897e680
- **Raison**: Synchroniser les changements sur GitHub

---

## 📊 Résultat Final

### Package PyPI
- ✅ **Nom**: syscred
- ✅ **Version**: 2.2.1
- ✅ **URL**: https://pypi.org/project/syscred/2.2.1/
- ✅ **Installation**: `pip install syscred==2.2.1`

### DOI Zenodo
- ✅ **DOI**: 10.5281/zenodo.18436691
- ✅ **Badge**: Affiché sur le README GitHub
- ✅ **Archivage**: Release v2.2.1 archivé sur Zenodo

### Documentation GitHub
- ✅ **README**: Mis à jour avec badge DOI
- ✅ **Release**: v2.2.1 documenté
- ✅ **Badges actifs**:
  - PyPI version
  - DOI Zenodo
  - License MIT
  - Python 3.8+
  - Colab
  - Kaggle
  - Buy me a coffee
  - GitHub Sponsors

---

## 🔧 Configuration Technique

### Structure du projet
```
systemFactChecking/
├── pyproject.toml          # Configuration du package (version 2.2.1)
├── README.md               # Documentation avec badges
├── LICENSE                 # MIT License
├── src/syscred/           # Code source du package
├── tests/                 # Tests unitaires
├── examples/              # Exemples d'utilisation
└── 03_Docs/              # Documentation (ce fichier)
```

### Dépendances de build
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### Métadonnées du package
- **Nom**: syscred
- **Version**: 2.2.1
- **Description**: A Neuro-Symbolic AI system for information credibility verification
- **Auteur**: Dominique S. Loyer
- **License**: MIT
- **Python requis**: >=3.8

---

## 📝 Notes Importantes

### À propos de GitHub Packages
- **Question posée**: Pourquoi "No packages published" apparaît sur GitHub?
- **Réponse**: GitHub Packages est un service séparé de PyPI
- **Décision**: Ne PAS publier sur GitHub Packages
- **Raison**: PyPI est suffisant et standard pour l'écosystème Python
- **Impact**: Aucun - le package est accessible via PyPI

### Problèmes rencontrés et solutions

#### 1. Tag v2.2.1 déjà existant
- **Problème**: `! [rejected] v2.2.1 -> v2.2.1 (already exists)`
- **Cause**: Tag créé lors d'une tentative précédente
- **Solution**: Utiliser le tag existant pour créer le release
- **Impact**: Aucun

#### 2. Badge DOI ne s'affichait pas immédiatement
- **Problème**: Badge montrait "?" au lieu de l'image
- **Cause**: Délai de propagation de Zenodo
- **Solution**: Attendre quelques minutes
- **Impact**: Résolu automatiquement

#### 3. Ancien DOI présent dans le README
- **Problème**: Deux badges DOI affichés
- **Cause**: Ancien DOI non supprimé
- **Solution**: Suppression manuelle avec sed
- **Impact**: README maintenant propre

---

## 🎓 Citations

### Format BibTeX
```bibtex
@software{loyer2025syscred,
  author = {Loyer, Dominique S.},
  title = {SysCRED: Neuro-Symbolic System for Information Credibility Verification},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/DominiqueLoyer/systemFactChecking},
  doi = {10.5281/zenodo.18436691},
  version = {2.2.1}
}
```

### Format APA
```
Loyer, D. S. (2026). SysCRED: Neuro-Symbolic System for Information Credibility 
Verification (Version 2.2.1) [Computer software]. 
https://doi.org/10.5281/zenodo.18436691
```

---

## 📈 Prochaines Étapes

### Court terme
- [ ] Surveiller les téléchargements sur PyPI Stats
- [ ] Vérifier l'indexation du DOI sur Google Scholar (peut prendre plusieurs jours)
- [ ] Tester l'installation sur différentes plateformes (Windows, Linux, macOS)

### Moyen terme
- [ ] Ajouter des exemples d'utilisation dans `examples/`
- [ ] Améliorer la documentation API
- [ ] Créer un fichier CONTRIBUTING.md pour les contributeurs potentiels

### Long terme (pour la thèse)
- [ ] Publier v3.0 avec les fonctionnalités neuro-symboliques complètes
- [ ] Soumettre un article de software paper dans JOSS ou SoftwareX
- [ ] Créer une page de documentation avec Sphinx ou MkDocs

---

## 🔗 Liens de Référence

### Package
- **PyPI**: https://pypi.org/project/syscred/
- **PyPI v2.2.1**: https://pypi.org/project/syscred/2.2.1/

### Code Source
- **GitHub Repo**: https://github.com/DominiqueLoyer/systemFactChecking
- **Release v2.2.1**: https://github.com/DominiqueLoyer/systemFactChecking/releases/tag/v2.2.1

### Archivage et Citation
- **Zenodo DOI**: https://doi.org/10.5281/zenodo.18436691
- **Zenodo Record**: https://zenodo.org/records/18436691

### Profils
- **ORCID**: https://orcid.org/0009-0003-9713-7109
- **Google Scholar**: (lien du profil)

---

## 📌 Méta-information

- **Document créé**: 30 janvier 2026, 18h30 EST
- **Dernière mise à jour**: 30 janvier 2026, 18h30 EST
- **Auteur**: Dominique S. Loyer
- **Contexte**: Publication officielle du package syscred v2.2.1 dans le cadre de la thèse de doctorat en informatique cognitive (UQAM)
- **Type de document**: Journal de session / Documentation technique
- **Statut**: Complété avec succès ✅

---

## 💡 Leçons Apprises

1. **Vérifier les versions**: Toujours incrémenter correctement la version dans `pyproject.toml` avant le build
2. **Nettoyer avant build**: Supprimer `dist/`, `build/`, `*.egg-info` pour éviter les conflits
3. **Tag Git**: Créer le tag AVANT de créer le release GitHub
4. **Zenodo activation**: S'assurer que le repo est activé sur Zenodo AVANT de créer le release
5. **DOI unique**: Garder seulement le DOI le plus récent dans le README pour éviter la confusion
6. **GitHub Packages**: Ne pas confondre avec PyPI - deux systèmes indépendants
7. **Documentation**: Documenter immédiatement après chaque étape importante

---

**✅ Session terminée avec succès à 18h30**

*Ce document fait partie de la documentation officielle du projet SysCRED et de la thèse de doctorat de Dominique S. Loyer.*
