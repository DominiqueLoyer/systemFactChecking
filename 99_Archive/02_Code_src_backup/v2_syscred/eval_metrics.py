# -*- coding: utf-8 -*-
"""
Evaluation Metrics Module - SysCRED
====================================
Information Retrieval evaluation metrics for TREC-style experiments.

Metrics:
- MAP (Mean Average Precision)
- NDCG (Normalized Discounted Cumulative Gain)
- P@K (Precision at K)
- Recall@K
- MRR (Mean Reciprocal Rank)

Based on pytrec_eval for official TREC evaluation.

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import math
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Check for pytrec_eval
try:
    import pytrec_eval
    HAS_PYTREC_EVAL = True
except ImportError:
    HAS_PYTREC_EVAL = False
    print("[EvalMetrics] pytrec_eval not installed. Using built-in metrics.")


class EvaluationMetrics:
    """
    IR Evaluation metrics using pytrec_eval or built-in implementations.
    
    Supports TREC-style evaluation with:
    - Official pytrec_eval (if available)
    - Fallback pure-Python implementations
    """
    
    def __init__(self):
        """Initialize the metrics calculator."""
        self.use_pytrec = HAS_PYTREC_EVAL
    
    # --- Built-in Metric Implementations ---
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """
        Calculate Precision@K.
        
        P@K = |relevant ∩ retrieved[:k]| / k
        """
        if k <= 0:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_retrieved = len([d for d in retrieved_k if d in relevant])
        return relevant_retrieved / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: set, k: int) -> float:
        """
        Calculate Recall@K.
        
        R@K = |relevant ∩ retrieved[:k]| / |relevant|
        """
        if not relevant:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_retrieved = len([d for d in retrieved_k if d in relevant])
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def average_precision(retrieved: List[str], relevant: set) -> float:
        """
        Calculate Average Precision for a single query.
        
        AP = (1/|relevant|) × Σ (P@k × rel(k))
        """
        if not relevant:
            return 0.0
        
        hits = 0
        sum_precision = 0.0
        
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                hits += 1
                sum_precision += hits / (i + 1)
        
        return sum_precision / len(relevant)
    
    @staticmethod
    def dcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int) -> float:
        """
        Calculate DCG@K (Discounted Cumulative Gain).
        
        DCG@K = Σ (2^rel(i) - 1) / log2(i + 2)
        """
        dcg = 0.0
        for i, doc in enumerate(retrieved[:k]):
            rel = relevance.get(doc, 0)
            dcg += (2 ** rel - 1) / math.log2(i + 2)
        return dcg
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int) -> float:
        """
        Calculate NDCG@K (Normalized DCG).
        
        NDCG@K = DCG@K / IDCG@K
        """
        dcg = EvaluationMetrics.dcg_at_k(retrieved, relevance, k)
        
        # Calculate IDCG (ideal DCG)
        sorted_rels = sorted(relevance.values(), reverse=True)[:k]
        idcg = 0.0
        for i, rel in enumerate(sorted_rels):
            idcg += (2 ** rel - 1) / math.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def reciprocal_rank(retrieved: List[str], relevant: set) -> float:
        """
        Calculate Reciprocal Rank.
        
        RR = 1 / rank of first relevant document
        """
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
    # --- TREC-Style Evaluation ---
    
    def evaluate_run(
        self,
        run: Dict[str, List[Tuple[str, float]]],
        qrels: Dict[str, Dict[str, int]],
        metrics: List[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a run against qrels (relevance judgments).
        
        Args:
            run: {query_id: [(doc_id, score), ...]}
            qrels: {query_id: {doc_id: relevance}}
            metrics: List of metrics to compute
                     ['map', 'ndcg', 'P_5', 'P_10', 'recall_100']
        
        Returns:
            {query_id: {metric: value}}
        """
        if metrics is None:
            metrics = ['map', 'ndcg', 'P_5', 'P_10', 'P_20', 'recall_100', 'recip_rank']
        
        if self.use_pytrec and HAS_PYTREC_EVAL:
            return self._evaluate_pytrec(run, qrels, metrics)
        else:
            return self._evaluate_builtin(run, qrels, metrics)
    
    def _evaluate_pytrec(
        self,
        run: Dict[str, List[Tuple[str, float]]],
        qrels: Dict[str, Dict[str, int]],
        metrics: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate using pytrec_eval."""
        # Convert run format for pytrec_eval
        pytrec_run = {}
        for qid, docs in run.items():
            pytrec_run[qid] = {doc_id: score for doc_id, score in docs}
        
        # Create evaluator
        evaluator = pytrec_eval.RelevanceEvaluator(qrels, set(metrics))
        
        # Evaluate
        results = evaluator.evaluate(pytrec_run)
        
        return results
    
    def _evaluate_builtin(
        self,
        run: Dict[str, List[Tuple[str, float]]],
        qrels: Dict[str, Dict[str, int]],
        metrics: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate using built-in implementations."""
        results = {}
        
        for qid, docs_scores in run.items():
            if qid not in qrels:
                continue
            
            q_results = {}
            retrieved = [doc_id for doc_id, _ in docs_scores]
            relevance = qrels[qid]
            relevant = set(doc_id for doc_id, rel in relevance.items() if rel > 0)
            
            for metric in metrics:
                if metric == 'map':
                    q_results['map'] = self.average_precision(retrieved, relevant)
                elif metric == 'ndcg':
                    q_results['ndcg'] = self.ndcg_at_k(retrieved, relevance, 1000)
                elif metric.startswith('ndcg_cut_'):
                    k = int(metric.split('_')[-1])
                    q_results[metric] = self.ndcg_at_k(retrieved, relevance, k)
                elif metric.startswith('P_'):
                    k = int(metric.split('_')[-1])
                    q_results[metric] = self.precision_at_k(retrieved, relevant, k)
                elif metric.startswith('recall_'):
                    k = int(metric.split('_')[-1])
                    q_results[metric] = self.recall_at_k(retrieved, relevant, k)
                elif metric == 'recip_rank':
                    q_results['recip_rank'] = self.reciprocal_rank(retrieved, relevant)
            
            results[qid] = q_results
        
        return results
    
    def compute_aggregate(
        self,
        results: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Compute aggregate metrics across all queries.
        
        Returns mean values for each metric.
        """
        if not results:
            return {}
        
        aggregated = defaultdict(list)
        for qid, metrics in results.items():
            for metric, value in metrics.items():
                aggregated[metric].append(value)
        
        return {metric: sum(values) / len(values) 
                for metric, values in aggregated.items()}
    
    def format_results(
        self,
        results: Dict[str, Dict[str, float]],
        include_per_query: bool = False
    ) -> str:
        """Format results as a readable string."""
        lines = []
        
        # Aggregate
        agg = self.compute_aggregate(results)
        lines.append("=" * 50)
        lines.append("AGGREGATE METRICS")
        lines.append("=" * 50)
        for metric, value in sorted(agg.items()):
            lines.append(f"  {metric:20s}: {value:.4f}")
        
        # Per-query (optional)
        if include_per_query:
            lines.append("")
            lines.append("=" * 50)
            lines.append("PER-QUERY METRICS")
            lines.append("=" * 50)
            for qid in sorted(results.keys()):
                lines.append(f"\nQuery {qid}:")
                for metric, value in sorted(results[qid].items()):
                    lines.append(f"  {metric:20s}: {value:.4f}")
        
        return '\n'.join(lines)


def parse_qrels_file(filepath: str) -> Dict[str, Dict[str, int]]:
    """
    Parse a TREC qrels file.
    
    Format: query_id 0 doc_id relevance
    """
    qrels = defaultdict(dict)
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                qid, _, docid, rel = parts[:4]
                qrels[qid][docid] = int(rel)
    return dict(qrels)


def parse_run_file(filepath: str) -> Dict[str, List[Tuple[str, float]]]:
    """
    Parse a TREC run file.
    
    Format: query_id Q0 doc_id rank score run_tag
    """
    run = defaultdict(list)
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                qid, _, docid, rank, score = parts[:5]
                run[qid].append((docid, float(score)))
    
    # Sort by score descending
    for qid in run:
        run[qid].sort(key=lambda x: x[1], reverse=True)
    
    return dict(run)


# --- Testing ---
if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED Evaluation Metrics - Tests")
    print("=" * 60)
    
    metrics = EvaluationMetrics()
    print(f"\nUsing pytrec_eval: {metrics.use_pytrec}")
    
    # Test data
    retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5', 'doc6', 'doc7', 'doc8', 'doc9', 'doc10']
    relevant = {'doc1', 'doc3', 'doc5', 'doc8'}
    relevance = {'doc1': 2, 'doc3': 1, 'doc5': 2, 'doc8': 1}
    
    print("\n--- Built-in Metrics Tests ---")
    print(f"P@5:  {metrics.precision_at_k(retrieved, relevant, 5):.4f}")
    print(f"P@10: {metrics.precision_at_k(retrieved, relevant, 10):.4f}")
    print(f"R@5:  {metrics.recall_at_k(retrieved, relevant, 5):.4f}")
    print(f"R@10: {metrics.recall_at_k(retrieved, relevant, 10):.4f}")
    print(f"AP:   {metrics.average_precision(retrieved, relevant):.4f}")
    print(f"NDCG@10: {metrics.ndcg_at_k(retrieved, relevance, 10):.4f}")
    print(f"RR:   {metrics.reciprocal_rank(retrieved, relevant):.4f}")
    
    # Test run evaluation
    print("\n--- Run Evaluation Test ---")
    run = {
        'Q1': [(doc, 10-i) for i, doc in enumerate(retrieved)],
        'Q2': [('doc2', 10), ('doc1', 9), ('doc4', 8), ('doc3', 7)]
    }
    qrels = {
        'Q1': relevance,
        'Q2': {'doc1': 1, 'doc3': 2}
    }
    
    results = metrics.evaluate_run(run, qrels)
    print(metrics.format_results(results))
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
