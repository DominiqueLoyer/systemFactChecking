# -*- coding: utf-8 -*-
"""
TREC Benchmark Script - SysCRED
================================
Run TREC-style evaluation on the fact-checking system.

This script:
1. Loads TREC AP88-90 topics and qrels
2. Runs retrieval with multiple models (BM25, QLD, TF-IDF)
3. Evaluates using pytrec_eval metrics
4. Generates comparison tables and visualizations

Usage:
    python run_trec_benchmark.py --index /path/to/index --qrels /path/to/qrels

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from syscred.trec_retriever import TRECRetriever, RetrievalResult
from syscred.trec_dataset import TRECDataset, SAMPLE_TOPICS
from syscred.eval_metrics import EvaluationMetrics


class TRECBenchmark:
    """
    TREC-style benchmark runner for SysCRED.
    
    Runs multiple retrieval configurations and compares performance
    using standard IR metrics.
    """
    
    # Configurations to test
    CONFIGURATIONS = [
        {"name": "BM25", "model": "bm25", "prf": False},
        {"name": "BM25+PRF", "model": "bm25", "prf": True},
        {"name": "QLD", "model": "qld", "prf": False},
        {"name": "QLD+PRF", "model": "qld", "prf": True},
    ]
    
    # Metrics to evaluate
    METRICS = ["map", "ndcg", "P_10", "P_20", "recall_100", "recip_rank"]
    
    def __init__(
        self,
        index_path: str = None,
        corpus_path: str = None,
        topics_path: str = None,
        qrels_path: str = None,
        output_dir: str = None
    ):
        """
        Initialize the benchmark runner.
        
        Args:
            index_path: Path to Lucene index
            corpus_path: Path to JSONL corpus
            topics_path: Path to TREC topics
            qrels_path: Path to TREC qrels
            output_dir: Directory for output files
        """
        self.index_path = index_path
        self.corpus_path = corpus_path
        self.topics_path = topics_path
        self.qrels_path = qrels_path
        self.output_dir = Path(output_dir) if output_dir else Path("benchmark_results")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.dataset = TRECDataset(
            topics_dir=topics_path,
            qrels_dir=qrels_path,
            corpus_path=corpus_path
        )
        
        self.retriever = TRECRetriever(
            index_path=index_path,
            corpus_path=corpus_path,
            use_stemming=True
        )
        
        self.metrics = EvaluationMetrics()
        
        # Results storage
        self.results: Dict[str, Dict[str, Any]] = {}
        
    def load_data(self):
        """Load topics and qrels."""
        print("\n" + "=" * 60)
        print("Loading TREC Data")
        print("=" * 60)
        
        # Load topics
        if self.topics_path:
            self.dataset.load_topics(self.topics_path)
        else:
            # Use sample topics
            print("[Benchmark] Using sample topics (no topics file provided)")
            self.dataset.topics = SAMPLE_TOPICS.copy()
        
        # Load qrels
        if self.qrels_path:
            self.dataset.load_qrels(self.qrels_path)
        else:
            print("[Benchmark] No qrels provided - evaluation will be limited")
        
        # Load corpus if available
        if self.corpus_path:
            self.dataset.load_corpus_jsonl(self.corpus_path)
        
        stats = self.dataset.get_statistics()
        print(f"\nDataset Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    def run_configuration(
        self,
        config: Dict[str, Any],
        query_type: str = "short",
        k: int = 100
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Run a single retrieval configuration.
        
        Returns:
            (run_tag, results_dict)
        """
        config_name = config["name"]
        model = config["model"]
        use_prf = config["prf"]
        
        run_tag = f"syscred_{config_name}_{query_type}"
        
        print(f"\n--- Running: {run_tag} ---")
        
        queries = self.dataset.get_topic_queries(query_type)
        
        if not queries:
            print(f"  No queries available!")
            return run_tag, {}
        
        # Run retrieval
        start_time = time.time()
        
        all_results = []
        run_lines = []
        
        for topic_id, query_text in queries.items():
            result = self.retriever.retrieve_evidence(
                claim=query_text,
                k=k,
                model=model,
                use_prf=use_prf
            )
            
            for evidence in result.evidences:
                all_results.append({
                    "topic_id": topic_id,
                    "doc_id": evidence.doc_id,
                    "score": evidence.score,
                    "rank": evidence.rank
                })
                run_lines.append(
                    f"{topic_id} Q0 {evidence.doc_id} {evidence.rank} {evidence.score:.6f} {run_tag}"
                )
        
        elapsed = time.time() - start_time
        
        # Save run file
        run_file = self.output_dir / f"{run_tag}.run"
        with open(run_file, 'w') as f:
            f.write("\n".join(run_lines))
        
        print(f"  Queries: {len(queries)}")
        print(f"  Total results: {len(all_results)}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Saved: {run_file}")
        
        return run_tag, {
            "config": config,
            "query_type": query_type,
            "results": all_results,
            "run_file": str(run_file),
            "elapsed_time": elapsed
        }
    
    def evaluate_run(self, run_tag: str, results: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate a run using pytrec_eval.
        
        Returns dictionary of metric -> value (aggregated across queries).
        """
        if not self.dataset.qrels:
            print(f"  [Skip evaluation - no qrels]")
            return {}
        
        # Convert results to pytrec format: {query_id: [(doc_id, score), ...]}
        run = defaultdict(list)
        for r in results["results"]:
            run[r["topic_id"]].append((r["doc_id"], r["score"]))
        
        # Sort each query's results by score descending
        for qid in run:
            run[qid].sort(key=lambda x: x[1], reverse=True)
        
        # Convert qrels to pytrec format
        qrels = {}
        for topic_id, docs in self.dataset.qrels.items():
            qrels[topic_id] = {doc_id: rel for doc_id, rel in docs.items()}
        
        # Evaluate
        try:
            per_query_results = self.metrics.evaluate_run(dict(run), qrels, self.METRICS)
            # Aggregate results across queries
            aggregated = self.metrics.compute_aggregate(per_query_results)
            return aggregated
        except Exception as e:
            print(f"  [Evaluation error: {e}]")
            return {}
    
    def run_full_benchmark(self, query_types: List[str] = None, k: int = 100):
        """
        Run the complete benchmark suite.
        
        Args:
            query_types: List of query types to test ("short", "long")
            k: Number of results per query
        """
        if query_types is None:
            query_types = ["short", "long"]
        
        print("\n" + "=" * 60)
        print("TREC Benchmark - SysCRED")
        print("=" * 60)
        
        # Load data
        self.load_data()
        
        # Run all configurations
        print("\n" + "=" * 60)
        print("Running Retrieval Experiments")
        print("=" * 60)
        
        for query_type in query_types:
            for config in self.CONFIGURATIONS:
                run_tag, results = self.run_configuration(
                    config, query_type, k
                )
                
                if results:
                    self.results[run_tag] = results
                    
                    # Evaluate
                    metrics = self.evaluate_run(run_tag, results)
                    self.results[run_tag]["metrics"] = metrics
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    def generate_report(self):
        """Generate summary report."""
        print("\n" + "=" * 60)
        print("Benchmark Results Summary")
        print("=" * 60)
        
        # Table header
        header = ["Configuration", "Query", "MAP", "NDCG", "P@10", "MRR", "Time(s)"]
        print("\n" + " | ".join(f"{h:^12}" for h in header))
        print("-" * 100)
        
        # Table rows
        for run_tag, data in self.results.items():
            metrics = data.get("metrics", {})
            
            row = [
                data["config"]["name"][:12],
                data["query_type"][:5],
                f"{metrics.get('map', 0):.4f}",
                f"{metrics.get('ndcg', 0):.4f}",
                f"{metrics.get('P_10', 0):.4f}",
                f"{metrics.get('recip_rank', 0):.4f}",
                f"{data.get('elapsed_time', 0):.2f}"
            ]
            print(" | ".join(f"{v:^12}" for v in row))
        
        # Save detailed results
        results_file = self.output_dir / "benchmark_results.json"
        
        # Make results JSON serializable
        serializable_results = {}
        for run_tag, data in self.results.items():
            serializable_results[run_tag] = {
                "config": data["config"],
                "query_type": data["query_type"],
                "metrics": data.get("metrics", {}),
                "elapsed_time": data.get("elapsed_time", 0),
                "num_results": len(data.get("results", []))
            }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Generate LaTeX table
        self._generate_latex_table()
    
    def _generate_latex_table(self):
        """Generate LaTeX table for paper."""
        latex_file = self.output_dir / "results_table.tex"
        
        lines = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{TREC AP88-90 Retrieval Results}",
            r"\label{tab:trec-results}",
            r"\begin{tabular}{l|l|cccc}",
            r"\toprule",
            r"Model & Query & MAP & NDCG & P@10 & MRR \\",
            r"\midrule"
        ]
        
        for run_tag, data in self.results.items():
            metrics = data.get("metrics", {})
            row = (
                f"{data['config']['name']} & {data['query_type']} & "
                f"{metrics.get('map', 0):.4f} & "
                f"{metrics.get('ndcg', 0):.4f} & "
                f"{metrics.get('P_10', 0):.4f} & "
                f"{metrics.get('recip_rank', 0):.4f} \\\\"
            )
            lines.append(row)
        
        lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}"
        ])
        
        with open(latex_file, 'w') as f:
            f.write("\n".join(lines))
        
        print(f"LaTeX table saved to: {latex_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run TREC benchmark for SysCRED"
    )
    parser.add_argument(
        "--index", "-i",
        help="Path to Lucene index"
    )
    parser.add_argument(
        "--corpus", "-c",
        help="Path to JSONL corpus"
    )
    parser.add_argument(
        "--topics", "-t",
        help="Path to TREC topics file/directory"
    )
    parser.add_argument(
        "--qrels", "-q",
        help="Path to TREC qrels file/directory"
    )
    parser.add_argument(
        "--output", "-o",
        default="benchmark_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=100,
        help="Number of results per query"
    )
    
    args = parser.parse_args()
    
    # Run benchmark
    benchmark = TRECBenchmark(
        index_path=args.index,
        corpus_path=args.corpus,
        topics_path=args.topics,
        qrels_path=args.qrels,
        output_dir=args.output
    )
    
    results = benchmark.run_full_benchmark(k=args.k)
    
    print("\n" + "=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
