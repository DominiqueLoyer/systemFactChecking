#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIAR Benchmark Runner - SysCRED
================================
Scientific evaluation of SysCRED on the LIAR benchmark dataset.

Usage:
    python run_liar_benchmark.py --split test
    python run_liar_benchmark.py --sample 100 --verbose
    python run_liar_benchmark.py --split test --output results/liar_benchmark.csv

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import argparse
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[Warning] pandas not installed. CSV export will be limited.")

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[Warning] sklearn not installed. Using basic metrics.")

from syscred.liar_dataset import LIARDataset, LiarStatement
from syscred.verification_system import CredibilityVerificationSystem
from syscred import config


class LIARBenchmark:
    """
    Benchmark runner for evaluating SysCRED on LIAR dataset.
    """
    
    # Map SysCRED score to binary label
    SYSCRED_THRESHOLD = 0.5  # Below = Fake, Above = Real
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        load_ml: bool = True,
        use_graphrag: bool = True
    ):
        """
        Initialize benchmark.
        
        Args:
            data_dir: Path to LIAR dataset directory
            load_ml: Whether to load ML models
            use_graphrag: Whether to use GraphRAG context
        """
        print("=" * 60)
        print("SysCRED LIAR Benchmark Runner")
        print("=" * 60)
        
        # Load dataset
        self.dataset = LIARDataset(data_dir)
        
        # Initialize SysCRED
        print("\n[Benchmark] Initializing SysCRED...")
        self.system = CredibilityVerificationSystem(
            ontology_base_path=str(config.Config.ONTOLOGY_BASE_PATH),
            ontology_data_path=str(config.Config.ONTOLOGY_DATA_PATH),
            load_ml_models=load_ml,
            google_api_key=config.Config.GOOGLE_FACT_CHECK_API_KEY
        )
        
        self.use_graphrag = use_graphrag
        self.results: List[Dict] = []
        
        print("[Benchmark] System ready.\n")
    
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
        """
        Evaluate a single statement.
        
        Args:
            statement: LiarStatement to evaluate
            
        Returns:
            Result dictionary with prediction and ground truth
        """
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
            'error': None
        }
        
        try:
            # Run SysCRED analysis on the statement text
            # Note: LIAR statements are short claims, not URLs
            report = self.system.verify_information(statement.statement)
            
            if 'error' not in report:
                score = report.get('scoreCredibilite', 0.5)
                result['syscred_score'] = score
                result['predicted_binary'] = self._syscred_to_binary(score)
                result['predicted_ternary'] = self._syscred_to_ternary(score)
                
                # Check correctness
                result['binary_correct'] = (result['predicted_binary'] == result['ground_truth_binary'])
                result['ternary_correct'] = (result['predicted_ternary'] == result['ground_truth_ternary'])
                
                # Add extra details if available
                if 'analyseNLP' in report:
                    result['sentiment'] = report['analyseNLP'].get('sentiment', {})
                    result['bias'] = report['analyseNLP'].get('bias_analysis', {})
            else:
                result['error'] = report['error']
                
        except Exception as e:
            result['error'] = str(e)
        
        result['processing_time'] = time.time() - start_time
        
        return result
    
    def run_benchmark(
        self,
        split: str = "test",
        sample_size: Optional[int] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run full benchmark on a dataset split.
        
        Args:
            split: 'train', 'valid', or 'test'
            sample_size: If set, only evaluate this many statements
            verbose: Print progress for each statement
            
        Returns:
            Dictionary with metrics and detailed results
        """
        print(f"\n[Benchmark] Running on {split} split...")
        
        # Load dataset
        statements = self.dataset.load_split(split)
        
        if sample_size:
            import random
            statements = random.sample(statements, min(sample_size, len(statements)))
            print(f"[Benchmark] Using sample of {len(statements)} statements")
        
        total = len(statements)
        self.results = []
        
        # Progress tracking
        start_time = time.time()
        
        for i, stmt in enumerate(statements):
            if verbose or (i + 1) % 50 == 0:
                print(f"[{i+1}/{total}] Processing: {stmt.statement[:50]}...")
            
            result = self.evaluate_statement(stmt)
            self.results.append(result)
            
            if verbose:
                symbol = "✅" if result['binary_correct'] else "❌"
                print(f"  -> Score: {result['syscred_score']:.2f} | "
                      f"Pred: {result['predicted_binary']} | "
                      f"True: {result['ground_truth_binary']} {symbol}")
        
        elapsed = time.time() - start_time
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        metrics['elapsed_time'] = elapsed
        metrics['statements_per_second'] = total / elapsed if elapsed > 0 else 0
        
        return metrics
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate evaluation metrics from results."""
        
        if not self.results:
            return {'error': 'No results to evaluate'}
        
        # Filter successful evaluations
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
        
        # Extract labels
        y_true_binary = [r['ground_truth_binary'] for r in valid_results]
        y_pred_binary = [r['predicted_binary'] for r in valid_results]
        
        y_true_ternary = [r['ground_truth_ternary'] for r in valid_results]
        y_pred_ternary = [r['predicted_ternary'] for r in valid_results]
        
        # Binary metrics
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
                'confusion_matrix': confusion_matrix(y_true_ternary, y_pred_ternary, 
                                                     labels=['False', 'Mixed', 'True']).tolist()
            }
            
            # Detailed classification report
            metrics['classification_report'] = classification_report(
                y_true_binary, y_pred_binary, 
                target_names=['Fake', 'Real'],
                output_dict=True
            )
        else:
            # Basic metrics without sklearn
            correct_binary = sum(1 for r in valid_results if r['binary_correct'])
            correct_ternary = sum(1 for r in valid_results if r['ternary_correct'])
            
            metrics['binary'] = {
                'accuracy': correct_binary / len(valid_results),
                'correct': correct_binary,
                'incorrect': len(valid_results) - correct_binary
            }
            
            metrics['ternary'] = {
                'accuracy': correct_ternary / len(valid_results),
                'correct': correct_ternary,
                'incorrect': len(valid_results) - correct_ternary
            }
        
        # Score distribution
        scores = [r['syscred_score'] for r in valid_results]
        metrics['score_distribution'] = {
            'mean': sum(scores) / len(scores),
            'min': min(scores),
            'max': max(scores),
            'median': sorted(scores)[len(scores) // 2]
        }
        
        # Per-party analysis
        party_results = {}
        for party in ['republican', 'democrat']:
            party_items = [r for r in valid_results if r['party'].lower() == party]
            if party_items:
                party_correct = sum(1 for r in party_items if r['binary_correct'])
                party_results[party] = {
                    'count': len(party_items),
                    'accuracy': party_correct / len(party_items)
                }
        metrics['per_party'] = party_results
        
        return metrics
    
    def print_results(self, metrics: Dict[str, Any]) -> None:
        """Pretty-print benchmark results."""
        print("\n" + "=" * 60)
        print("LIAR BENCHMARK RESULTS")
        print("=" * 60)
        
        print(f"\n📊 Overview:")
        print(f"  Total Statements: {metrics.get('total_statements', 0)}")
        print(f"  Successful: {metrics.get('successful_evaluations', 0)}")
        print(f"  Errors: {metrics.get('error_count', 0)} ({metrics.get('error_rate', 0):.1%})")
        print(f"  Processing Time: {metrics.get('elapsed_time', 0):.1f}s")
        print(f"  Speed: {metrics.get('statements_per_second', 0):.2f} stmt/sec")
        
        if 'binary' in metrics:
            print(f"\n📈 Binary Classification (Fake vs Real):")
            b = metrics['binary']
            print(f"  Accuracy:  {b.get('accuracy', 0):.2%}")
            print(f"  Precision: {b.get('precision', 0):.2%}")
            print(f"  Recall:    {b.get('recall', 0):.2%}")
            print(f"  F1-Score:  {b.get('f1', 0):.2f}")
            
            if 'confusion_matrix' in b:
                cm = b['confusion_matrix']
                print(f"\n  Confusion Matrix:")
                print(f"              Pred Fake  Pred Real")
                print(f"  True Fake    {cm[0][0]:5d}      {cm[0][1]:5d}")
                print(f"  True Real    {cm[1][0]:5d}      {cm[1][1]:5d}")
        
        if 'ternary' in metrics:
            print(f"\n📊 Ternary Classification (False/Mixed/True):")
            t = metrics['ternary']
            print(f"  Accuracy:  {t.get('accuracy', 0):.2%}")
            print(f"  Macro F1:  {t.get('macro_f1', 0):.2f}")
        
        if 'per_party' in metrics:
            print(f"\n🏛️ Per-Party Analysis:")
            for party, data in metrics['per_party'].items():
                print(f"  {party.capitalize()}: {data['accuracy']:.2%} accuracy ({data['count']} samples)")
        
        if 'score_distribution' in metrics:
            print(f"\n📉 Score Distribution:")
            sd = metrics['score_distribution']
            print(f"  Mean:   {sd['mean']:.3f}")
            print(f"  Median: {sd['median']:.3f}")
            print(f"  Range:  [{sd['min']:.3f}, {sd['max']:.3f}]")
        
        print("\n" + "=" * 60)
    
    def save_results(self, output_path: str, metrics: Dict[str, Any]) -> None:
        """Save results to files."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results as CSV
        if HAS_PANDAS and self.results:
            df = pd.DataFrame(self.results)
            csv_path = output.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            print(f"[Benchmark] Results saved to: {csv_path}")
        
        # Save metrics as JSON
        json_path = output.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dataset': 'LIAR',
                'metrics': metrics,
                'config': {
                    'threshold': self.SYSCRED_THRESHOLD,
                    'use_graphrag': self.use_graphrag,
                    'weights': dict(self.system.weights)
                }
            }, f, indent=2, default=str)
        print(f"[Benchmark] Metrics saved to: {json_path}")


def main():
    parser = argparse.ArgumentParser(description='Run LIAR benchmark on SysCRED')
    parser.add_argument('--split', type=str, default='test',
                       choices=['train', 'valid', 'test'],
                       help='Dataset split to evaluate')
    parser.add_argument('--sample', type=int, default=None,
                       help='Number of statements to sample (for quick testing)')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Path to LIAR dataset directory')
    parser.add_argument('--output', type=str, default=None,
                       help='Output path for results (CSV/JSON)')
    parser.add_argument('--no-ml', action='store_true',
                       help='Disable ML models for faster testing')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print details for each statement')
    
    args = parser.parse_args()
    
    # Run benchmark
    benchmark = LIARBenchmark(
        data_dir=args.data_dir,
        load_ml=not args.no_ml
    )
    
    try:
        metrics = benchmark.run_benchmark(
            split=args.split,
            sample_size=args.sample,
            verbose=args.verbose
        )
        
        benchmark.print_results(metrics)
        
        if args.output:
            benchmark.save_results(args.output, metrics)
        else:
            # Default output path
            default_output = Path(__file__).parent / f"liar_benchmark_{args.split}.csv"
            benchmark.save_results(str(default_output), metrics)
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo download the LIAR dataset:")
        print("  1. wget https://www.cs.ucsb.edu/~william/data/liar_dataset.zip")
        print("  2. unzip liar_dataset.zip -d 02_Code/syscred/datasets/liar/")
        sys.exit(1)


if __name__ == "__main__":
    main()
