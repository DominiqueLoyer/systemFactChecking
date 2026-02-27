#!/usr/bin/env python3
"""Simple SysCRED server for testing."""
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'version': '2.3.1', 'mode': 'simple'})

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.get_json() or {}
    input_data = data.get('input_data', '')
    
    # Simplified scoring
    score = 0.5
    if 'lemonde' in input_data.lower() or 'bbc' in input_data.lower():
        score = 0.85
    elif 'fake' in input_data.lower() or 'hoax' in input_data.lower():
        score = 0.25
    
    if score >= 0.7:
        niveau = "Élevée"
    elif score >= 0.5:
        niveau = "Moyenne"
    else:
        niveau = "Faible"
    
    return jsonify({
        'scoreCredibilite': score,
        'niveauCredibilite': niveau,
        'resumeAnalyse': f'Analyse simplifiée. Score: {score}',
        'informationEntree': input_data,
        'mode': 'simple_test'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("SysCRED Simple Server - Test Mode")
    print("=" * 50)
    print("Running on http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
