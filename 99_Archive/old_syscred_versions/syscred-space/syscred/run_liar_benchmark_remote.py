#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIAR Benchmark via Hugging Face Space API
==========================================
Runs the LIAR benchmark against the remote SysCRED instance on HF Space.
This uses the full ML pipeline (PyTorch, Transformers) running in the cloud.

Usage:
    python run_liar_benchmark_remote.py --sample 100
    python run_liar_benchmark_remote.py --split test --url https://your-space.hf.space

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import argparse
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from syscred.liar_dataset import LIARDataset, LiarStatement


class RemoteLIARBenchmark:
    """
    Benchmark runner using remote HF Space API.
    """
    
    # Default HF Space URL
    DEFAULT_API_URL = "https://domloyer-syscred.hf.space"
    
    SYSCRED_THRESHOLD = 0.5  # Below = Fake, Above = Real
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        data_dir: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize remote benchmark.
        
        Args:
            api_url: HF Space API URL
            data_dir: Path to LIAR dataset
            timeout: Request timeout in seconds
        """
        print("=" * 60)
        print("SysCRED LIAR Benchmark (Remote HF Space)")
        print("=" * 60)
        
        self.api_url = (api_url or self.DEFAULT_API_URL).rstrip('/')
        self.timeout = timeout
        
        # Test connection
        print(f"\n[Remote] API URL: {self.api_url}")
        self._test_connection()
        
        # Load dataset
        self.dataset = LIARDataset(data_dir)
        self.results: List[Dict] = []
        
        print("[Remote] Ready.\n")
    
    def _test_connection(self):
        """Test API connectivity."""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=10)
            if response.status_code == 200:
                print("[Remote] ✓ API connection successful")
            else:
                print(f"[Remote] ⚠ API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("[Remote] ⚠ Could not connect to API (may be sleeping)")
            print("[Remote] The first request will wake it up...")
        except Exception as e:
            print(f"[Remote] ⚠ Connection test failed: {e}")
    
    def _call_api(self, text: str) -> Dict[str, Any]:
        """Call the SysCRED API."""
        try:
            response = requests.post(
                f"{self.api_url}/api/verify",
                json={"input": text},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error"}
        except Exception as e:
            return {"error": str(e)}
    
    def _syscred_to_binary(self, score: float) -> str:
        """Convert SysCRED score to binary label."""
        return "Real" if score >= self.SYSCRED_THRESHOLD else "Fake"
    
    def _syscred_to_ternary(self, score: float) -> str:
        """Convert SysCRED score to ternary label."""
        if score >= 0.65:
            return "True"
        elif score >= 0.35:
            return "Mixed"
        else:
            return "False"
    
    def evaluate_statement(self, statement: LiarStatement) -> Dict[str, Any]:
        """Evaluate a single statement via API."""
        start_time = time.time()
        
        result = {
            'id': statement.id,
            'statement': statement.statement[:200],
            'ground_truth_6way': statement.label.name,
            'ground_truth_binary': statement.binary_label,
            'ground_truth_ternary': statement.ternary_label,
            'speaker': statement.speaker,
            'party': statement.party,
            'syscred_score': 0.5,
            'predicted_binary': 'Unknown',
            'predicted_ternary': 'Unknown',
            'binary_correct': False,
            'ternary_correct': False,
            'processing_time': 0,
            'error': None,
            'ml_used': False
        }
        
        # Call remote API
        api_result = self._call_api(statement.statement)
        
        if 'error' not in api_result:
            score = api_result.get('scoreCredibilite', 0.5)
            result['syscred_score'] = score
            result['predicted_binary'] = self._syscred_to_binary(score)
            result['predicted_ternary'] = self._syscred_to_ternary(score)
            
            result['binary_correct'] = (result['predicted_binary'] == result['ground_truth_binary'])
            result['ternary_correct'] = (result['predicted_ternary'] == result['ground_truth_ternary'])
            
            # Check if ML was used
            nlp = api_result.get('analyseNLP', {})
            result['ml_used'] = nlp.get('sentiment') is not None
            
            # GraphRAG info
            graphrag = api_result.get('graphRAG', {})
            result['graph_context_score'] = graphrag.get('context_score')
            result['graph_has_history'] = graphrag.get('has_history', False)
        else:
            result['error'] = api_result['error']
        
        result['processing_time'] = time.time() - start_time
        
        return result
    
    def run_benchmark(
        self,
        split: str = "test",
        sample_size: Optional[int] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Run benchmark against remote API."""
        print(f"\n[Remote] Running on {split} split via HF Space API...")
        
        statements = self.dataset.load_split(split)
        
        if sample_size:
            import random
            statements = random.sample(statements, min(sample_size, len(statements)))
            print(f"[Remote] Using sample of {len(statements)} statements")
        
        total = len(statements)
        self.results = []
        ml_used_count = 0
        
        start_time = time.time()
        
        for i, stmt in enumerate(statements):
            if verbose or (i + 1) % 10 == 0:
                print(f"[{i+1}/{total}] Processing: {stmt.statement[:50]}...")
            
            result = self.evaluate_statement(stmt)
            self.results.append(result)
            
            if result.get('ml_used'):
                ml_used_count += 1
            
            if verbose and not result.get('error'):
                symbol = "✅" if result['binary_correct'] else "❌"
                ml = "🧠" if result['ml_used'] else "📊"
                print(f"  -> Score: {result['syscred_score']:.2f} {ml} | "
                      f"Pred: {result['predicted_binary']} | "
                      f"True: {result['ground_truth_binary']} {symbol}")
            
            # Rate limiting - be nice to the API
            if i < total - 1:
                time.sleep(0.5)
        
        elapsed = time.time() - start_time
        
        metrics = self._calculate_metrics()
        metrics['elapsed_time'] = elapsed
        metrics['statements_per_second'] = total / elapsed if elapsed > 0 else 0
        metrics['ml_used_percentage'] = (ml_used_count / total * 100) if total > 0 else 0
        metrics['api_url'] = self.api_url
        
        return metrics
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate evaluation metrics."""
        if not self.results:
            return {'error': 'No results'}
        
        valid_results = [r for r in self.results if r['error'] is None]
        error_count = len(self.results) - len(valid_results)
        
        if not valid_results:
            return {'error': 'All evaluations failed'}
        
        metrics = {
            'total_statements': len(self.results),
            'successful_evaluations': len(valid_results),
            'error_count': error_count,
            'error_rate': error_count / len(self.results)
        }
        
        y_true_binary = [r['ground_truth_binary'] for r in valid_results]
        y_pred_binary = [r['predicted_binary'] for r in valid_results]
        
        y_true_ternary = [r['ground_truth_ternary'] for r in valid_results]
        y_pred_ternary = [r['predicted_ternary'] for r in valid_results]
        
        if HAS_SKLEARN:
            metrics['binary'] = {
                'accuracy': accuracy_score(y_true_binary, y_pred_binary),
                'precision': precision_score(y_true_binary, y_pred_binary, pos_label='Fake', zero_division=0),
                'recall': recall_score(y_true_binary, y_pred_binary, pos_label='Fake', zero_division=0),
                'f1': f1_score(y_true_binary, y_pred_binary, pos_label='Fake', zero_division=0),
                'confusion_matrix': confusion_matrix(y_true_binary, y_pred_binary, labels=['Fake', 'Real']).tolist()
            }
            
            metrics['ternary'] = {
                'accuracy': accuracy_score(y_true_ternary, y_pred_ternary),
                'macro_f1': f1_score(y_true_ternary, y_pred_ternary, average='macro', zero_division=0),
            }
        else:
            correct_binary = sum(1 for r in valid_results if r['binary_correct'])
            metrics['binary'] = {'accuracy': correct_binary / len(valid_results)}
        
        scores = [r['syscred_score'] for r in valid_results]
        metrics['score_distribution'] = {
            'mean': sum(scores) / len(scores),
            'min': min(scores),
            'max': max(scores),
        }
        
        return metrics
    
    def print_results(self, metrics: Dict[str, Any]) -> None:
        """Print benchmark results."""
        print("\n" + "=" * 60)
        print("LIAR BENCHMARK RESULTS (Remote HF Space)")
        print("=" * 60)
        
        print(f"\n🌐 API: {metrics.get('api_url', 'N/A')}")
        print(f"🧠 ML Models Used: {metrics.get('ml_used_percentage', 0):.1f}%")
        
        print(f"\n📊 Overview:")
        print(f"  Total: {metrics.get('total_statements', 0)}")
        print(f"  Success: {metrics.get('successful_evaluations', 0)}")
        print(f"  Errors: {metrics.get('error_count', 0)}")
        print(f"  Time: {metrics.get('elapsed_time', 0):.1f}s")
        
        if 'binary' in metrics:
            print(f"\n📈 Binary Classification:")
            b = metrics['binary']
            print(f"  Accuracy:  {b.get('accuracy', 0):.2%}")
            print(f"  Precision: {b.get('precision', 0):.2%}")
            print(f"  Recall:    {b.get('recall', 0):.2%}")
            print(f"  F1-Score:  {b.get('f1', 0):.2f}")
        
        print("\n" + "=" * 60)
    
    def save_results(self, output_path: str, metrics: Dict[str, Any]) -> None:
        """Save results."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        if HAS_PANDAS and self.results:
            df = pd.DataFrame(self.results)
            csv_path = output.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            print(f"[Remote] Results: {csv_path}")
        
        json_path = output.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dataset': 'LIAR',
                'mode': 'remote',
                'metrics': metrics
            }, f, indent=2, default=str)
        print(f"[Remote] Metrics: {json_path}")


def main():
    parser = argparse.ArgumentParser(description='LIAR benchmark via HF Space API')
    parser.add_argument('--url', type=str, default=None,
                       help='HF Space API URL')
    parser.add_argument('--split', type=str, default='test',
                       choices=['train', 'valid', 'test'])
    parser.add_argument('--sample', type=int, default=None,
                       help='Number of statements to sample')
    parser.add_argument('--data-dir', type=str, default=None)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--timeout', type=int, default=60)
    
    args = parser.parse_args()
    
    benchmark = RemoteLIARBenchmark(
        api_url=args.url,
        data_dir=args.data_dir,
        timeout=args.timeout
    )
    
    try:
        metrics = benchmark.run_benchmark(
            split=args.split,
            sample_size=args.sample,
            verbose=args.verbose
        )
        
        benchmark.print_results(metrics)
        
        output = args.output or f"liar_benchmark_remote_{args.split}.csv"
        benchmark.save_results(output, metrics)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
