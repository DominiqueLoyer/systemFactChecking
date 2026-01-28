import unittest
import sys
import os

# Point to parent directory (MonCode) so we can import 'syscred' package
# Current file is in MonCode/syscred/test_suite.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from syscred.verification_system import CredibilityVerificationSystem
from syscred.api_clients import ExternalAPIClients

class TestSysCRED(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n[TestSysCRED] Setting up system...")
        cls.system = CredibilityVerificationSystem(load_ml_models=False)
        cls.client = cls.system.api_clients
        
    def test_backlink_estimation_heuristic(self):
        """Test that backlink estimation respects reputation."""
        lemonde = self.client.estimate_backlinks("https://www.lemonde.fr")
        infowars = self.client.estimate_backlinks("https://infowars.com")
        
        self.assertGreater(lemonde['estimated_count'], infowars['estimated_count'], 
                           "High reputation should have more backlinks than Low")
        self.assertEqual(lemonde['method'], 'heuristic_v2.1')

    def test_coherence_heuristic(self):
        """Test coherence scoring heuristic."""
        good_text = "This is a coherent sentence. It follows logically."
        bad_text = "This is. Random words. Banana. Cloud."
        
        score_good = self.system._calculate_coherence(good_text)
        score_bad = self.system._calculate_coherence(bad_text)
        
        self.assertTrue(0 <= score_good <= 1)
        # Note: Heuristic using sentence length variance might be sensitive
        # bad_text has very short sentences, so average length is small -> penalty
        # good_text has normal length
        self.assertGreaterEqual(score_good, score_bad, "Coherent text should score >= incoherent")

    def test_bias_heuristic(self):
        """Test bias detection heuristic."""
        neutral = "The economy grew by 2%."
        biased = "The radical corrupt regime is destroying us!"
        
        res_neutral = self.system._analyze_bias(neutral)
        res_biased = self.system._analyze_bias(biased)
        
        self.assertLess(res_neutral['score'], res_biased['score'])
        self.assertIn("biased", res_biased['label'].lower())

    def test_full_pipeline(self):
        """Test the full verification pipeline (integration test)."""
        input_data = "https://www.example.com"
        result = self.system.verify_information(input_data)
        
        self.assertIn('scoreCredibilite', result)
        self.assertIn('resumeAnalyse', result)
        self.assertIsNotNone(result['scoreCredibilite'])

if __name__ == '__main__':
    unittest.main()
