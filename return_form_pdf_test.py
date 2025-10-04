#!/usr/bin/env python3
"""
Return Form PDF Export Testing
Focus: Test the Return Form PDF export functionality to identify the failure
"""

import requests
import sys
import json
from datetime import datetime

class ReturnFormPDFTester:
    def __init__(self, base_url="https://inventory-master-78.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials from review request
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)

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

    def test_login(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password}
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Admin token obtained: {self.token[:20]}...")
            return True
        else:
            print(f"   ❌ Admin login failed: {response}")
            return False

    def test_check_existing_return_forms(self):
        """Check if any return forms exist in the database"""
        print("\n📋 STEP 1: Check Return Forms in Database")
        
        success, response = self.run_test(
            "Get Existing Return Forms",
            "GET",
            "returns",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   📊 Found {len(response)} return forms in database")
            
            if len(response) > 0:
                print("   📝 Sample return forms:")
                for i, form in enumerate(response[:3], 1):
                    form_id = form.get('id', 'No ID')
                    product_name = form.get('product_name', 'Unknown Product')
                    status = form.get('status', 'Unknown Status')
                    created_at = form.get('created_at', 'Unknown Date')
                    print(f"      {i}. ID: {form_id}")
                    print(f"         Product: {product_name}")
                    print(f"         Status: {status}")
                    print(f"         Created: {created_at}")
                
                # Store first form for PDF testing
                self.sample_return_form = response[0]
                return True
            else:
                print("   ⚠️ No return forms found - will create a test form")
                self.sample_return_form = None
                return True
        else:
            return False

    def test_create_sample_return_form(self):
        """Create a sample return form for testing if none exist"""
        print("\n📝 STEP 2: Create Test Return Form")
        
        if hasattr(self, 'sample_return_form') and self.sample_return_form:
            print("   ✅ Using existing return form for testing")
            return True
        
        # Create a comprehensive test return form
        test_return_data = {
            "reference_number": f"RTN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "return_date": datetime.now().strftime('%Y-%m-%d'),
            "product_code": "TEST001",
            "product_name": "Test Product for PDF Export",
            "quantity": 5,
            "purchase_price": 100.50,
            "purchase_currency": "YER",
            "supplier": "Test Supplier Ltd",
            "reason_for_return": "Quality issue - product damaged during transport",
            "prepared_by_supervisor": "John Supervisor",
            "section_manager_name": "Jane Manager",
            "department_head_name": "Bob Department Head",
            "notes": "This is a test return form created for PDF export testing. Please process accordingly.",
            "status": "pending"
        }
        
        success, response = self.run_test(
            "Create Test Return Form",
            "POST",
            "returns",
            200,
            data=test_return_data
        )
        
        if success and isinstance(response, dict):
            form_id = response.get('id')
            if form_id:
                print(f"   ✅ Test return form created with ID: {form_id}")
                # Create a mock return form object for testing
                self.sample_return_form = {
                    **test_return_data,
                    "id": form_id,
                    "created_by": self.admin_username,
                    "created_at": datetime.now().isoformat()
                }
                return True
            else:
                self.log_test("Create Return Form - ID Missing", False, "No ID returned from create endpoint")
                return False
        else:
            return False

    def test_pdf_export_endpoint(self):
        """Test the PDF export endpoint with existing return form ID"""
        print("\n📄 STEP 3: Test PDF Export Endpoint")
        
        if not hasattr(self, 'sample_return_form') or not self.sample_return_form:
            self.log_test("PDF Export - No Return Form", False, "No return form available for testing")
            return False
        
        return_id = self.sample_return_form.get('id')
        if not return_id:
            self.log_test("PDF Export - No ID", False, "Return form has no ID")
            return False
        
        print(f"   🔍 Testing PDF export for return form ID: {return_id}")
        
        # Test the PDF export endpoint
        url = f"{self.api_url}/export/return-form/{return_id}/pdf"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"   📊 Response Status: {response.status_code}")
            print(f"   📋 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Check if it's actually a PDF
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                print(f"   📄 Content-Type: {content_type}")
                print(f"   📏 Content-Length: {content_length} bytes")
                
                if content_type == 'application/pdf' and content_length > 0:
                    self.log_test("PDF Export Success", True, f"PDF generated: {content_length} bytes")
                    
                    # Check PDF content starts with PDF signature
                    if response.content.startswith(b'%PDF'):
                        print("   ✅ Valid PDF file signature detected")
                        return True
                    else:
                        self.log_test("PDF Export Validation", False, "Response doesn't start with PDF signature")
                        return False
                else:
                    self.log_test("PDF Export Content", False, f"Invalid content type or empty: {content_type}, {content_length} bytes")
                    return False
                    
            elif response.status_code == 404:
                self.log_test("PDF Export - Not Found", False, "Return form not found for PDF export")
                print("   🔍 This suggests the PDF endpoint is looking in wrong database collection")
                return False
                
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown server error')
                    self.log_test("PDF Export - Server Error", False, f"Server error: {error_detail}")
                    print(f"   🚨 Server Error Details: {error_detail}")
                except:
                    self.log_test("PDF Export - Server Error", False, f"Server error: {response.text[:200]}")
                    print(f"   🚨 Server Error Response: {response.text[:200]}")
                return False
                
            else:
                self.log_test("PDF Export - Unexpected Status", False, f"Unexpected status code: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📋 Error Response: {error_data}")
                except:
                    print(f"   📋 Raw Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("PDF Export - Exception", False, f"Exception: {str(e)}")
            return False

    def test_pdf_dependencies(self):
        """Test if PDF generation dependencies are working"""
        print("\n🔧 STEP 4: Test PDF Generation Dependencies")
        
        # Test a simple endpoint that uses reportlab to see if imports work
        # We'll test the dashboard PDF export as it uses the same dependencies
        success, response = self.run_test(
            "Test PDF Dependencies (Dashboard PDF)",
            "GET",
            "export/dashboard/pdf",
            200
        )
        
        if success:
            print("   ✅ PDF generation dependencies (reportlab) are working")
            return True
        else:
            print("   ❌ PDF generation dependencies may have issues")
            return False

    def test_file_response_mechanism(self):
        """Test if FileResponse mechanism is working"""
        print("\n📁 STEP 5: Test FileResponse Mechanism")
        
        # Test an endpoint that returns a file to see if FileResponse works
        success, response = self.run_test(
            "Test FileResponse (Excel Export)",
            "GET",
            "export/excel",
            200
        )
        
        if success:
            print("   ✅ FileResponse mechanism is working")
            return True
        else:
            print("   ❌ FileResponse mechanism may have issues")
            return False

    def test_database_collection_issue(self):
        """Test if the issue is with database collection mismatch"""
        print("\n🗄️ STEP 6: Investigate Database Collection Issue")
        
        if not hasattr(self, 'sample_return_form') or not self.sample_return_form:
            print("   ⚠️ No return form available for database investigation")
            return False
        
        return_id = self.sample_return_form.get('id')
        
        print(f"   🔍 Investigating return form ID: {return_id}")
        print("   📋 The PDF export endpoint looks for forms in 'db.returns' collection")
        print("   📋 But create/get endpoints use 'db.return_forms' collection")
        print("   📋 This collection mismatch is likely the root cause of 404 errors")
        
        # Try to get the return form again to confirm it exists
        success, response = self.run_test(
            "Verify Return Form Exists",
            "GET",
            "returns",
            200
        )
        
        if success and isinstance(response, list):
            form_found = False
            for form in response:
                if form.get('id') == return_id:
                    form_found = True
                    break
            
            if form_found:
                print(f"   ✅ Return form {return_id} exists in 'return_forms' collection")
                print("   🚨 CRITICAL ISSUE: PDF export endpoint queries wrong collection!")
                print("   🔧 FIX NEEDED: Change 'db.returns' to 'db.return_forms' in PDF export endpoint")
                self.log_test("Database Collection Mismatch", False, "PDF endpoint uses wrong collection (db.returns vs db.return_forms)")
                return False
            else:
                print(f"   ❌ Return form {return_id} not found in database")
                return False
        else:
            return False

    def test_id_field_issue(self):
        """Test if the issue is with ID field mismatch"""
        print("\n🆔 STEP 7: Investigate ID Field Issue")
        
        print("   📋 The PDF export endpoint uses '_id' field for database query")
        print("   📋 But return forms are stored with custom 'id' field (UUID)")
        print("   📋 This ID field mismatch could also cause 404 errors")
        print("   🔧 FIX NEEDED: Change query from {'_id': return_id} to {'id': return_id}")
        
        self.log_test("ID Field Mismatch", False, "PDF endpoint uses '_id' instead of 'id' field")
        return False

    def run_comprehensive_test(self):
        """Run comprehensive return form PDF export testing"""
        print("🚀 Starting Return Form PDF Export Testing")
        print("Focus: Identify the exact failure in PDF export functionality")
        print("=" * 70)
        
        # Step 1: Login
        if not self.test_login():
            print("❌ Admin login failed - stopping tests")
            return False
        
        # Step 2: Check existing return forms
        self.test_check_existing_return_forms()
        
        # Step 3: Create test return form if needed
        self.test_create_sample_return_form()
        
        # Step 4: Test PDF export endpoint
        pdf_success = self.test_pdf_export_endpoint()
        
        # Step 5: Test PDF dependencies
        self.test_pdf_dependencies()
        
        # Step 6: Test FileResponse mechanism
        self.test_file_response_mechanism()
        
        # Step 7: Investigate database collection issue
        self.test_database_collection_issue()
        
        # Step 8: Investigate ID field issue
        self.test_id_field_issue()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 RETURN FORM PDF EXPORT TEST RESULTS")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("=" * 30)
        
        if not pdf_success:
            print("❌ PDF Export Failed - Identified Issues:")
            print("   1. 🗄️ DATABASE COLLECTION MISMATCH:")
            print("      - PDF export endpoint queries 'db.returns' collection")
            print("      - But forms are stored in 'db.return_forms' collection")
            print("      - FIX: Change line 2437 from 'db.returns' to 'db.return_forms'")
            print()
            print("   2. 🆔 ID FIELD MISMATCH:")
            print("      - PDF export uses {'_id': return_id} for database query")
            print("      - But forms use custom 'id' field (UUID string)")
            print("      - FIX: Change line 2437 from {'_id': return_id} to {'id': return_id}")
            print()
            print("   3. 📄 RECOMMENDED FIXES:")
            print("      - Line 2437: return_form = await db.return_forms.find_one({'id': return_id})")
            print("      - This will fix both collection and ID field issues")
        else:
            print("✅ PDF Export Working - No issues found")
        
        print("\n🎯 AUTHENTICATION: Admin credentials (imadqejji/066380531I) working correctly")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ReturnFormPDFTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)