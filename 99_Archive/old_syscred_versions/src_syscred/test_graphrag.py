# -*- coding: utf-8 -*-
"""
Test Script for GraphRAG
========================
Verifies that the GraphRAG module can correctly:
1. Connect to an in-memory ontology.
2. Retrieve context for a domain that has history.
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from syscred.ontology_manager import OntologyManager
from syscred.graph_rag import GraphRAG

def test_graphrag_retrieval():
    print("=== Testing GraphRAG Retrieval Logic ===\n")

    # 1. Setup In-Memory Ontology
    print("[1] Initializing in-memory Ontology...")
    om = OntologyManager(base_ontology_path=None, data_path=None)
    
    # 2. Add Fake History (Memory)
    print("[2] Injecting test memory for 'lemonde.fr'...")
    fake_report = {
        'scoreCredibilite': 0.95,
        'informationEntree': 'https://www.lemonde.fr/article/test',
        'resumeAnalyse': "Reliable source.",
        'reglesAppliquees': {
            'source_analysis': {'reputation': 'High', 'domain': 'lemonde.fr'}
        }
    }
    # Add it 3 times to simulate history
    om.add_evaluation_triplets(fake_report)
    om.add_evaluation_triplets(fake_report)
    om.add_evaluation_triplets(fake_report)
    print("    -> Added 3 evaluation records.")

    # 3. Initialize GraphRAG
    rag = GraphRAG(om)

    # 4. Query Context
    domain = "lemonde.fr"
    print(f"\n[3] Querying GraphRAG for domain: '{domain}'...")
    context = rag.get_context(domain)
    
    print("\n--- Result Context (Domain History) ---")
    print(context['full_text'])
    print("---------------------------------------\n")
    
    # 5. Validation 1 (History)
    if "Analyzed 3 times" in context['full_text']:
        print("✅ SUCCESS: GraphRAG correctly remembered the history.")
    else:
        print("❌ FAILURE: GraphRAG did not return the expected history count.")

    # 6. Test Similar Claims (New Feature)
    print(f"\n[4] Testing 'Similar Claims' for keywords: ['lemonde', 'fake']...")
    # The previous injection didn't use 'fake', let's check what it finds or if we need to inject more
    # Our fake_report had content: 'https://www.lemonde.fr/article/test'
    # The new logic searches regex in 'informationContent'
    
    # Let's add a specifically claim-like entry
    fake_claim = {
        'scoreCredibilite': 0.1,
        'informationEntree': 'The earth is flat and fake',
        'resumeAnalyse': "False claim.",
        'reglesAppliquees': {'source_analysis': {'reputation': 'Low'}}
    }
    om.add_evaluation_triplets(fake_claim)
    
    # Search for 'flat'
    similar_context = rag.get_context("unknown.com", keywords=["flat", "earth"])
    print("\n--- Result Context (Similar Claims) ---")
    print(similar_context['full_text'])
    print("---------------------------------------\n")

    if "Found 1 similar claims" in similar_context['full_text'] or "The earth is flat" in similar_context['full_text']:
        print("✅ SUCCESS: GraphRAG found similar claims by keywords.")
    else:
        print("❌ FAILURE: GraphRAG did not find the injected similar claim.")

if __name__ == "__main__":
    test_graphrag_retrieval()
