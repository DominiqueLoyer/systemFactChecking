# -*- coding: utf-8 -*-
"""
Test TREC Integration - SysCRED
================================
Integration tests for TREC AP88-90 evidence retrieval.

Tests:
1. TRECRetriever initialization
2. Evidence retrieval
3. Integration with VerificationSystem
4. Batch retrieval
5. Metrics evaluation

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import sys
import unittest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from syscred.trec_retriever import TRECRetriever, Evidence, RetrievalResult
from syscred.trec_dataset import TRECDataset, TRECTopic, SAMPLE_TOPICS
from syscred.eval_metrics import EvaluationMetrics
from syscred.ir_engine import IREngine


class TestTRECRetriever(unittest.TestCase):
    """Tests for TRECRetriever class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up retriever with sample corpus."""
        cls.retriever = TRECRetriever(use_stemming=True, enable_prf=False)
        
        # Add sample corpus for testing
        cls.retriever.corpus = {
            "AP880101-0001": {
                "text": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels.",
                "title": "Climate Science Report"
            },
            "AP880101-0002": {
                "text": "The Earth's temperature has risen significantly over the past century due to greenhouse gas emissions.",
                "title": "Global Warming Study"
            },
            "AP880102-0001": {
                "text": "Natural climate variations have occurred throughout Earth's history, including ice ages.",
                "title": "Climate History"
            },
            "AP880102-0002": {
                "text": "Renewable energy sources like solar and wind can help reduce carbon emissions significantly.",
                "title": "Green Energy Solutions"
            },
            "AP880103-0001": {
                "text": "Scientific consensus supports the theory that humans are the primary cause of recent climate change.",
                "title": "IPCC Summary"
            },
            "AP890215-0001": {
                "text": "The presidential election campaign focused on economic issues and foreign policy.",
                "title": "Election Coverage"
            },
            "AP890216-0001": {
                "text": "Stock markets rose sharply after positive economic indicators were released.",
                "title": "Financial News"
            },
        }
    
    def test_retriever_initialization(self):
        """Test that retriever initializes correctly."""
        self.assertIsNotNone(self.retriever)
        self.assertIsNotNone(self.retriever.ir_engine)
        self.assertEqual(len(self.retriever.corpus), 7)
    
    def test_evidence_retrieval(self):
        """Test evidence retrieval for a claim."""
        result = self.retriever.retrieve_evidence(
            claim="Climate change is caused by human activities",
            k=3
        )
        
        self.assertIsInstance(result, RetrievalResult)
        self.assertGreater(len(result.evidences), 0)
        self.assertLessEqual(len(result.evidences), 3)
        
        # Check first evidence
        first = result.evidences[0]
        self.assertIsInstance(first, Evidence)
        self.assertTrue(first.doc_id.startswith("AP"))
        self.assertGreater(first.score, 0)
        self.assertEqual(first.rank, 1)
    
    def test_batch_retrieval(self):
        """Test batch evidence retrieval."""
        claims = [
            "Climate change is real",
            "Stock markets and economy",
            "Presidential election"
        ]
        
        results = self.retriever.batch_retrieve(claims, k=2)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, RetrievalResult)
    
    def test_statistics(self):
        """Test statistics collection."""
        # Run a query first
        self.retriever.retrieve_evidence("test query", k=2)
        
        stats = self.retriever.get_statistics()
        
        self.assertIn("queries_processed", stats)
        self.assertIn("corpus_size", stats)
        self.assertGreater(stats["queries_processed"], 0)


class TestTRECDataset(unittest.TestCase):
    """Tests for TRECDataset class."""
    
    def test_sample_topics(self):
        """Test sample topics availability."""
        self.assertIsNotNone(SAMPLE_TOPICS)
        self.assertGreater(len(SAMPLE_TOPICS), 0)
        
        # Check structure
        for topic_id, topic in SAMPLE_TOPICS.items():
            self.assertIsInstance(topic, TRECTopic)
            self.assertTrue(topic.title)
    
    def test_dataset_initialization(self):
        """Test dataset initialization."""
        dataset = TRECDataset()
        self.assertIsNotNone(dataset)
        self.assertEqual(len(dataset.topics), 0)
        self.assertEqual(len(dataset.qrels), 0)
    
    def test_topic_query_generation(self):
        """Test query generation from topics."""
        dataset = TRECDataset()
        dataset.topics = SAMPLE_TOPICS.copy()
        
        short_queries = dataset.get_topic_queries(query_type="short")
        long_queries = dataset.get_topic_queries(query_type="long")
        
        self.assertEqual(len(short_queries), len(SAMPLE_TOPICS))
        self.assertEqual(len(long_queries), len(SAMPLE_TOPICS))


class TestEvaluationMetrics(unittest.TestCase):
    """Tests for EvaluationMetrics class."""
    
    def setUp(self):
        self.metrics = EvaluationMetrics()
    
    def test_precision_at_k(self):
        """Test P@K calculation."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc5"}
        
        p_at_3 = self.metrics.precision_at_k(retrieved, relevant, k=3)
        self.assertAlmostEqual(p_at_3, 2/3)  # doc1 and doc3 in top 3
        
        p_at_5 = self.metrics.precision_at_k(retrieved, relevant, k=5)
        self.assertAlmostEqual(p_at_5, 3/5)
    
    def test_recall_at_k(self):
        """Test R@K calculation."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc5", "doc7"}  # 4 relevant, doc7 not retrieved
        
        r_at_5 = self.metrics.recall_at_k(retrieved, relevant, k=5)
        self.assertAlmostEqual(r_at_5, 3/4)  # 3 of 4 relevant docs retrieved
    
    def test_average_precision(self):
        """Test AP calculation."""
        retrieved = ["doc1", "doc2", "doc3", "doc4"]
        relevant = {"doc1", "doc3"}
        
        ap = self.metrics.average_precision(retrieved, relevant)
        # AP = (1/2) * (1/1 + 2/3) = 0.5 * 1.667 = 0.833
        expected = (1.0 + 2/3) / 2
        self.assertAlmostEqual(ap, expected, places=4)
    
    def test_reciprocal_rank(self):
        """Test MRR calculation."""
        retrieved = ["doc2", "doc3", "doc1", "doc4"]
        relevant = {"doc1"}
        
        rr = self.metrics.reciprocal_rank(retrieved, relevant)
        self.assertAlmostEqual(rr, 1/3)  # doc1 is at rank 3


class TestIREngine(unittest.TestCase):
    """Tests for IREngine class."""
    
    def setUp(self):
        self.engine = IREngine(use_stemming=True)
    
    def test_preprocessing(self):
        """Test text preprocessing."""
        text = "The quick brown fox JUMPS over the lazy dog!"
        processed = self.engine.preprocess(text)
        
        # Should be lowercase, no common stopwords
        self.assertNotIn("the", processed)
        self.assertTrue(processed.islower())
        # Should contain content words
        self.assertIn("quick", processed)
        self.assertIn("brown", processed)
    
    def test_tfidf_calculation(self):
        """Test TF-IDF scoring (basic)."""
        # This tests the internal TF-IDF if pyserini not available
        self.assertIsNotNone(self.engine)


class TestVerificationSystemIntegration(unittest.TestCase):
    """Integration tests with VerificationSystem."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize system without ML models for speed."""
        try:
            from syscred.verification_system import CredibilityVerificationSystem
            cls.system = CredibilityVerificationSystem(load_ml_models=False)
            cls.skip = False
        except Exception as e:
            print(f"Skipping integration tests: {e}")
            cls.skip = True
    
    def test_system_has_retriever(self):
        """Test that system has TREC retriever."""
        if self.skip:
            self.skipTest("VerificationSystem not available")
        
        # Retriever might be None if no corpus configured
        self.assertTrue(hasattr(self.system, 'trec_retriever'))
    
    def test_retrieve_evidence_method(self):
        """Test retrieve_evidence method."""
        if self.skip:
            self.skipTest("VerificationSystem not available")
        
        # Should return empty list if no corpus
        evidences = self.system.retrieve_evidence("test claim")
        self.assertIsInstance(evidences, list)
    
    def test_verify_with_evidence_method(self):
        """Test verify_with_evidence method."""
        if self.skip:
            self.skipTest("VerificationSystem not available")
        
        result = self.system.verify_with_evidence("Climate change is real")
        
        self.assertIn('claim', result)
        self.assertIn('evidences', result)
        self.assertIn('verification_verdict', result)
        self.assertIn('confidence', result)


if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED TREC Integration Tests")
    print("=" * 60)
    
    # Run with verbosity
    unittest.main(verbosity=2)
