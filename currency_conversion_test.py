#!/usr/bin/env python3
"""
Dynamic Currency Conversion Dashboard Enhancement Testing
Testing comprehensive currency system implementation with admin-only currency management
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
DEFAULT_DISPLAY_CURRENCY = "USD"
DEFAULT_YER_EXCHANGE_RATE = 1610.0
DEFAULT_SAR_EXCHANGE_RATE = 3.75
TEST_CURRENCIES = ["USD", "SAR", "YER"]

class CurrencyConversionTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.original_settings = None
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.0f}ms",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({response_time:.0f}ms)")
        if details:
            print(f"    Details: {details}")
    
    def authenticate_admin(self):
        """Authenticate with admin credentials"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Admin Authentication", True, 
                    f"Admin user {ADMIN_USERNAME} authenticated successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
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