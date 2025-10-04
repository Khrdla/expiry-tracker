#!/usr/bin/env python3
"""
Detailed Debug Test for Single Page Layout
"""

import requests
import json
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class DetailedDebugTester:
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
    
    def test_four_item_return_form(self):
        """Test with 4-item return form (the failing case)"""
        try:
            return_form_data = {
                "reference_number": f"RTN-FOUR-ITEM-{int(time.time())}",
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
                        "quantity": 50,
                        "purchase_price": 3.75,
                        "purchase_currency": "SAR",
                        "total_value": 187.50,
                        "reason_for_return": "Quality issue",
                        "is_foc": False
                    },
                    {
                        "product_name": "Orange Juice Box 1L", 
                        "barcode": "3222471052747",
                        "quantity": 25,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR",
                        "total_value": 0.0,
                        "reason_for_return": "Promotional sample",
                        "is_foc": True,
                        "foc_reason": "Promotional sample"
                    },
                    {
                        "product_name": "Mango Juice Box 1L",
                        "barcode": "3222471075722", 
                        "quantity": 10,
                        "purchase_price": 4.00,
                        "purchase_currency": "SAR",
                        "total_value": 40.00,
                        "reason_for_return": "Damaged packaging",
                        "is_foc": False
                    },
                    {
                        "product_name": "Grape Juice Box 1L",
                        "barcode": "3222471081273",
                        "quantity": 15,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR", 
                        "total_value": 0.0,
                        "reason_for_return": "Expired promotion",
                        "is_foc": True,
                        "foc_reason": "Expired promotion"
                    }
                ],
                "total_items": 4,
                "total_quantity": 100,
                "total_value": 227.50,
                "notes": "Four-item test form with FOC items"
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                print(f"✅ Four-item return form created: {form_id}")
                return form_id
            else:
                print(f"❌ Failed to create four-item form: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating four-item form: {str(e)}")
            return None
    
    def analyze_pdf_content(self, form_id):
        """Analyze PDF content in detail"""
        try:
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check page count
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                page_count = len(pdf_reader.pages)
                
                print(f"📄 Four-Item PDF Analysis:")
                print(f"   Pages: {page_count}")
                print(f"   Size: {pdf_size} bytes")
                
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    print(f"\n   Page {i+1} ({len(page_text)} chars):")
                    print(f"   Content: {repr(page_text)}")
                    
                    # Look for specific content
                    if "GEANT" in page_text:
                        print(f"   ✅ Contains GEANT branding")
                    if "Apple Juice" in page_text:
                        print(f"   ✅ Contains Apple Juice")
                    if "3222471081716" in page_text:
                        print(f"   ✅ Contains barcode 3222471081716")
                    if "Signatures" in page_text or "signature" in page_text.lower():
                        print(f"   ✅ Contains signatures section")
                    if "___" in page_text:
                        print(f"   ⚠️  Contains signature lines (may be overflow)")
                
                return page_count == 1
            else:
                print(f"❌ Failed to generate PDF: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error analyzing PDF: {str(e)}")
            return False
    
    def run_detailed_analysis(self):
        """Run detailed analysis of the single-page layout issue"""
        print("🔍 DETAILED SINGLE PAGE LAYOUT ANALYSIS")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Test four-item form (the failing case)
        print("\n🧪 Testing four-item return form (failing case)...")
        four_item_form_id = self.test_four_item_return_form()
        if four_item_form_id:
            self.analyze_pdf_content(four_item_form_id)
        
        print("\n" + "=" * 60)
        print("🏁 DETAILED ANALYSIS COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = DetailedDebugTester()
    tester.run_detailed_analysis()