
import sys
import os
import traceback

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from syscred.verification_system import CredibilityVerificationSystem
from syscred.config import config
from syscred.seo_analyzer import SEOAnalyzer

print("=== DEBUG INITIALIZATION ===")
try:
    print("[1] Config check:")
    print(f"    Base Ontology: {config.ONTOLOGY_BASE_PATH}")
    print(f"    Data Path: {config.ONTOLOGY_DATA_PATH}")
    
    print("\n[2] Initializing SEO Analyzer...")
    seo = SEOAnalyzer()
    print("    OK")
    
    print("\n[3] Initializing Verification System...")
    sys = CredibilityVerificationSystem(
        ontology_base_path=config.ONTOLOGY_BASE_PATH,
        ontology_data_path=config.ONTOLOGY_DATA_PATH,
        load_ml_models=False # Disable ML for basic init test
    )
    print("    OK - System initialized successfully.")

except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    traceback.print_exc()
