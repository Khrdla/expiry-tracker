#!/usr/bin/env python3
"""
Focused test for approval workflow validation
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def test_approval_workflow():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BACKEND_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    
    if response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Create return form WITHOUT approvals
    incomplete_form_data = {
        "reference_number": f"RTN-NO-APPROVAL-{int(time.time())}",
        "product_code": "TEST-001",
        "product_name": "Test Product",
        "quantity": 1,
        "purchase_price": 10.0,
        "purchase_currency": "YER",
        "supplier": "Test Supplier",
        "reason_for_return": "Test incomplete form",
        "selected_supervisor": "Mahmoud Badr",
        # NO APPROVALS
        "supervisor_approved": False,
        "section_manager_approved": False
    }
    
    response = session.post(f"{BACKEND_URL}/return-forms", json=incomplete_form_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to create incomplete form: {response.status_code}")
        return
    
    form_id = response.json().get("id")
    print(f"✅ Created incomplete form: {form_id}")
    
    # Try to export PDF - should fail with 403
    export_response = session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
    print(f"📄 PDF Export Status: {export_response.status_code}")
    
    if export_response.status_code == 403:
        print("✅ PASS: Export correctly blocked without approvals")
    else:
        print(f"❌ FAIL: Export should be blocked but got status: {export_response.status_code}")
        print(f"Response: {export_response.text[:200]}")
    
    # Try main export endpoint too
    main_export_response = session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
    print(f"📄 Main Export Status: {main_export_response.status_code}")
    
    if main_export_response.status_code == 403:
        print("✅ PASS: Main export correctly blocked without approvals")
    else:
        print(f"❌ FAIL: Main export should be blocked but got status: {main_export_response.status_code}")
        print(f"Response: {main_export_response.text[:200]}")

if __name__ == "__main__":
    test_approval_workflow()