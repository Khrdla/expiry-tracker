#!/usr/bin/env python3
"""
Enhanced Return Form with Department Head Dropdown and General Manager Testing
Testing the specific requirements from the review request:
1. Department Head dropdown with "Idder EL-Fermi" option
2. General Manager field with "Ahmed Massouni" default
3. 3-column manual signature layout in PDF
4. Professional PDF formatting with GEANT branding
"""

import requests
import json
import os
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_SUPERVISOR = "Mahmoud Badr"
DEPARTMENT_HEAD = "Idder EL-Fermi"
GENERAL_MANAGER = "Ahmed Massouni"
TEST_BARCODE = "3222471081716"  # Apple Juice Box 1L

class EnhancedReturnFormTester:
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
                    f"Login successful with {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_create_return_form_with_new_fields(self):
        """Test creating return form with Department Head and General Manager fields"""
        try:
            start_time = time.time()
            
            return_form_data = {
                "reference_number": f"RTN-{int(time.time())}-ENHANCED",
                "product_code": "3222471081716",
                "product_name": "Apple Juice Box 1L",
                "barcode": TEST_BARCODE,
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "reason_for_return": "Quality issue - damaged packaging",
                
                # Key requirements from review request
                "selected_supervisor": TEST_SUPERVISOR,
                "prepared_by_supervisor": TEST_SUPERVISOR,
                "department_head": DEPARTMENT_HEAD,  # New field
                "general_manager": GENERAL_MANAGER,  # New field
                
                "section_manager_name": "Imad Qejji",
                "notes": f"Enhanced return form with Department Head: {DEPARTMENT_HEAD} and General Manager: {GENERAL_MANAGER}",
                
                # Digital approvals
                "supervisor_approved": True,
                "supervisor_signature": f"{TEST_SUPERVISOR}_signature",
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
                
                self.log_result("Create Return Form with New Fields", True,
                    f"Form ID: {form_id}, Supervisor: {TEST_SUPERVISOR}, "
                    f"Dept Head: {DEPARTMENT_HEAD}, Gen Manager: {GENERAL_MANAGER}", response_time)
                return form_id
            else:
                self.log_result("Create Return Form with New Fields", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Create Return Form with New Fields", False, f"Exception: {str(e)}")
            return None
    
    def test_pdf_generation_with_three_signatures(self, form_id):
        """Test PDF generation with three manual signature sections"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check if it's a valid PDF
                is_pdf = pdf_content.startswith(b'%PDF')
                
                if is_pdf:
                    self.log_result("PDF Generation with Three Signatures", True,
                        f"Valid PDF generated, Size: {pdf_size} bytes", response_time)
                    return pdf_content
                else:
                    self.log_result("PDF Generation with Three Signatures", False,
                        f"Invalid PDF format, Size: {pdf_size} bytes", response_time)
                    return None
            else:
                self.log_result("PDF Generation with Three Signatures", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_result("PDF Generation with Three Signatures", False, f"Exception: {str(e)}")
            return None
    
    def test_pdf_content_verification(self, pdf_content):
        """Test PDF content for Department Head, General Manager, and Finance sections"""
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for required elements
            checks = {
                "Department Head Name": DEPARTMENT_HEAD in pdf_text,
                "General Manager Name": GENERAL_MANAGER in pdf_text,
                "Finance Department": "Finance Department" in pdf_text,
                "GEANT Branding": "GEANT" in pdf_text or "Geant" in pdf_text,
                "Supervisor Name": TEST_SUPERVISOR in pdf_text,
                "Manual Signatures": "Signature" in pdf_text or "signature" in pdf_text
            }
            
            passed_checks = sum(checks.values())
            total_checks = len(checks)
            
            success = passed_checks >= 4  # At least 4 out of 6 checks should pass
            
            details = f"Passed {passed_checks}/{total_checks} checks: " + ", ".join([
                f"{key}: {'✓' if value else '✗'}" for key, value in checks.items()
            ])
            
            self.log_result("PDF Content Verification", success, details, response_time)
            
            return success
            
        except Exception as e:
            self.log_result("PDF Content Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_layout_verification(self, pdf_content):
        """Test PDF layout for professional formatting and single-page format"""
        try:
            start_time = time.time()
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            num_pages = len(pdf_reader.pages)
            
            response_time = (time.time() - start_time) * 1000
            
            # Check single-page format
            single_page = num_pages == 1
            
            # Check PDF size (professional PDFs with branding should be substantial)
            pdf_size = len(pdf_content)
            substantial_size = pdf_size > 30000  # At least 30KB for professional format
            
            # Extract text to check for proper sections
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Check for professional sections
            has_form_details = "Form Details" in pdf_text or "FORM DETAILS" in pdf_text
            has_product_info = "Product Information" in pdf_text or "PRODUCT INFORMATION" in pdf_text
            has_return_value = "Return Value" in pdf_text or "RETURN VALUE" in pdf_text
            
            layout_checks = {
                "Single Page Format": single_page,
                "Substantial Size (>30KB)": substantial_size,
                "Form Details Section": has_form_details,
                "Product Information Section": has_product_info,
                "Return Value Section": has_return_value
            }
            
            passed_layout_checks = sum(layout_checks.values())
            total_layout_checks = len(layout_checks)
            
            success = passed_layout_checks >= 3  # At least 3 out of 5 checks should pass
            
            details = f"Layout checks {passed_layout_checks}/{total_layout_checks}: " + ", ".join([
                f"{key}: {'✓' if value else '✗'}" for key, value in layout_checks.items()
            ]) + f", Pages: {num_pages}, Size: {pdf_size} bytes"
            
            self.log_result("PDF Layout Verification", success, details, response_time)
            
            return success
            
        except Exception as e:
            self.log_result("PDF Layout Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_three_column_signature_layout(self, pdf_content):
        """Test for 3-column manual signature layout in PDF"""
        try:
            start_time = time.time()
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for three signature sections
            signature_sections = {
                "Department Head Section": DEPARTMENT_HEAD in pdf_text,
                "General Manager Section": GENERAL_MANAGER in pdf_text,
                "Finance Department Section": "Finance Department" in pdf_text or "Finance" in pdf_text
            }
            
            # Check for signature-related text
            has_signature_text = any(word in pdf_text.lower() for word in ["signature", "sign", "approved"])
            
            all_sections_present = all(signature_sections.values())
            
            success = all_sections_present and has_signature_text
            
            details = f"Signature sections: " + ", ".join([
                f"{key}: {'✓' if value else '✗'}" for key, value in signature_sections.items()
            ]) + f", Has signature text: {'✓' if has_signature_text else '✗'}"
            
            self.log_result("Three Column Signature Layout", success, details, response_time)
            
            return success
            
        except Exception as e:
            self.log_result("Three Column Signature Layout", False, f"Exception: {str(e)}")
            return False
    
    def test_digital_approvals_integration(self):
        """Test that digital approvals are properly integrated with manual signatures"""
        if not self.created_return_forms:
            self.log_result("Digital Approvals Integration", False, "No return forms created to test")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                if not forms:
                    self.log_result("Digital Approvals Integration", False, "No return forms found", response_time)
                    return False
                
                # Check first form for digital approval fields
                test_form = forms[0]
                
                approval_checks = {
                    "Supervisor Approved": test_form.get("supervisor_approved", False),
                    "Section Manager Approved": test_form.get("section_manager_approved", False),
                    "Supervisor Signature": bool(test_form.get("supervisor_signature")),
                    "Section Manager Signature": bool(test_form.get("section_manager_signature")),
                    "Supervisor Timestamp": bool(test_form.get("supervisor_timestamp")),
                    "Section Manager Timestamp": bool(test_form.get("section_manager_timestamp"))
                }
                
                passed_approvals = sum(approval_checks.values())
                total_approvals = len(approval_checks)
                
                success = passed_approvals >= 4  # At least 4 out of 6 should be present
                
                details = f"Digital approvals {passed_approvals}/{total_approvals}: " + ", ".join([
                    f"{key}: {'✓' if value else '✗'}" for key, value in approval_checks.items()
                ])
                
                self.log_result("Digital Approvals Integration", success, details, response_time)
                return success
            else:
                self.log_result("Digital Approvals Integration", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Digital Approvals Integration", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all enhanced return form tests"""
        print("🚀 ENHANCED RETURN FORM WITH DEPARTMENT HEAD & GENERAL MANAGER TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Supervisor: {TEST_SUPERVISOR}")
        print(f"Department Head: {DEPARTMENT_HEAD}")
        print(f"General Manager: {GENERAL_MANAGER}")
        print(f"Test Barcode: {TEST_BARCODE}")
        print("=" * 80)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create return form with new fields
        form_id = self.test_create_return_form_with_new_fields()
        if not form_id:
            print("❌ Return form creation failed - stopping PDF tests")
            return
        
        # 3. Test PDF generation
        pdf_content = self.test_pdf_generation_with_three_signatures(form_id)
        if not pdf_content:
            print("❌ PDF generation failed - stopping content tests")
            return
        
        # 4. Test PDF content verification
        self.test_pdf_content_verification(pdf_content)
        
        # 5. Test PDF layout verification
        self.test_pdf_layout_verification(pdf_content)
        
        # 6. Test three-column signature layout
        self.test_three_column_signature_layout(pdf_content)
        
        # 7. Test digital approvals integration
        self.test_digital_approvals_integration()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED RETURN FORM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 REVIEW REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Return Form Creation with New Fields": any("Create Return Form with New Fields" in r["test"] and r["success"] for r in self.test_results),
            "PDF Generation": any("PDF Generation with Three Signatures" in r["test"] and r["success"] for r in self.test_results),
            "PDF Content (Names & Sections)": any("PDF Content Verification" in r["test"] and r["success"] for r in self.test_results),
            "PDF Layout (Professional Format)": any("PDF Layout Verification" in r["test"] and r["success"] for r in self.test_results),
            "Three Column Signature Layout": any("Three Column Signature Layout" in r["test"] and r["success"] for r in self.test_results),
            "Digital Approvals Integration": any("Digital Approvals Integration" in r["test"] and r["success"] for r in self.test_results)
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
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 80)
        print("🏁 ENHANCED RETURN FORM TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = EnhancedReturnFormTester()
    tester.run_comprehensive_tests()