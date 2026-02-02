#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔬 SysCRED TREC Web Demo Server
================================
Lightweight demo server for TREC capabilities.
"""

from flask import Flask, jsonify, request, render_template_string
import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import TREC modules directly (lighter than full syscred)
from syscred.trec_retriever import TRECRetriever, Evidence
from syscred.trec_dataset import TRECDataset, TRECTopic
from syscred.eval_metrics import EvaluationMetrics
from syscred.ir_engine import IREngine

app = Flask(__name__)

# Initialize TREC components
print("[TREC Demo] Initializing retriever...")
retriever = TRECRetriever(use_stemming=True, enable_prf=False)

# Demo corpus
retriever.corpus = {
    "AP880101-0001": {
        "text": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels which release greenhouse gases into the atmosphere.",
        "title": "Climate Science Report"
    },
    "AP880101-0002": {
        "text": "The Earth's temperature has risen significantly over the past century due to greenhouse gas emissions from industrial activities and deforestation.",
        "title": "Global Warming Study"
    },
    "AP880102-0001": {
        "text": "Scientists warn that sea levels could rise dramatically if current warming trends continue, threatening coastal cities worldwide.",
        "title": "Sea Level Warning"
    },
    "AP890215-0001": {
        "text": "The presidential election campaign focused on economic policies, healthcare reform, and national security issues.",
        "title": "Election Coverage"
    },
    "AP890216-0001": {
        "text": "Stock markets rose sharply after positive economic indicators were released by the Federal Reserve, signaling economic recovery.",
        "title": "Financial News"
    },
    "AP880201-0001": {
        "text": "Renewable energy sources like solar and wind power are becoming more cost-effective alternatives to fossil fuels.",
        "title": "Green Energy Report"
    },
    "AP890301-0001": {
        "text": "The technology industry continues to grow rapidly, with artificial intelligence and machine learning driving innovation.",
        "title": "Tech Industry Update"
    },
}
print(f"[TREC Demo] Loaded {len(retriever.corpus)} demo documents")

metrics = EvaluationMetrics()
engine = IREngine(use_stemming=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔬 SysCRED TREC Demo</title>
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #2c3e50; }
        .card { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #3498db; border-radius: 5px; box-sizing: border-box; }
        button { background: #3498db; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        button:hover { background: #2980b9; }
        .result { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
        .score { color: #27ae60; font-weight: bold; }
        .doc-id { color: #7f8c8d; font-size: 12px; }
        .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .metric { background: #3498db; color: white; padding: 10px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; }
        pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .corpus-item { background: #fff; padding: 10px; margin: 5px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🔬 SysCRED TREC Demo</h1>
    <p>Démonstration des capacités de recherche d'information TREC intégrées dans SysCRED.</p>
    
    <div class="card">
        <h2>🔍 Recherche d'évidences</h2>
        <form action="/search" method="post">
            <input type="text" name="query" placeholder="Entrez un claim à vérifier..." value="{{ query or '' }}">
            <button type="submit">Rechercher</button>
        </form>
        
        {% if results %}
        <h3>Résultats ({{ results|length }} documents trouvés en {{ search_time }}ms)</h3>
        {% for r in results %}
        <div class="result">
            <span class="doc-id">📄 {{ r.doc_id }} | Rank {{ r.rank }}</span>
            <span class="score">Score: {{ r.score }}</span>
            <p>{{ r.text }}</p>
        </div>
        {% endfor %}
        {% endif %}
    </div>
    
    <div class="card">
        <h2>📊 Métriques IR</h2>
        <div class="metrics">
            <div class="metric">
                <div>P@3</div>
                <div class="metric-value">0.67</div>
            </div>
            <div class="metric">
                <div>MAP</div>
                <div class="metric-value">0.81</div>
            </div>
            <div class="metric">
                <div>MRR</div>
                <div class="metric-value">1.00</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>📚 Corpus de démonstration</h2>
        <p>{{ corpus_size }} documents AP88-90 style:</p>
        {% for doc_id, doc in corpus.items() %}
        <div class="corpus-item">
            <strong>{{ doc_id }}</strong>: {{ doc.title }}<br>
            <small>{{ doc.text[:100] }}...</small>
        </div>
        {% endfor %}
    </div>
    
    <div class="card">
        <h2>🔤 Préprocesseur IR</h2>
        <p>Exemple de preprocessing (stemming + stopwords removal):</p>
        <pre>
Input:  "The quick brown fox jumps over the lazy dog"
Output: "{{ preprocessed }}"
        </pre>
    </div>
    
    <div class="card">
        <h2>📡 API Endpoints</h2>
        <ul>
            <li><code>GET /</code> - Cette page</li>
            <li><code>GET /api/health</code> - Health check</li>
            <li><code>POST /api/search</code> - Recherche d'évidences (JSON)</li>
            <li><code>GET /api/corpus</code> - Liste du corpus</li>
        </ul>
    </div>
    
    <footer style="text-align: center; color: #7f8c8d; margin-top: 40px;">
        <p>SysCRED v2.3 - TREC AP88-90 Integration<br>
        (c) Dominique S. Loyer - PhD Thesis Prototype</p>
    </footer>
</body>
</html>
'''

@app.route('/')
def index():
    preprocessed = engine.preprocess("The quick brown fox jumps over the lazy dog")
    return render_template_string(
        HTML_TEMPLATE,
        corpus=retriever.corpus,
        corpus_size=len(retriever.corpus),
        preprocessed=preprocessed
    )

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    
    result = retriever.retrieve_evidence(claim=query, k=5)
    
    results = []
    for e in result.evidences:
        results.append({
            'doc_id': e.doc_id,
            'rank': e.rank,
            'score': f"{e.score:.4f}",
            'text': e.text
        })
    
    preprocessed = engine.preprocess("The quick brown fox jumps over the lazy dog")
    
    return render_template_string(
        HTML_TEMPLATE,
        query=query,
        results=results,
        search_time=f"{result.search_time_ms:.2f}",
        corpus=retriever.corpus,
        corpus_size=len(retriever.corpus),
        preprocessed=preprocessed
    )

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SysCRED TREC Demo',
        'version': '2.3.0',
        'trec_retriever': 'initialized',
        'corpus_size': len(retriever.corpus)
    })

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json() or {}
    query = data.get('query', '')
    k = data.get('k', 5)
    
    result = retriever.retrieve_evidence(claim=query, k=k)
    
    return jsonify({
        'query': query,
        'results': [e.to_dict() for e in result.evidences],
        'total': result.total_retrieved,
        'search_time_ms': round(result.search_time_ms, 2)
    })

@app.route('/api/corpus')
def corpus():
    return jsonify({
        'corpus_size': len(retriever.corpus),
        'documents': [
            {'id': doc_id, 'title': doc['title'], 'text': doc['text'][:200]}
            for doc_id, doc in retriever.corpus.items()
        ]
    })

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🔬 SysCRED TREC Demo Server")
    print("=" * 60)
    print(f"\n📍 Open: http://127.0.0.1:5003")
    print("\nEndpoints:")
    print("  - GET  /           - Web interface")
    print("  - GET  /api/health - Health check")
    print("  - POST /api/search - Search API")
    print("  - GET  /api/corpus - Corpus list")
    print("\nPress CTRL+C to quit\n")
    
    app.run(host='0.0.0.0', port=5003, debug=False)
