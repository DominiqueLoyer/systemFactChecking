
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# 1. Manually load .env based on known structure
current_dir = Path(__file__).parent
env_path = current_dir.parent / '.env'
print(f"[Test] Looking for .env at: {env_path}")

if env_path.exists():
    load_dotenv(env_path)
    print("[Test] .env loaded manually.")
else:
    print("[Test] .env NOT found.")

# 2. Check import from config
try:
    # Add local path to sys.path to mimic app behavior
    sys.path.append(str(current_dir))
    from syscred.config import config
    print(f"[Test] Config loaded. Key present? {'Yes' if config.GOOGLE_FACT_CHECK_API_KEY else 'No'}")
    
    api_key = config.GOOGLE_FACT_CHECK_API_KEY
    if not api_key:
        print("[Test] ERROR: Key is missing in config.")
        exit(1)
        
    print(f"[Test] Key: {api_key[:5]}...{api_key[-5:]}")
    
    # 3. Test API Call
    print("[Test] Making API request for 'flat earth'...")
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        'key': api_key,
        'query': 'flat earth',
        'languageCode': 'en'
    }
    
    resp = requests.get(url, params=params)
    print(f"[Test] Response Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        claims = data.get('claims', [])
        print(f"[Test] Success! Found {len(claims)} claims.")
        for c in claims[:2]:
            print(f" - {c.get('text')[:50]}...")
    else:
        print(f"[Test] API Error: {resp.text}")

except Exception as e:
    print(f"[Test] Exception: {e}")
