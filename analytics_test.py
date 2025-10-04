#!/usr/bin/env python3
"""
Analytics Endpoints Testing
Testing analytics endpoints to understand the inconsistency with dashboard
"""

import requests
import json

# Test analytics endpoints
BACKEND_URL = 'https://inventory-master-78.preview.emergentagent.com/api'
session = requests.Session()

# Login
login_response = session.post(f'{BACKEND_URL}/auth/login', 
    json={'username': 'imadqejji', 'password': '066380531I'})
if login_response.status_code == 200:
    token = login_response.json().get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    print('✅ Authentication successful')
    
    # Test analytics endpoints
    endpoints = [
        '/analytics/department-breakdown',
        '/analytics/stock-levels', 
        '/analytics/supplier-performance'
    ]
    
    for endpoint in endpoints:
        response = session.get(f'{BACKEND_URL}{endpoint}')
        print(f'\n📊 {endpoint}:')
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            if 'departments' in data:
                print(f'  Found {len(data["departments"])} departments')
                for dept in data['departments']:
                    print(f'  {dept.get("department", "Unknown")}: total_value_usd=${dept.get("total_value_usd", 0):.2f}')
            elif 'suppliers' in data:
                print(f'  Found {len(data["suppliers"])} suppliers')
                for supplier in data['suppliers'][:3]:
                    print(f'  {supplier.get("supplier_name", "Unknown")}: total_value_usd=${supplier.get("total_value_usd", 0):.2f}')
            else:
                if isinstance(data, dict):
                    print(f'  Response keys: {list(data.keys())}')
                    print(f'  Sample data: {str(data)[:200]}...')
                else:
                    print(f'  Response type: {type(data)}')
                    print(f'  Sample data: {str(data)[:200]}...')
        else:
            print(f'  Error: {response.text[:200]}')
else:
    print('❌ Authentication failed')