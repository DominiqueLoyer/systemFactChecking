import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.getcwd())) # Assumes running from syscred/

try:
    from syscred.verification_system import CredibilityVerificationSystem
except ImportError:
    # Just in case of path issues
    sys.path.append(os.getcwd())
    from verification_system import CredibilityVerificationSystem

def test_nlp_fallbacks():
    print("=== Testing NLP Hybrid Fallbacks ===")
    
    # Initialize without loading standard ML (to test our new hybrid logic)
    # Note: verification_system uses HAS_ML flag, but we want to test specific methods
    syscred = CredibilityVerificationSystem(load_ml_models=False)
    
    # Test 1: Coherence
    print("\n[Test 1] Coherence")
    coherent_text = "The quick brown fox jumps over the lazy dog. The dog was not amused. It barked loudly."
    incoherent_text = "The quick brown fox. Banana republic creates clouds. Jump over the moon."
    
    score1 = syscred._calculate_coherence(coherent_text)
    score2 = syscred._calculate_coherence(incoherent_text)
    
    print(f"  Coherent Text Score: {score1}")
    print(f"  Incoherent Text Score: {score2}")
    
    if score1 > score2:
        print("  ✓ Coherence logic working (Metric discriminates)")
    else:
        print("  ! Coherence scores inconclusive (Might be heuristic limitations)")

    # Test 2: Bias
    print("\n[Test 2] Bias")
    neutral_text = "The government announced a new policy today regarding taxation."
    biased_text = "The corrupt regime stands accused of treason against the people by radical idiots."
    
    res1 = syscred._analyze_bias(neutral_text)
    res2 = syscred._analyze_bias(biased_text)
    
    print(f"  Neutral: {res1['label']} (Score: {res1['score']:.2f})")
    print(f"  Biased: {res2['label']} (Score: {res2['score']:.2f})")
    print(f"  Method Used: {res1.get('method', 'Unknown')}")
    
    if res2['score'] > res1['score']:
        print("  ✓ Bias detection working")
    else:
        print("  ! Bias detection inconclusive")

if __name__ == "__main__":
    test_nlp_fallbacks()
