#!/usr/bin/env python3
"""
Single Page Layout Debug Test
Testing to identify what's causing the 2-page layout
"""

import requests
import json
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class SinglePageDebugTester:
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
    
    def test_minimal_return_form(self):
        """Test with minimal single-item return form"""
        try:
            return_form_data = {
                "reference_number": f"RTN-MINIMAL-{int(time.time())}",
                "supplier": "ExtenC",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature",
                "section_manager_timestamp": datetime.now().isoformat(),
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 1,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "reason_for_return": "Quality issue",
                "notes": "Minimal test form"
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                print(f"✅ Minimal return form created: {form_id}")
                return form_id
            else:
                print(f"❌ Failed to create minimal form: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating minimal form: {str(e)}")
            return None
    
    def test_two_item_return_form(self):
        """Test with 2-item return form"""
        try:
            return_form_data = {
                "reference_number": f"RTN-TWO-ITEM-{int(time.time())}",
                "supplier": "ExtenC",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature",
                "section_manager_timestamp": datetime.now().isoformat(),
                "items": [
                    {
                        "product_name": "Apple Juice Box 1L",
                        "barcode": "3222471081716",
                        "quantity": 10,
                        "purchase_price": 3.75,
                        "purchase_currency": "SAR",
                        "total_value": 37.50,
                        "reason_for_return": "Quality issue",
                        "is_foc": False
                    },
                    {
                        "product_name": "Orange Juice Box 1L", 
                        "barcode": "3222471052747",
                        "quantity": 5,
                        "purchase_price": 4.00,
                        "purchase_currency": "SAR",
                        "total_value": 20.00,
                        "reason_for_return": "Damaged packaging",
                        "is_foc": False
                    }
                ],
                "total_items": 2,
                "total_quantity": 15,
                "total_value": 57.50,
                "notes": "Two-item test form"
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                print(f"✅ Two-item return form created: {form_id}")
                return form_id
            else:
                print(f"❌ Failed to create two-item form: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating two-item form: {str(e)}")
            return None
    
    def check_pdf_pages(self, form_id, form_type):
        """Check how many pages the PDF has"""
        try:
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check page count
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                page_count = len(pdf_reader.pages)
                
                print(f"📄 {form_type} PDF: {page_count} pages, {pdf_size} bytes")
                
                if page_count > 0:
                    # Extract text to see content
                    page_text = pdf_reader.pages[0].extract_text()
                    print(f"   First page content length: {len(page_text)} characters")
                    
                    if page_count > 1:
                        page2_text = pdf_reader.pages[1].extract_text()
                        print(f"   Second page content length: {len(page2_text)} characters")
                        print(f"   Second page preview: {page2_text[:200]}...")
                
                return page_count == 1
            else:
                print(f"❌ Failed to generate {form_type} PDF: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking {form_type} PDF: {str(e)}")
            return False
    
    def run_debug_tests(self):
        """Run debug tests to identify single-page layout issues"""
        print("🔍 SINGLE PAGE LAYOUT DEBUG TESTING")
        print("=" * 50)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Test minimal single-item form
        print("\n🧪 Testing minimal single-item return form...")
        minimal_form_id = self.test_minimal_return_form()
        if minimal_form_id:
            minimal_single_page = self.check_pdf_pages(minimal_form_id, "Minimal Single-Item")
        
        # 3. Test two-item form
        print("\n🧪 Testing two-item return form...")
        two_item_form_id = self.test_two_item_return_form()
        if two_item_form_id:
            two_item_single_page = self.check_pdf_pages(two_item_form_id, "Two-Item")
        
        print("\n" + "=" * 50)
        print("🏁 DEBUG TESTING COMPLETE")
        print("=" * 50)

if __name__ == "__main__":
    tester = SinglePageDebugTester()
    tester.run_debug_tests()