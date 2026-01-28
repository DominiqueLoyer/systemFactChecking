# Résumés de la Revue de Littérature - sysCRED

Ce document synthétise les 12 articles clés sélectionnés pour la proposition de recherche doctorale.

---

## 1. Fondements de l'IA Neuro-Symbolique (La 3ème Vague)

### Garcez & Lamb (2023) - *Neurosymbolic AI: The 3rd Wave*

* **Apport Principal :** Définit formellement la "3ème vague" de l'IA comme l'intégration nécessaire du raisonnement (Symbolique/S2) et de l'apprentissage (Neuronal/S1). Ils catégorisent les architectures (Pipeline vs Intégration complète).
* **Pourquoi ce choix :** C'est l'article séminal qui cadre théoriquement votre projet. Il justifie pourquoi les LLM seuls ne suffisent pas et pourquoi une approche hybride est l'avenir de l'IA robuste.

### Hitzler et al. (2025) - *Neuro-Symbolic AI Survey 2024-2025*

* **Apport Principal :** Un état de l'art exhaustif des techniques récentes. Il met l'accent sur les défis actuels : scalabilité, explicabilité, et l'intégration des ontologies avec les réseaux de neurones.
* **Pourquoi ce choix :** Prouve que vous êtes à jour (SOTA 2025) et permet de situer sysCRED par rapport aux autres solutions existantes.

### Yang et al. (2025) - *Improving Reasoning Abilities of LLMs*

* **Apport Principal :** Analyse les limites de raisonnement des LLM (problème des "hallucinations logiques") et propose des modules symboliques externes pour les "corriger".
* **Pourquoi ce choix :** Valide directement votre hypothèse : un LLM a besoin d'un "tuteur" logique pour être fiable.

### Mao et al. (2019) - *The Neuro-Symbolic Concept Learner (NSCL)*

* **Apport Principal :** Une démonstration technique classique montrant comment un système peut *apprendre* des concepts visuels et linguistiques (Neuronal) puis raisonner dessus (Symbolique), sans supervision explicite massive.
* **Pourquoi ce choix :** Sert de preuve de concept technique historique. Montre la faisabilité de l'extraction de concepts symboliques à partir de données brutes.

---

## 2. Confiance, Sécurité et Véracité

### Sarker et al. (2023) - *Neuro-Symbolic methods for Trustworthy AI*

* **Apport Principal :** Lie l'architecture NeSy au concept de "Trustworthy AI" (IA de confiance). Définit les critères : explicabilité, robustesse, et équité.
* **Pourquoi ce choix :** Lie votre architecture technique à votre problématique éthique/sociale ("Le Léviathan Algorithmique"). Crucial pour justifier l'impact sociétal de la thèse.

### Hakim et al. (2025) - *Neuro-Symbolic AI for Cybersecurity*

* **Apport Principal :** Applique le NeSy à la sécurité. Montre comment les règles symboliques peuvent bloquer des attaques que les modèles statistiques (ML) laissent passer.
* **Pourquoi ce choix :** Analogie forte avec la désinformation (qui est une forme d'attaque cognitive). Justifie l'approche "Zero Trust" de sysCRED.

---

## 3. GraphRAG et Ancrage Sémantique

### Pan et al. (2025) - *LLMs and Knowledge Graphs: Opportunities and Challenges*

* **Apport Principal :** Explore la synergie LLM + KG. Le KG fournit les faits (la "mémoire"), le LLM fournit l'interface et la compréhension. Introduction au concept de GraphRAG.
* **Pourquoi ce choix :** C'est le cœur de l'implémentation de sysCRED (v2.1). Justifie l'architecture technique (Neo4j + LLM).

### Wang & Cohen (2025) - *Integrating Knowledge Graphs... for Hallucination Reduction*

* **Apport Principal :** Montre empiriquement que l'utilisation d'un graphe de connaissances réduit drastiquement les hallucinations factuelles des LLM.
* **Pourquoi ce choix :** Argument massue pour l'efficacité de votre solution. "On ne fait pas juste du NeSy pour le plaisir, on le fait car ça marche mieux pour la vérité."

### Marconato et al. (2025) - *Symbol Grounding & Reasoning Shortcuts*

* **Apport Principal :** Met en garde contre les "raccourcis de raisonnement" (quand le modèle devine la réponse sans raisonner). Propose l'ancrage (grounding) pour forcer le modèle à utiliser les preuves.
* **Pourquoi ce choix :** Touche à la difficulté scientifique majeure de la thèse (comment être sûr que l'IA a *vraiment* compris). Montre la profondeur de votre analyse scientifique.

---

## 4. Méthodologie et Normes

### Hevner et al. (2004) - *Design Science in Information Systems Research*

* **Apport Principal :** La "Bible" de la méthodologie *Design Science Research* (DSR). Définit ce qu'est un "artefact" scientifique (sysCRED n'est pas juste un logiciel, c'est un artefact de recherche).
* **Pourquoi ce choix :** Indispensable pour la section "Méthodologie" de la thèse. Cadre votre démarche de "recherche par la construction".

### Peffers et al. (2007) - *A Design Science Research Methodology (DSRM)*

* **Apport Principal :** Fournit le processus étape par étape (Identification problème -> Objectifs -> Design -> Démo -> Éval -> Com).
* **Pourquoi ce choix :** Vous structurez votre plan de thèse (et votre présentation) exactement selon ces étapes.

### UQAM (2024) - *Guide de présentation des mémoires et des thèses*

* **Apport Principal :** Normes institutionnelles.
* **Pourquoi ce choix :** Assure la conformité administrative de votre document final.
