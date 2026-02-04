#!/usr/bin/env python3
"""Migrate SQLite data to Supabase."""
import sqlite3
import requests
import json
import os

# Supabase config
SUPABASE_URL = "https://zmluirvqfkmfazqitqgi.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY", "YOUR_SECRET_KEY_HERE")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

LOCAL_DB = "/Users/bk280625/Desktop/systemFactChecking/02_Code/syscred/syscred_local.db"

print("=" * 60)
print("Migration SQLite -> Supabase")
print("=" * 60)

# Connect to SQLite
conn = sqlite3.connect(LOCAL_DB)
cur = conn.cursor()

# Get triplets
cur.execute("SELECT subject, predicate, object, object_type, graph_name FROM rdf_triples")
triples = cur.fetchall()
print(f"\n1. Found {len(triples)} triplets in SQLite")

# Migrate in batches
BATCH_SIZE = 100
success = 0
errors = 0

print(f"\n2. Migrating to Supabase in batches of {BATCH_SIZE}...")

for i in range(0, len(triples), BATCH_SIZE):
    batch = triples[i:i+BATCH_SIZE]
    
    data = [
        {
            "subject": t[0],
            "predicate": t[1],
            "object": t[2],
            "object_type": t[3],
            "graph_name": t[4]
        }
        for t in batch
    ]
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rdf_triples",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code in [200, 201]:
        success += len(batch)
        print(f"   Batch {i//BATCH_SIZE + 1}: {len(batch)} triplets OK")
    else:
        errors += len(batch)
        print(f"   Batch {i//BATCH_SIZE + 1}: ERROR - {response.text[:100]}")

conn.close()

print(f"\n3. Migration complete!")
print(f"   Success: {success}")
print(f"   Errors: {errors}")

# Verify
print(f"\n4. Verifying in Supabase...")
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/rdf_triples?select=graph_name&limit=1",
    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
)

if response.status_code == 200:
    print(f"   ✅ Supabase connection OK!")
    
    # Count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/rdf_triples?select=count",
        headers={
            "apikey": SUPABASE_KEY, 
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact"
        }
    )
    count = response.headers.get('content-range', '0').split('/')[-1]
    print(f"   Total triplets in Supabase: {count}")
else:
    print(f"   ❌ Error: {response.text}")
