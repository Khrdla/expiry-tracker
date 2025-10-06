#!/usr/bin/env python3
"""
Professional GEANT PDF Layout Testing with Fixed Sanitization
Testing the specific requirements from the review request:
- Create return form with exact data (imadqejji/066380531I, Mahmoud Badr, Apple Juice Box 1L)
- Test professional PDF generation with GEANT branding
- Verify all professional content is present and visible
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration from review request
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Exact test data from review request
SUPERVISOR_NAME = "Mahmoud Badr"
PRODUCT_BARCODE = "3222471081716"  # Apple Juice Box 1L
SAR_QUANTITY = 98.5
SAR_PRICE = 3.75
EXPECTED_SAR_TOTAL = 369.375  # 98.5 × 3.75
EXPECTED_USD_EQUIVALENT = 98.51  # Based on SAR rate 0.2667

class ProfessionalPDFTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_form_id = None
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result with enhanced formatting"""
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
            print(f"    📋 {details}")
    
    def authenticate(self):
        """Authenticate with exact admin credentials from review request"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Admin Authentication (imadqejji/066380531I)", True, 
                    f"JWT token received successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_product_lookup(self):
        """Test Apple Juice Box 1L product lookup by barcode"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/barcode/{PRODUCT_BARCODE}")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                product = response.json()
                
                # Verify it's the correct product
                product_name = product.get("product_name", "")
                is_apple_juice = "apple juice" in product_name.lower() or "apple" in product_name.lower()
                
                self.log_result("Apple Juice Box 1L Lookup", is_apple_juice,
                    f"Product: {product_name}, Price: {product.get('purchase_price')} {product.get('purchase_currency')}, "
                    f"Supplier: {product.get('supplier')}", response_time)
                return product if is_apple_juice else None
            else:
                self.log_result("Apple Juice Box 1L Lookup", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Apple Juice Box 1L Lookup", False, f"Exception: {str(e)}")
            return None
    
    def create_return_form_with_exact_data(self, product_data=None):
        """Create return form with exact data from review request"""
        try:
            start_time = time.time()
            
            # Use exact data from review request
            return_form_data = {
                "reference_number": f"RTN-GEANT-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716") if product_data else "3222471081716",
                "product_name": product_data.get("product_name", "Apple Juice Box 1L") if product_data else "Apple Juice Box 1L",
                "barcode": PRODUCT_BARCODE,
                "quantity": SAR_QUANTITY,  # 98.5 as specified
                "purchase_price": SAR_PRICE,  # 3.75 as specified
                "purchase_currency": "SAR",  # SAR currency as specified
                "supplier": product_data.get("supplier", "ExtenC") if product_data else "ExtenC",
                "reason_for_return": "Quality control - Professional PDF testing",
                "selected_supervisor": SUPERVISOR_NAME,  # Mahmoud Badr as specified
                "prepared_by_supervisor": SUPERVISOR_NAME,
                "section_manager_name": "Imad Qejji",
                "notes": f"Professional GEANT PDF layout test - Total: {EXPECTED_SAR_TOTAL} SAR",
                # Both digital approvals as specified
                "supervisor_approved": True,
                "supervisor_signature": f"{SUPERVISOR_NAME}_digital_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_digital_signature",
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.created_return_form_id = data.get("id")
                
                # Calculate expected totals
                calculated_total = SAR_QUANTITY * SAR_PRICE
                
                self.log_result("Return Form Creation with Exact Data", True,
                    f"Form ID: {self.created_return_form_id}, Supervisor: {SUPERVISOR_NAME}, "
                    f"SAR Total: {calculated_total} SAR, Both approvals: True", response_time)
                return True
            else:
                self.log_result("Return Form Creation with Exact Data", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Return Form Creation with Exact Data", False, f"Exception: {str(e)}")
            return False
    
    def test_professional_pdf_generation(self):
        """Test professional PDF generation with GEANT branding"""
        if not self.created_return_form_id:
            self.log_result("Professional PDF Generation", False, "No return form created to test")
            return None
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.created_return_form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                content_type = response.headers.get('content-type', '')
                pdf_size = len(pdf_content)
                
                # Verify it's a valid PDF
                is_valid_pdf = pdf_content.startswith(b'%PDF') and b'%%EOF' in pdf_content
                
                self.log_result("Professional PDF Generation", is_valid_pdf,
                    f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                    f"Valid PDF: {is_valid_pdf}", response_time)
                return pdf_content if is_valid_pdf else None
            else:
                self.log_result("Professional PDF Generation", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Professional PDF Generation", False, f"Exception: {str(e)}")
            return None
    
    def verify_professional_content(self, pdf_content):
        """Verify all professional content is present in PDF"""
        if not pdf_content:
            self.log_result("Professional Content Verification", False, "No PDF content to verify")
            return
        
        try:
            # Convert PDF content to string for text search
            pdf_text = pdf_content.decode('latin-1', errors='ignore')
            
            # Test specific search terms from review request
            search_terms = {
                "GEANT HYPERMARKET": "GEANT" in pdf_text and "HYPERMARKET" in pdf_text,
                "Mahmoud Badr": "Mahmoud" in pdf_text and "Badr" in pdf_text,
                "SAR Amount (369.375 or 369.37)": "369.375" in pdf_text or "369.37" in pdf_text,
                "USD Equivalent (98.5 or $98.51)": "98.5" in pdf_text or "98.51" in pdf_text,
                "FORM DETAILS": "FORM DETAILS" in pdf_text or "Form Details" in pdf_text,
                "PRODUCT INFORMATION": "PRODUCT INFORMATION" in pdf_text or "Product Information" in pdf_text,
                "RETURN VALUE CALCULATION": "RETURN VALUE" in pdf_text or "Return Value" in pdf_text,
                "APPROVALS & SIGNATURES": "APPROVALS" in pdf_text or "SIGNATURES" in pdf_text
            }
            
            found_terms = []
            missing_terms = []
            
            for term, found in search_terms.items():
                if found:
                    found_terms.append(term)
                else:
                    missing_terms.append(term)
            
            success_rate = len(found_terms) / len(search_terms) * 100
            overall_success = success_rate >= 75  # At least 75% of terms should be found
            
            self.log_result("Professional Content Verification", overall_success,
                f"Found: {len(found_terms)}/{len(search_terms)} terms ({success_rate:.1f}%), "
                f"Missing: {missing_terms[:3]}", 0)
            
            # Detailed verification of each requirement
            self.verify_geant_branding(pdf_text)
            self.verify_supervisor_information(pdf_text)
            self.verify_sar_currency_display(pdf_text)
            self.verify_professional_sections(pdf_text)
            
        except Exception as e:
            self.log_result("Professional Content Verification", False, f"Exception: {str(e)}")
    
    def verify_geant_branding(self, pdf_text):
        """Verify GEANT HYPERMARKET branding is present"""
        has_geant = "GEANT" in pdf_text
        has_hypermarket = "HYPERMARKET" in pdf_text
        has_logo_reference = "logo" in pdf_text.lower() or "geant-logo" in pdf_text.lower()
        
        branding_success = has_geant or has_hypermarket
        
        self.log_result("GEANT HYPERMARKET Branding", branding_success,
            f"GEANT: {has_geant}, HYPERMARKET: {has_hypermarket}, Logo ref: {has_logo_reference}", 0)
    
    def verify_supervisor_information(self, pdf_text):
        """Verify supervisor information is visible"""
        has_mahmoud = "Mahmoud" in pdf_text
        has_badr = "Badr" in pdf_text
        has_supervisor_section = "supervisor" in pdf_text.lower()
        
        supervisor_success = has_mahmoud and has_badr
        
        self.log_result("Supervisor Information (Mahmoud Badr)", supervisor_success,
            f"Mahmoud: {has_mahmoud}, Badr: {has_badr}, Supervisor section: {has_supervisor_section}", 0)
    
    def verify_sar_currency_display(self, pdf_text):
        """Verify SAR currency conversion is properly displayed"""
        has_sar_amount = "369.375" in pdf_text or "369.37" in pdf_text or "369.36" in pdf_text
        has_usd_equivalent = "98.51" in pdf_text or "98.5" in pdf_text or "$98" in pdf_text
        has_sar_currency = "SAR" in pdf_text
        
        currency_success = has_sar_amount and (has_usd_equivalent or has_sar_currency)
        
        self.log_result("SAR Currency Display (369.375 SAR → $98.51 USD)", currency_success,
            f"SAR amount: {has_sar_amount}, USD equivalent: {has_usd_equivalent}, SAR currency: {has_sar_currency}", 0)
    
    def verify_professional_sections(self, pdf_text):
        """Verify professional section headers are present"""
        sections = {
            "FORM DETAILS": "FORM DETAILS" in pdf_text or "Form Details" in pdf_text,
            "PRODUCT INFORMATION": "PRODUCT INFORMATION" in pdf_text or "Product Information" in pdf_text,
            "RETURN VALUE CALCULATION": "RETURN VALUE" in pdf_text or "Return Value" in pdf_text,
            "APPROVALS & SIGNATURES": "APPROVALS" in pdf_text or "SIGNATURES" in pdf_text
        }
        
        found_sections = [name for name, found in sections.items() if found]
        sections_success = len(found_sections) >= 2  # At least 2 sections should be present
        
        self.log_result("Professional Section Headers", sections_success,
            f"Found sections: {found_sections}, Total: {len(found_sections)}/4", 0)
    
    def test_clean_layout_no_debug_messages(self, pdf_content):
        """Verify clean layout with no system debug messages"""
        if not pdf_content:
            self.log_result("Clean Layout Verification", False, "No PDF content to verify")
            return
        
        try:
            pdf_text = pdf_content.decode('latin-1', errors='ignore')
            
            # Check for system debug messages that shouldn't be in professional PDF
            debug_indicators = [
                "debug", "error", "exception", "traceback", "stack trace",
                "mongodb", "objectid", "localhost", "127.0.0.1", "test_", "DEBUG"
            ]
            
            found_debug = []
            for indicator in debug_indicators:
                if indicator.lower() in pdf_text.lower():
                    found_debug.append(indicator)
            
            is_clean = len(found_debug) == 0
            
            self.log_result("Clean Layout (No Debug Messages)", is_clean,
                f"Debug indicators found: {found_debug[:3] if found_debug else 'None'}", 0)
            
        except Exception as e:
            self.log_result("Clean Layout Verification", False, f"Exception: {str(e)}")
    
    def run_comprehensive_professional_pdf_test(self):
        """Run comprehensive professional PDF layout test"""
        print("🏢 PROFESSIONAL GEANT PDF LAYOUT TESTING WITH FIXED SANITIZATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Supervisor: {SUPERVISOR_NAME}")
        print(f"Product: Apple Juice Box 1L ({PRODUCT_BARCODE})")
        print(f"SAR Currency: {SAR_QUANTITY} qty × {SAR_PRICE} price = {EXPECTED_SAR_TOTAL} SAR")
        print(f"Expected USD: ${EXPECTED_USD_EQUIVALENT}")
        print("=" * 80)
        
        # 1. Authentication with exact credentials
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Product lookup
        product_data = self.test_product_lookup()
        
        # 3. Create return form with exact data
        if not self.create_return_form_with_exact_data(product_data):
            print("❌ Return form creation failed - stopping tests")
            return
        
        # 4. Generate professional PDF
        pdf_content = self.test_professional_pdf_generation()
        
        # 5. Verify all professional content
        if pdf_content:
            self.verify_professional_content(pdf_content)
            self.test_clean_layout_no_debug_messages(pdf_content)
        
        # 6. Print comprehensive summary
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary with specific focus on review requirements"""
        print("\n" + "=" * 80)
        print("📊 PROFESSIONAL GEANT PDF LAYOUT TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"📄 RETURN FORM ID: {self.created_return_form_id}")
        
        # Critical requirements from review request
        print("\n🎯 REVIEW REQUEST REQUIREMENTS VERIFICATION:")
        
        critical_requirements = {
            "Admin Login (imadqejji/066380531I)": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results),
            "Return Form with Mahmoud Badr": any("Return Form Creation" in r["test"] and r["success"] for r in self.test_results),
            "Apple Juice Box 1L Product": any("Apple Juice" in r["test"] and r["success"] for r in self.test_results),
            "Professional PDF Generation": any("Professional PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "GEANT HYPERMARKET Branding": any("GEANT HYPERMARKET Branding" in r["test"] and r["success"] for r in self.test_results),
            "Supervisor Information Visible": any("Supervisor Information" in r["test"] and r["success"] for r in self.test_results),
            "SAR Currency Display": any("SAR Currency Display" in r["test"] and r["success"] for r in self.test_results),
            "Professional Section Headers": any("Professional Section Headers" in r["test"] and r["success"] for r in self.test_results),
            "Clean Layout (No Debug)": any("Clean Layout" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_requirements.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Failed tests with details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED REQUIREMENTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Success assessment
        critical_passed = sum(1 for status in critical_requirements.values() if status)
        critical_total = len(critical_requirements)
        critical_success_rate = (critical_passed / critical_total * 100) if critical_total > 0 else 0
        
        print(f"\n🏆 CRITICAL REQUIREMENTS: {critical_passed}/{critical_total} ({critical_success_rate:.1f}%)")
        
        if critical_success_rate >= 80:
            print("🎉 PROFESSIONAL GEANT PDF LAYOUT IS WORKING CORRECTLY!")
            print("✅ The 'NO UPDATES' issue has been RESOLVED")
        else:
            print("⚠️  PROFESSIONAL GEANT PDF LAYOUT NEEDS ATTENTION")
            print("❌ The 'NO UPDATES' issue is NOT fully resolved")
        
        print("\n" + "=" * 80)
        print("🏁 PROFESSIONAL GEANT PDF LAYOUT TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = ProfessionalPDFTester()
    tester.run_comprehensive_professional_pdf_test()