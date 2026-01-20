# SysCRED - Système Neuro-Symbolique de Vérification de Crédibilité

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**PhD Thesis Prototype** - Dominique S. Loyer, UQAM

## 🎯 Features

- **Information Retrieval**: BM25, QLD, TF-IDF, Pseudo-Relevance Feedback
- **NLP Analysis**: Sentiment, NER, Bias detection (transformers)
- **SEO Analysis**: PageRank estimation, keyword density
- **Ontology**: RDF/OWL for explainability
- **Evaluation**: MAP, NDCG, P@K, Recall (pytrec_eval)

## 🚀 Quick Start

### Installation

```bash
# Basic
pip install -e .

# With ML (GPU)
pip install -e ".[ml]"

# Full installation
pip install -e ".[full]"
```

### Kaggle Usage

```python
from syscred import SysCRED

system = SysCRED()
result = system.verify("Your text or URL here")
print(f"Credibility Score: {result['score']}")
```

## 📁 Structure

```
syscred/
├── api_clients.py      # Web scraping, WHOIS, Fact Check
├── ir_engine.py        # BM25, QLD, PRF (from TREC)
├── seo_analyzer.py     # TF-IDF, PageRank
├── eval_metrics.py     # MAP, NDCG, P@K
├── ontology_manager.py # RDFLib integration
├── verification_system.py
├── backend_app.py      # Flask API
└── syscred_kaggle.ipynb
```

## 📚 Citations

```bibtex
@phdthesis{loyerModelingHybridSystem2025,
  author = {Loyer, Dominique S.},
  title = {Modeling a Hybrid System for Credibility Verification},
  school = {UQAM},
  year = {2025}
}
```

## License

MIT License - (c) 2025 Dominique S. Loyer
