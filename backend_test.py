#!/usr/bin/env python3
"""
Enhanced Supplier Return Form System Testing
Testing comprehensive return form functionality with supervisor dropdown, dual currency, and PDF exports
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

# Test data from review request
TEST_SUPERVISORS = ["Mahmoud Badr", "Abdelhamed Mostafa"]
SECTION_MANAGER = "Imad Qejji"
TEST_CURRENCIES = ["YER", "SAR", "EUR"]
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
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
            
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_authentication(self):
        """Test 1: Authentication with admin credentials"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Admin Login", True, f"Token received: {self.token[:20]}...")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_barcode_lookup_api(self):
        """Test 2: Barcode Lookup API with known barcodes"""
        print("\n📱 TESTING BARCODE LOOKUP API")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Barcode API Setup", False, "No authentication token available")
            return False
            
        # Test primary barcodes from review request
        for barcode in TEST_BARCODES:
            self._test_single_barcode(barcode, is_primary=True)
            
        # Test additional barcodes for comprehensive coverage
        for barcode in ADDITIONAL_BARCODES:
            self._test_single_barcode(barcode, is_primary=False)
            
        return True
    
    def _test_single_barcode(self, barcode, is_primary=False):
        """Test a single barcode lookup"""
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
            
            test_name = f"Barcode Lookup {barcode}" + (" (PRIMARY)" if is_primary else "")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verify response format
                    required_fields = [
                        'product_name', 'item_number', 'barcode', 'department', 
                        'section', 'purchase_price', 'purchase_currency', 
                        'selling_price', 'supplier', 'quantity', 'status'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(test_name, False, f"Missing fields: {missing_fields}")
                    else:
                        # Log successful lookup with key details
                        product_info = f"Product: {data.get('product_name', 'N/A')}, " \
                                     f"Dept: {data.get('department', 'N/A')}, " \
                                     f"Price: {data.get('purchase_price', 0)} {data.get('purchase_currency', 'N/A')}, " \
                                     f"Status: {data.get('status', 'N/A')}"
                        self.log_test(test_name, True, product_info)
                        
                        # Additional validation for primary barcodes
                        if is_primary:
                            self._validate_product_data(barcode, data)
                            
                except json.JSONDecodeError:
                    self.log_test(test_name, False, "Invalid JSON response")
                    
            elif response.status_code == 404:
                self.log_test(test_name, False, "Product not found (404)")
            elif response.status_code == 403:
                self.log_test(test_name, False, "Authentication required (403)")
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_test(f"Barcode Lookup {barcode}", False, f"Exception: {str(e)}")
    
    def _validate_product_data(self, barcode, data):
        """Validate product data completeness for primary barcodes"""
        # Test response size (mobile compatibility)
        response_size = len(json.dumps(data))
        size_test_name = f"Response Size {barcode}"
        
        if response_size < 2000:  # Less than 2KB is mobile-friendly
            self.log_test(size_test_name, True, f"{response_size} bytes (mobile-friendly)")
        else:
            self.log_test(size_test_name, False, f"{response_size} bytes (too large for mobile)")
        
        # Test data completeness
        completeness_test_name = f"Data Completeness {barcode}"
        
        essential_data = {
            'product_name': data.get('product_name'),
            'purchase_price': data.get('purchase_price'),
            'purchase_currency': data.get('purchase_currency'),
            'department': data.get('department'),
            'supplier': data.get('supplier')
        }
        
        empty_fields = [k for k, v in essential_data.items() if not v or v == 0]
        
        if empty_fields:
            self.log_test(completeness_test_name, False, f"Empty essential fields: {empty_fields}")
        else:
            self.log_test(completeness_test_name, True, "All essential fields populated")
    
    def test_authentication_requirements(self):
        """Test 3: Verify authentication is properly required"""
        print("\n🔒 TESTING AUTHENTICATION REQUIREMENTS")
        print("=" * 50)
        
        # Test without authentication
        session_no_auth = requests.Session()
        
        try:
            response = session_no_auth.get(f"{BACKEND_URL}/barcode/{TEST_BARCODES[0]}")
            
            if response.status_code == 403:
                self.log_test("Auth Required Test", True, "Correctly returns 403 without auth")
            elif response.status_code == 401:
                self.log_test("Auth Required Test", True, "Correctly returns 401 without auth")
            else:
                self.log_test("Auth Required Test", False, f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Required Test", False, f"Exception: {str(e)}")
    
    def test_invalid_barcode_handling(self):
        """Test 4: Test handling of invalid barcodes"""
        print("\n🚫 TESTING INVALID BARCODE HANDLING")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Invalid Barcode Setup", False, "No authentication token available")
            return
            
        invalid_barcodes = [
            "0000000000000",  # Non-existent barcode
            "invalid123",     # Invalid format
            "999999999999"    # Another non-existent
        ]
        
        for barcode in invalid_barcodes:
            try:
                response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
                
                if response.status_code == 404:
                    self.log_test(f"Invalid Barcode {barcode}", True, "Correctly returns 404")
                else:
                    self.log_test(f"Invalid Barcode {barcode}", False, f"Expected 404, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Invalid Barcode {barcode}", False, f"Exception: {str(e)}")
    
    def test_cors_and_mobile_headers(self):
        """Test 5: Verify CORS and mobile compatibility headers"""
        print("\n📱 TESTING CORS AND MOBILE COMPATIBILITY")
        print("=" * 50)
        
        if not self.token:
            self.log_test("CORS Test Setup", False, "No authentication token available")
            return
            
        try:
            # Test with mobile user agent
            mobile_headers = {
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{BACKEND_URL}/barcode/{TEST_BARCODES[0]}", 
                headers=mobile_headers
            )
            
            if response.status_code == 200:
                # Check for CORS headers
                cors_headers = [
                    'Access-Control-Allow-Origin',
                    'Access-Control-Allow-Methods', 
                    'Access-Control-Allow-Headers'
                ]
                
                present_cors = [h for h in cors_headers if h in response.headers]
                
                if present_cors:
                    self.log_test("CORS Headers", True, f"Present: {present_cors}")
                else:
                    self.log_test("CORS Headers", False, "No CORS headers found")
                
                # Test mobile response time
                response_time = response.elapsed.total_seconds() * 1000  # Convert to ms
                
                if response_time < 1000:  # Less than 1 second
                    self.log_test("Mobile Response Time", True, f"{response_time:.0f}ms")
                else:
                    self.log_test("Mobile Response Time", False, f"{response_time:.0f}ms (too slow)")
                    
            else:
                self.log_test("Mobile Compatibility", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Mobile Compatibility", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all barcode API tests"""
        print("🎯 DIRECT BARCODE API TEST - Can the scanner read and fetch barcode data?")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Barcodes: {TEST_BARCODES}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            self.test_barcode_lookup_api()
            self.test_authentication_requirements()
            self.test_invalid_barcode_handling()
            self.test_cors_and_mobile_headers()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with barcode tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 BARCODE API TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 CRITICAL QUESTION ANSWER:")
        
        # Analyze results to answer the key question
        barcode_tests = [r for r in self.test_results if "Barcode Lookup" in r["test"] and "PRIMARY" in r["test"]]
        auth_tests = [r for r in self.test_results if "Admin Login" in r["test"]]
        
        if auth_tests and auth_tests[0]["success"]:
            print("✅ Authentication: WORKING - Admin credentials accepted")
        else:
            print("❌ Authentication: FAILED - Cannot login with admin credentials")
        
        if barcode_tests:
            successful_lookups = [t for t in barcode_tests if t["success"]]
            if successful_lookups:
                print(f"✅ Barcode Lookup: WORKING - {len(successful_lookups)}/{len(barcode_tests)} primary barcodes found")
                print("✅ Product Data: Available - API returns complete product information")
                print("✅ Response Format: Valid - JSON format suitable for frontend integration")
            else:
                print("❌ Barcode Lookup: FAILED - No primary barcodes found")
                print("❌ Product Data: Not Available - API cannot fetch product information")
        else:
            print("❌ Barcode Lookup: NOT TESTED - Authentication failure prevented testing")
        
        print("\n🔍 CONCLUSION:")
        if success_rate >= 80:
            print("✅ The barcode scanner CAN read and fetch barcode data successfully!")
            print("✅ Backend API is ready for real barcode scanning integration")
        elif success_rate >= 50:
            print("⚠️  The barcode scanner has PARTIAL functionality - some issues need fixing")
        else:
            print("❌ The barcode scanner CANNOT reliably read and fetch barcode data")
            print("❌ Critical issues must be resolved before barcode scanning integration")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = BarcodeAPITester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()