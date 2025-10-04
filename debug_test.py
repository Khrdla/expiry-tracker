#!/usr/bin/env python3
"""
Debug test for failing endpoints
"""

import requests
import json

BASE_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def debug_currency_endpoints():
    """Debug currency endpoints"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Debugging Currency Endpoints...")
    
    # Test currency settings GET
    response = requests.get(f"{BASE_URL}/currency/settings", headers=headers)
    print(f"Currency Settings GET: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # Test currency rates GET
    response = requests.get(f"{BASE_URL}/currency/rates", headers=headers)
    print(f"Currency Rates GET: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")

def debug_waste_endpoints():
    """Debug waste endpoints"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🗑️ Debugging Waste Endpoints...")
    
    # First get a real product ID
    response = requests.get(f"{BASE_URL}/products?limit=1", headers=headers)
    if response.status_code == 200:
        products = response.json()
        if products:
            product_id = products[0].get('id')
            print(f"Using product ID: {product_id}")
            
            # Test waste entry creation with real product ID
            waste_entry = {
                "product_id": product_id,
                "quantity_wasted": 5,
                "waste_reason": "damaged",
                "notes": "Test waste entry"
            }
            
            response = requests.post(f"{BASE_URL}/waste/entries", 
                json=waste_entry, headers=headers)
            print(f"Create Waste Entry: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
            else:
                print("✅ Waste entry created successfully")
        else:
            print("❌ No products found")
    else:
        print(f"❌ Failed to get products: {response.status_code}")

def debug_return_form_export():
    """Debug return form export"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📊 Debugging Return Form Export...")
    
    # Get return forms
    response = requests.get(f"{BASE_URL}/returns?limit=5", headers=headers)
    if response.status_code == 200:
        forms = response.json()
        print(f"Found {len(forms)} return forms")
        
        for form in forms:
            form_id = form.get('id')
            print(f"Form ID: {form_id}")
            print(f"Supervisor approved: {form.get('supervisor_approved', 'N/A')}")
            print(f"Section manager approved: {form.get('section_manager_approved', 'N/A')}")
            
            # Try to export this form
            response = requests.get(f"{BASE_URL}/export/return-form/{form_id}?format=pdf", 
                headers=headers)
            print(f"Export PDF status: {response.status_code}")
            if response.status_code != 200:
                print(f"Export error: {response.text}")
            break
    else:
        print(f"❌ Failed to get return forms: {response.status_code}")

if __name__ == "__main__":
    debug_currency_endpoints()
    debug_waste_endpoints()
    debug_return_form_export()