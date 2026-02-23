# -*- coding: utf-8 -*-
"""
SysCRED Backend API - Flask Server
===================================
REST API for the credibility verification system.

Endpoints:
- POST /api/verify - Verify URL or text credibility
- POST /api/seo - Get SEO analysis only
- GET /api/ontology/stats - Get ontology statistics
- GET /api/health - Health check
- GET /api/config - View current configuration

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import sys
import os
import traceback

# Load environment variables from .env file
from pathlib import Path
try:
    from dotenv import load_dotenv
    # .env is at project root (parent of syscred/)
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        # Fallback: check syscred/ directory
        env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[SysCRED Backend] Loaded .env from {env_path}")
    else:
        print(f"[SysCRED Backend] No .env file found, using system env vars")
except ImportError:
    print("[SysCRED Backend] python-dotenv not installed, using system env vars")

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add syscred package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SysCRED modules (with graceful fallbacks)
SYSCRED_AVAILABLE = False
TREC_AVAILABLE = False
DB_AVAILABLE = False

# Core modules (required)
try:
    from syscred.verification_system import CredibilityVerificationSystem
    from syscred.seo_analyzer import SEOAnalyzer
    from syscred.ontology_manager import OntologyManager
    from syscred.config import config, Config
    SYSCRED_AVAILABLE = True
    print("[SysCRED Backend] Core modules imported successfully")
except ImportError as e:
    print(f"[SysCRED Backend] Warning: Core modules failed: {e}")
    # Fallback config
    class Config:
        HOST = "0.0.0.0"
        PORT = 5000
        DEBUG = True
        ONTOLOGY_BASE_PATH = None
        ONTOLOGY_DATA_PATH = None
        LOAD_ML_MODELS = True
        GOOGLE_FACT_CHECK_API_KEY = None
    config = Config()

# Database (optional)
try:
    from syscred.database import init_db, db, AnalysisResult
    DB_AVAILABLE = True
    print("[SysCRED Backend] Database module loaded")
except ImportError as e:
    print(f"[SysCRED Backend] Database disabled: {e}")
    def init_db(app): pass

# TREC modules (optional)
try:
    from syscred.trec_retriever import TRECRetriever, Evidence, RetrievalResult
    from syscred.eval_metrics import EvaluationMetrics
    TREC_AVAILABLE = True
    print("[SysCRED Backend] TREC modules loaded")
except ImportError as e:
    print(f"[SysCRED Backend] TREC modules disabled: {e}")

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Allow iframe embedding on UQAM domains (for syscred.uqam.ca mirror)
@app.after_request
def add_security_headers(response):
    """Add security headers allowing UQAM iframe embedding."""
    response.headers['X-Frame-Options'] = 'ALLOW-FROM https://syscred.uqam.ca'
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://syscred.uqam.ca https://*.uqam.ca"
    )
    return response

# Initialize Database
try:
    init_db(app) # [NEW] Setup DB connection
except Exception as e:
    print(f"[SysCRED Backend] Warning: DB init failed: {e}")

# --- Initialize SysCRED System ---
credibility_system = None
seo_analyzer = None
trec_retriever = None
eval_metrics = None

# Demo corpus for TREC (AP88-90 style documents)
TREC_DEMO_CORPUS = {
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

def initialize_system():
    """Initialize the credibility system (lazy loading)."""
    global credibility_system, seo_analyzer
    
    if not SYSCRED_AVAILABLE:
        print("[SysCRED Backend] Cannot initialize - modules not available")
        return False
    
    try:
        # Initialize SEO analyzer (lightweight)
        seo_analyzer = SEOAnalyzer()
        print("[SysCRED Backend] SEO Analyzer initialized")
        
        # Initialize full system (may take time to load ML models)
        print("[SysCRED Backend] Initializing credibility system (loading ML models)...")
        ontology_base = str(config.ONTOLOGY_BASE_PATH) if config.ONTOLOGY_BASE_PATH else None
        ontology_data = str(config.ONTOLOGY_DATA_PATH) if config.ONTOLOGY_DATA_PATH else None
        credibility_system = CredibilityVerificationSystem(
            ontology_base_path=ontology_base if ontology_base and os.path.exists(ontology_base) else None,
            ontology_data_path=ontology_data,
            load_ml_models=config.LOAD_ML_MODELS,
            google_api_key=config.GOOGLE_FACT_CHECK_API_KEY
        )
        print("[SysCRED Backend] System initialized successfully!")
        return True
        
    except Exception as e:
        print(f"[SysCRED Backend] Error initializing system: {e}")
        traceback.print_exc()
        return False

# --- API Routes ---

@app.route('/')
def index():
    """Serve the frontend."""
    return send_from_directory('static', 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'syscred_available': SYSCRED_AVAILABLE,
        'system_initialized': credibility_system is not None,
        'seo_analyzer_ready': seo_analyzer is not None
    })


@app.route('/api/verify', methods=['POST'])
def verify_endpoint():
    """
    Main verification endpoint.
    
    Request JSON:
    {
        "input_data": "URL or text to verify",
        "include_seo": true/false (optional, default true),
        "include_pagerank": true/false (optional, default true)
    }
    """
    global credibility_system
    
    # Lazy initialization
    if credibility_system is None:
        if not initialize_system():
            return jsonify({
                'error': 'System initialization failed. Check server logs.'
            }), 503
    
    # Validate request
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    input_data = data.get('input_data', '').strip()
    
    if not input_data:
        return jsonify({'error': "'input_data' is required"}), 400
    
    include_seo = data.get('include_seo', True)
    include_pagerank = data.get('include_pagerank', True)
    
    print(f"[SysCRED Backend] Verifying: {input_data[:100]}...")
    
    try:
        # Run main verification
        result = credibility_system.verify_information(input_data)
        
        if 'error' in result:
            return jsonify(result), 400
        
        # Add SEO analysis if requested and it's a URL
        if include_seo and credibility_system.is_url(input_data):
            try:
                web_content = credibility_system.api_clients.fetch_web_content(input_data)
                if web_content.success:
                    seo_result = seo_analyzer.analyze_seo(
                        url=input_data,
                        title=web_content.title,
                        meta_description=web_content.meta_description,
                        text_content=web_content.text_content
                    )
                    result['seoAnalysis'] = {
                        'titleLength': seo_result.title_length,
                        'titleHasKeywords': seo_result.title_has_keywords,
                        'metaDescriptionLength': seo_result.meta_description_length,
                        'wordCount': seo_result.word_count,
                        'readabilityScore': round(seo_result.readability_score, 2),
                        'seoScore': round(seo_result.seo_score, 2),
                        'topKeywords': list(seo_result.keyword_density.keys())
                    }
            except Exception as e:
                print(f"[SysCRED Backend] SEO analysis error: {e}")
                result['seoAnalysis'] = {'error': str(e)}
        
        # Add PageRank estimation if requested
        if include_pagerank and credibility_system.is_url(input_data):
            try:
                external_data = credibility_system.api_clients.fetch_external_data(input_data)
                pr_result = seo_analyzer.estimate_pagerank(
                    url=input_data,
                    domain_age_days=external_data.domain_age_days,
                    source_reputation=external_data.source_reputation
                )
                result['pageRankEstimation'] = {
                    'estimatedPR': round(pr_result.estimated_pr, 3),
                    'confidence': round(pr_result.confidence, 2),
                    'factors': pr_result.factors,
                    'explanation': pr_result.explanation_text
                }
            except Exception as e:
                print(f"[SysCRED Backend] PageRank estimation error: {e}")
                result['pageRankEstimation'] = {'error': str(e)}
        
        print(f"[SysCRED Backend] Score: {result.get('scoreCredibilite', 'N/A')}")
        
        # [NEW] TREC Evidence Search + IR Metrics
        try:
            global trec_retriever, eval_metrics
            
            # Initialize TREC if needed
            if trec_retriever is None and TREC_AVAILABLE:
                trec_retriever = TRECRetriever(use_stemming=True, enable_prf=False)
                trec_retriever.corpus = TREC_DEMO_CORPUS
                eval_metrics = EvaluationMetrics()
                print("[SysCRED Backend] TREC Retriever initialized with demo corpus")
            
            if trec_retriever and eval_metrics:
                import time
                start_time = time.time()
                
                # Use the input text as query
                query_text = input_data[:200] if not credibility_system.is_url(input_data) else result.get('informationEntree', input_data)[:200]
                
                trec_result = trec_retriever.retrieve_evidence(query_text, k=5, model='bm25')
                search_time = (time.time() - start_time) * 1000
                
                retrieved_ids = [e.doc_id for e in trec_result.evidences]
                
                # Use climate-related docs as "relevant" for demo evaluation
                # In production, this would come from qrels files
                relevant_ids = set(TREC_DEMO_CORPUS.keys())  # All docs as relevant pool
                
                # Compute IR metrics
                k = len(retrieved_ids) if retrieved_ids else 1
                precision = eval_metrics.precision_at_k(retrieved_ids, relevant_ids, k) if retrieved_ids else 0
                recall = eval_metrics.recall_at_k(retrieved_ids, relevant_ids, k) if retrieved_ids else 0
                ap = eval_metrics.average_precision(retrieved_ids, relevant_ids) if retrieved_ids else 0
                mrr = eval_metrics.mrr(retrieved_ids, relevant_ids) if retrieved_ids else 0
                
                relevance_dict = {doc: 1 for doc in relevant_ids}
                ndcg = eval_metrics.ndcg_at_k(retrieved_ids, relevance_dict, k) if retrieved_ids else 0
                
                # TF-IDF score from top result
                tfidf_score = trec_result.evidences[0].score if trec_result.evidences else 0
                
                result['trec_metrics'] = {
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'map': round(ap, 4),
                    'ndcg': round(ndcg, 4),
                    'tfidf_score': round(tfidf_score, 4),
                    'mrr': round(mrr, 4),
                    'retrieved_count': len(retrieved_ids),
                    'corpus_size': len(TREC_DEMO_CORPUS),
                    'search_time_ms': round(search_time, 2)
                }
                print(f"[SysCRED Backend] TREC: P={precision:.3f} R={recall:.3f} MAP={ap:.3f} NDCG={ndcg:.3f} MRR={mrr:.3f}")
        except Exception as e:
            print(f"[SysCRED Backend] TREC metrics error: {e}")
            result['trec_metrics'] = {'error': str(e)}
        
        # [NEW] Persist to Database
        try:
            new_analysis = AnalysisResult(
                url=input_data[:500],
                credibility_score=result.get('scoreCredibilite', 0.5),
                summary=result.get('resumeAnalyse', ''),
                source_reputation=result.get('detailsScore', {}).get('factors', [{}])[0].get('value')
            )
            db.session.add(new_analysis)
            db.session.commit()
            print(f"[SysCRED-DB] Result saved. ID: {new_analysis.id}")
        except Exception as e:
            print(f"[SysCRED-DB] Save failed: {e}")

        return jsonify(result), 200
        
    except Exception as e:
        print(f"[SysCRED Backend] Error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@app.route('/api/seo', methods=['POST'])
def seo_endpoint():
    """
    SEO-only analysis endpoint (faster, no ML models needed).
    
    Request JSON:
    {
        "url": "URL to analyze"
    }
    """
    global seo_analyzer
    
    if seo_analyzer is None:
        seo_analyzer = SEOAnalyzer()
    
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url or not url.startswith('http'):
        return jsonify({'error': 'Valid URL is required'}), 400
    
    try:
        # Fetch content
        from syscred.api_clients import ExternalAPIClients
        api_client = ExternalAPIClients()
        
        web_content = api_client.fetch_web_content(url)
        if not web_content.success:
            return jsonify({'error': f'Failed to fetch URL: {web_content.error}'}), 400
        
        # SEO analysis
        seo_result = seo_analyzer.analyze_seo(
            url=url,
            title=web_content.title,
            meta_description=web_content.meta_description,
            text_content=web_content.text_content
        )
        
        # IR metrics
        ir_metrics = seo_analyzer.get_ir_metrics(web_content.text_content)
        
        # PageRank estimation
        external_data = api_client.fetch_external_data(url)
        pr_result = seo_analyzer.estimate_pagerank(
            url=url,
            domain_age_days=external_data.domain_age_days,
            source_reputation=external_data.source_reputation
        )
        
        return jsonify({
            'url': url,
            'title': web_content.title,
            'seo': {
                'titleLength': seo_result.title_length,
                'metaDescriptionLength': seo_result.meta_description_length,
                'wordCount': seo_result.word_count,
                'readabilityScore': round(seo_result.readability_score, 2),
                'seoScore': round(seo_result.seo_score, 2),
                'keywordDensity': seo_result.keyword_density
            },
            'irMetrics': {
                'documentLength': ir_metrics.document_length,
                'topTerms': ir_metrics.top_terms[:5],
                'avgTermFrequency': round(ir_metrics.avg_term_frequency, 4)
            },
            'pageRank': {
                'estimated': round(pr_result.estimated_pr, 3),
                'confidence': round(pr_result.confidence, 2),
                'factors': pr_result.factors
            },
            'domain': {
                'reputation': external_data.source_reputation,
                'ageDays': external_data.domain_age_days
            }
        }), 200
        
    except Exception as e:
        print(f"[SysCRED Backend] SEO endpoint error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@app.route('/api/ontology/graph', methods=['GET'])
def ontology_graph():
    """Get ontology graph data for D3.js."""
    global credibility_system
    
    if credibility_system and credibility_system.ontology_manager:
        graph_data = credibility_system.ontology_manager.get_graph_json()
        return jsonify(graph_data), 200
    else:
        # Return empty graph rather than 400 to avoid breaking frontend
        return jsonify({'nodes': [], 'links': []}), 200


@app.route('/api/ontology/stats', methods=['GET'])
def ontology_stats():
    """Get ontology statistics."""
    global credibility_system
    
    if credibility_system and credibility_system.ontology_manager:
        stats = credibility_system.ontology_manager.get_statistics()
        return jsonify(stats), 200
    else:
        return jsonify({
            'error': 'Ontology not loaded',
            'base_triples': 0,
            'data_triples': 0
        }), 200


# --- TREC Endpoints ---

@app.route('/api/trec/search', methods=['POST'])
def trec_search():
    """
    Search for evidence using TREC retrieval methods.
    
    Request JSON:
    {
        "query": "Claim or query to search for",
        "k": 10,              # Number of results (optional, default 10)
        "model": "bm25"       # Retrieval model: bm25, tfidf, qld (optional)
    }
    
    Response:
    {
        "query": "original query",
        "results": [
            {"doc_id": "AP880101-0001", "score": 6.27, "rank": 1, "text": "...", "title": "..."},
            ...
        ],
        "total": 3,
        "model": "bm25",
        "search_time_ms": 12.5
    }
    """
    global trec_retriever, eval_metrics
    
    # Initialize TREC components if needed
    if trec_retriever is None:
        try:
            trec_retriever = TRECRetriever(use_stemming=True, enable_prf=False)
            trec_retriever.corpus = TREC_DEMO_CORPUS
            eval_metrics = EvaluationMetrics()
            print("[SysCRED Backend] TREC Retriever initialized with demo corpus")
        except Exception as e:
            return jsonify({'error': f'TREC initialization failed: {str(e)}'}), 503
    
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': "'query' is required"}), 400
    
    k = data.get('k', 10)
    model = data.get('model', 'bm25')
    
    try:
        import time
        start_time = time.time()
        
        # Retrieve evidence
        result = trec_retriever.retrieve_evidence(query, k=k, model=model)
        search_time_ms = (time.time() - start_time) * 1000
        
        # Format results
        results = []
        for ev in result.evidences:
            doc_info = trec_retriever.corpus.get(ev.doc_id, {})
            results.append({
                'doc_id': ev.doc_id,
                'score': round(ev.score, 4),
                'rank': ev.rank,
                'text': ev.text,
                'title': doc_info.get('title', ''),
                'model': ev.retrieval_model
            })
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'model': model,
            'search_time_ms': round(search_time_ms, 2)
        }), 200
        
    except Exception as e:
        print(f"[SysCRED Backend] TREC search error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/trec/corpus', methods=['GET'])
def trec_corpus():
    """
    Get the TREC demo corpus information.
    
    Response:
    {
        "corpus_size": 7,
        "corpus_type": "AP88-90 Demo",
        "documents": [
            {"doc_id": "AP880101-0001", "title": "...", "text_preview": "..."},
            ...
        ]
    }
    """
    docs = []
    for doc_id, doc in TREC_DEMO_CORPUS.items():
        docs.append({
            'doc_id': doc_id,
            'title': doc.get('title', ''),
            'text_preview': doc['text'][:150] + '...' if len(doc['text']) > 150 else doc['text']
        })
    
    return jsonify({
        'corpus_size': len(TREC_DEMO_CORPUS),
        'corpus_type': 'AP88-90 Demo',
        'documents': docs
    }), 200


@app.route('/api/trec/metrics', methods=['POST'])
def trec_metrics():
    """
    Calculate IR evaluation metrics for a retrieval result.
    
    Request JSON:
    {
        "retrieved": ["AP880101-0001", "AP890215-0001", "AP880101-0002"],
        "relevant": ["AP880101-0001", "AP880101-0002", "AP880102-0001"]
    }
    
    Response:
    {
        "precision_at_3": 0.67,
        "recall_at_3": 0.67,
        "average_precision": 0.81,
        "mrr": 1.0,
        "ndcg_at_3": 0.88
    }
    """
    global eval_metrics
    
    if eval_metrics is None:
        eval_metrics = EvaluationMetrics()
    
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.get_json()
    retrieved = data.get('retrieved', [])
    relevant = set(data.get('relevant', []))
    
    if not retrieved:
        return jsonify({'error': "'retrieved' list is required"}), 400
    
    k = len(retrieved)
    
    try:
        # Calculate metrics
        p_at_k = eval_metrics.precision_at_k(retrieved, relevant, k)
        r_at_k = eval_metrics.recall_at_k(retrieved, relevant, k)
        ap = eval_metrics.average_precision(retrieved, relevant)
        mrr = eval_metrics.mrr(retrieved, relevant)
        
        # For NDCG, create relevance dict (binary: 1 if relevant, 0 otherwise)
        relevance_dict = {doc: 1 for doc in relevant}
        ndcg = eval_metrics.ndcg_at_k(retrieved, relevance_dict, k)
        
        return jsonify({
            f'precision_at_{k}': round(p_at_k, 4),
            f'recall_at_{k}': round(r_at_k, 4),
            'average_precision': round(ap, 4),
            'mrr': round(mrr, 4),
            f'ndcg_at_{k}': round(ndcg, 4),
            'metrics_explanation': {
                'P@K': 'Proportion de documents pertinents parmi les K premiers récupérés',
                'R@K': 'Proportion de documents pertinents récupérés parmi tous les pertinents',
                'AP': 'Moyenne des précisions à chaque document pertinent trouvé',
                'MRR': 'Rang réciproque du premier document pertinent',
                'NDCG': 'Gain cumulatif normalisé avec décroissance logarithmique'
            }
        }), 200
        
    except Exception as e:
        print(f"[SysCRED Backend] TREC metrics error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trec/health', methods=['GET'])
def trec_health():
    """Health check for TREC module."""
    return jsonify({
        'status': 'healthy',
        'trec_available': TREC_AVAILABLE if 'TREC_AVAILABLE' in dir() else True,
        'retriever_initialized': trec_retriever is not None,
        'corpus_size': len(TREC_DEMO_CORPUS),
        'models_available': ['bm25', 'tfidf', 'qld']
    }), 200


# --- Main ---
if __name__ == '__main__':
    print("=" * 60)
    print("SysCRED Backend API Server")
    print("(c) Dominique S. Loyer - PhD Thesis Prototype")
    print("=" * 60)
    print()
    
    # Initialize system at startup
    print("[SysCRED Backend] Pre-initializing system...")
    initialize_system()
    
    print()
    print("[SysCRED Backend] Starting Flask server...")
    print("[SysCRED Backend] Endpoints:")
    print("  - POST /api/verify          - Full credibility verification")
    print("  - POST /api/seo             - SEO analysis only (faster)")
    print("  - GET  /api/ontology/stats  - Ontology statistics")
    print("  - GET  /api/health          - Health check")
    print("  --- TREC Endpoints ---")
    print("  - POST /api/trec/search     - Evidence retrieval (BM25/TF-IDF/QLD)")
    print("  - POST /api/trec/metrics    - Calculate IR metrics (MAP, P@K, NDCG)")
    print("  - GET  /api/trec/corpus     - Demo corpus info")
    print("  - GET  /api/trec/health     - TREC module health")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
