
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime

# Add project root to path (one level up from this script)
sys.path.append(str(Path(__file__).parent.parent))

from syscred.verification_system import CredibilityVerificationSystem
from syscred.config import config

def run_benchmark():
    print("="*60)
    print("      SysCRED v2.1 - Scientific Evaluation Benchmark      ")
    print("="*60)
    
    # Load Benchmark Data
    data_path = Path(__file__).parent / "benchmark_data.json"
    if not data_path.exists():
        print(f"❌ Error: {data_path} not found.")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)
    
    print(f"Loaded {len(dataset)} test cases.\n")

    # Initialize System with Full Capabilities
    print("Initializing SysCRED (ML Models + Google API)...")
    system = CredibilityVerificationSystem(
        ontology_base_path=str(config.ONTOLOGY_BASE_PATH),
        ontology_data_path=str(config.ONTOLOGY_DATA_PATH),
        load_ml_models=True, # Use full ML for benchmark
        google_api_key=config.GOOGLE_FACT_CHECK_API_KEY
    )
    print("System ready.\n")

    results = []
    
    # Run Evaluation
    for i, item in enumerate(dataset):
        url = item['url']
        label = item['label']
        print(f"[{i+1}/{len(dataset)}] Analyzing: {url} (Expected: {label})...")
        
        start_time = time.time()
        try:
            # Run analysis
            # We treat empty text fallbacks as valid logic path
            report = system.verify_information(url)
            score = report.get('score_credibilite', 0.5)
            
            # Determine System Verdict
            sys_verdict = "High" if score >= 0.55 else "Low"
            
            # Compare
            match = (sys_verdict == label) or (label == "High" and sys_verdict == "High") or (label == "Low" and sys_verdict == "Low")
            # Handling Medium? For binary benchmark, we assume simplified threshold.
            # Or we can map:
            #   High (>=0.7)
            #   Medium (0.4-0.7)
            #   Low (<0.4)
            
            # Simple Binary Metric for Precision/Recall:
            # Positive Class = "High Credibility"
            
            results.append({
                "url": url,
                "expected": label,
                "score": score,
                "system_verdict": sys_verdict,
                "match": match,
                "time": time.time() - start_time,
                "error": None
            })
            print(f"   -> Score: {score:.2f} | Verdict: {sys_verdict} | match: {'✅' if match else '❌'}")
            
        except Exception as e:
            print(f"   -> ❌ Error: {e}")
            results.append({
                "url": url,
                "expected": label,
                "score": 0,
                "system_verdict": "Error",
                "match": False,
                "time": time.time() - start_time,
                "error": str(e)
            })

    # Calculate Metrics
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    df = pd.DataFrame(results)
    
    # Logic for metrics
    # TP: System=High, Expected=High
    # FP: System=High, Expected=Low
    # TN: System=Low, Expected=Low
    # FN: System=Low, Expected=High
    
    tp = len(df[(df['system_verdict'] == 'High') & (df['expected'] == 'High')])
    fp = len(df[(df['system_verdict'] == 'High') & (df['expected'] == 'Low')])
    tn = len(df[(df['system_verdict'] == 'Low') & (df['expected'] == 'Low')])
    fn = len(df[(df['system_verdict'] == 'Low') & (df['expected'] == 'High')])
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    accuracy = (tp + tn) / len(df) if len(df) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"Total Cases: {len(df)}")
    print(f"Accuracy:    {accuracy:.2%}")
    print(f"Precision:   {precision:.2%}")
    print(f"Recall:      {recall:.2%}")
    print(f"F1-Score:    {f1:.2f}")
    
    print("\nConfusion Matrix:")
    print(f"      | Pred High | Pred Low")
    print(f"True High |    {tp}    |    {fn}")
    print(f"True Low  |    {fp}    |    {tn}")
    
    # Save detailed report
    report_path = Path(__file__).parent / "benchmark_results.csv"
    df.to_csv(report_path, index=False)
    print(f"\nDetailed CSV Saved to: {report_path}")

if __name__ == "__main__":
    run_benchmark()
