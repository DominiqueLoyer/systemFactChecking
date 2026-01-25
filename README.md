# Fact Checking System: Information Credibility Verification

[![DOI](https://zenodo.org/badge/992891582.svg)](https://doi.org/10.5281/zenodo.17943226)]
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DominiqueLoyer/systemFactChecking/blob/main/v2_syscred/syscred_colab.ipynb)
[![Kaggle](https://kaggle.com/static/images/open-in-kaggle.svg)](https://kaggle.com/kernels/welcome?src=https://github.com/DominiqueLoyer/systemFactChecking/blob/main/v2_syscred/syscred_kaggle.ipynb)
[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/dominiqueloyer)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-DominiqueLoyer-EA4AAA?logo=github-sponsors)](https://github.com/sponsors/DominiqueLoyer)

**PhD Thesis Prototype** - Dominique S. Loyer  
*Citation Key: loyerModelingHybridSystem2025*

---

## 📋 Overview

A **neuro-symbolic AI system** for verifying information credibility that combines:

- **Symbolic AI**: Rule-based reasoning with OWL ontologies (RDF/Turtle)
- **Neural AI**: Transformer models for sentiment analysis and NER
- **IR Engine**: BM25, TF-IDF, and PageRank estimation

The system provides explainable credibility scores (High/Medium/Low) with detailed factor breakdown.

---

## 🚀 Quick Start (v2.0 - January 2026)

### Option 1: Run on Kaggle/Colab (Recommended)

1. Click the **Kaggle** or **Colab** badge above
2. Enable GPU runtime
3. Run All cells

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/DominiqueLoyer/systemFactChecking.git
cd systemFactChecking/v2_syscred

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python backend_app.py

# Server starts at http://localhost:5000
```

### Option 3: Python API

```python
from v2_syscred.verification_system import CredibilityVerificationSystem

# Initialize
system = CredibilityVerificationSystem()

# Verify a URL
result = system.verify_information("https://www.lemonde.fr/article")
print(f"Score: {result['scoreCredibilite']} ({result['niveauCredibilite']})")

# Verify text directly
result = system.verify_information(
    "According to Harvard researchers, the new study shows significant results."
)
```

---

## 📡 REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/verify` | POST | Full credibility verification |
| `/api/seo` | POST | SEO analysis only (faster) |
| `/api/ontology/stats` | GET | Ontology statistics |
| `/api/health` | GET | Server health check |

### Example Request

```bash
curl -X POST http://localhost:5000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"input_data": "https://www.bbc.com/news/article"}'
```

### Example Response

```json
{
  "scoreCredibilite": 0.78,
  "niveauCredibilite": "HIGH",
  "analysisDetails": {
    "sourceReputation": "High",
    "domainAge": 9125,
    "sentiment": {"label": "NEUTRAL", "score": 0.52},
    "entities": [{"word": "BBC", "entity_group": "ORG"}]
  }
}
```

---

## 📁 Project Structure

```
systemFactChecking/
├── README.md                    # This file
├── v2_syscred/                  # ⭐ VERSION 2.0 (January 2026)
│   ├── verification_system.py  # Main verification pipeline
│   ├── api_clients.py          # External API integrations
│   ├── ontology_manager.py     # RDF/OWL ontology management
│   ├── seo_analyzer.py         # SEO & PageRank analysis
│   ├── ir_engine.py            # Information Retrieval engine
│   ├── eval_metrics.py         # Evaluation metrics (MAP, NDCG, P@K)
│   ├── config.py               # Centralized configuration
│   ├── backend_app.py          # Flask REST API server
│   ├── syscred_kaggle.ipynb    # Kaggle notebook
│   ├── syscred_colab.ipynb     # Colab notebook
│   └── requirements.txt        # Dependencies
│
├── # Legacy v1.0 files (April 2025)
├── sys-cred-Python-27avril2025.py
├── backend_flask.py
├── interface806.html
├── projetFinal_sysCred_Onto_28avril.ttl
└── *.pdf                        # Documentation papers
```

---

## 🔧 Configuration

Set environment variables or edit `v2_syscred/config.py`:

```bash
# Optional: Google Fact Check API key
export SYSCRED_GOOGLE_API_KEY=your_key_here

# Server settings
export SYSCRED_PORT=5000
export SYSCRED_DEBUG=true
export SYSCRED_ENV=production  # or development, testing
```

---

## 📊 Credibility Scoring

The system uses weighted factors to calculate credibility:

| Factor | Weight | Description |
|--------|--------|-------------|
| Source Reputation | 25% | Known credible sources database |
| Domain Age | 10% | WHOIS lookup for domain history |
| Sentiment Neutrality | 15% | Extreme sentiment = lower score |
| Entity Presence | 15% | Named entities (ORG, PER) |
| Text Coherence | 15% | Vocabulary diversity |
| Fact Check | 20% | Google Fact Check API results |

**Thresholds:**

- **HIGH**: Score ≥ 0.7
- **MEDIUM**: 0.4 ≤ Score < 0.7
- **LOW**: Score < 0.4

---

## 📚 Documentation & Papers

- [Modeling and Hybrid System for Verification of Sources Credibility (PDF)](Modeling%20and%20Hybrid%20System%20for%20Verification%20of%20sources%20credibility.pdf)
- [Ontology of a Verification System (PDF)](Ontology_of_a_verification_system_for_liability_of_the_information_may15_2025.pdf)
- [Beamer Presentation - DIC9335 (PDF)](VF_Beamer_30avril25Système_d_évaluation_de_crédibilité_d_information__Une_Ontologie_projetfinal_dic9335.pdf)

---

## 🏷️ Citation

```bibtex
@software{loyer2025syscred,
  author = {Loyer, Dominique S.},
  title = {SysCRED: Neuro-Symbolic System for Information Credibility Verification},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/DominiqueLoyer/systemFactChecking}
}
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | Jan 2026 | Complete rewrite with modular architecture, Kaggle/Colab support, REST API |
| v1.0 | Apr 2025 | Initial prototype with basic credibility scoring |
