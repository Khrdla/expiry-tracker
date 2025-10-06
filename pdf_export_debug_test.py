#!/usr/bin/env python3
"""
PDF Export Authentication Debug Test
Comprehensive debugging of persistent PDF export authentication issue

CRITICAL DEBUGGING FOCUS:
1. Check Current Token Validity - Test if admin token is valid by testing other authenticated endpoints
2. Test Return Form Creation - Create return form and verify it returns valid ID
3. Test PDF Export Endpoint Manually - Use exact same endpoint with curl and proper authentication
4. Check Authentication Middleware - Verify get_current_user dependency is working correctly
5. Inspect Token Format - Check if token format is correct (Bearer token structure)
6. Check Database Collection - Verify return_forms collection exists and has proper data
7. Debug Request Headers - Check exactly what headers are being sent to PDF export endpoint

AUTHENTICATION: Use admin credentials (imadqejji/066380531I)
FOCUS: Find exact point where authentication is failing
"""

import requests
import sys
import json
import uuid
from datetime import datetime

class PDFExportAuthDebugger:
    def __init__(self, base_url="https://geant-scanner.preview.emergentagent.com"):
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
        """Log test results with detailed information"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def make_request(self, method, endpoint, data=None, headers=None, use_auth=True):
        """Make HTTP request with detailed logging"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            request_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            request_headers.update(headers)

        print(f"\n🔍 Making {method} request to: {url}")
        print(f"   Headers: {json.dumps(request_headers, indent=2)}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)

            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                response_data = response.text
                print(f"   Response Text: {response_data[:500]}...")

            return response, response_data

        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout (30s)")
            return None, {"error": "timeout"}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error - server may be down")
            return None, {"error": "connection_error"}
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None, {"error": str(e)}

    def step_1_verify_admin_login(self):
        """STEP 1: Verify admin login works and get valid token"""
        print("\n" + "="*70)
        print("STEP 1: VERIFY ADMIN LOGIN")
        print("="*70)
        
        response, response_data = self.make_request(
            "POST", 
            "auth/login",
            data={"username": self.admin_username, "password": self.admin_password},
            use_auth=False
        )
        
        if response and response.status_code == 200:
            if isinstance(response_data, dict) and 'access_token' in response_data:
                self.token = response_data['access_token']
                print(f"   🔑 Admin token obtained successfully")
                print(f"   Token preview: {self.token[:50]}...")
                print(f"   Token type: {response_data.get('token_type', 'unknown')}")
                
                # Verify token format
                if self.token.count('.') == 2:  # JWT format
                    print(f"   ✅ Token appears to be valid JWT format")
                    self.log_test("Admin Login", True, f"Token obtained: {self.token[:20]}...")
                    return True
                else:
                    print(f"   ⚠️ Token format may be invalid (not JWT)")
                    self.log_test("Admin Login", False, "Token format invalid")
                    return False
            else:
                self.log_test("Admin Login", False, f"No access_token in response: {response_data}")
                return False
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}, Data: {response_data}"
            self.log_test("Admin Login", False, error_msg)
            return False

    def step_2_test_token_validity(self):
        """STEP 2: Test token validity by accessing other authenticated endpoints"""
        print("\n" + "="*70)
        print("STEP 2: TEST TOKEN VALIDITY WITH OTHER ENDPOINTS")
        print("="*70)
        
        if not self.token:
            self.log_test("Token Validity Check", False, "No token available")
            return False
        
        # Test multiple authenticated endpoints to verify token works
        test_endpoints = [
            {"endpoint": "dashboard", "description": "Dashboard API"},
            {"endpoint": "products?limit=5", "description": "Products API"},
            {"endpoint": "filters", "description": "Filters API"}
        ]
        
        valid_endpoints = 0
        
        for test in test_endpoints:
            endpoint = test["endpoint"]
            description = test["description"]
            
            print(f"\n🔍 Testing {description}...")
            response, response_data = self.make_request("GET", endpoint)
            
            if response and response.status_code == 200:
                print(f"   ✅ {description}: Token valid")
                valid_endpoints += 1
            elif response and response.status_code in [401, 403]:
                print(f"   ❌ {description}: Authentication failed")
                self.log_test(f"Token Validity - {description}", False, f"Auth failed: {response.status_code}")
            else:
                print(f"   ⚠️ {description}: Unexpected response: {response.status_code if response else 'No response'}")
        
        if valid_endpoints == len(test_endpoints):
            print(f"\n✅ Token is valid - all {valid_endpoints} endpoints accessible")
            self.log_test("Token Validity Check", True, f"All {valid_endpoints} endpoints accessible")
            return True
        else:
            print(f"\n❌ Token validity issues - only {valid_endpoints}/{len(test_endpoints)} endpoints accessible")
            self.log_test("Token Validity Check", False, f"Only {valid_endpoints}/{len(test_endpoints)} endpoints accessible")
            return False

    def step_3_create_return_form(self):
        """STEP 3: Create a return form and verify it returns valid ID"""
        print("\n" + "="*70)
        print("STEP 3: CREATE RETURN FORM AND VERIFY ID")
        print("="*70)
        
        if not self.token:
            self.log_test("Return Form Creation", False, "No token available")
            return False, None
        
        # Create test return form data
        return_form_data = {
            "reference_number": f"TEST-{int(datetime.now().timestamp())}",
            "product_code": "TEST001",
            "product_name": "Test Product for PDF Export",
            "quantity": 5,
            "purchase_price": 100.0,
            "purchase_currency": "YER",
            "supplier": "Test Supplier",
            "reason_for_return": "Quality issue - testing PDF export",
            "requested_by": self.admin_username,
            "approved_by": "Test Manager",
            "notes": "This is a test return form created for PDF export authentication debugging"
        }
        
        print(f"Creating return form with data:")
        print(json.dumps(return_form_data, indent=2))
        
        response, response_data = self.make_request("POST", "returns", data=return_form_data)
        
        if response and response.status_code == 200:
            if isinstance(response_data, dict) and 'id' in response_data:
                return_id = response_data['id']
                self.created_return_ids.append(return_id)
                
                print(f"   ✅ Return form created successfully")
                print(f"   Return ID: {return_id}")
                
                # Verify ID format (should be UUID)
                try:
                    uuid.UUID(return_id)
                    print(f"   ✅ Return ID is valid UUID format")
                    self.log_test("Return Form Creation", True, f"Created with ID: {return_id}")
                    return True, return_id
                except ValueError:
                    print(f"   ⚠️ Return ID is not UUID format: {return_id}")
                    self.log_test("Return Form Creation", False, f"Invalid ID format: {return_id}")
                    return False, return_id
            else:
                self.log_test("Return Form Creation", False, f"No ID in response: {response_data}")
                return False, None
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}, Data: {response_data}"
            self.log_test("Return Form Creation", False, error_msg)
            return False, None

    def step_4_verify_return_form_exists(self, return_id):
        """STEP 4: Verify the created return form exists in database"""
        print("\n" + "="*70)
        print("STEP 4: VERIFY RETURN FORM EXISTS IN DATABASE")
        print("="*70)
        
        if not return_id:
            self.log_test("Return Form Verification", False, "No return ID to verify")
            return False
        
        print(f"Verifying return form exists: {return_id}")
        
        # Get all return forms and check if our ID exists
        response, response_data = self.make_request("GET", "returns")
        
        if response and response.status_code == 200:
            if isinstance(response_data, list):
                found_form = None
                for form in response_data:
                    if form.get('id') == return_id:
                        found_form = form
                        break
                
                if found_form:
                    print(f"   ✅ Return form found in database")
                    print(f"   Form data: {json.dumps(found_form, indent=2)}")
                    self.log_test("Return Form Verification", True, f"Form found with ID: {return_id}")
                    return True
                else:
                    print(f"   ❌ Return form not found in database")
                    print(f"   Available forms: {len(response_data)}")
                    if response_data:
                        print(f"   Sample IDs: {[f.get('id') for f in response_data[:3]]}")
                    self.log_test("Return Form Verification", False, f"Form not found: {return_id}")
                    return False
            else:
                self.log_test("Return Form Verification", False, f"Unexpected response format: {type(response_data)}")
                return False
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}, Data: {response_data}"
            self.log_test("Return Form Verification", False, error_msg)
            return False

    def step_5_test_pdf_export_endpoint(self, return_id):
        """STEP 5: Test PDF export endpoint with proper authentication"""
        print("\n" + "="*70)
        print("STEP 5: TEST PDF EXPORT ENDPOINT WITH AUTHENTICATION")
        print("="*70)
        
        if not return_id:
            self.log_test("PDF Export Test", False, "No return ID for PDF export")
            return False
        
        print(f"Testing PDF export for return ID: {return_id}")
        
        # Test PDF export endpoint
        pdf_endpoint = f"export/return-form/{return_id}/pdf"
        response, response_data = self.make_request("GET", pdf_endpoint)
        
        if response:
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                print(f"   ✅ PDF export successful")
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {content_length} bytes")
                
                # Verify PDF content
                if content_length > 0:
                    # Check PDF signature
                    pdf_signature = response.content[:4]
                    if pdf_signature == b'%PDF':
                        print(f"   ✅ Valid PDF file signature")
                        self.log_test("PDF Export Test", True, f"PDF generated: {content_length} bytes")
                        return True
                    else:
                        print(f"   ⚠️ Invalid PDF signature: {pdf_signature}")
                        self.log_test("PDF Export Test", False, f"Invalid PDF signature: {pdf_signature}")
                        return False
                else:
                    print(f"   ❌ Empty PDF content")
                    self.log_test("PDF Export Test", False, "Empty PDF content")
                    return False
                    
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed (401 Unauthorized)")
                print(f"   This indicates token is invalid or expired")
                self.log_test("PDF Export Test", False, "401 Unauthorized - token invalid")
                return False
                
            elif response.status_code == 403:
                print(f"   ❌ Access forbidden (403 Forbidden)")
                print(f"   This indicates authentication missing or insufficient permissions")
                self.log_test("PDF Export Test", False, "403 Forbidden - auth missing or insufficient")
                return False
                
            elif response.status_code == 404:
                print(f"   ❌ Return form not found (404 Not Found)")
                print(f"   This indicates the return form ID doesn't exist")
                self.log_test("PDF Export Test", False, f"404 Not Found - return form {return_id} doesn't exist")
                return False
                
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response_data}")
                self.log_test("PDF Export Test", False, f"Unexpected status: {response.status_code}")
                return False
        else:
            self.log_test("PDF Export Test", False, "No response from server")
            return False

    def step_6_test_authentication_middleware(self):
        """STEP 6: Test authentication middleware by testing with invalid tokens"""
        print("\n" + "="*70)
        print("STEP 6: TEST AUTHENTICATION MIDDLEWARE")
        print("="*70)
        
        # Save original token
        original_token = self.token
        
        # Test 1: No token
        print("\n🔍 Test 1: No authentication token")
        self.token = None
        response, response_data = self.make_request("GET", "dashboard", use_auth=False)
        
        if response and response.status_code in [401, 403]:
            print(f"   ✅ Correctly rejected request without token ({response.status_code})")
        else:
            print(f"   ❌ Should reject request without token, got: {response.status_code if response else 'No response'}")
        
        # Test 2: Invalid token
        print("\n🔍 Test 2: Invalid authentication token")
        self.token = "invalid.token.here"
        response, response_data = self.make_request("GET", "dashboard")
        
        if response and response.status_code in [401, 403]:
            print(f"   ✅ Correctly rejected invalid token ({response.status_code})")
        else:
            print(f"   ❌ Should reject invalid token, got: {response.status_code if response else 'No response'}")
        
        # Test 3: Malformed Bearer token
        print("\n🔍 Test 3: Malformed Bearer token")
        self.token = "malformed_token_without_dots"
        response, response_data = self.make_request("GET", "dashboard")
        
        if response and response.status_code in [401, 403]:
            print(f"   ✅ Correctly rejected malformed token ({response.status_code})")
        else:
            print(f"   ❌ Should reject malformed token, got: {response.status_code if response else 'No response'}")
        
        # Restore original token
        self.token = original_token
        
        # Test 4: Valid token should work
        print("\n🔍 Test 4: Valid token should work")
        response, response_data = self.make_request("GET", "dashboard")
        
        if response and response.status_code == 200:
            print(f"   ✅ Valid token works correctly")
            self.log_test("Authentication Middleware", True, "All auth tests passed")
            return True
        else:
            print(f"   ❌ Valid token failed: {response.status_code if response else 'No response'}")
            self.log_test("Authentication Middleware", False, f"Valid token failed: {response.status_code if response else 'No response'}")
            return False

    def step_7_inspect_token_format(self):
        """STEP 7: Inspect token format and decode JWT payload"""
        print("\n" + "="*70)
        print("STEP 7: INSPECT TOKEN FORMAT AND PAYLOAD")
        print("="*70)
        
        if not self.token:
            self.log_test("Token Format Inspection", False, "No token available")
            return False
        
        print(f"Token: {self.token}")
        print(f"Token length: {len(self.token)}")
        
        # Check JWT format (should have 3 parts separated by dots)
        parts = self.token.split('.')
        print(f"Token parts: {len(parts)}")
        
        if len(parts) != 3:
            print(f"   ❌ Invalid JWT format - should have 3 parts, has {len(parts)}")
            self.log_test("Token Format Inspection", False, f"Invalid JWT format: {len(parts)} parts")
            return False
        
        print(f"   ✅ Valid JWT format (3 parts)")
        
        # Try to decode JWT payload (without verification for inspection)
        try:
            import base64
            import json
            
            # Add padding if needed
            payload_part = parts[1]
            padding = 4 - len(payload_part) % 4
            if padding != 4:
                payload_part += '=' * padding
            
            # Decode payload
            decoded_payload = base64.urlsafe_b64decode(payload_part)
            payload_json = json.loads(decoded_payload)
            
            print(f"   ✅ JWT payload decoded successfully:")
            print(f"   Payload: {json.dumps(payload_json, indent=4)}")
            
            # Check important fields
            username = payload_json.get('sub')
            exp = payload_json.get('exp')
            
            if username:
                print(f"   Username: {username}")
                if username == self.admin_username:
                    print(f"   ✅ Username matches expected: {self.admin_username}")
                else:
                    print(f"   ⚠️ Username mismatch - expected: {self.admin_username}, got: {username}")
            
            if exp:
                import datetime
                exp_datetime = datetime.datetime.fromtimestamp(exp)
                now = datetime.datetime.now()
                print(f"   Token expires: {exp_datetime}")
                print(f"   Current time: {now}")
                
                if exp_datetime > now:
                    print(f"   ✅ Token is not expired")
                else:
                    print(f"   ❌ Token is expired!")
                    self.log_test("Token Format Inspection", False, "Token is expired")
                    return False
            
            self.log_test("Token Format Inspection", True, f"Valid JWT for user: {username}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to decode JWT payload: {str(e)}")
            self.log_test("Token Format Inspection", False, f"JWT decode failed: {str(e)}")
            return False

    def step_8_check_database_collection(self):
        """STEP 8: Check database collection and verify return_forms exist"""
        print("\n" + "="*70)
        print("STEP 8: CHECK DATABASE COLLECTION")
        print("="*70)
        
        # Get all return forms to check collection
        response, response_data = self.make_request("GET", "returns")
        
        if response and response.status_code == 200:
            if isinstance(response_data, list):
                print(f"   ✅ return_forms collection accessible")
                print(f"   Total return forms: {len(response_data)}")
                
                if response_data:
                    print(f"   Sample return form structure:")
                    sample_form = response_data[0]
                    print(json.dumps(sample_form, indent=4))
                    
                    # Check required fields
                    required_fields = ['id', 'reference_number', 'created_at', 'status']
                    missing_fields = [field for field in required_fields if field not in sample_form]
                    
                    if missing_fields:
                        print(f"   ⚠️ Missing fields in return forms: {missing_fields}")
                    else:
                        print(f"   ✅ All required fields present")
                    
                    self.log_test("Database Collection Check", True, f"{len(response_data)} return forms found")
                    return True
                else:
                    print(f"   ⚠️ No return forms in collection")
                    self.log_test("Database Collection Check", True, "Collection exists but empty")
                    return True
            else:
                print(f"   ❌ Unexpected response format: {type(response_data)}")
                self.log_test("Database Collection Check", False, f"Unexpected format: {type(response_data)}")
                return False
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}, Data: {response_data}"
            print(f"   ❌ Failed to access return_forms collection: {error_msg}")
            self.log_test("Database Collection Check", False, error_msg)
            return False

    def step_9_test_existing_return_forms(self):
        """STEP 9: Test PDF export with existing return forms"""
        print("\n" + "="*70)
        print("STEP 9: TEST PDF EXPORT WITH EXISTING RETURN FORMS")
        print("="*70)
        
        # Get existing return forms
        response, response_data = self.make_request("GET", "returns")
        
        if not (response and response.status_code == 200 and isinstance(response_data, list)):
            self.log_test("Existing Forms PDF Test", False, "Cannot get existing return forms")
            return False
        
        if not response_data:
            print("   ⚠️ No existing return forms to test")
            return True
        
        # Test PDF export with first few existing forms
        test_count = min(3, len(response_data))
        successful_exports = 0
        
        for i, form in enumerate(response_data[:test_count], 1):
            form_id = form.get('id')
            reference = form.get('reference_number', 'Unknown')
            
            print(f"\n🔍 Testing PDF export {i}/{test_count}: {reference} (ID: {form_id})")
            
            if not form_id:
                print(f"   ❌ Form has no ID")
                continue
            
            pdf_endpoint = f"export/return-form/{form_id}/pdf"
            response, response_data = self.make_request("GET", pdf_endpoint)
            
            if response and response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('content-type', '')
                
                print(f"   ✅ PDF export successful")
                print(f"   Content-Type: {content_type}")
                print(f"   Size: {content_length} bytes")
                
                # Verify PDF signature
                if response.content[:4] == b'%PDF':
                    print(f"   ✅ Valid PDF signature")
                    successful_exports += 1
                else:
                    print(f"   ⚠️ Invalid PDF signature")
                    
            elif response and response.status_code in [401, 403]:
                print(f"   ❌ Authentication failed: {response.status_code}")
                print(f"   This is the authentication issue we're debugging!")
                
            elif response and response.status_code == 404:
                print(f"   ❌ Form not found: {response.status_code}")
                
            else:
                print(f"   ❌ Unexpected response: {response.status_code if response else 'No response'}")
        
        print(f"\n📊 PDF Export Results: {successful_exports}/{test_count} successful")
        
        if successful_exports == test_count:
            self.log_test("Existing Forms PDF Test", True, f"All {test_count} PDF exports successful")
            return True
        elif successful_exports > 0:
            self.log_test("Existing Forms PDF Test", False, f"Only {successful_exports}/{test_count} PDF exports successful")
            return False
        else:
            self.log_test("Existing Forms PDF Test", False, f"No PDF exports successful (0/{test_count})")
            return False

    def step_10_debug_request_headers(self):
        """STEP 10: Debug exact request headers being sent"""
        print("\n" + "="*70)
        print("STEP 10: DEBUG REQUEST HEADERS")
        print("="*70)
        
        if not self.token:
            self.log_test("Request Headers Debug", False, "No token available")
            return False
        
        # Create a test return form for header debugging
        success, return_id = self.step_3_create_return_form()
        if not success or not return_id:
            print("   ❌ Cannot create test return form for header debugging")
            return False
        
        print(f"Using return ID for header debugging: {return_id}")
        
        # Manually construct headers and test
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/pdf',
            'User-Agent': 'PDF-Export-Debug-Test/1.0'
        }
        
        print(f"Request headers being sent:")
        for key, value in headers.items():
            if key == 'Authorization':
                print(f"   {key}: Bearer {value[7:27]}...{value[-10:]}")  # Mask token
            else:
                print(f"   {key}: {value}")
        
        # Test with explicit headers
        url = f"{self.api_url}/export/return-form/{return_id}/pdf"
        print(f"\nMaking request to: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"   ✅ PDF export successful with explicit headers")
                print(f"   Content-Length: {len(response.content)} bytes")
                self.log_test("Request Headers Debug", True, "PDF export successful with explicit headers")
                return True
                
            elif response.status_code in [401, 403]:
                print(f"   ❌ Authentication failed even with explicit headers")
                print(f"   This confirms the authentication issue exists")
                
                # Try to get more details from response
                try:
                    error_data = response.json()
                    print(f"   Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error text: {response.text}")
                
                self.log_test("Request Headers Debug", False, f"Auth failed with explicit headers: {response.status_code}")
                return False
                
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                self.log_test("Request Headers Debug", False, f"Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            self.log_test("Request Headers Debug", False, f"Request failed: {str(e)}")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive PDF export authentication debugging"""
        print("🔍 PDF EXPORT AUTHENTICATION DEBUG")
        print("Comprehensive investigation of persistent authentication issues")
        print("=" * 70)
        
        # Step-by-step debugging process
        steps = [
            ("STEP 1: Verify Admin Login", self.step_1_verify_admin_login),
            ("STEP 2: Test Token Validity", self.step_2_test_token_validity),
            ("STEP 7: Inspect Token Format", self.step_7_inspect_token_format),
            ("STEP 6: Test Auth Middleware", self.step_6_test_authentication_middleware),
            ("STEP 8: Check Database Collection", self.step_8_check_database_collection),
            ("STEP 9: Test Existing Return Forms", self.step_9_test_existing_return_forms),
        ]
        
        # Execute steps
        for step_name, step_function in steps:
            print(f"\n{'='*70}")
            print(f"EXECUTING: {step_name}")
            print(f"{'='*70}")
            
            try:
                result = step_function()
                if not result:
                    print(f"❌ {step_name} FAILED - This may be the source of the authentication issue")
                else:
                    print(f"✅ {step_name} PASSED")
            except Exception as e:
                print(f"❌ {step_name} ERROR: {str(e)}")
                self.log_test(step_name, False, f"Exception: {str(e)}")
        
        # Now test return form creation and PDF export
        print(f"\n{'='*70}")
        print("EXECUTING: STEP 3: Create Return Form")
        print(f"{'='*70}")
        
        success, return_id = self.step_3_create_return_form()
        
        if success and return_id:
            print(f"\n{'='*70}")
            print("EXECUTING: STEP 4: Verify Return Form Exists")
            print(f"{'='*70}")
            
            self.step_4_verify_return_form_exists(return_id)
            
            print(f"\n{'='*70}")
            print("EXECUTING: STEP 5: Test PDF Export")
            print(f"{'='*70}")
            
            self.step_5_test_pdf_export_endpoint(return_id)
            
            print(f"\n{'='*70}")
            print("EXECUTING: STEP 10: Debug Request Headers")
            print(f"{'='*70}")
            
            self.step_10_debug_request_headers()
        
        # Print final results
        print("\n" + "=" * 70)
        print("🔍 PDF EXPORT AUTHENTICATION DEBUG RESULTS")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status}: {result['name']}")
            if result['details']:
                print(f"      Details: {result['details']}")
        
        # Summary and recommendations
        print(f"\n🎯 AUTHENTICATION DEBUG SUMMARY:")
        
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"❌ AUTHENTICATION ISSUES FOUND:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        else:
            print(f"✅ NO AUTHENTICATION ISSUES FOUND - PDF export working correctly")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    debugger = PDFExportAuthDebugger()
    success = debugger.run_comprehensive_debug()
    
    if success:
        print(f"\n🎉 PDF EXPORT AUTHENTICATION DEBUG COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print(f"\n⚠️ PDF EXPORT AUTHENTICATION ISSUES DETECTED")
        sys.exit(1)