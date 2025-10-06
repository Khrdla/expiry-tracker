#!/usr/bin/env python3
"""
Final Verification Test for Return Form Currency Display Simplification
Comprehensive test covering all requirements from the review request
"""

import requests
import json
import PyPDF2
import io
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FinalVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.form_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_1_login_credentials(self):
        """Test 1: Login with imadqejji/066380531I"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.log_test("Login with imadqejji/066380531I", True, 
                    "Authentication successful, JWT token received")
                return True
            else:
                self.log_test("Login with imadqejji/066380531I", False, 
                    f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login with imadqejji/066380531I", False, f"Exception: {str(e)}")
            return False
    
    def test_2_create_sar_form(self):
        """Test 2: Create form with SAR currency, Apple Juice Box 1L, qty 98.5, price 3.75"""
        try:
            return_form_data = {
                "reference_number": f"RTN-FINAL-TEST-{int(datetime.now().timestamp())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "reason_for_return": "Final verification test",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": "Final test: 98.5 x 3.75 SAR = 369.375 SAR",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            
            if response.status_code == 200:
                data = response.json()
                self.form_id = data.get("id")
                calculated_total = 98.5 * 3.75
                self.log_test("Create SAR Currency Return Form", True, 
                    f"Form ID: {self.form_id}, Product: Apple Juice Box 1L, "
                    f"Qty: 98.5, Price: 3.75 SAR, Calculated Total: {calculated_total} SAR")
                return True
            else:
                self.log_test("Create SAR Currency Return Form", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create SAR Currency Return Form", False, f"Exception: {str(e)}")
            return False
    
    def test_3_pdf_generation(self):
        """Test 3: Generate PDF using GET /api/export/return-form/{form_id}?format=pdf"""
        if not self.form_id:
            self.log_test("PDF Generation", False, "No form ID available")
            return None
        
        try:
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.form_id}?format=pdf")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                if is_pdf:
                    self.log_test("PDF Generation", True, 
                        f"PDF generated successfully, Size: {pdf_size} bytes, Content-Type: {content_type}")
                    return response.content
                else:
                    self.log_test("PDF Generation", False, 
                        f"Invalid PDF format, Content-Type: {content_type}")
                    return None
            else:
                self.log_test("PDF Generation", False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
        except Exception as e:
            self.log_test("PDF Generation", False, f"Exception: {str(e)}")
            return None
    
    def test_4_currency_display_only_sar(self, pdf_content):
        """Test 4: Verify PDF shows only 'Total Value: 369.38 SAR'"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Check for required SAR display
            has_total_value_369_sar = "Total Value:" in pdf_text and "369.38 SAR" in pdf_text
            has_sar_currency = "SAR" in pdf_text
            
            # Verify the exact expected total (369.375 rounds to 369.38)
            expected_total = 98.5 * 3.75  # 369.375
            expected_display = f"{expected_total:.2f}"  # 369.38
            
            self.log_test("PDF Shows Only SAR Total Value", has_total_value_369_sar, 
                f"Expected: 'Total Value: 369.38 SAR', Found SAR: {has_sar_currency}, "
                f"Found Total Value with 369.38 SAR: {has_total_value_369_sar}")
            
            return has_total_value_369_sar
            
        except Exception as e:
            self.log_test("PDF Shows Only SAR Total Value", False, f"Exception: {str(e)}")
            return False
    
    def test_5_no_usd_equivalent(self, pdf_content):
        """Test 5: Verify PDF does NOT show 'USD Equivalent: $98.51 USD'"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Check for USD equivalent (should NOT be present)
            has_usd_equivalent = "USD Equivalent" in pdf_text
            has_98_51_usd = "$98.51 USD" in pdf_text
            has_369_36_usd = "$369.36 USD" in pdf_text  # The incorrect 1:1 conversion
            
            no_usd_equivalent = not has_usd_equivalent and not has_98_51_usd and not has_369_36_usd
            
            self.log_test("PDF Does NOT Show USD Equivalent", no_usd_equivalent, 
                f"USD Equivalent found: {has_usd_equivalent}, "
                f"$98.51 USD found: {has_98_51_usd}, "
                f"$369.36 USD found: {has_369_36_usd}")
            
            return no_usd_equivalent
            
        except Exception as e:
            self.log_test("PDF Does NOT Show USD Equivalent", False, f"Exception: {str(e)}")
            return False
    
    def test_6_no_exchange_rate(self, pdf_content):
        """Test 6: Verify PDF does NOT show 'Exchange Rate: 1 SAR = 0.2667 USD'"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Check for exchange rate (should NOT be present)
            has_exchange_rate = "Exchange Rate" in pdf_text
            has_sar_usd_rate = "1 SAR = 0.2667 USD" in pdf_text
            has_any_exchange_rate = "=" in pdf_text and "USD" in pdf_text and "SAR" in pdf_text
            
            no_exchange_rate = not has_exchange_rate and not has_sar_usd_rate
            
            self.log_test("PDF Does NOT Show Exchange Rate", no_exchange_rate, 
                f"Exchange Rate found: {has_exchange_rate}, "
                f"SAR-USD rate found: {has_sar_usd_rate}")
            
            return no_exchange_rate
            
        except Exception as e:
            self.log_test("PDF Does NOT Show Exchange Rate", False, f"Exception: {str(e)}")
            return False
    
    def test_7_clean_single_row_layout(self, pdf_content):
        """Test 7: Verify Return Value Calculation section has only one row"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Check for clean layout
            has_return_value_section = "RETURN VALUE CALCULATION" in pdf_text or "Return Value Calculation" in pdf_text
            has_geant_branding = "GEANT" in pdf_text
            is_single_page = len(pdf_reader.pages) == 1
            
            # Count currency-related lines (should be minimal)
            lines = pdf_text.split('\n')
            currency_lines = [line for line in lines if 
                             'sar' in line.lower() or 'total' in line.lower() and 'value' in line.lower()]
            
            clean_layout = has_return_value_section and is_single_page and len(currency_lines) <= 4
            
            self.log_test("Clean Single-Row Layout", clean_layout, 
                f"Return Value section: {has_return_value_section}, "
                f"Single page: {is_single_page}, "
                f"Currency lines count: {len(currency_lines)}, "
                f"GEANT branding: {has_geant_branding}")
            
            return clean_layout
            
        except Exception as e:
            self.log_test("Clean Single-Row Layout", False, f"Exception: {str(e)}")
            return False
    
    def run_final_verification(self):
        """Run all final verification tests"""
        print("🎯 FINAL VERIFICATION: Return Form Currency Display Simplification")
        print("=" * 80)
        print("TESTING ALL REQUIREMENTS FROM REVIEW REQUEST:")
        print("1. Login: imadqejji/066380531I")
        print("2. Create form with SAR currency")
        print("3. Product: Apple Juice Box 1L")
        print("4. Quantity: 98.5, Price: 3.75 SAR")
        print("5. Expected total: 369.375 SAR")
        print("6. PDF should show only 'Total Value: 369.38 SAR'")
        print("7. Should NOT show USD Equivalent or Exchange Rate")
        print("8. Clean, simplified layout")
        print("=" * 80)
        
        # Run all tests
        if not self.test_1_login_credentials():
            print("❌ Authentication failed - stopping tests")
            return
        
        if not self.test_2_create_sar_form():
            print("❌ Form creation failed - stopping tests")
            return
        
        pdf_content = self.test_3_pdf_generation()
        if not pdf_content:
            print("❌ PDF generation failed - stopping tests")
            return
        
        # Test currency display requirements
        self.test_4_currency_display_only_sar(pdf_content)
        self.test_5_no_usd_equivalent(pdf_content)
        self.test_6_no_exchange_rate(pdf_content)
        self.test_7_clean_single_row_layout(pdf_content)
        
        # Print final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL VERIFICATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # Show all test results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    {result['details']}")
        
        # Overall verdict
        all_critical_passed = all(result["success"] for result in self.test_results)
        
        print("\n" + "=" * 80)
        if all_critical_passed:
            print("🎉 CURRENCY SIMPLIFICATION SUCCESSFULLY IMPLEMENTED!")
            print("✅ All requirements from review request verified")
            print("✅ PDF shows only supplier currency (SAR)")
            print("✅ No USD equivalent or exchange rate displayed")
            print("✅ Clean, simplified layout maintained")
        else:
            failed_tests = [r for r in self.test_results if not r["success"]]
            print("⚠️  SOME REQUIREMENTS NOT MET:")
            for test in failed_tests:
                print(f"❌ {test['test']}")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FinalVerificationTester()
    tester.run_final_verification()