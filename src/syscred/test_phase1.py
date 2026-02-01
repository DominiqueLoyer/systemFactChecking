import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from syscred.api_clients import ExternalAPIClients

def test_backlinks():
    client = ExternalAPIClients()
    
    test_urls = [
        "https://www.lemonde.fr", # High + Old
        "https://www.infowars.com", # Low + Old
        "https://example.com", # Unknown + Old
        "https://new-suspicious-site.xyz" # Unknown + New (likely)
    ]
    
    print("=== Testing Backlink Estimation Heuristic ===")
    for url in test_urls:
        print(f"\nTesting: {url}")
        res = client.estimate_backlinks(url)
        print(f"  Count: {res['estimated_count']}")
        print(f"  Method: {res['method']}")
        print(f"  Note: {res['note']}")

if __name__ == "__main__":
    test_backlinks()
