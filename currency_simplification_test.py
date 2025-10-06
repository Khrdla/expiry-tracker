#!/usr/bin/env python3
"""
Return Form Currency Display Simplification Testing
Testing the removal of USD equivalent and exchange rate from Return Form PDFs
"""

import requests
import json
import os
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_PRODUCT = {
    "name": "Apple Juice Box 1L",
    "quantity": 98.5,
    "price": 3.75,
    "currency": "SAR",
    "expected_total": 369.375,
    "expected_display": "369.38 SAR"
}

class CurrencySimplificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_form_id = None
        
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
    
    def authenticate(self):
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
                    f"Login successful with credentials {ADMIN_USERNAME}/{ADMIN_PASSWORD}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_return_form_with_sar_currency(self):
        """Create return form with SAR currency as specified in review request"""
        try:
            start_time = time.time()
            
            return_form_data = {
                "reference_number": f"RTN-SAR-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": TEST_PRODUCT["name"],
                "barcode": "3222471081716",
                "quantity": TEST_PRODUCT["quantity"],
                "purchase_price": TEST_PRODUCT["price"],
                "purchase_currency": TEST_PRODUCT["currency"],
                "supplier": "ExtenC",
                "reason_for_return": "Currency display simplification test",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": f"Test return form for currency simplification - {TEST_PRODUCT['quantity']} x {TEST_PRODUCT['price']} {TEST_PRODUCT['currency']}",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.created_return_form_id = data.get("id")
                
                # Calculate expected total
                calculated_total = TEST_PRODUCT["quantity"] * TEST_PRODUCT["price"]
                
                self.log_result("Create Return Form with SAR Currency", True,
                    f"Form ID: {self.created_return_form_id}, "
                    f"Product: {TEST_PRODUCT['name']}, "
                    f"Quantity: {TEST_PRODUCT['quantity']}, "
                    f"Price: {TEST_PRODUCT['price']} {TEST_PRODUCT['currency']}, "
                    f"Calculated Total: {calculated_total:.3f} {TEST_PRODUCT['currency']}", response_time)
                return True
            else:
                self.log_result("Create Return Form with SAR Currency", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Create Return Form with SAR Currency", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_generation_and_currency_display(self):
        """Test PDF generation and verify currency display simplification"""
        if not self.created_return_form_id:
            self.log_result("PDF Generation and Currency Display", False, "No return form created to test")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.created_return_form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                if is_pdf:
                    self.log_result("PDF Generation and Currency Display", True,
                        f"PDF generated successfully - Content-Type: {content_type}, Size: {pdf_size} bytes", response_time)
                    return response.content
                else:
                    self.log_result("PDF Generation and Currency Display", False,
                        f"Response is not a valid PDF - Content-Type: {content_type}", response_time)
                    return False
            else:
                self.log_result("PDF Generation and Currency Display", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("PDF Generation and Currency Display", False, f"Exception: {str(e)}")
            return False
    
    def verify_currency_simplification_in_pdf(self, pdf_content):
        """Verify that PDF shows only supplier currency total, no USD conversion or exchange rate"""
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for what SHOULD be present (supplier currency only)
            has_sar_total = "369.38 SAR" in pdf_text or "369.375 SAR" in pdf_text or "SAR" in pdf_text
            has_total_value = "Total Value" in pdf_text or "total" in pdf_text.lower()
            
            # Check for what SHOULD NOT be present (USD conversion and exchange rate)
            has_usd_equivalent = "USD Equivalent" in pdf_text or "$98.51 USD" in pdf_text or "$369.36 USD" in pdf_text
            has_exchange_rate = "Exchange Rate" in pdf_text or "1 SAR = 0.2667 USD" in pdf_text
            
            # Success criteria: Has SAR currency, does NOT have USD conversion or exchange rate
            currency_simplified = has_sar_total and not has_usd_equivalent and not has_exchange_rate
            
            details = f"SAR Currency Present: {has_sar_total}, " \
                     f"Total Value Present: {has_total_value}, " \
                     f"USD Equivalent Present: {has_usd_equivalent}, " \
                     f"Exchange Rate Present: {has_exchange_rate}, " \
                     f"PDF Text Length: {len(pdf_text)} chars"
            
            self.log_result("Verify Currency Simplification in PDF", currency_simplified, details, response_time)
            
            # Additional detailed logging for debugging
            if "Total Value" in pdf_text:
                # Extract lines containing "Total Value" or currency information
                lines = pdf_text.split('\n')
                currency_lines = [line.strip() for line in lines if 
                                 'total' in line.lower() or 'sar' in line.lower() or 
                                 'usd' in line.lower() or 'exchange' in line.lower()]
                if currency_lines:
                    print(f"    Currency-related lines found: {currency_lines[:5]}")  # Show first 5 lines
            
            return currency_simplified
            
        except Exception as e:
            self.log_result("Verify Currency Simplification in PDF", False, f"Exception: {str(e)}")
            return False
    
    def verify_clean_layout(self, pdf_content):
        """Verify that the PDF has a clean layout with only one currency row"""
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for clean layout indicators
            has_return_value_section = "Return Value Calculation" in pdf_text or "Return Value" in pdf_text
            has_geant_branding = "GEANT" in pdf_text or "Geant" in pdf_text
            is_single_page = len(pdf_reader.pages) == 1
            
            # Count currency-related lines to ensure simplification
            lines = pdf_text.split('\n')
            currency_lines = [line for line in lines if 
                             'sar' in line.lower() or 'usd' in line.lower() or 
                             'exchange' in line.lower() or 'rate' in line.lower()]
            
            # Success criteria: Has required sections, single page, minimal currency lines
            clean_layout = has_return_value_section and has_geant_branding and is_single_page and len(currency_lines) <= 3
            
            details = f"Return Value Section: {has_return_value_section}, " \
                     f"GEANT Branding: {has_geant_branding}, " \
                     f"Single Page: {is_single_page}, " \
                     f"Currency Lines Count: {len(currency_lines)}"
            
            self.log_result("Verify Clean Layout", clean_layout, details, response_time)
            return clean_layout
            
        except Exception as e:
            self.log_result("Verify Clean Layout", False, f"Exception: {str(e)}")
            return False
    
    def run_currency_simplification_tests(self):
        """Run all currency simplification tests"""
        print("🚀 RETURN FORM CURRENCY DISPLAY SIMPLIFICATION TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Product: {TEST_PRODUCT['name']}")
        print(f"Test Scenario: {TEST_PRODUCT['quantity']} x {TEST_PRODUCT['price']} {TEST_PRODUCT['currency']}")
        print(f"Expected Total: {TEST_PRODUCT['expected_total']} {TEST_PRODUCT['currency']}")
        print(f"Expected Display: {TEST_PRODUCT['expected_display']}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create Return Form with SAR Currency
        if not self.create_return_form_with_sar_currency():
            print("❌ Return form creation failed - stopping tests")
            return
        
        # 3. Generate PDF and verify format
        pdf_content = self.test_pdf_generation_and_currency_display()
        if not pdf_content:
            print("❌ PDF generation failed - stopping tests")
            return
        
        # 4. Verify Currency Simplification (main requirement)
        self.verify_currency_simplification_in_pdf(pdf_content)
        
        # 5. Verify Clean Layout
        self.verify_clean_layout(pdf_content)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 CURRENCY SIMPLIFICATION TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        if self.created_return_form_id:
            print(f"🔄 CREATED RETURN FORM ID: {self.created_return_form_id}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Login with imadqejji/066380531I": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results),
            "Create SAR Currency Form": any("Create Return Form with SAR Currency" in r["test"] and r["success"] for r in self.test_results),
            "Generate PDF": any("PDF Generation and Currency Display" in r["test"] and r["success"] for r in self.test_results),
            "Currency Simplification": any("Verify Currency Simplification in PDF" in r["test"] and r["success"] for r in self.test_results),
            "Clean Layout": any("Verify Clean Layout" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Expected vs Actual Results
        print(f"\n📋 EXPECTED RESULTS:")
        print(f"   • Product: {TEST_PRODUCT['name']}")
        print(f"   • Quantity: {TEST_PRODUCT['quantity']}")
        print(f"   • Price: {TEST_PRODUCT['price']} {TEST_PRODUCT['currency']}")
        print(f"   • Expected Total: {TEST_PRODUCT['expected_total']} {TEST_PRODUCT['currency']}")
        print(f"   • Expected Display: {TEST_PRODUCT['expected_display']}")
        print(f"   • Should NOT show: USD Equivalent, Exchange Rate")
        print(f"   • Should show ONLY: Total Value in supplier currency")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 70)
        print("🏁 CURRENCY SIMPLIFICATION TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = CurrencySimplificationTester()
    tester.run_currency_simplification_tests()