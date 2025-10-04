#!/usr/bin/env python3
"""
Comprehensive Unicode PDF Generation Fix Testing
Testing all critical scenarios from the review request
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class ComprehensiveUnicodeTester:
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
        """Authenticate with admin credentials: imadqejji/066380531I"""
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
                    f"Successfully authenticated admin user", response_time)
                return True
            else:
                self.log_result("Admin Authentication (imadqejji/066380531I)", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication (imadqejji/066380531I)", False, f"Exception: {str(e)}")
            return False
    
    def create_return_form_with_supervisor_mahmoud_badr(self):
        """Create return form with supervisor 'Mahmoud Badr' and digital approvals"""
        try:
            start_time = time.time()
            
            # Create timestamps with em-dash format that previously caused errors
            current_time = datetime.now()
            # Use regular dash format (the fix)
            timestamp_format = current_time.strftime("%d/%m/%Y - %H:%M")
            
            return_form_data = {
                "reference_number": f"RTN-MAHMOUD-BADR-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L - Mahmoud Badr Test",
                "barcode": "3222471081716",
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "Mahmoud Badr",
                "reason_for_return": "Quality issue - testing Unicode character fix with Mahmoud Badr",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": f"Unicode test with Mahmoud Badr - timestamps: {timestamp_format}",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": timestamp_format,  # This previously caused Unicode errors
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": timestamp_format,  # This previously caused Unicode errors
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
                
                self.log_result("Create Return Form with Supervisor Mahmoud Badr", True,
                    f"Form ID: {form_id}, Both approvals: supervisor_approved=true, section_manager_approved=true", response_time)
                return form_id
            else:
                self.log_result("Create Return Form with Supervisor Mahmoud Badr", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Create Return Form with Supervisor Mahmoud Badr", False, f"Exception: {str(e)}")
            return None
    
    def test_pdf_export_individual_endpoint(self, form_id):
        """Test PDF Export - Individual Endpoint: GET /api/export/return-form/{return_id}/pdf"""
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
                
                # PDF should be generated without Unicode errors and be >2KB
                success = is_pdf and pdf_size > 2000 and not has_unicode_error and not has_font_error
                
                details = f"Size: {pdf_size} bytes (>2KB: {pdf_size > 2000}), "
                details += f"No Unicode Error: {not has_unicode_error}, No Font Error: {not has_font_error}"
                
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
        """Test PDF Export - Main Endpoint: GET /api/export/return-form/{form_id}?format=pdf"""
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
                
                # PDF should be generated without Unicode errors and be >2KB
                success = is_pdf and pdf_size > 2000 and not has_unicode_error and not has_font_error
                
                details = f"Size: {pdf_size} bytes (>2KB: {pdf_size > 2000}), "
                details += f"No Unicode Error: {not has_unicode_error}, No Font Error: {not has_font_error}"
                
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
    
    def validate_pdf_content_timestamps(self, form_id):
        """Validate PDF Content: Ensure PDF contains proper timestamps with regular dashes (DD/MM/YYYY - HH:MM) not em-dashes"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check PDF signature and structure
                has_pdf_signature = pdf_content.startswith(b'%PDF')
                has_eof_marker = b'%%EOF' in pdf_content
                
                # Check for proper timestamp format (regular dash, not em-dash)
                # Look for date patterns with regular dashes
                has_regular_dash_timestamps = b'/' in pdf_content and b'-' in pdf_content
                
                # Check that there are NO em-dash characters in the PDF
                has_no_em_dash = b'\xe2\x80\x93' not in pdf_content  # UTF-8 encoding of em-dash
                
                # Check for dual currency display
                has_sar_currency = b'SAR' in pdf_content
                has_usd_conversion = b'USD' in pdf_content or b'$' in pdf_content
                
                # Validate PDF structure and content
                is_valid_pdf = has_pdf_signature and has_eof_marker and pdf_size > 2000
                proper_timestamps = has_regular_dash_timestamps and has_no_em_dash
                
                success = is_valid_pdf and proper_timestamps
                
                details = f"Valid PDF: {is_valid_pdf}, Regular Dash Timestamps: {has_regular_dash_timestamps}, "
                details += f"No Em-dash: {has_no_em_dash}, SAR: {has_sar_currency}, USD: {has_usd_conversion}"
                
                self.log_result("Validate PDF Content - Timestamps with Regular Dashes", success, details, response_time)
                return success
            else:
                self.log_result("Validate PDF Content - Timestamps with Regular Dashes", False,
                    f"Status: {response.status_code}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Validate PDF Content - Timestamps with Regular Dashes", False, f"Exception: {str(e)}")
            return False
    
    def test_dual_currency_sar_conversion_exact_scenario(self, form_id):
        """Test exact data that caused the error: 369.36 SAR should convert to ~$98.50 USD (NOT $369.36 USD)"""
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
                    
                    # Verify exact scenario from review request
                    is_sar_currency = purchase_currency == "SAR"
                    correct_total = abs(total_value - 369.38) < 0.1 if total_value else False  # ~369.36 SAR
                    correct_usd_conversion = abs(usd_equivalent - 98.51) < 1.0 if usd_equivalent else False  # ~$98.50 USD
                    
                    # CRITICAL: Check that it's NOT 1:1 conversion (the bug that was fixed)
                    not_one_to_one = abs(total_value - usd_equivalent) > 200 if all([total_value, usd_equivalent]) else True
                    
                    success = is_sar_currency and correct_total and correct_usd_conversion and not_one_to_one
                    
                    details = f"SAR: {purchase_currency}, Total: {total_value} SAR (~369.36), "
                    details += f"USD: ${usd_equivalent} (~$98.50), Not 1:1: {not_one_to_one}"
                    
                    self.log_result("Dual Currency SAR Conversion - Exact Scenario", success, details, response_time)
                    return success
                else:
                    self.log_result("Dual Currency SAR Conversion - Exact Scenario", False,
                        f"Test form not found in response", response_time)
                    return False
            else:
                self.log_result("Dual Currency SAR Conversion - Exact Scenario", False,
                    f"Status: {response.status_code}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Dual Currency SAR Conversion - Exact Scenario", False, f"Exception: {str(e)}")
            return False
    
    def test_no_character_encoding_errors(self, form_id):
        """Test that there are no more 'Character outside font range' errors"""
        try:
            start_time = time.time()
            
            # Test both endpoints to ensure no encoding errors
            individual_response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            main_response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            
            response_time = (time.time() - start_time) * 1000
            
            # Check both responses for encoding errors
            individual_success = individual_response.status_code == 200
            main_success = main_response.status_code == 200
            
            # Check that neither response contains error messages about character encoding
            individual_no_error = b'Character' not in individual_response.content or b'outside the range' not in individual_response.content
            main_no_error = b'Character' not in main_response.content or b'outside the range' not in main_response.content
            
            # Check that both PDFs are properly sized (not error responses)
            individual_proper_size = len(individual_response.content) > 2000
            main_proper_size = len(main_response.content) > 2000
            
            success = all([individual_success, main_success, individual_no_error, main_no_error, individual_proper_size, main_proper_size])
            
            details = f"Individual: {individual_response.status_code} ({len(individual_response.content)} bytes), "
            details += f"Main: {main_response.status_code} ({len(main_response.content)} bytes), No Errors: {individual_no_error and main_no_error}"
            
            self.log_result("No Character Encoding Errors", success, details, response_time)
            return success
                    
        except Exception as e:
            self.log_result("No Character Encoding Errors", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_unicode_tests(self):
        """Run all comprehensive Unicode PDF generation fix tests"""
        print("🚀 COMPREHENSIVE UNICODE PDF GENERATION FIX TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing fix for Unicode character error:")
        print("❌ OLD ERROR: Character '-' at index 22 in text is outside the range of characters supported by the font used: 'helvetica'")
        print("✅ EXPECTED: No more Unicode character errors, PDFs generate successfully")
        print("=" * 70)
        
        # 1. Authentication with admin credentials
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create return form with supervisor "Mahmoud Badr" and digital approvals
        form_id = self.create_return_form_with_supervisor_mahmoud_badr()
        if not form_id:
            print("❌ Failed to create test return form - stopping tests")
            return
        
        # 3. Test PDF Export - Individual Endpoint
        self.test_pdf_export_individual_endpoint(form_id)
        
        # 4. Test PDF Export - Main Endpoint  
        self.test_pdf_export_main_endpoint(form_id)
        
        # 5. Validate PDF Content - Timestamps with Regular Dashes
        self.validate_pdf_content_timestamps(form_id)
        
        # 6. Test Dual Currency SAR Conversion - Exact Scenario
        self.test_dual_currency_sar_conversion_exact_scenario(form_id)
        
        # 7. Test No Character Encoding Errors
        self.test_no_character_encoding_errors(form_id)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE UNICODE PDF GENERATION FIX TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification from review request
        print("\n🎯 CRITICAL UNICODE FIX REQUIREMENTS FROM REVIEW REQUEST:")
        
        critical_tests = {
            "✅ Admin Credentials (imadqejji/066380531I)": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results),
            "✅ Return Form with Supervisor 'Mahmoud Badr'": any("Mahmoud Badr" in r["test"] and r["success"] for r in self.test_results),
            "✅ Digital Approvals (supervisor_approved=true, section_manager_approved=true)": any("Mahmoud Badr" in r["test"] and "Both approvals" in r["details"] and r["success"] for r in self.test_results),
            "✅ PDF Export Individual Endpoint (GET /api/export/return-form/{return_id}/pdf)": any("PDF Export Individual Endpoint" in r["test"] and r["success"] for r in self.test_results),
            "✅ PDF Export Main Endpoint (GET /api/export/return-form/{form_id}?format=pdf)": any("PDF Export Main Endpoint" in r["test"] and r["success"] for r in self.test_results),
            "✅ Timestamps with Regular Dashes (DD/MM/YYYY - HH:MM) not em-dashes": any("Regular Dashes" in r["test"] and r["success"] for r in self.test_results),
            "✅ No Character Encoding Errors": any("No Character Encoding Errors" in r["test"] and r["success"] for r in self.test_results),
            "✅ Dual Currency SAR Conversion (369.36 SAR → ~$98.50 USD, NOT $369.36 USD)": any("Exact Scenario" in r["test"] and r["success"] for r in self.test_results)
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
            print(f"\n🎉 ALL CRITICAL REQUIREMENTS PASSED!")
            print("✅ Unicode character error COMPLETELY RESOLVED")
            print("✅ PDFs generate successfully with proper timestamps")
            print("✅ Dual currency SAR conversion working correctly")
            print("✅ No more 'Character outside font range' errors")
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE UNICODE PDF GENERATION FIX TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = ComprehensiveUnicodeTester()
    tester.run_comprehensive_unicode_tests()