# Protocole de Publication v2.2 & Zenodo

Ce guide vous permet de finaliser la mise en ligne de la version du code (v2.2) et d'obtenir votre DOI Zenodo.

## Étape 1 : Pousser le Code (La synchro manquante)

Comme la sécurité bloque mes tentatives automatiques, faites-le manuellement :

1.  Ouvrez **VS Code** (si ce n'est pas déjà fait).
2.  Dans le menu de gauche, cliquez sur l'icône **Source Control** (le petit arbre avec des branches).
3.  Cliquez sur les `...` (trois points) ou le bouton **Sync Changes** (ou **Push**).
    *   *Si demandé, choisissez la branche `main`.*
    *   *Alternative Terminal :* Tapez `git push origin master:main` dans votre terminal à vous.

👉 **Vérification** : Allez sur la page GitHub. Vous devriez voir "Last updated: now" (ou "seconds ago").

## Étape 2 : Créer la Release v2.2

C'est cette étape qui dit à Zenodo : "Ceci est une version officielle, crée un DOI !"

1.  Sur la page d'accueil de votre répertoire GitHub.
2.  Regardez à droite, cliquez sur **Releases** (ou "Create a new release").
3.  Cliquez sur le bouton vert **Draft a new release**.
4.  Remplissez le formulaire :
    *   **Choose a tag** : Écrivez `v2.2` (et cliquez sur "Create new tag").
    *   **Release title** : `SysCRED v2.2 - Neuro-Symbolic Credibility System`
    *   **Description** : Cliquez sur le bouton "Generate release notes" (automatique) ou copiez ceci :
        ```markdown
        ## Major Update v2.2
        - **GraphRAG Integration**: Added contextual memory using RDF knowledge graph.
        - **Interactive Graph**: D3.js visualization with physics and detail view.
        - **Deployment Ready**: Added Dockerfile and Supabase connection logic.
        - **Documentation**: Updated README and protocols.
        ```
5.  Cliquez sur **Publish release**.

## Étape 3 : Synchronisation Zenodo

Dès que vous avez cliqué sur "Publish" :

1.  **Zenodo** va recevoir le signal instantanément.
2.  Il va prendre une "photo" de votre code à cet instant.
3.  Il va générer un **nouveau DOI** (différent de la v1).
4.  Le badge sur votre README se mettra à jour automatiquement (parfois il faut attendre quelques minutes).

---
**Résumé** :
Push Code ➡️ Create GitHub Release ➡️ Zenodo se réveille tout seul.
