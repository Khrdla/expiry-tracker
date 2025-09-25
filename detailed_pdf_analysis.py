#!/usr/bin/env python3
"""
Detailed PDF Analysis for Professional GEANT Layout
This script will download the PDF and analyze its content more thoroughly
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data
SUPERVISOR_NAME = "Mahmoud Badr"
PRODUCT_BARCODE = "3222471081716"
SAR_QUANTITY = 98.5
SAR_PRICE = 3.75

class DetailedPDFAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate and get token"""
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
            print(f"❌ Authentication error: {e}")
            return False
    
    def create_test_return_form(self):
        """Create a test return form with exact specifications"""
        try:
            return_form_data = {
                "reference_number": f"RTN-ANALYSIS-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L",
                "barcode": PRODUCT_BARCODE,
                "quantity": SAR_QUANTITY,
                "purchase_price": SAR_PRICE,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "reason_for_return": "Professional PDF layout testing",
                "selected_supervisor": SUPERVISOR_NAME,
                "prepared_by_supervisor": SUPERVISOR_NAME,
                "section_manager_name": "Imad Qejji",
                "notes": f"Testing GEANT branding - Total: {SAR_QUANTITY * SAR_PRICE} SAR",
                "supervisor_approved": True,
                "supervisor_signature": f"{SUPERVISOR_NAME}_digital_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_digital_signature",
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                print(f"✅ Return form created: {form_id}")
                return form_id
            else:
                print(f"❌ Return form creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Return form creation error: {e}")
            return None
    
    def download_and_analyze_pdf(self, form_id):
        """Download PDF and perform detailed analysis"""
        try:
            # Download PDF
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            
            if response.status_code != 200:
                print(f"❌ PDF download failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            pdf_content = response.content
            pdf_size = len(pdf_content)
            
            print(f"✅ PDF downloaded successfully: {pdf_size} bytes")
            
            # Save PDF to file for manual inspection
            pdf_filename = f"/app/test_return_form_{form_id[:8]}.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_content)
            print(f"📄 PDF saved to: {pdf_filename}")
            
            # Basic PDF validation
            is_valid_pdf = pdf_content.startswith(b'%PDF') and b'%%EOF' in pdf_content
            print(f"📋 Valid PDF format: {is_valid_pdf}")
            
            # Content analysis using different approaches
            self.analyze_pdf_content_binary(pdf_content)
            self.analyze_pdf_content_text(pdf_content)
            
            # Try to extract text using different methods
            self.try_extract_pdf_text(pdf_filename)
            
            return True
            
        except Exception as e:
            print(f"❌ PDF analysis error: {e}")
            return False
    
    def analyze_pdf_content_binary(self, pdf_content):
        """Analyze PDF content at binary level"""
        print("\n🔍 BINARY CONTENT ANALYSIS:")
        
        # Look for key terms in binary content
        search_terms = [
            b'GEANT', b'Geant', b'HYPERMARKET', b'Hypermarket',
            b'Mahmoud', b'Badr', b'369.375', b'369.37', b'369.36',
            b'98.51', b'98.5', b'SAR', b'USD',
            b'FORM DETAILS', b'Form Details',
            b'PRODUCT INFORMATION', b'Product Information',
            b'RETURN VALUE', b'Return Value',
            b'APPROVALS', b'SIGNATURES'
        ]
        
        found_terms = []
        for term in search_terms:
            if term in pdf_content:
                found_terms.append(term.decode('utf-8', errors='ignore'))
        
        print(f"📋 Found terms in binary: {found_terms}")
        print(f"📊 Binary search success rate: {len(found_terms)}/{len(search_terms)} ({len(found_terms)/len(search_terms)*100:.1f}%)")
    
    def analyze_pdf_content_text(self, pdf_content):
        """Analyze PDF content as text"""
        print("\n🔍 TEXT CONTENT ANALYSIS:")
        
        try:
            # Try different encodings
            encodings = ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    pdf_text = pdf_content.decode(encoding, errors='ignore')
                    
                    # Look for key terms
                    search_terms = [
                        'GEANT', 'HYPERMARKET', 'Mahmoud', 'Badr',
                        '369.375', '369.37', '369.36', '98.51', '98.5',
                        'SAR', 'USD', 'FORM DETAILS', 'PRODUCT INFORMATION',
                        'RETURN VALUE', 'APPROVALS', 'SIGNATURES'
                    ]
                    
                    found_terms = []
                    for term in search_terms:
                        if term in pdf_text:
                            found_terms.append(term)
                    
                    if found_terms:
                        print(f"📋 Found terms with {encoding}: {found_terms}")
                        print(f"📊 Text search success rate: {len(found_terms)}/{len(search_terms)} ({len(found_terms)/len(search_terms)*100:.1f}%)")
                        
                        # Show a sample of the text content
                        sample_text = pdf_text[:500].replace('\n', ' ').replace('\r', ' ')
                        print(f"📄 Text sample: {sample_text}...")
                        break
                    
                except Exception as e:
                    continue
            else:
                print("❌ No readable text found with any encoding")
                
        except Exception as e:
            print(f"❌ Text analysis error: {e}")
    
    def try_extract_pdf_text(self, pdf_filename):
        """Try to extract text using PDF libraries if available"""
        print("\n🔍 PDF TEXT EXTRACTION:")
        
        # Try with pdfplumber if available
        try:
            import pdfplumber
            with pdfplumber.open(pdf_filename) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                if text:
                    print(f"📄 Extracted text length: {len(text)} characters")
                    
                    # Search for key terms
                    search_terms = [
                        'GEANT', 'HYPERMARKET', 'Mahmoud', 'Badr',
                        '369.375', '369.37', '369.36', '98.51', '98.5',
                        'SAR', 'USD', 'FORM DETAILS', 'PRODUCT INFORMATION'
                    ]
                    
                    found_terms = [term for term in search_terms if term in text]
                    print(f"📋 Found terms in extracted text: {found_terms}")
                    
                    # Show sample
                    sample = text[:300].replace('\n', ' ')
                    print(f"📄 Extracted text sample: {sample}...")
                else:
                    print("❌ No text extracted with pdfplumber")
                    
        except ImportError:
            print("📋 pdfplumber not available, trying PyPDF2...")
            
            # Try with PyPDF2 if available
            try:
                import PyPDF2
                with open(pdf_filename, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    
                    if text:
                        print(f"📄 PyPDF2 extracted text length: {len(text)} characters")
                        sample = text[:300].replace('\n', ' ')
                        print(f"📄 PyPDF2 text sample: {sample}...")
                    else:
                        print("❌ No text extracted with PyPDF2")
                        
            except ImportError:
                print("📋 PyPDF2 not available")
                
        except Exception as e:
            print(f"❌ PDF text extraction error: {e}")
    
    def run_detailed_analysis(self):
        """Run complete detailed PDF analysis"""
        print("🔬 DETAILED PROFESSIONAL GEANT PDF ANALYSIS")
        print("=" * 60)
        
        # 1. Authenticate
        if not self.authenticate():
            return
        
        # 2. Create test return form
        form_id = self.create_test_return_form()
        if not form_id:
            return
        
        # 3. Download and analyze PDF
        success = self.download_and_analyze_pdf(form_id)
        
        if success:
            print("\n✅ ANALYSIS COMPLETE")
            print("📋 Check the saved PDF file for manual inspection")
        else:
            print("\n❌ ANALYSIS FAILED")

if __name__ == "__main__":
    analyzer = DetailedPDFAnalyzer()
    analyzer.run_detailed_analysis()