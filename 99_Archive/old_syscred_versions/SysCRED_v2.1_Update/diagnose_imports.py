
import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("--- DIAGNOSTIC START ---")
try:
    print("[1] Importing config...")
    from syscred.config import config
    print("    OK")
except Exception:
    traceback.print_exc()

try:
    print("[2] Importing database...")
    from syscred.database import init_db
    print("    OK")
except Exception:
    traceback.print_exc()

try:
    print("[3] Importing ontology_manager...")
    from syscred.ontology_manager import OntologyManager
    print("    OK")
except Exception:
    traceback.print_exc()

try:
    print("[4] Importing verification_system...")
    from syscred.verification_system import CredibilityVerificationSystem
    print("    OK")
except Exception:
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
