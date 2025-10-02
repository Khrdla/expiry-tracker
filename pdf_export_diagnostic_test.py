#!/usr/bin/env python3
"""
PDF Export Failure Diagnostic Test
URGENT: Diagnose PDF Export Failure for Return Forms

The user reports they cannot export Return Form as PDF. This test will identify 
and diagnose the exact issue causing the PDF export to fail.
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

class PDFExportDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_forms = []
        self.existing_return_forms = []
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result with detailed information"""
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
                    f"Token received: {self.token[:20]}...", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_existing_return_forms(self):
        """Get existing return forms to test with"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                self.existing_return_forms = [form.get("id") for form in forms if form.get("id")]
                
                self.log_result("Get Existing Return Forms", True, 
                    f"Found {len(self.existing_return_forms)} existing forms", response_time)
                
                # Log details of first few forms
                if forms:
                    for i, form in enumerate(forms[:3]):
                        print(f"    Form {i+1}: ID={form.get('id')}, Ref={form.get('reference_number')}, "
                              f"Product={form.get('product_name', 'N/A')}")
                
                return len(self.existing_return_forms) > 0
            else:
                self.log_result("Get Existing Return Forms", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Get Existing Return Forms", False, f"Exception: {str(e)}")
            return False
    
    def create_test_return_form_single_item(self):
        """Create a single-item return form for testing"""
        try:
            start_time = time.time()
            
            return_form_data = {
                "reference_number": f"RTN-SINGLE-{int(time.time())}",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "reason_for_return": "Quality issue - damaged packaging",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": "Single-item test return form for PDF export diagnosis",
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
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                self.log_result("Create Single-Item Return Form", True,
                    f"Form ID: {form_id}, Product: Apple Juice Box 1L, "
                    f"Total: {return_form_data['quantity']} × {return_form_data['purchase_price']} SAR", response_time)
                return form_id
            else:
                self.log_result("Create Single-Item Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Create Single-Item Return Form", False, f"Exception: {str(e)}")
            return None
    
    def create_test_return_form_multi_item(self):
        """Create a multi-item return form with FOC items for testing"""
        try:
            start_time = time.time()
            
            return_form_data = {
                "reference_number": f"RTN-MULTI-{int(time.time())}",
                "items": [
                    {
                        "product_code": "3222471081716",
                        "product_name": "Apple Juice Box 1L",
                        "barcode": "3222471081716",
                        "quantity": 50,
                        "purchase_price": 3.75,
                        "purchase_currency": "SAR",
                        "supplier": "ExtenC",
                        "reason_for_return": "Quality issue",
                        "is_foc": False
                    },
                    {
                        "product_code": "3222471052747",
                        "product_name": "Orange Juice Box 1L",
                        "barcode": "3222471052747",
                        "quantity": 25,
                        "purchase_price": 0,
                        "purchase_currency": "SAR",
                        "supplier": "ExtenC",
                        "reason_for_return": "Promotional sample",
                        "is_foc": True,
                        "foc_reason": "Promotional sample"
                    }
                ],
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": "Multi-item test return form with FOC items for PDF export diagnosis",
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
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                self.log_result("Create Multi-Item Return Form", True,
                    f"Form ID: {form_id}, Items: 2 (1 normal, 1 FOC)", response_time)
                return form_id
            else:
                self.log_result("Create Multi-Item Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Create Multi-Item Return Form", False, f"Exception: {str(e)}")
            return None
    
    def test_pdf_export_endpoint_main(self, form_id, form_type="existing"):
        """Test main PDF export endpoint: GET /api/export/return-form/{form_id}?format=pdf"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            # Detailed response analysis
            status_code = response.status_code
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            if status_code == 200:
                # Check if it's actually a PDF
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_signature = response.content[:20] if response.content else b''
                
                self.log_result(f"Main PDF Export ({form_type})", is_pdf,
                    f"Status: {status_code}, Content-Type: {content_type}, "
                    f"Size: {content_length} bytes, PDF signature: {pdf_signature}", response_time)
                
                return is_pdf
            elif status_code == 401:
                self.log_result(f"Main PDF Export ({form_type})", False,
                    f"Authentication Error (401): {response.text[:200]}", response_time)
            elif status_code == 403:
                self.log_result(f"Main PDF Export ({form_type})", False,
                    f"Authorization Error (403): {response.text[:200]}", response_time)
            elif status_code == 404:
                self.log_result(f"Main PDF Export ({form_type})", False,
                    f"Form Not Found (404): {response.text[:200]}", response_time)
            elif status_code == 500:
                self.log_result(f"Main PDF Export ({form_type})", False,
                    f"Server Error (500): {response.text[:200]}", response_time)
            else:
                self.log_result(f"Main PDF Export ({form_type})", False,
                    f"Unexpected Status ({status_code}): {response.text[:200]}", response_time)
            
            return False
                    
        except Exception as e:
            self.log_result(f"Main PDF Export ({form_type})", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_export_endpoint_individual(self, form_id, form_type="existing"):
        """Test individual PDF export endpoint: GET /api/export/return-form/{form_id}/pdf"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            # Detailed response analysis
            status_code = response.status_code
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            if status_code == 200:
                # Check if it's actually a PDF
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_signature = response.content[:20] if response.content else b''
                
                self.log_result(f"Individual PDF Export ({form_type})", is_pdf,
                    f"Status: {status_code}, Content-Type: {content_type}, "
                    f"Size: {content_length} bytes, PDF signature: {pdf_signature}", response_time)
                
                return is_pdf
            elif status_code == 401:
                self.log_result(f"Individual PDF Export ({form_type})", False,
                    f"Authentication Error (401): {response.text[:200]}", response_time)
            elif status_code == 403:
                self.log_result(f"Individual PDF Export ({form_type})", False,
                    f"Authorization Error (403): {response.text[:200]}", response_time)
            elif status_code == 404:
                self.log_result(f"Individual PDF Export ({form_type})", False,
                    f"Form Not Found (404): {response.text[:200]}", response_time)
            elif status_code == 500:
                self.log_result(f"Individual PDF Export ({form_type})", False,
                    f"Server Error (500): {response.text[:200]}", response_time)
            else:
                self.log_result(f"Individual PDF Export ({form_type})", False,
                    f"Unexpected Status ({status_code}): {response.text[:200]}", response_time)
            
            return False
                    
        except Exception as e:
            self.log_result(f"Individual PDF Export ({form_type})", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_generation_functions(self, form_id):
        """Test PDF generation by examining response details"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                content = response.content
                
                # Check for ReportLab PDF structure
                has_reportlab_signature = b'ReportLab' in content
                has_pdf_structure = b'/Type /Catalog' in content
                has_geant_branding = b'GEANT' in content or b'Geant' in content
                
                # Check for multi-item vs single-item logic
                has_items_array = b'items' in content.lower()
                has_single_item = b'product_name' in content.lower()
                
                self.log_result("PDF Generation Functions Analysis", True,
                    f"ReportLab: {has_reportlab_signature}, PDF structure: {has_pdf_structure}, "
                    f"GEANT branding: {has_geant_branding}, Items array: {has_items_array}, "
                    f"Single item: {has_single_item}", response_time)
                
                return True
            else:
                self.log_result("PDF Generation Functions Analysis", False,
                    f"Cannot analyze - Status: {response.status_code}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("PDF Generation Functions Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_issues(self):
        """Test for authentication issues with PDF export"""
        try:
            # Test without authentication
            temp_session = requests.Session()
            
            if self.existing_return_forms:
                form_id = self.existing_return_forms[0]
                
                start_time = time.time()
                response = temp_session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 401 or response.status_code == 403:
                    self.log_result("Authentication Required Check", True,
                        f"Correctly requires authentication (Status: {response.status_code})", response_time)
                else:
                    self.log_result("Authentication Required Check", False,
                        f"Should require auth but got Status: {response.status_code}", response_time)
            else:
                self.log_result("Authentication Required Check", False,
                    "No forms available to test authentication")
                    
        except Exception as e:
            self.log_result("Authentication Required Check", False, f"Exception: {str(e)}")
    
    def test_different_data_scenarios(self):
        """Test PDF export with different data scenarios"""
        test_scenarios = []
        
        # Add existing forms
        for i, form_id in enumerate(self.existing_return_forms[:2]):
            test_scenarios.append((form_id, f"existing-{i+1}"))
        
        # Add newly created forms
        for i, form_id in enumerate(self.created_return_forms):
            test_scenarios.append((form_id, f"new-{i+1}"))
        
        for form_id, scenario in test_scenarios:
            # Test both endpoints
            self.test_pdf_export_endpoint_main(form_id, scenario)
            self.test_pdf_export_endpoint_individual(form_id, scenario)
    
    def validate_api_response_headers(self, form_id):
        """Validate API response headers for PDF export"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                headers = response.headers
                
                # Check required headers
                content_type = headers.get('content-type', '')
                content_disposition = headers.get('content-disposition', '')
                content_length = headers.get('content-length', '0')
                
                correct_content_type = 'application/pdf' in content_type
                has_filename = 'filename' in content_disposition
                valid_size = int(content_length) > 1000 if content_length.isdigit() else len(response.content) > 1000
                
                self.log_result("API Response Headers Validation", 
                    correct_content_type and valid_size,
                    f"Content-Type: {content_type}, Content-Disposition: {content_disposition}, "
                    f"Size: {content_length} bytes, Valid PDF size: {valid_size}", response_time)
            else:
                self.log_result("API Response Headers Validation", False,
                    f"Cannot validate headers - Status: {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("API Response Headers Validation", False, f"Exception: {str(e)}")
    
    def run_comprehensive_pdf_diagnostic(self):
        """Run comprehensive PDF export diagnostic tests"""
        print("🚨 PDF EXPORT FAILURE DIAGNOSTIC TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{'*' * len(ADMIN_PASSWORD)}")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Get existing return forms
        self.get_existing_return_forms()
        
        # 3. Create test return forms
        print("\n📝 Creating test return forms...")
        single_form_id = self.create_test_return_form_single_item()
        multi_form_id = self.create_test_return_form_multi_item()
        
        # 4. Test authentication issues
        print("\n🔐 Testing authentication requirements...")
        self.test_authentication_issues()
        
        # 5. Test basic PDF export endpoints
        print("\n📄 Testing PDF export endpoints...")
        self.test_different_data_scenarios()
        
        # 6. Test PDF generation functions
        if self.created_return_forms:
            print("\n🔧 Analyzing PDF generation functions...")
            self.test_pdf_generation_functions(self.created_return_forms[0])
            
            # 7. Validate API response
            print("\n✅ Validating API response headers...")
            self.validate_api_response_headers(self.created_return_forms[0])
        
        # Summary
        self.print_diagnostic_summary()
    
    def print_diagnostic_summary(self):
        """Print comprehensive diagnostic summary"""
        print("\n" + "=" * 60)
        print("🔍 PDF EXPORT DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"📋 EXISTING FORMS: {len(self.existing_return_forms)}")
        print(f"🆕 CREATED FORMS: {len(self.created_return_forms)}")
        
        # Critical diagnostic results
        print("\n🎯 CRITICAL DIAGNOSTIC RESULTS:")
        
        # Check for specific failure patterns
        auth_issues = [r for r in self.test_results if "401" in r["details"] or "403" in r["details"]]
        not_found_issues = [r for r in self.test_results if "404" in r["details"]]
        server_errors = [r for r in self.test_results if "500" in r["details"]]
        pdf_generation_issues = [r for r in self.test_results if not r["success"] and "PDF Export" in r["test"]]
        
        if auth_issues:
            print(f"🔐 Authentication Issues: {len(auth_issues)} tests failed with 401/403")
        if not_found_issues:
            print(f"📭 Missing Data Issues: {len(not_found_issues)} tests failed with 404")
        if server_errors:
            print(f"💥 Server Errors: {len(server_errors)} tests failed with 500")
        if pdf_generation_issues:
            print(f"📄 PDF Generation Issues: {len(pdf_generation_issues)} PDF export tests failed")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Success tests summary
        successful_tests = [r for r in self.test_results if r["success"]]
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS ({len(successful_tests)}):")
            for test in successful_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        # Root cause analysis
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        if success_rate == 0:
            print("   🚨 CRITICAL: All tests failed - likely authentication or server issues")
        elif success_rate < 50:
            print("   ⚠️  MAJOR: Most tests failed - likely PDF generation or endpoint issues")
        elif success_rate < 80:
            print("   ⚠️  MODERATE: Some tests failed - likely specific scenario issues")
        else:
            print("   ✅ GOOD: Most tests passed - minor issues or edge cases")
        
        print("\n" + "=" * 60)
        print("🏁 PDF EXPORT DIAGNOSTIC COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = PDFExportDiagnosticTester()
    tester.run_comprehensive_pdf_diagnostic()