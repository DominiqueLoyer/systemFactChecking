#!/usr/bin/env python3
"""Test all Supabase regions and execute schema."""
import psycopg2

project_ref = 'zmluirvqfkmfazqitqgi'
password = 'FactCheckingSystem2026_test'

regions = ['us-east-1', 'us-west-1', 'eu-west-1', 'eu-west-2', 'ap-southeast-1', 'ap-northeast-1']

working_url = None

# Test pooler connections
for region in regions:
    url = f'postgresql://postgres.{project_ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres'
    print(f'Testing {region}...', end=' ')
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        print('SUCCESS!')
        working_url = url
        conn.close()
        break
    except Exception as e:
        print('Not found' if 'Tenant' in str(e) else str(e)[:40])

# Try direct connection if pooler failed
if not working_url:
    print('\nTrying direct connection...')
    url = f'postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres'
    try:
        conn = psycopg2.connect(url, connect_timeout=10)
        print('Direct connection SUCCESS!')
        working_url = url
        conn.close()
    except Exception as e:
        print(f'Direct failed: {e}')

if working_url:
    print(f'\n✅ WORKING URL:\n{working_url}')
else:
    print('\n❌ No connection worked. Project may not exist.')
