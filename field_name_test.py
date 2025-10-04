#!/usr/bin/env python3
"""
Field Name Verification Test
Testing that frontend gets the correct field names
"""

import requests
import json

# Test the exact field names that frontend expects
BACKEND_URL = 'https://inventory-master-78.preview.emergentagent.com/api'
session = requests.Session()

# Login
login_response = session.post(f'{BACKEND_URL}/auth/login', 
    json={'username': 'imadqejji', 'password': '066380531I'})
if login_response.status_code == 200:
    token = login_response.json().get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    # Get dashboard data
    response = session.get(f'{BACKEND_URL}/dashboard')
    if response.status_code == 200:
        data = response.json()
        print('✅ Dashboard Response Structure:')
        
        for kpi in data.get('kpis', []):
            dept = kpi.get('department')
            # Check for the field names frontend expects
            has_total_stock_value = 'total_stock_value' in kpi
            has_old_stock_value = 'stock_value' in kpi
            
            print(f'  {dept}:')
            print(f'    - total_stock_value (NEW): {"✅" if has_total_stock_value else "❌"} = ${kpi.get("total_stock_value", 0):.2f}')
            print(f'    - stock_value (OLD): {"✅" if has_old_stock_value else "❌"} = ${kpi.get("stock_value", "N/A")}')
            print(f'    - total_items: {kpi.get("total_items", 0)}')
            print(f'    - total_quantity: {kpi.get("total_quantity", 0)}')
            print()
    else:
        print(f'❌ Dashboard request failed: {response.status_code}')
else:
    print('❌ Authentication failed')