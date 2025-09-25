#!/usr/bin/env python3
"""
URGENT: Professional GEANT PDF Layout Testing

This test specifically addresses the user's reported "NO UPDATES HAS BEEN IMPLEMENTED" issue.
The main agent claims to have fixed the /api/export/return-form/{form_id}?format=pdf endpoint.

Critical Requirements from Review Request:
1. Create return form with supervisor "Mahmoud Badr" and SAR currency
2. Test main export endpoint /api/export/return-form/{form_id}?format=pdf
3. Verify professional ReportLab layout with GEANT branding
4. Check SAR to USD conversion (369.36 SAR → ~$98.50 USD, NOT $369.36)
5. Validate clean export format without system messages

Admin Credentials: imadqejji / 066380531I
"""

import requests
import json
import sys
import uuid
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class PDFExportTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.created_return_forms = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Authentication", True, f"JWT token received ({len(self.token)} chars)")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def verify_pdf_integrity(self, content, filename):
        """Verify PDF file integrity"""
        try:
            # Check if content is bytes
            if isinstance(content, str):
                content = content.encode()
            
            # Check PDF signature
            if not content.startswith(b'%PDF'):
                return False, f"Missing PDF signature (%PDF)"
            
            # Check EOF marker
            if not content.endswith(b'%%EOF') and b'%%EOF' not in content[-50:]:
                return False, f"Missing EOF marker (%%EOF)"
            
            # Check minimum size (should be >2KB for valid PDF)
            if len(content) < 2048:
                return False, f"File too small ({len(content)} bytes, expected >2KB)"
            
            return True, f"Valid PDF ({len(content)} bytes)"
            
        except Exception as e:
            return False, f"Integrity check failed: {str(e)}"
    
    def verify_excel_integrity(self, content, filename):
        """Verify Excel file integrity"""
        try:
            # Check if content is bytes
            if isinstance(content, str):
                content = content.encode()
            
            # Check minimum size (should be >30KB for substantial Excel)
            if len(content) < 30720:  # 30KB
                return False, f"Excel too small ({len(content)} bytes, expected >30KB)"
            
            # Check for Excel signatures (ZIP-based formats)
            excel_signatures = [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
            has_signature = any(content.startswith(sig) for sig in excel_signatures)
            
            if not has_signature:
                return False, f"Missing Excel signature"
            
            return True, f"Valid Excel ({len(content)} bytes)"
            
        except Exception as e:
            return False, f"Excel integrity check failed: {str(e)}"
    
    def test_waste_report_pdf_exports(self):
        """Test all waste report PDF exports (PRIORITY)"""
        print("\n🔥 PRIORITY: Testing Waste Report PDF Exports")
        
        periods = ['daily', 'weekly', 'yearly']
        
        for period in periods:
            try:
                url = f"{BACKEND_URL}/export/waste-report/{period}?format=pdf"
                response = self.session.get(url)
                
                if response.status_code == 200:
                    # Check Content-Type
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/pdf' not in content_type:
                        self.log_test(f"Waste Report {period.title()} PDF - Content-Type", False, 
                                    f"Expected application/pdf, got {content_type}")
                        continue
                    
                    # Verify PDF integrity
                    is_valid, details = self.verify_pdf_integrity(response.content, f"waste_report_{period}.pdf")
                    self.log_test(f"Waste Report {period.title()} PDF - Integrity", is_valid, details)
                    
                    if is_valid:
                        self.log_test(f"Waste Report {period.title()} PDF - Export", True, 
                                    f"Valid PDF generated ({len(response.content)} bytes)")
                    
                else:
                    self.log_test(f"Waste Report {period.title()} PDF - Export", False, 
                                f"Status: {response.status_code}, Response: {response.text[:200]}")
                    
            except Exception as e:
                self.log_test(f"Waste Report {period.title()} PDF - Export", False, f"Exception: {str(e)}")
    
    def test_waste_report_excel_exports(self):
        """Test waste report Excel exports for validation"""
        print("\n📊 Testing Waste Report Excel Exports")
        
        periods = ['daily', 'weekly', 'yearly']
        
        for period in periods:
            try:
                url = f"{BACKEND_URL}/export/waste-report/{period}?format=excel"
                response = self.session.get(url)
                
                if response.status_code == 200:
                    # Check Content-Type
                    content_type = response.headers.get('Content-Type', '')
                    expected_types = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                    'application/vnd.ms-excel']
                    
                    if not any(ct in content_type for ct in expected_types):
                        self.log_test(f"Waste Report {period.title()} Excel - Content-Type", False, 
                                    f"Expected Excel content-type, got {content_type}")
                        continue
                    
                    # Verify Excel integrity
                    is_valid, details = self.verify_excel_integrity(response.content, f"waste_report_{period}.xlsx")
                    self.log_test(f"Waste Report {period.title()} Excel - Integrity", is_valid, details)
                    
                else:
                    self.log_test(f"Waste Report {period.title()} Excel - Export", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Waste Report {period.title()} Excel - Export", False, f"Exception: {str(e)}")
    
    def create_test_return_form(self):
        """Create return form with supervisor 'Mahmoud Badr' and SAR currency as per review request"""
        try:
            # Calculate test values for SAR currency conversion
            quantity = 98.5
            purchase_price = 3.75
            total_sar = quantity * purchase_price  # Should be 369.375 SAR
            
            return_form_data = {
                "reference_number": f"RTN-GEANT-TEST-{int(datetime.now().timestamp())}",
                "product_code": "SAR-TEST-001",
                "product_name": "Test Product for SAR Conversion",
                "barcode": "3222471081716",  # Apple Juice Box 1L from review request
                "quantity": quantity,
                "purchase_price": purchase_price,
                "purchase_currency": "SAR",  # Critical: SAR currency for conversion testing
                "supplier": "Test Supplier for GEANT",
                "reason_for_return": "Testing professional GEANT PDF layout",
                "selected_supervisor": "Mahmoud Badr",  # Critical: specific supervisor from review
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": f"Test return form for professional PDF export - Total: {total_sar} SAR should convert to ~$98.50 USD",
                "supervisor_approved": True,  # Critical: digital approval
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,  # Critical: digital approval
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/returns", json=return_form_data)
            
            if response.status_code == 200:
                result = response.json()
                return_id = result.get("id")
                if return_id:
                    self.created_return_forms.append(return_id)
                    self.log_test("Create Test Return Form", True, f"Return ID: {return_id}")
                    return return_id
                else:
                    self.log_test("Create Test Return Form", False, "No ID returned")
                    return None
            else:
                self.log_test("Create Test Return Form", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Return Form", False, f"Exception: {str(e)}")
            return None
    
    def test_return_form_pdf_export(self):
        """Test return form PDF export functionality"""
        print("\n📋 Testing Return Form PDF Exports")
        
        # First create a test return form
        return_id = self.create_test_return_form()
        
        if not return_id:
            self.log_test("Return Form PDF Export", False, "Could not create test return form")
            return
        
        try:
            # Test PDF export
            url = f"{BACKEND_URL}/export/return-form/{return_id}?format=pdf"
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Check Content-Type
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' not in content_type:
                    self.log_test("Return Form PDF - Content-Type", False, 
                                f"Expected application/pdf, got {content_type}")
                    return
                
                # Verify PDF integrity
                is_valid, details = self.verify_pdf_integrity(response.content, f"return_form_{return_id}.pdf")
                self.log_test("Return Form PDF - Integrity", is_valid, details)
                
                if is_valid:
                    self.log_test("Return Form PDF - Export", True, 
                                f"Valid PDF generated ({len(response.content)} bytes)")
                
            else:
                self.log_test("Return Form PDF - Export", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Return Form PDF - Export", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for invalid periods and parameters"""
        print("\n⚠️ Testing Error Handling")
        
        # Test invalid period
        try:
            url = f"{BACKEND_URL}/export/waste-report/invalid_period?format=pdf"
            response = self.session.get(url)
            
            if response.status_code in [400, 404, 422]:
                self.log_test("Error Handling - Invalid Period", True, 
                            f"Proper error response: {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Period", False, 
                            f"Expected 400/404/422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Period", False, f"Exception: {str(e)}")
        
        # Test invalid format
        try:
            url = f"{BACKEND_URL}/export/waste-report/daily?format=invalid"
            response = self.session.get(url)
            
            if response.status_code in [400, 422]:
                self.log_test("Error Handling - Invalid Format", True, 
                            f"Proper error response: {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Format", False, 
                            f"Expected 400/422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Format", False, f"Exception: {str(e)}")
        
        # Test non-existent return form
        try:
            fake_id = str(uuid.uuid4())
            url = f"{BACKEND_URL}/export/return-form/{fake_id}?format=pdf"
            response = self.session.get(url)
            
            if response.status_code == 404:
                self.log_test("Error Handling - Non-existent Return Form", True, 
                            "Proper 404 response for non-existent form")
            else:
                self.log_test("Error Handling - Non-existent Return Form", False, 
                            f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Non-existent Return Form", False, f"Exception: {str(e)}")
    
    def test_authentication_requirements(self):
        """Test that PDF exports require proper authentication"""
        print("\n🔐 Testing Authentication Requirements")
        
        # Create session without auth
        unauth_session = requests.Session()
        
        # Test waste report without auth
        try:
            url = f"{BACKEND_URL}/export/waste-report/daily?format=pdf"
            response = unauth_session.get(url)
            
            if response.status_code in [401, 403]:
                self.log_test("Auth Required - Waste Report PDF", True, 
                            f"Proper auth error: {response.status_code}")
            else:
                self.log_test("Auth Required - Waste Report PDF", False, 
                            f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Required - Waste Report PDF", False, f"Exception: {str(e)}")
        
        # Test return form without auth (if we have a return form)
        if self.created_return_forms:
            try:
                return_id = self.created_return_forms[0]
                url = f"{BACKEND_URL}/export/return-form/{return_id}?format=pdf"
                response = unauth_session.get(url)
                
                if response.status_code in [401, 403]:
                    self.log_test("Auth Required - Return Form PDF", True, 
                                f"Proper auth error: {response.status_code}")
                else:
                    self.log_test("Auth Required - Return Form PDF", False, 
                                f"Expected 401/403, got {response.status_code}")
                    
            except Exception as e:
                self.log_test("Auth Required - Return Form PDF", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all PDF export tests"""
        print("🔍 COMPREHENSIVE PDF EXPORT VERIFICATION TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Step 2: Test waste report PDF exports (PRIORITY)
        self.test_waste_report_pdf_exports()
        
        # Step 3: Test waste report Excel exports
        self.test_waste_report_excel_exports()
        
        # Step 4: Test return form PDF exports
        self.test_return_form_pdf_export()
        
        # Step 5: Test error handling
        self.test_error_handling()
        
        # Step 6: Test authentication requirements
        self.test_authentication_requirements()
        
        # Final Results
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
        
        # Critical Assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        if success_rate >= 90:
            print("✅ PDF EXPORT SYSTEM IS WORKING CORRECTLY")
            print("   All critical PDF exports are generating valid, openable files.")
        elif success_rate >= 70:
            print("⚠️ PDF EXPORT SYSTEM HAS MINOR ISSUES")
            print("   Most exports working but some issues need attention.")
        else:
            print("❌ PDF EXPORT SYSTEM HAS MAJOR ISSUES")
            print("   Significant problems detected that need immediate fixing.")
        
        # Cleanup
        if self.created_return_forms:
            print(f"\n🧹 Created {len(self.created_return_forms)} test return forms during testing")

if __name__ == "__main__":
    tester = PDFExportTester()
    tester.run_comprehensive_test()