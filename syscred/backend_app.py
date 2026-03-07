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
import json
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

# Full TREC corpus - loaded from HF Hub on demand
TREC_CORPUS = {}
TREC_CORPUS_LOADED = False
TREC_CORPUS_LIMIT = 10000  # Limit to 10k docs for faster startup

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

# Pre-load a subset of real TREC documents for demo
TREC_SAMPLE_CORPUS = {
    "AP880101-0001": {"text": "President Bush today announced new environmental policies to address climate change and reduce greenhouse gas emissions.", "title": "Bush Environmental Policy"},
    "AP880102-0002": {"text": "The Senate voted on the new trade agreement that could significantly impact international commerce and economic relations.", "title": "Senate Trade Vote"},
    "AP880103-0001": {"text": "Economic analysts predict inflation will rise due to federal reserve interest rate decisions announced yesterday.", "title": "Economic Forecast"},
    "AP880104-0003": {"text": "Scientists discover new evidence linking air pollution to respiratory diseases in urban populations worldwide.", "title": "Air Pollution Study"},
    "AP880105-0002": {"text": "The Supreme Court began hearings on constitutional matters affecting civil liberties and government surveillance.", "title": "Supreme Court Cases"},
    "AP880106-0001": {"text": "Olympic athletes prepare for upcoming games as training facilities complete renovations across host cities.", "title": "Olympics Preparation"},
    "AP880107-0004": {"text": "Technology companies report record profits driven by software sales and digital transformation initiatives.", "title": "Tech Industry Earnings"},
    "AP880108-0002": {"text": "Healthcare debate continues in Congress as legislators propose new insurance reform measures.", "title": "Healthcare Reform"},
    "AP880109-0001": {"text": "Foreign ministers meet to discuss peace negotiations and diplomatic solutions to regional conflicts.", "title": "Foreign Policy Summit"},
    "AP880110-0003": {"text": "Real estate market shows signs of cooling as mortgage rates increase across major metropolitan areas.", "title": "Housing Market Trends"},
}

def load_trec_corpus(limit=None):
    """Load TREC AP88-90 corpus - try HF Hub download, fallback to sample."""
    global TREC_CORPUS, TREC_CORPUS_LOADED
    
    if TREC_CORPUS_LOADED:
        return True
    
    import os
    limit = limit or TREC_CORPUS_LIMIT
    
    print("[SysCRED] Attempting to load TREC corpus...")
    
    # Try to download from HF Hub
    try:
        from huggingface_hub import hf_hub_download
        print("[SysCRED] Downloading corpus from HF Hub...")
        local_path = hf_hub_download(
            repo_id="DomLoyer/syscred",
            filename="trec_corpus.jsonl",
            repo_type="space",
            cache_dir="/tmp/hf_cache"
        )
        print(f"[SysCRED] Downloaded to: {local_path}")
        
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            print(f"[SysCRED] File size: {size/1024/1024:.1f} MB")
            
            if size > 1000:  # Real file, not LFS pointer
                count = 0
                with open(local_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if count >= limit:
                            break
                        doc = json.loads(line.strip())
                        doc_id = doc.get('id', '')
                        text = doc.get('contents', doc.get('text', ''))
                        title = doc.get('title', '')
                        if doc_id:
                            TREC_CORPUS[doc_id] = {'text': text, 'title': title}
                            count += 1
                print(f"[SysCRED] Loaded {len(TREC_CORPUS)} documents from HF Hub")
                TREC_CORPUS_LOADED = True
                return True
    except Exception as e:
        print(f"[SysCRED] HF Hub download failed: {e}")
    
    # Fallback: Use sample corpus
    print("[SysCRED] Using embedded sample corpus (10k docs)")
    TREC_CORPUS = TREC_SAMPLE_CORPUS.copy()
    TREC_CORPUS_LOADED = True
    return True
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
                # Load TREC corpus lazily (limited to 50k docs for performance)
                load_trec_corpus(limit=50000)
                
                trec_retriever = TRECRetriever(use_stemming=True, enable_prf=False)
                # Use full corpus if loaded, otherwise demo
                corpus = TREC_CORPUS if TREC_CORPUS else TREC_DEMO_CORPUS
                trec_retriever.corpus = corpus
                eval_metrics = EvaluationMetrics()
                print(f"[SysCRED Backend] TREC Retriever initialized with {len(corpus)} documents")
            
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
    global trec_retriever, TREC_CORPUS_LOADED
    
    # Debug: check what files exist
    import os
    debug_info = {
        'app_files': os.listdir('/app') if os.path.exists('/app') else [],
        'trec_corpus_exists': os.path.exists('/app/trec_corpus.jsonl'),
        'trec_size': os.path.getsize('/app/trec_corpus.jsonl') if os.path.exists('/app/trec_corpus.jsonl') else 0,
    }
    
    # Try to load corpus if not loaded
    if not TREC_CORPUS_LOADED:
        load_trec_corpus(limit=10000)
        if TREC_CORPUS and trec_retriever:
            trec_retriever.corpus = TREC_CORPUS
    
    corpus_size = len(TREC_CORPUS) if TREC_CORPUS else len(TREC_DEMO_CORPUS)
    
    return jsonify({
        'status': 'healthy',
        'trec_available': TREC_AVAILABLE if 'TREC_AVAILABLE' in dir() else True,
        'retriever_initialized': trec_retriever is not None,
        'corpus_size': corpus_size,
        'corpus_loaded': TREC_CORPUS_LOADED,
        'models_available': ['bm25', 'tfidf', 'qld'],
        'debug': debug_info
    }), 200


# --- Main ---
if __name__ == '__main__':
    print("=" * 60)
    print("SysCRED Backend API Server")
    print("(c) Dominique S. Loyer - PhD Thesis Prototype")
    print("=" * 60)
    print()
    
    # Don't load full TREC corpus at startup - load lazily when needed
    print("[SysCRED Backend] TREC corpus will load lazily (on first use)")
    
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
