#!/usr/bin/env python3
"""Test Supabase connection."""
import psycopg2

project_ref = 'zmluirvqfkmfazqitqgi'
password = 'FactCheckingSystem2026_test'

urls = [
    f'postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:5432/postgres',
    f'postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres',
]

for i, url in enumerate(urls):
    print(f'\nTest {i+1}:')
    try:
        conn = psycopg2.connect(url, connect_timeout=15)
        print('SUCCESS!')
        cur = conn.cursor()
        cur.execute('SELECT current_database(), current_user')
        print(f'   Result: {cur.fetchone()}')
        conn.close()
        print(f'\nWorking URL:\n{url}')
        break
    except Exception as e:
        print(f'   Error: {e}')
