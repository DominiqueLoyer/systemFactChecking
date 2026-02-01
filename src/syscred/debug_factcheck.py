import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='/Users/bk280625/documents041025/MonCode/syscred/.env')

API_KEY = os.getenv('SYSCRED_GOOGLE_API_KEY')
print(f"Loaded API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'None'}")

if not API_KEY:
    print("❌ Error: API Key not found in .env")
    exit(1)

query = "La terre est plate"
url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
params = {
    'key': API_KEY,
    'query': query,
}

print(f"\nSending request for query: '{query}'...")
try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        claims = data.get('claims', [])
        print(f"✅ Success! Found {len(claims)} claims.")
        for i, claim in enumerate(claims[:3]):
            print(f"\n--- Result {i+1} ---")
            print(f"Claim: {claim.get('text')}")
            print(f"Claimant: {claim.get('claimant')}")
            reviews = claim.get('claimReview', [])
            if reviews:
                print(f"Rating: {reviews[0].get('textualRating')}")
                print(f"URL: {reviews[0].get('url')}")
    else:
        print(f"❌ API Error: {response.text}")

except Exception as e:
    print(f"❌ Connection Error: {e}")
