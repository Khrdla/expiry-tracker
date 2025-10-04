#!/usr/bin/env python3
"""
Test USD conversion functionality in return forms
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def test_currency_conversion():
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
    
    # Test currency rates API
    rates_response = session.get(f"{BACKEND_URL}/currency/rates")
    print(f"📊 Currency Rates API Status: {rates_response.status_code}")
    
    if rates_response.status_code == 200:
        rates_data = rates_response.json()
        print(f"   Base Currency: {rates_data.get('base_currency')}")
        print(f"   Exchange Rates: {rates_data.get('exchange_rates')}")
        print(f"   Last Updated: {rates_data.get('last_updated')}")
    
    # Create return forms with different currencies
    test_currencies = [
        {"currency": "YER", "price": 1000.0, "product": "Test Product YER"},
        {"currency": "SAR", "price": 50.0, "product": "Test Product SAR"},
        {"currency": "EUR", "price": 10.0, "product": "Test Product EUR"}
    ]
    
    created_forms = []
    
    for curr_data in test_currencies:
        form_data = {
            "reference_number": f"RTN-{curr_data['currency']}-{int(time.time())}",
            "product_code": f"TEST-{curr_data['currency']}",
            "product_name": curr_data['product'],
            "quantity": 5,
            "purchase_price": curr_data['price'],
            "purchase_currency": curr_data['currency'],
            "supplier": "Test Supplier",
            "reason_for_return": f"Test {curr_data['currency']} conversion",
            "selected_supervisor": "Mahmoud Badr",
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            "supervisor_approved": True,
            "supervisor_signature": "test_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "test_signature",
            "section_manager_timestamp": datetime.now().isoformat()
        }
        
        response = session.post(f"{BACKEND_URL}/return-forms", json=form_data)
        
        if response.status_code == 200:
            form_id = response.json().get("id")
            created_forms.append({"id": form_id, "currency": curr_data['currency'], "price": curr_data['price']})
            print(f"✅ Created {curr_data['currency']} form: {form_id}")
        else:
            print(f"❌ Failed to create {curr_data['currency']} form: {response.status_code}")
    
    # Test PDF exports to check for USD conversion
    for form in created_forms:
        print(f"\n📄 Testing PDF export for {form['currency']} form...")
        
        # Test individual PDF export (this one works)
        pdf_response = session.get(f"{BACKEND_URL}/export/return-form/{form['id']}/pdf")
        
        if pdf_response.status_code == 200:
            pdf_content = pdf_response.content
            pdf_size = len(pdf_content)
            
            # Check for USD conversion indicators in PDF
            has_usd = b'USD' in pdf_content
            has_conversion = b'conversion' in pdf_content or b'Conversion' in pdf_content
            has_exchange = b'exchange' in pdf_content or b'Exchange' in pdf_content
            
            print(f"   ✅ PDF generated: {pdf_size} bytes")
            print(f"   💱 USD mentioned: {has_usd}")
            print(f"   💱 Conversion mentioned: {has_conversion}")
            print(f"   💱 Exchange mentioned: {has_exchange}")
            
            # Check for original currency
            currency_bytes = form['currency'].encode()
            has_original_currency = currency_bytes in pdf_content
            print(f"   💰 Original currency ({form['currency']}): {has_original_currency}")
            
        else:
            print(f"   ❌ PDF export failed: {pdf_response.status_code}")

if __name__ == "__main__":
    test_currency_conversion()