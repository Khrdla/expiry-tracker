#!/usr/bin/env python3
"""
FOC PDF Content Analysis - Deep inspection of PDF content
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FOCPDFAnalyzer:
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
    
    def create_foc_form(self):
        """Create a FOC return form for testing"""
        try:
            foc_form_data = {
                "reference_number": f"RTN-FOC-ANALYSIS-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 50,
                "purchase_price": 0,  # FOC price
                "original_purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "reason_for_return": "Quality issue - damaged packaging",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": "FOC return form - Promotional sample items",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat(),
                # FOC specific fields
                "is_foc": True,
                "foc_enabled": True,
                "foc_reason": "Promotional sample items",
                "total_value": 0,
                "unit_price": 0
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=foc_form_data)
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                print(f"✅ FOC form created: {form_id}")
                return form_id
            else:
                print(f"❌ FOC form creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ FOC form creation error: {str(e)}")
            return None
    
    def analyze_pdf_content(self, form_id):
        """Download and analyze PDF content in detail"""
        try:
            print(f"\n🔍 Analyzing PDF content for form: {form_id}")
            
            # Download PDF
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            
            if response.status_code != 200:
                print(f"❌ PDF download failed: {response.status_code}")
                print(f"Response: {response.text}")
                return
            
            pdf_content = response.content
            pdf_size = len(pdf_content)
            content_type = response.headers.get('content-type', '')
            
            print(f"📄 PDF Info:")
            print(f"   Size: {pdf_size} bytes")
            print(f"   Content-Type: {content_type}")
            print(f"   PDF signature: {pdf_content[:10]}")
            
            # Try to extract text using PyPDF2 if available
            try:
                import PyPDF2
                from io import BytesIO
                
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                
                print(f"   Pages: {len(pdf_reader.pages)}")
                
                # Extract text from all pages
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    full_text += page_text
                    print(f"   Page {page_num + 1} text length: {len(page_text)} chars")
                
                print(f"\n📝 Extracted Text Analysis:")
                print(f"   Total text length: {len(full_text)} characters")
                
                # Search for FOC indicators with more variations
                foc_patterns = {
                    "FOC - FREE": "FOC - FREE" in full_text,
                    "FOC-FREE": "FOC-FREE" in full_text,
                    "FOC FREE": "FOC FREE" in full_text,
                    "Free of Cost": "Free of Cost" in full_text,
                    "FREE OF COST": "FREE OF COST" in full_text,
                    "FOC Status": "FOC Status" in full_text,
                    "FOC Reason": "FOC Reason" in full_text,
                    "Promotional sample items": "Promotional sample items" in full_text,
                    "0 EUR": "0 EUR" in full_text,
                    "0.00 EUR": "0.00 EUR" in full_text,
                    "FREE ITEM": "FREE ITEM" in full_text,
                    "No Cost": "No Cost" in full_text,
                    "FREE - No Cost": "FREE - No Cost" in full_text,
                    "Yes - Free of Cost": "Yes - Free of Cost" in full_text,
                    "No - Regular Item": "No - Regular Item" in full_text
                }
                
                print(f"\n🔍 FOC Pattern Search Results:")
                found_patterns = []
                for pattern, found in foc_patterns.items():
                    status = "✅" if found else "❌"
                    print(f"   {status} {pattern}")
                    if found:
                        found_patterns.append(pattern)
                
                print(f"\n📊 Summary:")
                print(f"   Found {len(found_patterns)}/{len(foc_patterns)} FOC patterns")
                print(f"   Found patterns: {found_patterns}")
                
                # Show a sample of the extracted text
                print(f"\n📄 Text Sample (first 500 chars):")
                print(f"   {full_text[:500]}...")
                
                # Search for specific sections
                sections = ["PRODUCT INFORMATION", "RETURN VALUE CALCULATION", "FOC Status", "Purchase Price"]
                print(f"\n📋 Section Analysis:")
                for section in sections:
                    found = section in full_text
                    status = "✅" if found else "❌"
                    print(f"   {status} {section}")
                
                return len(found_patterns) > 0
                
            except ImportError:
                print("⚠️  PyPDF2 not available, using binary search")
                
                # Fallback to binary search
                foc_binary_patterns = {
                    "FOC_FREE": b'FOC - FREE' in pdf_content,
                    "Free_of_Cost": b'Free of Cost' in pdf_content,
                    "FOC_Status": b'FOC Status' in pdf_content,
                    "Promotional": b'Promotional' in pdf_content,
                    "0_EUR": b'0 EUR' in pdf_content,
                    "FREE_ITEM": b'FREE ITEM' in pdf_content
                }
                
                print(f"\n🔍 Binary FOC Pattern Search:")
                found_binary = []
                for pattern, found in foc_binary_patterns.items():
                    status = "✅" if found else "❌"
                    print(f"   {status} {pattern}")
                    if found:
                        found_binary.append(pattern)
                
                return len(found_binary) > 0
                
        except Exception as e:
            print(f"❌ PDF analysis error: {str(e)}")
            return False
    
    def run_analysis(self):
        """Run complete FOC PDF analysis"""
        print("🔍 FOC PDF CONTENT ANALYSIS")
        print("=" * 50)
        
        # 1. Authenticate
        if not self.authenticate():
            return
        
        # 2. Create FOC form
        form_id = self.create_foc_form()
        if not form_id:
            return
        
        # 3. Analyze PDF content
        success = self.analyze_pdf_content(form_id)
        
        print(f"\n🏁 Analysis Complete")
        print(f"FOC indicators found: {'✅ YES' if success else '❌ NO'}")

if __name__ == "__main__":
    analyzer = FOCPDFAnalyzer()
    analyzer.run_analysis()