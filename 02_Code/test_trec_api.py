#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for TREC API endpoints.
Run this while the server is running on port 5001.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_endpoint(name, method, url, data=None):
    print(f"\n{'='*60}")
    print(f"📡 Testing: {name}")
    print(f"   {method} {url}")
    print('='*60)
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🔬 SysCRED TREC API Test Suite")
    print("Server:", BASE_URL)
    
    # Test 1: TREC Health
    test_endpoint(
        "TREC Health Check",
        "GET",
        f"{BASE_URL}/api/trec/health"
    )
    
    # Test 2: TREC Corpus
    test_endpoint(
        "TREC Corpus Info",
        "GET",
        f"{BASE_URL}/api/trec/corpus"
    )
    
    # Test 3: TREC Search
    test_endpoint(
        "TREC Evidence Search",
        "POST",
        f"{BASE_URL}/api/trec/search",
        data={
            "query": "Climate change is caused by humans",
            "k": 3,
            "model": "bm25"
        }
    )
    
    # Test 4: TREC Metrics
    test_endpoint(
        "TREC IR Metrics Calculation",
        "POST",
        f"{BASE_URL}/api/trec/metrics",
        data={
            "retrieved": ["AP880101-0001", "AP890215-0001", "AP880101-0002"],
            "relevant": ["AP880101-0001", "AP880101-0002", "AP880102-0001"]
        }
    )
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)
