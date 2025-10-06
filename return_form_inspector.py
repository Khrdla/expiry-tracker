#!/usr/bin/env python3
"""
Return Form Data Inspector
Inspects the actual return form data to understand what's being generated
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"
RETURN_FORM_ID = "69166bb7-5694-46e5-bc01-b320717cee77"

class ReturnFormInspector:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def inspect_return_forms(self):
        """Inspect all return forms to find our test form"""
        try:
            print("📋 Fetching all return forms...")
            response = self.session.get(f"{BACKEND_URL}/returns")
            
            if response.status_code == 200:
                forms = response.json()
                print(f"📊 Found {len(forms)} return forms")
                
                # Find our specific test form
                test_form = None
                for form in forms:
                    if form.get("id") == RETURN_FORM_ID:
                        test_form = form
                        break
                
                if test_form:
                    print(f"\n🎯 FOUND TEST RETURN FORM: {RETURN_FORM_ID}")
                    print("=" * 60)
                    
                    # Display all fields in the form
                    for key, value in test_form.items():
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"{key}: {value}")
                    
                    print("=" * 60)
                    
                    # Check critical fields for PDF generation
                    critical_fields = [
                        "reference_number", "product_name", "barcode", "quantity",
                        "purchase_price", "purchase_currency", "supplier",
                        "selected_supervisor", "section_manager_name",
                        "supervisor_approved", "section_manager_approved"
                    ]
                    
                    print("\n🔍 CRITICAL FIELDS FOR PDF GENERATION:")
                    for field in critical_fields:
                        value = test_form.get(field, "MISSING")
                        status = "✅" if field in test_form else "❌"
                        print(f"{status} {field}: {value}")
                    
                    return test_form
                else:
                    print(f"❌ Test form {RETURN_FORM_ID} not found")
                    
                    # Show first few forms for reference
                    print("\n📋 AVAILABLE RETURN FORMS:")
                    for i, form in enumerate(forms[:3]):
                        print(f"{i+1}. ID: {form.get('id', 'N/A')}")
                        print(f"   Reference: {form.get('reference_number', 'N/A')}")
                        print(f"   Product: {form.get('product_name', 'N/A')}")
                        print(f"   Created: {form.get('created_at', 'N/A')}")
                        print()
                    
                    return None
            else:
                print(f"❌ Failed to fetch return forms: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Error inspecting return forms: {str(e)}")
            return None
    
    def test_pdf_generation_endpoints(self):
        """Test both PDF generation endpoints"""
        print("\n🔄 TESTING PDF GENERATION ENDPOINTS")
        print("=" * 50)
        
        endpoints = [
            f"/export/return-form/{RETURN_FORM_ID}/pdf",
            f"/export/return-form/{RETURN_FORM_ID}?format=pdf"
        ]
        
        for i, endpoint in enumerate(endpoints, 1):
            try:
                print(f"\n📄 Testing Endpoint {i}: {endpoint}")
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    pdf_size = len(response.content)
                    is_pdf = response.content.startswith(b'%PDF')
                    
                    print(f"✅ Status: {response.status_code}")
                    print(f"📏 Size: {pdf_size} bytes")
                    print(f"📋 Content-Type: {content_type}")
                    print(f"📄 Valid PDF: {is_pdf}")
                    
                    # Save PDF for inspection
                    filename = f"/app/test_pdf_endpoint_{i}_{RETURN_FORM_ID[:8]}.pdf"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"💾 Saved to: {filename}")
                    
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Error testing endpoint {i}: {str(e)}")
    
    def check_pdf_generation_function(self):
        """Check if there are multiple PDF generation functions in the backend"""
        print("\n🔍 CHECKING PDF GENERATION IMPLEMENTATION")
        print("=" * 50)
        
        # This would require access to the backend code, but we can infer from responses
        print("Based on the different file sizes (51KB vs 2.8KB), there appear to be")
        print("two different PDF generation implementations:")
        print("1. Enhanced PDF with company branding (51KB)")
        print("2. Basic PDF without branding (2.8KB)")
        print()
        print("The larger PDF suggests enhanced formatting but may not have")
        print("the correct text content extraction for our analysis.")
    
    def run_inspection(self):
        """Run complete return form inspection"""
        print("🔍 GEANT HYPERMARKET RETURN FORM INSPECTOR")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        # Inspect return form data
        test_form = self.inspect_return_forms()
        
        # Test PDF generation endpoints
        self.test_pdf_generation_endpoints()
        
        # Check PDF generation implementation
        self.check_pdf_generation_function()
        
        print("\n🏁 RETURN FORM INSPECTION COMPLETE")

if __name__ == "__main__":
    inspector = ReturnFormInspector()
    inspector.run_inspection()