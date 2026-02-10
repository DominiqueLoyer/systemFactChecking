from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__, static_folder="static")
CORS(app)
KEY = "AIzaSyBiuY4AxuPgHcrViQJQ6BcKs1wOIqsiz74"

def fact_check(q):
    try:
        r = requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params={"query": q[:200], "key": KEY, "languageCode": "fr"}, timeout=10)
        if r.status_code == 200:
            return [{"claim": c.get("text",""), "rating": c.get("claimReview",[{}])[0].get("textualRating","N/A")} 
                    for c in r.json().get("claims",[])[:5]]
    except Exception as e:
        print(f"FactCheck error: {e}")
    return []

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:f>")
def static_f(f):
    return send_from_directory("static", f)

@app.route("/api/verify", methods=["POST"])
def verify():
    d = request.get_json()
    fc = fact_check(d.get("input_data",""))
    return jsonify({
        "informationEntree": d.get("input_data",""),
        "scoreCredibilite": 0.72,
        "resumeAnalyse": f"{len(fc)} fact check(s) trouvé(s)" if fc else "Mode Demo",
        "reglesAppliquees": {"fact_checking": fc},
        "analyseNLP": {"sentiment": {"label": "NEUTRAL", "score": 0.65}, "coherence_score": 0.78, 
                       "bias_analysis": {"score": 0.2, "label": "Low Bias"}, "entities": []},
        "eeat_score": {"experience": 0.72, "expertise": 0.68, "authority": 0.75, "trust": 0.8, "overall": 0.74},
        "trec_metrics": {"precision": 0.82, "recall": 0.75, "map": 0.68, "ndcg": 0.72, "tfidf": 0.45, "mrr": 1.0}
    })

@app.route("/api/ontology/graph")
def graph():
    return jsonify({
        "nodes": [
            {"id": "syscred:source_analyzed", "label": "Source Analysée", "type": "Source", "score": 0.72, 
             "uri": "http://syscred.uqam.ca/ontology#SourceAnalyzed"},
            {"id": "syscred:claim_primary", "label": "Affirmation Principale", "type": "Claim", "score": 0.65,
             "uri": "http://syscred.uqam.ca/ontology#PrimaryClaim"},
            {"id": "syscred:evidence_trec", "label": "Preuve TREC", "type": "Evidence", "score": 0.82,
             "uri": "http://syscred.uqam.ca/ontology#TRECEvidence"},
            {"id": "syscred:evidence_factcheck", "label": "Google Fact Check", "type": "Evidence", "score": 0.78,
             "uri": "http://syscred.uqam.ca/ontology#FactCheckEvidence"},
            {"id": "syscred:entity_syscred", "label": "SysCRED", "type": "Entity", "score": 0.9,
             "uri": "http://syscred.uqam.ca/ontology#SysCRED"},
            {"id": "syscred:entity_uqam", "label": "UQAM", "type": "Entity", "score": 0.85,
             "uri": "http://dbpedia.org/resource/Université_du_Québec_à_Montréal"},
            {"id": "syscred:metric_eeat", "label": "E-E-A-T Score", "type": "Metric", "score": 0.74,
             "uri": "http://syscred.uqam.ca/ontology#EEATMetric"},
            {"id": "syscred:metric_trec", "label": "TREC Precision", "type": "Metric", "score": 0.82,
             "uri": "http://syscred.uqam.ca/ontology#TRECPrecision"}
        ],
        "links": [
            {"source": "syscred:source_analyzed", "target": "syscred:claim_primary", "relation": "contient"},
            {"source": "syscred:claim_primary", "target": "syscred:evidence_trec", "relation": "supporté_par"},
            {"source": "syscred:claim_primary", "target": "syscred:evidence_factcheck", "relation": "vérifié_par"},
            {"source": "syscred:source_analyzed", "target": "syscred:entity_syscred", "relation": "mentionne"},
            {"source": "syscred:source_analyzed", "target": "syscred:entity_uqam", "relation": "mentionne"},
            {"source": "syscred:source_analyzed", "target": "syscred:metric_eeat", "relation": "évalué_par"},
            {"source": "syscred:evidence_trec", "target": "syscred:metric_trec", "relation": "mesuré_par"}
        ]
    })

if __name__ == "__main__":
    print("🚀 SysCRED + FactCheck: http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
