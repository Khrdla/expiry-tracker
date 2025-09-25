#!/usr/bin/env python3
"""
Return Form PDF Export Authentication Debug Test
Focus: Debug the PDF export authentication issue for Return Form

CRITICAL INVESTIGATION:
1. Test Return Form Creation - Create a test return form to get a valid return_id
2. Test PDF Export Endpoint - Test GET /api/export/return-form/{return_id}/pdf with proper Bearer token
3. Check Authentication Dependency - Verify get_current_user dependency is working correctly
4. Test Token Validation - Verify the Bearer token format and validation
5. Check Database Query - Ensure return_forms collection exists and has data
6. Debug Authentication Flow - Step through the entire authentication process

AUTHENTICATION: Use admin credentials (imadqejji/066380531I)
FOCUS: Find exactly why the PDF export endpoint returns "Not authenticated" despite proper Bearer token being sent.
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class ReturnFormPDFDebugTester:
    def __init__(self, base_url="https://geant-inventory-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials from review request
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"
        self.created_return_ids = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, return_response=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        print(f"   Headers: {test_headers}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:500] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)

            if return_response:
                return success, response_data, response
            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - server may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test login with admin credentials"""
        print("\n🔐 STEP 1: ADMIN LOGIN TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin Login (imadqejji/066380531I)",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password}
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Admin token obtained: {self.token[:50]}...")
            print(f"   🔑 Token type: {response.get('token_type', 'unknown')}")
            
            # Verify token format
            if self.token and len(self.token) > 20:
                print("   ✅ Token appears to be valid JWT format")
                return True
            else:
                print("   ❌ Token appears to be invalid")
                return False
        else:
            print(f"   ❌ Admin login failed: {response}")
            return False

    def test_token_validation(self):
        """Test token validation by calling a protected endpoint"""
        print("\n🔐 STEP 2: TOKEN VALIDATION TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Token Validation", False, "No token available")
            return False
        
        # Test with dashboard endpoint (known to require auth)
        success, response = self.run_test(
            "Token Validation via Dashboard",
            "GET",
            "dashboard",
            200
        )
        
        if success:
            print("   ✅ Token is valid and accepted by protected endpoints")
            return True
        else:
            print("   ❌ Token validation failed")
            return False

    def test_get_current_user_dependency(self):
        """Test the get_current_user dependency directly"""
        print("\n👤 STEP 3: GET_CURRENT_USER DEPENDENCY TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Get Current User", False, "No token available")
            return False
        
        # Try to access user info endpoint if it exists
        success, response = self.run_test(
            "Get Current User Info",
            "GET",
            "auth/me",
            200
        )
        
        if success and isinstance(response, dict):
            self.user_data = response
            print(f"   👤 User: {response.get('username')}")
            print(f"   🔑 Admin: {response.get('is_admin')}")
            print(f"   🏢 Role: {response.get('role')}")
            print(f"   🏢 Department: {response.get('department')}")
            return True
        else:
            # Try alternative endpoint
            success2, response2 = self.run_test(
                "Get Current User via Products",
                "GET",
                "products?limit=1",
                200
            )
            if success2:
                print("   ✅ Authentication dependency working (verified via products endpoint)")
                return True
            else:
                print("   ❌ Authentication dependency not working")
                return False

    def create_test_return_form(self):
        """Create a test return form to get a valid return_id"""
        print("\n📝 STEP 4: CREATE TEST RETURN FORM")
        print("=" * 50)
        
        # Create test return form data
        test_return_data = {
            "reference_number": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "product_code": "TEST001",
            "product_name": "Test Product for PDF Export",
            "quantity": 5,
            "purchase_price": 100.0,
            "purchase_currency": "YER",
            "supplier": "Test Supplier",
            "reason_for_return": "Quality issue - testing PDF export functionality",
            "manager_approval": {
                "approved": True,
                "manager_name": "Test Manager",
                "approval_date": datetime.now().isoformat(),
                "signature": "Test Manager Signature"
            },
            "finance_approval": {
                "approved": True,
                "finance_officer": "Test Finance Officer",
                "approval_date": datetime.now().isoformat(),
                "signature": "Test Finance Signature"
            },
            "notes": "This is a test return form created for PDF export authentication debugging"
        }
        
        success, response = self.run_test(
            "Create Test Return Form",
            "POST",
            "returns",
            200,
            data=test_return_data
        )
        
        if success and isinstance(response, dict):
            return_id = response.get('id')
            if return_id:
                self.created_return_ids.append(return_id)
                print(f"   📝 Created return form with ID: {return_id}")
                return return_id
            else:
                print("   ❌ No return ID in response")
                return None
        else:
            print("   ❌ Failed to create return form")
            return None

    def test_return_form_retrieval(self, return_id):
        """Test retrieving the created return form"""
        print("\n📋 STEP 5: RETURN FORM RETRIEVAL TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            f"Retrieve Return Form {return_id}",
            "GET",
            "returns",
            200
        )
        
        if success and isinstance(response, list):
            # Find our return form
            our_form = None
            for form in response:
                if form.get('id') == return_id:
                    our_form = form
                    break
            
            if our_form:
                print(f"   ✅ Return form found in database")
                print(f"   📝 Reference: {our_form.get('reference_number')}")
                print(f"   📦 Product: {our_form.get('product_name')}")
                print(f"   👤 Created by: {our_form.get('created_by')}")
                return True
            else:
                print(f"   ❌ Return form {return_id} not found in database")
                return False
        else:
            print("   ❌ Failed to retrieve return forms")
            return False

    def test_pdf_export_endpoint_detailed(self, return_id):
        """Test PDF export endpoint with detailed debugging"""
        print("\n📄 STEP 6: PDF EXPORT ENDPOINT DETAILED TEST")
        print("=" * 50)
        
        if not return_id:
            self.log_test("PDF Export", False, "No return_id available")
            return False
        
        # Test the PDF export endpoint
        success, response_data, full_response = self.run_test(
            f"PDF Export for Return {return_id}",
            "GET",
            f"export/return-form/{return_id}/pdf",
            200,
            return_response=True
        )
        
        print(f"   📊 Response Status: {full_response.status_code}")
        print(f"   📊 Response Headers: {dict(full_response.headers)}")
        print(f"   📊 Content-Type: {full_response.headers.get('content-type', 'Not set')}")
        print(f"   📊 Content-Length: {full_response.headers.get('content-length', 'Not set')}")
        
        if full_response.status_code == 200:
            # Check if it's actually a PDF
            content_type = full_response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                print("   ✅ PDF export successful - correct content type")
                print(f"   📄 PDF size: {len(full_response.content)} bytes")
                
                # Verify PDF signature
                if full_response.content.startswith(b'%PDF'):
                    print("   ✅ Valid PDF file signature")
                    return True
                else:
                    print("   ❌ Invalid PDF file signature")
                    return False
            else:
                print(f"   ❌ Wrong content type: {content_type}")
                return False
        elif full_response.status_code == 401:
            print("   ❌ AUTHENTICATION ERROR: 401 Unauthorized")
            print("   🔍 This indicates the Bearer token is not being accepted")
            return False
        elif full_response.status_code == 403:
            print("   ❌ AUTHORIZATION ERROR: 403 Forbidden")
            print("   🔍 This indicates the user doesn't have permission")
            return False
        elif full_response.status_code == 404:
            print("   ❌ NOT FOUND ERROR: 404")
            print("   🔍 This indicates the return form or endpoint doesn't exist")
            return False
        else:
            print(f"   ❌ Unexpected status code: {full_response.status_code}")
            print(f"   📄 Response body: {full_response.text[:500]}")
            return False

    def test_pdf_export_without_auth(self, return_id):
        """Test PDF export without authentication to verify it fails properly"""
        print("\n🚫 STEP 7: PDF EXPORT WITHOUT AUTH TEST")
        print("=" * 50)
        
        if not return_id:
            self.log_test("PDF Export No Auth", False, "No return_id available")
            return False
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            f"PDF Export No Auth for Return {return_id}",
            "GET",
            f"export/return-form/{return_id}/pdf",
            403  # Should return 403 or 401
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ PDF export correctly requires authentication")
            return True
        else:
            print("   ❌ PDF export should require authentication but doesn't")
            return False

    def test_pdf_export_with_invalid_token(self, return_id):
        """Test PDF export with invalid token"""
        print("\n🔐 STEP 8: PDF EXPORT WITH INVALID TOKEN TEST")
        print("=" * 50)
        
        if not return_id:
            self.log_test("PDF Export Invalid Token", False, "No return_id available")
            return False
        
        # Temporarily set invalid token
        original_token = self.token
        self.token = "invalid_token_12345"
        
        success, response = self.run_test(
            f"PDF Export Invalid Token for Return {return_id}",
            "GET",
            f"export/return-form/{return_id}/pdf",
            401  # Should return 401 for invalid token
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ PDF export correctly rejects invalid tokens")
            return True
        else:
            print("   ❌ PDF export should reject invalid tokens")
            return False

    def test_database_collection_verification(self):
        """Verify the return_forms collection exists and has data"""
        print("\n🗄️ STEP 9: DATABASE COLLECTION VERIFICATION")
        print("=" * 50)
        
        # Get all return forms to verify collection exists
        success, response = self.run_test(
            "Verify return_forms Collection",
            "GET",
            "returns",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ return_forms collection accessible")
            print(f"   📊 Total return forms: {len(response)}")
            
            if len(response) > 0:
                # Check structure of first form
                first_form = response[0]
                print(f"   📝 Sample form structure:")
                for key, value in first_form.items():
                    if key != 'notes':  # Skip long notes field
                        print(f"      {key}: {value}")
                
                # Verify our created forms are there
                our_forms = [f for f in response if f.get('id') in self.created_return_ids]
                print(f"   📝 Our test forms found: {len(our_forms)}")
                
                return True
            else:
                print("   ⚠️ Collection exists but is empty")
                return True
        else:
            print("   ❌ Cannot access return_forms collection")
            return False

    def test_authentication_flow_step_by_step(self):
        """Test the complete authentication flow step by step"""
        print("\n🔄 STEP 10: COMPLETE AUTHENTICATION FLOW TEST")
        print("=" * 50)
        
        # Step 1: Fresh login
        print("   🔐 Step 1: Fresh login...")
        login_success, login_response = self.run_test(
            "Fresh Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password}
        )
        
        if not login_success:
            print("   ❌ Fresh login failed")
            return False
        
        fresh_token = login_response.get('access_token')
        if not fresh_token:
            print("   ❌ No token in fresh login response")
            return False
        
        print(f"   ✅ Fresh token obtained: {fresh_token[:50]}...")
        
        # Step 2: Test token with simple endpoint
        print("   🔍 Step 2: Test token with simple endpoint...")
        original_token = self.token
        self.token = fresh_token
        
        simple_success, simple_response = self.run_test(
            "Test Fresh Token with Products",
            "GET",
            "products?limit=1",
            200
        )
        
        if not simple_success:
            print("   ❌ Fresh token doesn't work with simple endpoint")
            self.token = original_token
            return False
        
        print("   ✅ Fresh token works with simple endpoints")
        
        # Step 3: Create return form with fresh token
        print("   📝 Step 3: Create return form with fresh token...")
        fresh_return_id = self.create_test_return_form()
        
        if not fresh_return_id:
            print("   ❌ Cannot create return form with fresh token")
            self.token = original_token
            return False
        
        print(f"   ✅ Return form created with fresh token: {fresh_return_id}")
        
        # Step 4: Test PDF export with fresh token
        print("   📄 Step 4: Test PDF export with fresh token...")
        pdf_success = self.test_pdf_export_endpoint_detailed(fresh_return_id)
        
        # Restore original token
        self.token = original_token
        
        if pdf_success:
            print("   ✅ Complete authentication flow successful")
            return True
        else:
            print("   ❌ PDF export failed even with fresh authentication flow")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of PDF export authentication"""
        print("🚀 RETURN FORM PDF EXPORT AUTHENTICATION DEBUG")
        print("=" * 70)
        print("Focus: Debug 'Not authenticated' issue with PDF export endpoint")
        print("Authentication: Admin credentials (imadqejji/066380531I)")
        print("=" * 70)
        
        # Step 1: Admin Login
        if not self.test_admin_login():
            print("❌ Cannot proceed - admin login failed")
            return False
        
        # Step 2: Token Validation
        if not self.test_token_validation():
            print("❌ Cannot proceed - token validation failed")
            return False
        
        # Step 3: Get Current User Dependency
        if not self.test_get_current_user_dependency():
            print("❌ Cannot proceed - get_current_user dependency failed")
            return False
        
        # Step 4: Create Test Return Form
        return_id = self.create_test_return_form()
        if not return_id:
            print("❌ Cannot proceed - return form creation failed")
            return False
        
        # Step 5: Return Form Retrieval
        if not self.test_return_form_retrieval(return_id):
            print("❌ Cannot proceed - return form retrieval failed")
            return False
        
        # Step 6: PDF Export Endpoint (Main Test)
        pdf_success = self.test_pdf_export_endpoint_detailed(return_id)
        
        # Step 7: PDF Export Without Auth (Verification)
        self.test_pdf_export_without_auth(return_id)
        
        # Step 8: PDF Export With Invalid Token (Verification)
        self.test_pdf_export_with_invalid_token(return_id)
        
        # Step 9: Database Collection Verification
        self.test_database_collection_verification()
        
        # Step 10: Complete Authentication Flow Test
        self.test_authentication_flow_step_by_step()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 PDF EXPORT AUTHENTICATION DEBUG RESULTS")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n🔍 CRITICAL FINDINGS:")
        print("-" * 30)
        
        if pdf_success:
            print("✅ PDF EXPORT IS WORKING CORRECTLY")
            print("   - Authentication is functioning properly")
            print("   - Bearer token is being accepted")
            print("   - Return forms are accessible")
            print("   - PDF generation is successful")
        else:
            print("❌ PDF EXPORT AUTHENTICATION ISSUE CONFIRMED")
            print("   - Check the specific error messages above")
            print("   - Verify the endpoint URL is correct")
            print("   - Check if the authentication middleware is properly configured")
            print("   - Verify the get_current_user dependency is working")
        
        print(f"\n📝 Created Return Form IDs for testing: {self.created_return_ids}")
        
        # Detailed failure analysis
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            print("-" * 30)
            for test in failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        return pdf_success

if __name__ == "__main__":
    tester = ReturnFormPDFDebugTester()
    success = tester.run_comprehensive_debug()
    
    if success:
        print("\n🎉 PDF EXPORT AUTHENTICATION IS WORKING!")
        sys.exit(0)
    else:
        print("\n🚨 PDF EXPORT AUTHENTICATION ISSUE CONFIRMED!")
        sys.exit(1)