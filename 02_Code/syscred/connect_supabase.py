#!/usr/bin/env python3
"""Connect to Supabase and create schema."""
import psycopg2

project = 'zmluirvqfkmfazqitqgi'
password = 'FactCheckingSystem2026_test'

# Supavisor pooler - Transaction mode
url = f'postgresql://postgres.{project}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres'
print(f'Connecting to Supabase...')

try:
    conn = psycopg2.connect(url, connect_timeout=15)
    print('SUCCESS!')
    
    cur = conn.cursor()
    cur.execute('SELECT current_database(), current_user')
    print(f'   DB: {cur.fetchone()}')
    
    # List tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [r[0] for r in cur.fetchall()]
    print(f'   Tables: {tables}')
    
    conn.close()
    print(f'\nWorking URL:\n{url}')
    
except Exception as e:
    print(f'Error: {e}')
