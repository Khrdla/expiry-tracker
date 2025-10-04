#!/usr/bin/env python3
"""
Final Return Form PDF Export Test
Verify the fix is working correctly
"""

import requests
import sys
import json
from datetime import datetime

class FinalReturnFormPDFTester:
    def __init__(self, base_url="https://inventory-master-78.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        # Admin credentials
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")

    def test_login(self):
        """Test login with admin credentials"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": self.admin_username, "password": self.admin_password},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_test("Admin Login", True, f"Token obtained")
                return True
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def test_create_return_form(self):
        """Create a new return form for testing"""
        test_data = {
            "reference_number": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "return_date": datetime.now().strftime('%Y-%m-%d'),
            "product_code": "TEST123",
            "product_name": "Test Product for PDF Export Verification",
            "quantity": 10,
            "purchase_price": 250.75,
            "purchase_currency": "YER",
            "supplier": "Test Supplier Company",
            "reason_for_return": "Quality control testing - PDF export verification",
            "prepared_by_supervisor": "Test Supervisor",
            "section_manager_name": "Test Section Manager",
            "department_head_name": "Test Department Head",
            "notes": "This return form was created to verify PDF export functionality is working correctly after bug fixes.",
            "status": "pending"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/returns",
                json=test_data,
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return_id = data.get('id')
                if return_id:
                    self.log_test("Create Return Form", True, f"ID: {return_id}")
                    return return_id
                else:
                    self.log_test("Create Return Form", False, "No ID returned")
                    return None
            else:
                self.log_test("Create Return Form", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Create Return Form", False, f"Error: {str(e)}")
            return None

    def test_pdf_export(self, return_id):
        """Test PDF export for a specific return form"""
        try:
            response = requests.get(
                f"{self.api_url}/export/return-form/{return_id}/pdf",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if content_type == 'application/pdf' and content_length > 0:
                    # Verify PDF signature
                    if response.content.startswith(b'%PDF'):
                        self.log_test(f"PDF Export ({return_id[:8]}...)", True, 
                                    f"{content_length} bytes, valid PDF")
                        return True
                    else:
                        self.log_test(f"PDF Export ({return_id[:8]}...)", False, 
                                    "Invalid PDF signature")
                        return False
                else:
                    self.log_test(f"PDF Export ({return_id[:8]}...)", False, 
                                f"Wrong content type or empty: {content_type}")
                    return False
            else:
                self.log_test(f"PDF Export ({return_id[:8]}...)", False, 
                            f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(f"PDF Export ({return_id[:8]}...)", False, f"Error: {str(e)}")
            return False

    def test_get_existing_forms(self):
        """Get existing return forms"""
        try:
            response = requests.get(
                f"{self.api_url}/returns",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                forms = response.json()
                self.log_test("Get Return Forms", True, f"Found {len(forms)} forms")
                return forms
            else:
                self.log_test("Get Return Forms", False, f"Status: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Return Forms", False, f"Error: {str(e)}")
            return []

    def run_final_test(self):
        """Run final comprehensive test"""
        print("🎯 Final Return Form PDF Export Verification")
        print("Testing the fixed functionality")
        print("=" * 50)
        
        # Step 1: Login
        if not self.test_login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Get existing forms
        existing_forms = self.test_get_existing_forms()
        
        # Step 3: Test PDF export with existing forms
        if existing_forms:
            print(f"\n📋 Testing PDF export with {min(3, len(existing_forms))} existing forms:")
            for i, form in enumerate(existing_forms[:3], 1):
                form_id = form.get('id')
                if form_id:
                    print(f"   {i}. Testing form: {form.get('product_name', 'Unknown')}")
                    self.test_pdf_export(form_id)
        
        # Step 4: Create new form and test
        print(f"\n📝 Creating new return form for testing:")
        new_form_id = self.test_create_return_form()
        
        if new_form_id:
            print(f"📄 Testing PDF export with newly created form:")
            self.test_pdf_export(new_form_id)
        
        # Results
        print("\n" + "=" * 50)
        print("📊 FINAL TEST RESULTS")
        print("=" * 50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Return Form PDF Export functionality is working correctly")
            print("✅ Database collection issue fixed (db.return_forms)")
            print("✅ ID field issue fixed (using 'id' instead of '_id')")
            print("✅ FileResponse issue fixed (using Response)")
            print("✅ PDF generation working with reportlab")
            print("✅ Authentication working correctly")
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} tests failed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = FinalReturnFormPDFTester()
    success = tester.run_final_test()
    sys.exit(0 if success else 1)