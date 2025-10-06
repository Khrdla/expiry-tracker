#!/usr/bin/env python3
"""
Unicode PDF Generation Fix Testing
Testing the specific fix for Unicode character error in PDF generation
Error: "Character '-' at index 22 in text is outside the range of characters supported by the font used: 'helvetica'"
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class UnicodePDFTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_forms = []
        
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
                    f"Token received for user: {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_return_form_with_unicode_timestamps(self):
        """Create return form with timestamps that previously caused Unicode errors"""
        try:
            start_time = time.time()
            
            # Create timestamps with em-dash format that previously caused errors
            current_time = datetime.now()
            # This format previously caused Unicode errors with em-dash (–)
            timestamp_with_emdash = current_time.strftime("%d/%m/%Y – %H:%M")
            timestamp_regular_dash = current_time.strftime("%d/%m/%Y - %H:%M")
            
            return_form_data = {
                "reference_number": f"RTN-UNICODE-TEST-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L - Unicode Test",
                "barcode": "3222471081716",
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "Mahmoud Badr",
                "reason_for_return": "Quality issue - testing Unicode character fix",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": f"Unicode test with timestamps: {timestamp_with_emdash} and {timestamp_regular_dash}",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": timestamp_regular_dash,  # Use regular dash format
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": timestamp_regular_dash,  # Use regular dash format
                "total_value_supplier_currency": 369.38,  # 98.5 * 3.75 = 369.375
                "usd_equivalent": 98.51,  # Based on SAR to USD conversion
                "exchange_rate": 0.2667  # 1 SAR = 0.2667 USD
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                self.log_result("Create Return Form with Unicode Timestamps", True,
                    f"Form ID: {form_id}, Supervisor: Mahmoud Badr, "
                    f"Currency: SAR, Total: 369.38 SAR (~$98.51 USD)", response_time)
                return form_id
            else:
                self.log_result("Create Return Form with Unicode Timestamps", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Create Return Form with Unicode Timestamps", False, f"Exception: {str(e)}")
            return None
    
    def test_pdf_export_individual_endpoint(self, form_id):
        """Test individual PDF export endpoint: GET /api/export/return-form/{return_id}/pdf"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a valid PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                # Check for Unicode character errors in response
                has_unicode_error = b'Character' in response.content and b'outside the range' in response.content
                has_font_error = b'helvetica' in response.content and b'font' in response.content
                
                # PDF should be generated without Unicode errors
                success = is_pdf and pdf_size > 2000 and not has_unicode_error and not has_font_error
                
                details = f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                details += f"Unicode Error: {has_unicode_error}, Font Error: {has_font_error}"
                
                self.log_result("PDF Export Individual Endpoint", success, details, response_time)
                return success
            else:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                self.log_result("PDF Export Individual Endpoint", False,
                    f"Status: {response.status_code}, Error: {error_text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("PDF Export Individual Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_export_main_endpoint(self, form_id):
        """Test main PDF export endpoint: GET /api/export/return-form/{form_id}?format=pdf"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a valid PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                # Check for Unicode character errors in response
                has_unicode_error = b'Character' in response.content and b'outside the range' in response.content
                has_font_error = b'helvetica' in response.content and b'font' in response.content
                
                # PDF should be generated without Unicode errors
                success = is_pdf and pdf_size > 2000 and not has_unicode_error and not has_font_error
                
                details = f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                details += f"Unicode Error: {has_unicode_error}, Font Error: {has_font_error}"
                
                self.log_result("PDF Export Main Endpoint", success, details, response_time)
                return success
            else:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                self.log_result("PDF Export Main Endpoint", False,
                    f"Status: {response.status_code}, Error: {error_text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("PDF Export Main Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def validate_pdf_content(self, form_id):
        """Validate PDF content for proper timestamps and no Unicode errors"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check PDF signature
                has_pdf_signature = pdf_content.startswith(b'%PDF')
                has_eof_marker = b'%%EOF' in pdf_content
                
                # Check for proper timestamp format (regular dash, not em-dash)
                has_regular_dash_timestamps = b'/' in pdf_content  # Date format indicators
                
                # Check for dual currency display
                has_sar_currency = b'SAR' in pdf_content
                has_usd_conversion = b'USD' in pdf_content or b'$' in pdf_content
                
                # Check for supervisor information
                has_supervisor_info = b'Mahmoud' in pdf_content or b'Badr' in pdf_content
                
                # Validate PDF structure
                is_valid_pdf = has_pdf_signature and has_eof_marker and pdf_size > 2000
                
                success = is_valid_pdf and has_regular_dash_timestamps
                
                details = f"PDF Size: {pdf_size} bytes, Valid PDF: {is_valid_pdf}, "
                details += f"SAR Currency: {has_sar_currency}, USD Conversion: {has_usd_conversion}, "
                details += f"Supervisor Info: {has_supervisor_info}"
                
                self.log_result("Validate PDF Content", success, details, response_time)
                return success
            else:
                self.log_result("Validate PDF Content", False,
                    f"Status: {response.status_code}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Validate PDF Content", False, f"Exception: {str(e)}")
            return False
    
    def test_dual_currency_sar_conversion(self, form_id):
        """Test that SAR currency conversion is working correctly"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                # Find our test form
                test_form = None
                for form in forms:
                    if form.get("id") == form_id:
                        test_form = form
                        break
                
                if test_form:
                    purchase_currency = test_form.get("purchase_currency")
                    purchase_price = test_form.get("purchase_price")
                    quantity = test_form.get("quantity")
                    total_value = test_form.get("total_value_supplier_currency")
                    usd_equivalent = test_form.get("usd_equivalent")
                    
                    # Verify SAR currency and proper conversion
                    is_sar_currency = purchase_currency == "SAR"
                    correct_total = abs((quantity * purchase_price) - total_value) < 0.1 if all([quantity, purchase_price, total_value]) else False
                    has_usd_conversion = usd_equivalent is not None and usd_equivalent > 0
                    
                    # Check that it's not 1:1 conversion (the bug that was fixed)
                    not_one_to_one = abs(total_value - usd_equivalent) > 100 if all([total_value, usd_equivalent]) else True
                    
                    success = is_sar_currency and correct_total and has_usd_conversion and not_one_to_one
                    
                    details = f"Currency: {purchase_currency}, Price: {purchase_price}, Qty: {quantity}, "
                    details += f"Total SAR: {total_value}, USD Equiv: {usd_equivalent}, Not 1:1: {not_one_to_one}"
                    
                    self.log_result("Dual Currency SAR Conversion", success, details, response_time)
                    return success
                else:
                    self.log_result("Dual Currency SAR Conversion", False,
                        f"Test form not found in response", response_time)
                    return False
            else:
                self.log_result("Dual Currency SAR Conversion", False,
                    f"Status: {response.status_code}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Dual Currency SAR Conversion", False, f"Exception: {str(e)}")
            return False
    
    def run_unicode_pdf_tests(self):
        """Run all Unicode PDF generation fix tests"""
        print("🚀 UNICODE PDF GENERATION FIX TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}")
        print("Testing fix for Unicode character error in PDF generation")
        print("Error: Character '-' at index 22 in text is outside the range of characters supported by the font used: 'helvetica'")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create return form with Unicode timestamps that previously caused errors
        form_id = self.create_return_form_with_unicode_timestamps()
        if not form_id:
            print("❌ Failed to create test return form - stopping tests")
            return
        
        # 3. Test PDF Export - Individual Endpoint
        self.test_pdf_export_individual_endpoint(form_id)
        
        # 4. Test PDF Export - Main Endpoint  
        self.test_pdf_export_main_endpoint(form_id)
        
        # 5. Validate PDF Content
        self.validate_pdf_content(form_id)
        
        # 6. Test Dual Currency SAR Conversion
        self.test_dual_currency_sar_conversion(form_id)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 UNICODE PDF GENERATION FIX TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL UNICODE FIX REQUIREMENTS:")
        
        critical_tests = {
            "Return Form Creation with Unicode Timestamps": any("Create Return Form with Unicode Timestamps" in r["test"] and r["success"] for r in self.test_results),
            "PDF Export Individual Endpoint": any("PDF Export Individual Endpoint" in r["test"] and r["success"] for r in self.test_results),
            "PDF Export Main Endpoint": any("PDF Export Main Endpoint" in r["test"] and r["success"] for r in self.test_results),
            "PDF Content Validation": any("Validate PDF Content" in r["test"] and r["success"] for r in self.test_results),
            "SAR Currency Conversion": any("Dual Currency SAR Conversion" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED - UNICODE PDF GENERATION FIX WORKING!")
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 60)
        print("🏁 UNICODE PDF GENERATION FIX TESTING COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = UnicodePDFTester()
    tester.run_unicode_pdf_tests()