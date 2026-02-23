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
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add syscred package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SysCRED modules
try:
    from syscred.verification_system import CredibilityVerificationSystem
    from syscred.seo_analyzer import SEOAnalyzer
    from syscred.ontology_manager import OntologyManager
    from syscred.ontology_manager import OntologyManager
    from syscred.config import config, Config
    from syscred.database import init_db, db, AnalysisResult
    SYSCRED_AVAILABLE = True
    print("[SysCRED Backend] Modules imported successfully")
except ImportError as e:
    SYSCRED_AVAILABLE = False
    print(f"[SysCRED Backend] Warning: Could not import modules: {e}")
    # Define dummy init_db to prevent crash
    def init_db(app): pass

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

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize Database
try:
    init_db(app) # [NEW] Setup DB connection
except Exception as e:
    print(f"[SysCRED Backend] Warning: DB init failed: {e}")

# --- Initialize SysCRED System ---
credibility_system = None
seo_analyzer = None

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
    print("  - POST /api/verify     - Full credibility verification")
    print("  - POST /api/seo        - SEO analysis only (faster)")
    print("  - GET  /api/ontology/stats - Ontology statistics")
    print("  - GET  /api/health     - Health check")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)
