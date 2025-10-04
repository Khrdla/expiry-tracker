#!/usr/bin/env python3
"""
PDF Content Analyzer for GEANT Hypermarket Return Forms
Downloads and analyzes the actual PDF content to verify branding and layout
"""

import requests
import os
import time

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"
RETURN_FORM_ID = "69166bb7-5694-46e5-bc01-b320717cee77"  # From previous test

class PDFContentAnalyzer:
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
    
    def download_and_analyze_pdf(self):
        """Download PDF and perform detailed content analysis"""
        try:
            print(f"📥 Downloading PDF for return form: {RETURN_FORM_ID}")
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{RETURN_FORM_ID}/pdf")
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                print(f"📄 PDF downloaded successfully: {pdf_size} bytes")
                
                # Save PDF to file for manual inspection
                pdf_filename = f"/app/geant_return_form_{RETURN_FORM_ID[:8]}.pdf"
                with open(pdf_filename, 'wb') as f:
                    f.write(pdf_content)
                print(f"💾 PDF saved to: {pdf_filename}")
                
                # Analyze PDF content
                self.analyze_pdf_content(pdf_content)
                
                return pdf_content
            else:
                print(f"❌ PDF download failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ PDF download error: {str(e)}")
            return None
    
    def analyze_pdf_content(self, pdf_content):
        """Perform detailed analysis of PDF content"""
        print("\n🔍 DETAILED PDF CONTENT ANALYSIS")
        print("=" * 50)
        
        # Basic PDF structure
        is_valid_pdf = pdf_content.startswith(b'%PDF')
        has_eof = b'%%EOF' in pdf_content
        print(f"📋 Valid PDF structure: {is_valid_pdf and has_eof}")
        
        # Extract readable text content (simple approach)
        try:
            # Convert bytes to string, ignoring non-UTF-8 characters
            text_content = pdf_content.decode('utf-8', errors='ignore')
            
            # Look for specific branding elements
            branding_checks = {
                "GEANT": "GEANT" in text_content,
                "Geant": "Geant" in text_content,
                "HYPERMARKET": "HYPERMARKET" in text_content,
                "Hypermarket": "Hypermarket" in text_content,
                "Supplier Return Form": "Supplier Return Form" in text_content,
                "Return Form": "Return Form" in text_content
            }
            
            print("\n🏢 BRANDING ELEMENTS:")
            for element, found in branding_checks.items():
                status = "✅" if found else "❌"
                print(f"{status} {element}: {found}")
            
            # Look for section organization elements
            section_checks = {
                "Reference Number": "Reference Number" in text_content,
                "Return Date": "Return Date" in text_content,
                "Generated On": "Generated On" in text_content,
                "Product Information": "Product" in text_content,
                "Barcode": "Barcode" in text_content or "3222471081716" in text_content,
                "SAR Currency": "SAR" in text_content,
                "USD Equivalent": "USD" in text_content,
                "Signatures": "Signature" in text_content,
                "Mahmoud Badr": "Mahmoud Badr" in text_content,
                "Imad Qejji": "Imad Qejji" in text_content
            }
            
            print("\n📋 SECTION ORGANIZATION:")
            for element, found in section_checks.items():
                status = "✅" if found else "❌"
                print(f"{status} {element}: {found}")
            
            # Look for system messages that should NOT be present
            system_message_checks = {
                "Status: PENDING": "Status: PENDING" in text_content,
                "Selected Supervisor:": "Selected Supervisor:" in text_content,
                "Debug": "debug" in text_content.lower(),
                "Error": "error" in text_content.lower()
            }
            
            print("\n🚫 SYSTEM MESSAGES (should be absent):")
            for element, found in system_message_checks.items():
                status = "❌" if found else "✅"
                print(f"{status} {element}: {found}")
            
            # Currency conversion verification
            currency_checks = {
                "74.27": "74.27" in text_content,  # SAR amount
                "19.81": "19.81" in text_content,  # USD equivalent
                "Apple Juice Box 1L": "Apple Juice Box 1L" in text_content,
                "ExtenC": "ExtenC" in text_content
            }
            
            print("\n💰 CURRENCY & PRODUCT DATA:")
            for element, found in currency_checks.items():
                status = "✅" if found else "❌"
                print(f"{status} {element}: {found}")
            
            # Extract first 500 characters of readable text for inspection
            readable_text = ''.join(c for c in text_content if c.isprintable())[:500]
            print(f"\n📝 FIRST 500 CHARACTERS OF READABLE TEXT:")
            print("-" * 50)
            print(readable_text)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Text analysis error: {str(e)}")
    
    def test_alternative_pdf_endpoint(self):
        """Test alternative PDF export endpoint"""
        try:
            print(f"\n🔄 Testing alternative PDF endpoint...")
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{RETURN_FORM_ID}?format=pdf")
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                print(f"📄 Alternative PDF endpoint successful: {pdf_size} bytes")
                
                # Save alternative PDF
                alt_pdf_filename = f"/app/geant_return_form_alt_{RETURN_FORM_ID[:8]}.pdf"
                with open(alt_pdf_filename, 'wb') as f:
                    f.write(pdf_content)
                print(f"💾 Alternative PDF saved to: {alt_pdf_filename}")
                
                return pdf_content
            else:
                print(f"❌ Alternative PDF endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Alternative PDF test error: {str(e)}")
            return None
    
    def run_analysis(self):
        """Run complete PDF content analysis"""
        print("🔍 GEANT HYPERMARKET PDF CONTENT ANALYZER")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        # Download and analyze main PDF
        pdf_content = self.download_and_analyze_pdf()
        
        # Test alternative endpoint
        alt_pdf_content = self.test_alternative_pdf_endpoint()
        
        print("\n🏁 PDF CONTENT ANALYSIS COMPLETE")

if __name__ == "__main__":
    analyzer = PDFContentAnalyzer()
    analyzer.run_analysis()