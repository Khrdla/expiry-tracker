#!/usr/bin/env python3
"""
CRITICAL FIXES VERIFICATION TEST
Testing the two specific issues identified in the review request:
1. Excel Export MergedCell Fix - Test Excel export without "MergedCell column_letter" error
2. Individual PDF Export Validation - Verify /api/export/return-form/{return_id}/pdf blocks exports without approvals
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

# Test data from review request
TEST_SUPERVISORS = ["Mahmoud Badr", "Abdelhamed Mostafa"]
SECTION_MANAGER = "Imad Qejji"
TEST_BARCODE = "3222471081716"  # Apple Juice Box 1L

class SupplierReturnFormFixesTester:
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
                    f"Token received for testing", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_approved_return_form(self):
        """Create return form WITH approvals for testing Excel export"""
        try:
            start_time = time.time()
            
            approved_form_data = {
                "reference_number": f"RTN-APPROVED-{int(time.time())}",
                "product_code": "TEST-APPROVED-001",
                "product_name": "Apple Juice Box 1L",
                "barcode": TEST_BARCODE,
                "quantity": 10,
                "purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "reason_for_return": "Quality issue - testing approved form",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": SECTION_MANAGER,
                "notes": "Test approved return form for Excel export",
                # CRITICAL: Both approvals set to TRUE
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": f"{SECTION_MANAGER}_signature", 
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=approved_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append({"id": form_id, "type": "approved"})
                
                self.log_result("Create Approved Return Form", True,
                    f"Form ID: {form_id}, Both approvals: TRUE", response_time)
                return form_id
            else:
                self.log_result("Create Approved Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Create Approved Return Form", False, f"Exception: {str(e)}")
            return None
    
    def create_unapproved_return_form(self):
        """Create return form WITHOUT approvals for testing PDF export validation"""
        try:
            start_time = time.time()
            
            unapproved_form_data = {
                "reference_number": f"RTN-UNAPPROVED-{int(time.time())}",
                "product_code": "TEST-UNAPPROVED-001",
                "product_name": "Apple Juice Box 1L",
                "barcode": TEST_BARCODE,
                "quantity": 5,
                "purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "reason_for_return": "Quality issue - testing unapproved form",
                "selected_supervisor": "Abdelhamed Mostafa",
                "prepared_by_supervisor": "Abdelhamed Mostafa",
                "section_manager_name": SECTION_MANAGER,
                "notes": "Test unapproved return form for PDF validation",
                # CRITICAL: Both approvals set to FALSE
                "supervisor_approved": False,
                "section_manager_approved": False
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=unapproved_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append({"id": form_id, "type": "unapproved"})
                
                self.log_result("Create Unapproved Return Form", True,
                    f"Form ID: {form_id}, Both approvals: FALSE", response_time)
                return form_id
            else:
                self.log_result("Create Unapproved Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Create Unapproved Return Form", False, f"Exception: {str(e)}")
            return None
    
    def test_excel_export_mergedcell_fix(self, approved_form_id):
        """
        CRITICAL FIX 1: Test Excel export without "MergedCell column_letter" error
        This should work for approved return forms
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{approved_form_id}?format=excel")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a valid Excel file
                content_type = response.headers.get('content-type', '')
                excel_size = len(response.content)
                
                # Check for Excel file signatures
                is_excel = (
                    'spreadsheet' in content_type.lower() or 
                    'excel' in content_type.lower() or
                    response.content.startswith(b'PK') or  # ZIP-based Excel format
                    excel_size > 5000  # Reasonable Excel file size
                )
                
                # Check if response contains error messages
                response_text = response.content.decode('utf-8', errors='ignore')
                has_mergedcell_error = 'MergedCell' in response_text or 'column_letter' in response_text
                
                success = is_excel and not has_mergedcell_error
                
                self.log_result("Excel Export MergedCell Fix", success,
                    f"Content-Type: {content_type}, Size: {excel_size} bytes, "
                    f"Excel format: {is_excel}, MergedCell error: {has_mergedcell_error}", response_time)
                
                return success
            else:
                self.log_result("Excel Export MergedCell Fix", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Excel Export MergedCell Fix", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_export_validation_fix_unapproved(self, unapproved_form_id):
        """
        CRITICAL FIX 2: Test individual PDF export validation - should BLOCK unapproved forms
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{unapproved_form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            # This should return 400 error with message about approvals required
            if response.status_code == 400:
                response_text = response.text.lower()
                has_approval_message = (
                    'approval' in response_text or 
                    'approved' in response_text or
                    'signature' in response_text or
                    'authorization' in response_text
                )
                
                self.log_result("PDF Export Validation - Block Unapproved", True,
                    f"Correctly blocked with 400 status, Approval message: {has_approval_message}, "
                    f"Response: {response.text[:100]}", response_time)
                return True
            elif response.status_code == 403:
                # Also acceptable - forbidden access
                self.log_result("PDF Export Validation - Block Unapproved", True,
                    f"Correctly blocked with 403 status, Response: {response.text[:100]}", response_time)
                return True
            else:
                # Should not allow export without approvals
                self.log_result("PDF Export Validation - Block Unapproved", False,
                    f"SHOULD BLOCK but got status: {response.status_code}, "
                    f"Response: {response.text[:100]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("PDF Export Validation - Block Unapproved", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_export_validation_fix_approved(self, approved_form_id):
        """
        CRITICAL FIX 2: Test individual PDF export validation - should ALLOW approved forms
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{approved_form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a valid PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                self.log_result("PDF Export Validation - Allow Approved", is_pdf,
                    f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                    f"PDF signature: {response.content[:10]}", response_time)
                return is_pdf
            else:
                self.log_result("PDF Export Validation - Allow Approved", False,
                    f"SHOULD ALLOW but got status: {response.status_code}, "
                    f"Response: {response.text[:100]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("PDF Export Validation - Allow Approved", False, f"Exception: {str(e)}")
            return False
    
    def test_dual_currency_display_in_exports(self, approved_form_id):
        """Test dual currency display in both PDF and Excel exports"""
        try:
            # Test PDF dual currency
            start_time = time.time()
            pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{approved_form_id}/pdf")
            pdf_response_time = (time.time() - start_time) * 1000
            
            pdf_has_dual_currency = False
            if pdf_response.status_code == 200:
                pdf_content = pdf_response.content.decode('utf-8', errors='ignore')
                # Look for currency indicators
                has_eur = 'EUR' in pdf_content
                has_usd = 'USD' in pdf_content or '$' in pdf_content
                pdf_has_dual_currency = has_eur and (has_usd or 'equivalent' in pdf_content.lower())
            
            # Test Excel dual currency
            start_time = time.time()
            excel_response = self.session.get(f"{BACKEND_URL}/export/return-form/{approved_form_id}?format=excel")
            excel_response_time = (time.time() - start_time) * 1000
            
            excel_has_dual_currency = False
            if excel_response.status_code == 200:
                # Excel files are binary, but we can check for basic currency indicators
                excel_content = excel_response.content.decode('utf-8', errors='ignore')
                has_eur = 'EUR' in excel_content
                has_usd = 'USD' in excel_content or '$' in excel_content
                excel_has_dual_currency = has_eur and (has_usd or 'equivalent' in excel_content.lower())
            
            overall_success = pdf_has_dual_currency or excel_has_dual_currency
            
            self.log_result("Dual Currency Display in Exports", overall_success,
                f"PDF dual currency: {pdf_has_dual_currency}, Excel dual currency: {excel_has_dual_currency}",
                (pdf_response_time + excel_response_time) / 2)
            
            return overall_success
            
        except Exception as e:
            self.log_result("Dual Currency Display in Exports", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_workflow(self):
        """Test complete workflow as specified in review request"""
        try:
            # Create return form with supervisor "Mahmoud Badr"
            start_time = time.time()
            
            complete_workflow_data = {
                "reference_number": f"RTN-WORKFLOW-{int(time.time())}",
                "product_code": "WORKFLOW-001",
                "product_name": "Apple Juice Box 1L",
                "barcode": TEST_BARCODE,
                "quantity": 15,
                "purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "reason_for_return": "Complete workflow test",
                "selected_supervisor": "Mahmoud Badr",  # As specified in review
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": SECTION_MANAGER,
                "notes": "Complete workflow test with dual currency",
                # Add digital approvals as specified
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_digital_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": f"{SECTION_MANAGER}_digital_signature", 
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=complete_workflow_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                workflow_form_id = data.get("id")
                
                # Test both export formats
                pdf_success = self.test_pdf_export_validation_fix_approved(workflow_form_id)
                excel_success = self.test_excel_export_mergedcell_fix(workflow_form_id)
                
                overall_success = pdf_success and excel_success
                
                self.log_result("Complete Workflow Test", overall_success,
                    f"Form ID: {workflow_form_id}, PDF export: {pdf_success}, Excel export: {excel_success}",
                    response_time)
                
                return overall_success
            else:
                self.log_result("Complete Workflow Test", False,
                    f"Failed to create workflow form: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Complete Workflow Test", False, f"Exception: {str(e)}")
            return False
    
    def run_critical_fixes_tests(self):
        """Run all critical fixes tests as specified in review request"""
        print("🎯 CRITICAL FIXES VERIFICATION TEST")
        print("=" * 60)
        print("Testing the two specific issues identified:")
        print("1. Excel Export MergedCell Fix")
        print("2. Individual PDF Export Validation")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}")
        print(f"Test Barcode: {TEST_BARCODE}")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create test data
        print("\n📝 Creating test return forms...")
        approved_form_id = self.create_approved_return_form()
        unapproved_form_id = self.create_unapproved_return_form()
        
        if not approved_form_id or not unapproved_form_id:
            print("❌ Failed to create test forms - stopping tests")
            return
        
        print(f"✅ Created approved form: {approved_form_id}")
        print(f"✅ Created unapproved form: {unapproved_form_id}")
        
        # 3. CRITICAL FIX 1: Excel Export MergedCell Fix
        print(f"\n🔧 TESTING CRITICAL FIX 1: Excel Export MergedCell Fix")
        self.test_excel_export_mergedcell_fix(approved_form_id)
        
        # 4. CRITICAL FIX 2: PDF Export Validation Fix
        print(f"\n🔧 TESTING CRITICAL FIX 2: PDF Export Validation Fix")
        self.test_pdf_export_validation_fix_unapproved(unapproved_form_id)
        self.test_pdf_export_validation_fix_approved(approved_form_id)
        
        # 5. Additional verification tests
        print(f"\n🔍 ADDITIONAL VERIFICATION TESTS")
        self.test_dual_currency_display_in_exports(approved_form_id)
        self.test_complete_workflow()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary focused on critical fixes"""
        print("\n" + "=" * 60)
        print("📊 CRITICAL FIXES TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical fixes verification
        print("\n🎯 CRITICAL FIXES VERIFICATION:")
        
        critical_fixes = {
            "Excel Export MergedCell Fix": any("Excel Export MergedCell Fix" in r["test"] and r["success"] for r in self.test_results),
            "PDF Export Validation - Block Unapproved": any("PDF Export Validation - Block Unapproved" in r["test"] and r["success"] for r in self.test_results),
            "PDF Export Validation - Allow Approved": any("PDF Export Validation - Allow Approved" in r["test"] and r["success"] for r in self.test_results),
        }
        
        for fix, status in critical_fixes.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {fix}")
        
        # Overall assessment
        all_critical_fixes_working = all(critical_fixes.values())
        print(f"\n🏆 OVERALL ASSESSMENT: {'✅ ALL CRITICAL FIXES WORKING' if all_critical_fixes_working else '❌ SOME CRITICAL FIXES NEED ATTENTION'}")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)
        print("🏁 CRITICAL FIXES VERIFICATION COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = SupplierReturnFormFixesTester()
    tester.run_critical_fixes_tests()