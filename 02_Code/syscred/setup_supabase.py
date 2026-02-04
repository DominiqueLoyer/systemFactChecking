#!/usr/bin/env python3
"""
Setup Supabase schema and migrate data from SQLite.
"""
import os
os.environ['SUPABASE_URL'] = 'https://zmluirvqfkmfazqitqgi.supabase.co'

from supabase import create_client
import sqlite3

# Supabase credentials
SUPABASE_URL = "https://zmluirvqfkmfazqitqgi.supabase.co"
# Try both keys
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InptbHVpcnZxZmttZmF6cWl0cWdpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg2ODcyMDAsImV4cCI6MjA1NDI2MzIwMH0.placeholder"

print("=" * 60)
print("SysCRED Supabase Setup")
print("=" * 60)

# For now, let's just verify the local SQLite is working
# and provide instructions

LOCAL_DB = "/Users/bk280625/Desktop/systemFactChecking/02_Code/syscred/syscred_local.db"

print("\n1. Checking local SQLite database...")
conn = sqlite3.connect(LOCAL_DB)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM rdf_triples WHERE graph_name='base'")
base_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM rdf_triples WHERE graph_name='data'")
data_count = cur.fetchone()[0]

print(f"   ✅ Base triples: {base_count}")
print(f"   ✅ Data triples: {data_count}")
print(f"   ✅ Total: {base_count + data_count}")

conn.close()

print("\n2. Supabase connection...")
print("   Le projet existe: https://zmluirvqfkmfazqitqgi.supabase.co")
print("   Mais nous avons besoin de la clé anon correcte.")

print("\n" + "=" * 60)
print("INSTRUCTIONS POUR SUPABASE:")
print("=" * 60)
print("""
1. Allez sur: https://supabase.com/dashboard/project/zmluirvqfkmfazqitqgi/settings/api

2. Copiez la clé 'anon public' (commence par 'eyJ...')

3. Allez sur: https://supabase.com/dashboard/project/zmluirvqfkmfazqitqgi/sql/new

4. Collez et exécutez le SQL du fichier:
   /Users/bk280625/Desktop/systemFactChecking/supabase_schema.sql

5. Donnez-moi la clé anon et je ferai la migration automatiquement!
""")
