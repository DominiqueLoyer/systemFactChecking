# 📚 Documentation: Intégration TREC AP88-90 dans SysCRED

**Auteur:** Dominique S. Loyer  
**Date:** 2 février 2026  
**Version:** 2.3  
**Citation Key:** loyerEvaluationModelesRecherche2025

---

## 📖 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Qu'est-ce que TREC AP88-90?](#quest-ce-que-trec-ap88-90)
3. [Architecture du module](#architecture-du-module)
4. [Les métriques IR expliquées](#les-métriques-ir-expliquées)
5. [Comment fonctionne la recherche d'évidences](#comment-fonctionne-la-recherche-dévidences)
6. [API Endpoints](#api-endpoints)
7. [Exemples d'utilisation](#exemples-dutilisation)
8. [Intégration avec SysCRED](#intégration-avec-syscred)

---

## Vue d'ensemble

Le module TREC intègre des capacités de **Recherche d'Information (IR)** dans SysCRED, permettant de :

1. **Rechercher des évidences** pour vérifier des affirmations (claims)
2. **Calculer des métriques d'évaluation** standardisées (MAP, NDCG, P@K)
3. **Utiliser différents modèles de scoring** : BM25, TF-IDF, QLD

Cette intégration repose sur la méthodologie **TREC (Text REtrieval Conference)**, le standard de référence en évaluation de systèmes de recherche d'information.

---

## Qu'est-ce que TREC AP88-90?

### 📰 Le corpus Associated Press (AP)

Le corpus **AP88-90** est une collection de **242 918 articles** de l'Associated Press publiés entre 1988 et 1990. C'est l'un des corpus les plus utilisés dans la recherche en IR.

| Caractéristique | Valeur |
|----------------|--------|
| Source | Associated Press (agence de presse) |
| Période | 1988-1990 |
| Nombre de documents | 242 918 |
| Format | SGML/XML avec balises `<DOC>`, `<DOCNO>`, `<TEXT>` |
| Langue | Anglais |

### 🎯 Les Topics (requêtes)

Les topics TREC sont des **requêtes structurées** avec :
- **Title** : Version courte (2-4 mots)
- **Description** : Phrase décrivant le besoin d'information
- **Narrative** : Critères détaillés de pertinence

**Exemple de topic :**
```xml
<top>
  <num>51</num>
  <title>Airbus Subsidies</title>
  <desc>How have the European governments subsidized Airbus?</desc>
  <narr>A relevant document will discuss European governmental 
  subsidies to Airbus Industrie...</narr>
</top>
```

### ✓ Les Qrels (jugements de pertinence)

Les **qrels** (Query RELevance judgments) sont les jugements humains de pertinence :
```
topic_id  0  doc_id  relevance
51        0  AP880212-0001  1
51        0  AP880304-0035  0
```

---

## Architecture du module

```
syscred/
├── trec_retriever.py    # 🔍 Recherche d'évidences
├── trec_dataset.py      # 📚 Gestion du corpus TREC
├── ir_engine.py         # ⚙️ Moteur IR (BM25, TF-IDF, QLD)
├── eval_metrics.py      # 📊 Métriques d'évaluation
└── backend_app.py       # 🌐 Endpoints API (intégré)
```

### Dépendances entre modules

```
┌─────────────────────────────────────────────────────────────┐
│                     backend_app.py                          │
│                    (API REST Flask)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   TREC      │  │    IR       │  │  Eval       │
│  Retriever  │  │   Engine    │  │  Metrics    │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │
         │               │
         ▼               │
┌─────────────┐          │
│    TREC     │◄─────────┘
│   Dataset   │
└─────────────┘
```

---

## Les métriques IR expliquées

### 📊 Comprendre l'interface de démo

Dans la capture d'écran de l'interface TREC Demo, vous voyez :

```
📊 Métriques IR
┌─────────┬─────────┬─────────┐
│  P@3    │   MAP   │   MRR   │
│  0.67   │  0.81   │  1.00   │
└─────────┴─────────┴─────────┘
```

**Ces métriques sont calculées sur un exemple de démonstration :**

| Éléments | Valeur |
|----------|--------|
| Documents récupérés | ["AP880101-0001", "AP890215-0001", "AP880101-0002"] |
| Documents pertinents | ["AP880101-0001", "AP880101-0002", "AP880102-0001"] |
| K (nombre de résultats) | 3 |

### 📐 P@K (Precision at K) = 0.67

**Définition :** Proportion de documents pertinents parmi les K premiers récupérés.

**Formule :**
$$P@K = \frac{|\text{pertinents} \cap \text{récupérés}[:K]|}{K}$$

**Calcul :**
- Récupérés (top 3) : AP880101-0001 ✓, AP890215-0001 ✗, AP880101-0002 ✓
- Pertinents trouvés : 2 sur 3
- **P@3 = 2/3 = 0.67**

**Interprétation :** 67% des 3 premiers documents sont pertinents.

---

### 📐 MAP (Mean Average Precision) = 0.81

**Définition :** Moyenne des précisions calculées à chaque document pertinent.

**Formule :**
$$MAP = \frac{1}{|R|} \sum_{k=1}^{n} P(k) \times rel(k)$$

où $rel(k) = 1$ si le document au rang $k$ est pertinent.

**Calcul détaillé :**
1. Rang 1 (AP880101-0001) : pertinent ✓ → P@1 = 1/1 = 1.00
2. Rang 2 (AP890215-0001) : non pertinent ✗ → ignoré
3. Rang 3 (AP880101-0002) : pertinent ✓ → P@3 = 2/3 = 0.67

$$AP = \frac{1.00 + 0.67}{2} = 0.835 \approx 0.81$$

**Interprétation :** Qualité globale du ranking. Plus les documents pertinents sont en haut, plus le MAP est élevé.

---

### 📐 MRR (Mean Reciprocal Rank) = 1.00

**Définition :** Inverse du rang du premier document pertinent.

**Formule :**
$$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{rank_i}$$

**Calcul :**
- Premier document pertinent : AP880101-0001 (rang 1)
- **MRR = 1/1 = 1.00**

**Interprétation :** Le premier document pertinent est en position 1 (optimal).

---

### 📐 NDCG (Normalized Discounted Cumulative Gain)

**Définition :** Mesure la qualité du ranking avec pénalité logarithmique pour les rangs inférieurs.

**Formule :**
$$DCG@K = \sum_{i=1}^{K} \frac{2^{rel_i} - 1}{\log_2(i+1)}$$

$$NDCG@K = \frac{DCG@K}{IDCG@K}$$

où IDCG est le DCG du ranking parfait.

**Interprétation :** 1.0 = ranking parfait, 0.0 = aucun document pertinent en haut.

---

### 📐 Recall@K (Rappel)

**Définition :** Proportion de documents pertinents récupérés parmi tous les pertinents.

**Formule :**
$$R@K = \frac{|\text{pertinents} \cap \text{récupérés}[:K]|}{|\text{pertinents}|}$$

**Calcul :**
- Total pertinents : 3 (AP880101-0001, AP880101-0002, AP880102-0001)
- Récupérés et pertinents : 2
- **R@3 = 2/3 = 0.67**

---

## Comment fonctionne la recherche d'évidences

### 🔍 Pipeline de recherche

```
┌──────────────────────────────────────────────────────────────┐
│                    Claim (requête)                           │
│         "Climate change is caused by humans"                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   1. Prétraitement                           │
│  • Tokenization (découpage en mots)                          │
│  • Suppression des stopwords (the, is, by...)                │
│  • Stemming Porter (caused → caus, humans → human)           │
│                                                               │
│  Résultat: ["climat", "chang", "caus", "human"]              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   2. Scoring BM25                            │
│                                                               │
│  BM25(D,Q) = Σ IDF(qi) × [f(qi,D) × (k1+1)]                 │
│              ────────────────────────────────                │
│              f(qi,D) + k1 × (1-b+b×|D|/avgdl)               │
│                                                               │
│  Paramètres optimisés sur AP88-90:                           │
│  • k1 = 0.9 (saturation des termes)                          │
│  • b = 0.4 (normalisation longueur)                          │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   3. Ranking des résultats                   │
│                                                               │
│  Rank 1: AP880101-0001 (score: 6.27) ← "Climate change..."   │
│  Rank 2: AP880101-0002 (score: 3.93) ← "Earth's temperature" │
│  Rank 3: AP880102-0001 (score: 4.11) ← "Sea levels..."       │
└──────────────────────────────────────────────────────────────┘
```

### ⚙️ Modèles de scoring disponibles

| Modèle | Description | Usage recommandé |
|--------|-------------|------------------|
| **BM25** | Best Match 25, standard TREC | Par défaut, meilleur pour requêtes courtes |
| **TF-IDF** | Term Frequency × Inverse Document Frequency | Recherche classique |
| **QLD** | Query Likelihood (Dirichlet) | Modèle probabiliste de langue |

---

## API Endpoints

### POST `/api/trec/search`

Recherche d'évidences pour une affirmation.

**Requête :**
```json
{
  "query": "Climate change is caused by humans",
  "k": 10,
  "model": "bm25"
}
```

**Réponse :**
```json
{
  "query": "Climate change is caused by humans",
  "results": [
    {
      "doc_id": "AP880101-0001",
      "score": 6.2745,
      "rank": 1,
      "text": "Climate change is primarily caused by human activities...",
      "title": "Climate Science Report",
      "model": "bm25"
    }
  ],
  "total": 3,
  "model": "bm25",
  "search_time_ms": 12.5
}
```

---

### POST `/api/trec/metrics`

Calcule les métriques IR pour un résultat de recherche.

**Requête :**
```json
{
  "retrieved": ["AP880101-0001", "AP890215-0001", "AP880101-0002"],
  "relevant": ["AP880101-0001", "AP880101-0002", "AP880102-0001"]
}
```

**Réponse :**
```json
{
  "precision_at_3": 0.6667,
  "recall_at_3": 0.6667,
  "average_precision": 0.8125,
  "mrr": 1.0,
  "ndcg_at_3": 0.8789,
  "metrics_explanation": {
    "P@K": "Proportion de documents pertinents parmi les K premiers récupérés",
    "R@K": "Proportion de documents pertinents récupérés parmi tous les pertinents",
    "AP": "Moyenne des précisions à chaque document pertinent trouvé",
    "MRR": "Rang réciproque du premier document pertinent",
    "NDCG": "Gain cumulatif normalisé avec décroissance logarithmique"
  }
}
```

---

### GET `/api/trec/corpus`

Retourne les informations du corpus de démonstration.

**Réponse :**
```json
{
  "corpus_size": 7,
  "corpus_type": "AP88-90 Demo",
  "documents": [
    {
      "doc_id": "AP880101-0001",
      "title": "Climate Science Report",
      "text_preview": "Climate change is primarily caused by human activities..."
    }
  ]
}
```

---

### GET `/api/trec/health`

Vérifie l'état du module TREC.

**Réponse :**
```json
{
  "status": "healthy",
  "trec_available": true,
  "retriever_initialized": true,
  "corpus_size": 7,
  "models_available": ["bm25", "tfidf", "qld"]
}
```

---

## Exemples d'utilisation

### Python (requests)

```python
import requests

# Recherche d'évidences
response = requests.post('http://localhost:5001/api/trec/search', json={
    'query': 'Climate change is caused by humans',
    'k': 5,
    'model': 'bm25'
})

results = response.json()
for r in results['results']:
    print(f"[{r['rank']}] {r['doc_id']} (score: {r['score']:.4f})")
    print(f"    {r['text'][:80]}...")
```

### cURL

```bash
# Recherche
curl -X POST http://localhost:5001/api/trec/search \
  -H "Content-Type: application/json" \
  -d '{"query": "global warming effects", "k": 3}'

# Métriques
curl -X POST http://localhost:5001/api/trec/metrics \
  -H "Content-Type: application/json" \
  -d '{"retrieved": ["doc1", "doc2"], "relevant": ["doc1", "doc3"]}'
```

### JavaScript (Fetch)

```javascript
const response = await fetch('/api/trec/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'renewable energy alternatives',
    k: 10
  })
});

const data = await response.json();
console.log(`Found ${data.total} results in ${data.search_time_ms}ms`);
```

---

## Intégration avec SysCRED

### 🔗 Pipeline de fact-checking avec TREC

Le module TREC s'intègre dans le pipeline de vérification :

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claim (entrée)                           │
│            "Le changement climatique est causé par l'homme"     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│   TREC Evidence         │    │    External APIs                │
│   Retrieval             │    │    (Google Fact Check,          │
│   (/api/trec/search)    │    │     Wikipedia, etc.)            │
└─────────────────────────┘    └─────────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Evidence Aggregation                         │
│  • Combinaison des évidences trouvées                           │
│  • Scoring de pertinence                                        │
│  • Classification du support/réfutation                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Verdict Generation                              │
│  • SUPPORTS / REFUTES / NOT ENOUGH INFO                         │
│  • Score de crédibilité                                         │
│  • Explication textuelle                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Méthode `verify_with_evidence()`

Dans `verification_system.py`, la nouvelle méthode combine TREC avec la vérification :

```python
def verify_with_evidence(self, claim: str, k: int = 5) -> Dict[str, Any]:
    """
    Complete fact-checking pipeline with evidence retrieval.
    
    1. Retrieve evidence using TREC
    2. Analyze evidence for support/refutation
    3. Generate verdict
    """
    # 1. Retrieve evidence
    retrieval_result = self.retrieve_evidence(claim, k=k)
    
    # 2. Analyze evidence
    evidences = retrieval_result.evidences
    supporting = [e for e in evidences if e.score > 5.0]
    
    # 3. Generate verdict
    if len(supporting) >= 2:
        verdict = "SUPPORTS"
        confidence = 0.8
    elif len(supporting) >= 1:
        verdict = "LIKELY_SUPPORTS"
        confidence = 0.6
    else:
        verdict = "NOT_ENOUGH_INFO"
        confidence = 0.3
    
    return {
        "claim": claim,
        "verdict": verdict,
        "confidence": confidence,
        "evidences": [e.to_dict() for e in evidences[:3]]
    }
```

---

## Références

1. **TREC (Text REtrieval Conference)**  
   [https://trec.nist.gov/](https://trec.nist.gov/)

2. **AP Corpus**  
   Harman, D. (1993). "Overview of TREC-1." NIST Special Publication 500-207.

3. **BM25**  
   Robertson, S. E., & Walker, S. (1994). "Some simple effective approximations to the 2-Poisson model."

4. **pytrec_eval**  
   [https://github.com/cvangysel/pytrec_eval](https://github.com/cvangysel/pytrec_eval)

5. **Loyer, D. S. (2025)**  
   "Évaluation des modèles de recherche d'information sur le corpus TREC AP88-90."
   (loyerEvaluationModelesRecherche2025)

---

## 🔄 Recommandations pour reprendre le travail

### État actuel (2 février 2026)

**Branche `main`** est à jour avec tous les commits TREC :
```
743b689 chore: Update Docker configs and add HuggingFace deploy script
f0bf7ba feat(trec): Add TREC API endpoints to backend and documentation
b11f1b2 fix(config): Support both SYSCRED_LOAD_ML and SYSCRED_LOAD_ML_MODELS
d981b06 feat(trec): Integrate TRECRetriever into VerificationSystem
```

### Pour reprendre le travail

1. **Mettre à jour votre copie locale :**
   ```bash
   cd /Users/bk280625/Desktop/systemFactChecking
   git fetch origin
   git pull origin main
   ```

2. **Synchroniser la branche feature (si vous y travaillez encore) :**
   ```bash
   git checkout feature/trec-88-90-integration
   git merge main
   git push origin feature/trec-88-90-integration
   ```

3. **Lancer le serveur SysCRED avec TREC :**
   ```bash
   cd 02_Code
   source venv/bin/activate
   SYSCRED_LOAD_ML_MODELS=false python -m syscred.backend_app
   ```
   Le serveur sera accessible sur http://127.0.0.1:5001

4. **Tester les endpoints TREC :**
   ```bash
   # Dans un autre terminal
   curl http://127.0.0.1:5001/api/trec/health
   curl http://127.0.0.1:5001/api/trec/corpus
   ```

### Fichiers clés créés/modifiés

| Fichier | Description |
|---------|-------------|
| `02_Code/syscred/backend_app.py` | Backend Flask avec endpoints TREC intégrés |
| `02_Code/syscred/trec_retriever.py` | Module de recherche d'évidences |
| `02_Code/syscred/eval_metrics.py` | Métriques IR (MAP, NDCG, P@K) |
| `02_Code/demo_trec.py` | Script de démonstration CLI |
| `02_Code/demo_trec_web.py` | Serveur web de démo léger (port 5003) |
| `03_Docs/TREC_Integration_Documentation.md` | Cette documentation |

### Prochaines étapes suggérées

- [ ] Intégrer la recherche TREC dans l'interface frontend (index.html)
- [ ] Connecter avec un vrai corpus AP88-90 (pas juste le démo)
- [ ] Ajouter les tests d'intégration automatisés
- [ ] Déployer sur Render/HuggingFace avec les nouveaux endpoints

---

*SysCRED v2.3 - TREC AP88-90 Integration*  
*(c) Dominique S. Loyer - PhD Thesis Prototype*
