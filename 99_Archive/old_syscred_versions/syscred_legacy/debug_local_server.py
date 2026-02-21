import requests
import json

url = "http://localhost:5001/api/verify"
payload = {
    "input_data": "la terre est plate",
    "include_seo": True
}
headers = {'Content-Type': 'application/json'}

try:
    print(f"Sending POST to {url} with payload: {payload}")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n--- JSON RESPONSE PARTIAL ---")
        facts = data.get('reglesAppliquees', {}).get('fact_checking', [])
        print(f"Fact Checks Count: {len(facts)}")
        print("Fact Checks Items:", json.dumps(facts, indent=2, ensure_ascii=False))
    else:
        print("Error:", response.text)
except Exception as e:
    print(f"Connection failed: {e}")
