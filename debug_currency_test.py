#!/usr/bin/env python3
"""
Debug Currency Calculation Test
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def authenticate():
    """Get authentication token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def test_currency_api(session):
    """Test currency rates API"""
    try:
        response = session.get(f"{BACKEND_URL}/currency/rates")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Currency API working")
            print(f"   Base currency: {data.get('base_currency')}")
            print(f"   SAR rate: {data.get('exchange_rates', {}).get('SAR', 'Not found')}")
            return data.get('exchange_rates', {}).get('SAR', 0.267)
        else:
            print(f"❌ Currency API failed: {response.status_code}")
            return 0.267
    except Exception as e:
        print(f"❌ Currency API error: {e}")
        return 0.267

def create_and_check_return_form(session):
    """Create return form and check the stored data"""
    return_form_data = {
        "reference_number": f"RTN-DEBUG-{int(datetime.now().timestamp())}",
        "product_code": "DEBUG-SAR-001",
        "product_name": "Debug SAR Test Product",
        "barcode": "3222471081716",
        "quantity": 98.5,
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "Debug Test Supplier",
        "reason_for_return": "Debug test for SAR conversion",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "section_manager_name": "Imad Qejji",
        "notes": "Debug: 98.5 × 3.75 = 369.375 SAR",
        "supervisor_approved": True,
        "supervisor_signature": "Mahmoud_Badr_signature",
        "supervisor_timestamp": datetime.now().isoformat(),
        "section_manager_approved": True,
        "section_manager_signature": "Imad_Qejji_signature", 
        "section_manager_timestamp": datetime.now().isoformat()
    }
    
    print(f"📝 Creating return form with:")
    print(f"   Quantity: {return_form_data['quantity']} (type: {type(return_form_data['quantity'])})")
    print(f"   Price: {return_form_data['purchase_price']} (type: {type(return_form_data['purchase_price'])})")
    print(f"   Currency: {return_form_data['purchase_currency']}")
    print(f"   Expected total: {return_form_data['quantity'] * return_form_data['purchase_price']} SAR")
    
    response = session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
    if response.status_code == 200:
        data = response.json()
        return_id = data.get("id")
        print(f"✅ Return form created: {return_id}")
        
        # Fetch the created form to see what was stored
        forms_response = session.get(f"{BACKEND_URL}/returns")
        if forms_response.status_code == 200:
            forms = forms_response.json()
            created_form = next((f for f in forms if f.get('id') == return_id), None)
            if created_form:
                print(f"📋 Stored form data:")
                print(f"   Quantity: {created_form.get('quantity')} (type: {type(created_form.get('quantity'))})")
                print(f"   Price: {created_form.get('purchase_price')} (type: {type(created_form.get('purchase_price'))})")
                print(f"   Currency: {created_form.get('purchase_currency')}")
                print(f"   Supervisor: {created_form.get('selected_supervisor')}")
        
        return return_id
    else:
        print(f"❌ Failed to create return form: {response.status_code} - {response.text}")
        return None

def main():
    print("🐛 Debug Currency Calculation Test")
    print("=" * 50)
    
    # Authenticate
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated successfully")
    
    # Test currency API
    sar_rate = test_currency_api(session)
    expected_usd = 369.375 * sar_rate
    print(f"💰 Expected USD conversion: 369.375 SAR × {sar_rate} = ${expected_usd:.2f}")
    
    # Create and check return form
    return_id = create_and_check_return_form(session)
    if return_id:
        print(f"✅ Debug test completed for form: {return_id}")
    else:
        print("❌ Debug test failed")

if __name__ == "__main__":
    main()