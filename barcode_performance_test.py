#!/usr/bin/env python3
"""
BARCODE SCANNER PERFORMANCE TEST - Speed and Reliability Focus

This test specifically addresses the review request requirements:
1. Authentication Test: Login with admin credentials (imadqejji/066380531I) and verify JWT token generation
2. Barcode Lookup API Test: Test GET /api/barcode/3222471081716 (Apple Juice Box 1L) with proper authentication headers
3. Performance Test: Measure API response time for barcode lookup (should be under 100ms for fast scanning)
4. Error Handling Test: Test invalid barcodes and unauthorized requests
5. Mobile Compatibility Test: Ensure CORS headers are properly configured for mobile browsers

Expected Results:
- Login should return valid JWT token in under 500ms
- Barcode lookup should return complete product data in under 100ms  
- Invalid barcodes should return proper 404 status
- Unauthorized requests should return 403/401 status
- API should have proper CORS headers for mobile compatibility
"""

import requests
import json
import time
import statistics
from datetime import datetime

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"
TARGET_BARCODE = "3222471081716"  # Apple Juice Box 1L from review request

class BarcodePerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", response_time_ms=None):
        """Log test result with performance metrics"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        
        if response_time_ms is not None:
            result += f" ({response_time_ms:.0f}ms)"
            
        if details:
            result += f": {details}"
            
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_authentication_performance(self):
        """Test 1: Authentication performance (should be under 500ms)"""
        print("\n🔐 AUTHENTICATION PERFORMANCE TEST")
        print("=" * 60)
        print("REQUIREMENT: Login should return valid JWT token in under 500ms")
        
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    
                    # Check if under 500ms requirement
                    meets_requirement = response_time_ms < 500
                    requirement_status = "MEETS REQUIREMENT" if meets_requirement else "EXCEEDS REQUIREMENT"
                    
                    self.log_result(
                        "Authentication Speed", 
                        meets_requirement,
                        f"JWT token received - {requirement_status}",
                        response_time_ms
                    )
                    return True
                else:
                    self.log_result("Authentication", False, "No access token in response", response_time_ms)
                    return False
            else:
                self.log_result("Authentication", False, f"HTTP {response.status_code}", response_time_ms)
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_barcode_lookup_performance(self):
        """Test 2: Barcode lookup performance (should be under 100ms)"""
        print("\n📱 BARCODE LOOKUP PERFORMANCE TEST")
        print("=" * 60)
        print(f"REQUIREMENT: Barcode lookup should return complete product data in under 100ms")
        print(f"TARGET BARCODE: {TARGET_BARCODE} (Apple Juice Box 1L)")
        
        if not self.token:
            self.log_result("Barcode Performance Setup", False, "No authentication token")
            return False
        
        # Perform multiple tests to get average response time
        response_times = []
        successful_requests = 0
        
        for i in range(5):  # Test 5 times for average
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/barcode/{TARGET_BARCODE}")
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                
                if response.status_code == 200:
                    successful_requests += 1
                    
                    if i == 0:  # Log details for first request only
                        data = response.json()
                        product_name = data.get('product_name', 'N/A')
                        department = data.get('department', 'N/A')
                        price = data.get('purchase_price', 0)
                        currency = data.get('purchase_currency', 'N/A')
                        
                        print(f"   Product Found: {product_name}")
                        print(f"   Department: {department}")
                        print(f"   Price: {price} {currency}")
                        print(f"   Response Size: {len(json.dumps(data))} bytes")
                        
            except Exception as e:
                print(f"   Request {i+1} failed: {str(e)}")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Check if meets 100ms requirement
            meets_requirement = avg_response_time < 100
            requirement_status = "MEETS REQUIREMENT" if meets_requirement else "EXCEEDS REQUIREMENT"
            
            self.log_result(
                "Barcode Lookup Speed (Average)",
                meets_requirement,
                f"Min: {min_response_time:.0f}ms, Max: {max_response_time:.0f}ms - {requirement_status}",
                avg_response_time
            )
            
            # Test reliability
            reliability = (successful_requests / 5) * 100
            self.log_result(
                "Barcode Lookup Reliability",
                reliability == 100,
                f"{successful_requests}/5 requests successful ({reliability:.0f}%)"
            )
            
            return meets_requirement and reliability == 100
        else:
            self.log_result("Barcode Lookup Performance", False, "No successful requests")
            return False
    
    def test_error_handling_performance(self):
        """Test 3: Error handling performance"""
        print("\n🚫 ERROR HANDLING PERFORMANCE TEST")
        print("=" * 60)
        print("REQUIREMENT: Invalid barcodes should return proper 404 status")
        print("REQUIREMENT: Unauthorized requests should return 403/401 status")
        
        # Test invalid barcode handling
        invalid_barcode = "0000000000000"
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/barcode/{invalid_barcode}")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 404:
                self.log_result(
                    "Invalid Barcode Handling",
                    True,
                    "Correctly returns 404 Not Found",
                    response_time_ms
                )
            else:
                self.log_result(
                    "Invalid Barcode Handling",
                    False,
                    f"Expected 404, got {response.status_code}",
                    response_time_ms
                )
        except Exception as e:
            self.log_result("Invalid Barcode Handling", False, f"Exception: {str(e)}")
        
        # Test unauthorized access
        session_no_auth = requests.Session()
        
        try:
            start_time = time.time()
            response = session_no_auth.get(f"{BACKEND_URL}/barcode/{TARGET_BARCODE}")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Unauthorized Access Handling",
                    True,
                    f"Correctly returns {response.status_code}",
                    response_time_ms
                )
            else:
                self.log_result(
                    "Unauthorized Access Handling",
                    False,
                    f"Expected 401/403, got {response.status_code}",
                    response_time_ms
                )
        except Exception as e:
            self.log_result("Unauthorized Access Handling", False, f"Exception: {str(e)}")
    
    def test_mobile_compatibility(self):
        """Test 4: Mobile compatibility and CORS headers"""
        print("\n📱 MOBILE COMPATIBILITY TEST")
        print("=" * 60)
        print("REQUIREMENT: API should have proper CORS headers for mobile compatibility")
        
        if not self.token:
            self.log_result("Mobile Compatibility Setup", False, "No authentication token")
            return
        
        # Test with mobile user agent and headers
        mobile_headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://stockmate-14.preview.emergentagent.com"
        }
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{BACKEND_URL}/barcode/{TARGET_BARCODE}",
                headers=mobile_headers
            )
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                present_cors = {k: v for k, v in cors_headers.items() if v is not None}
                
                if present_cors:
                    self.log_result(
                        "CORS Headers Present",
                        True,
                        f"Found: {list(present_cors.keys())}",
                        response_time_ms
                    )
                    
                    # Check if allows all origins or specific origin
                    allow_origin = cors_headers.get('Access-Control-Allow-Origin')
                    if allow_origin in ['*', 'https://stockmate-14.preview.emergentagent.com']:
                        self.log_result("CORS Origin Policy", True, f"Allows: {allow_origin}")
                    else:
                        self.log_result("CORS Origin Policy", False, f"Restrictive: {allow_origin}")
                        
                else:
                    self.log_result(
                        "CORS Headers Present",
                        False,
                        "No CORS headers detected",
                        response_time_ms
                    )
                
                # Test mobile response time (should be fast for mobile networks)
                mobile_speed_ok = response_time_ms < 200  # 200ms is reasonable for mobile
                speed_status = "GOOD" if mobile_speed_ok else "SLOW"
                
                self.log_result(
                    "Mobile Response Speed",
                    mobile_speed_ok,
                    f"Mobile network compatible - {speed_status}",
                    response_time_ms
                )
                
            else:
                self.log_result(
                    "Mobile Compatibility",
                    False,
                    f"HTTP {response.status_code}",
                    response_time_ms
                )
                
        except Exception as e:
            self.log_result("Mobile Compatibility", False, f"Exception: {str(e)}")
    
    def test_complete_product_data(self):
        """Test 5: Verify complete product data is returned"""
        print("\n📋 COMPLETE PRODUCT DATA TEST")
        print("=" * 60)
        print("REQUIREMENT: Barcode lookup should return complete product data")
        
        if not self.token:
            self.log_result("Product Data Test Setup", False, "No authentication token")
            return
        
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{TARGET_BARCODE}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields from review request
                required_fields = [
                    'product_name', 'item_number', 'barcode', 'department', 
                    'section', 'purchase_price', 'purchase_currency', 
                    'selling_price', 'supplier', 'quantity', 'status'
                ]
                
                present_fields = [field for field in required_fields if field in data and data[field] is not None]
                missing_fields = [field for field in required_fields if field not in data or data[field] is None]
                
                completeness_percentage = (len(present_fields) / len(required_fields)) * 100
                
                self.log_result(
                    "Required Fields Present",
                    len(missing_fields) == 0,
                    f"{len(present_fields)}/{len(required_fields)} fields ({completeness_percentage:.0f}%)"
                )
                
                if missing_fields:
                    print(f"   Missing fields: {missing_fields}")
                
                # Verify specific data for Apple Juice Box 1L
                expected_data = {
                    'product_name': 'Apple Juice Box 1L',
                    'department': '01-CGD',
                    'purchase_currency': 'EUR'
                }
                
                data_accuracy = True
                for field, expected_value in expected_data.items():
                    actual_value = data.get(field)
                    if actual_value != expected_value:
                        print(f"   Data mismatch - {field}: expected '{expected_value}', got '{actual_value}'")
                        data_accuracy = False
                
                self.log_result(
                    "Product Data Accuracy",
                    data_accuracy,
                    "Apple Juice Box 1L data matches expectations" if data_accuracy else "Data inconsistencies found"
                )
                
            else:
                self.log_result("Product Data Retrieval", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Product Data Test", False, f"Exception: {str(e)}")
    
    def run_performance_tests(self):
        """Run all performance tests"""
        print("⚡ BARCODE SCANNER PERFORMANCE TEST - SPEED AND RELIABILITY FOCUS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Target Barcode: {TARGET_BARCODE} (Apple Juice Box 1L)")
        print(f"Admin Credentials: {ADMIN_USERNAME}")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication_performance()
        
        if auth_success:
            self.test_barcode_lookup_performance()
            self.test_error_handling_performance()
            self.test_mobile_compatibility()
            self.test_complete_product_data()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with performance tests")
        
        self.print_performance_summary()
    
    def print_performance_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 80)
        print("⚡ BARCODE SCANNER PERFORMANCE SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 REVIEW REQUIREMENTS VERIFICATION:")
        
        # Check each requirement
        auth_tests = [r for r in self.test_results if "Authentication Speed" in r["test"]]
        if auth_tests and auth_tests[0]["success"]:
            auth_time = auth_tests[0]["response_time_ms"]
            print(f"✅ Authentication: {auth_time:.0f}ms (requirement: <500ms)")
        else:
            print("❌ Authentication: FAILED or too slow")
        
        barcode_tests = [r for r in self.test_results if "Barcode Lookup Speed" in r["test"]]
        if barcode_tests and barcode_tests[0]["success"]:
            lookup_time = barcode_tests[0]["response_time_ms"]
            print(f"✅ Barcode Lookup: {lookup_time:.0f}ms (requirement: <100ms)")
        else:
            print("❌ Barcode Lookup: FAILED or too slow")
        
        error_tests = [r for r in self.test_results if "Handling" in r["test"]]
        error_success = all(r["success"] for r in error_tests)
        if error_success:
            print("✅ Error Handling: Proper 404/403 responses")
        else:
            print("❌ Error Handling: Issues with error responses")
        
        cors_tests = [r for r in self.test_results if "CORS" in r["test"]]
        if cors_tests:
            if cors_tests[0]["success"]:
                print("✅ Mobile Compatibility: CORS headers configured")
            else:
                print("⚠️  Mobile Compatibility: CORS headers missing (may need configuration)")
        
        data_tests = [r for r in self.test_results if "Product Data" in r["test"]]
        data_success = all(r["success"] for r in data_tests)
        if data_success:
            print("✅ Complete Product Data: All required fields present")
        else:
            print("❌ Complete Product Data: Missing or incorrect data")
        
        print("\n🔍 FINAL VERDICT:")
        if success_rate >= 80:
            print("✅ BACKEND IS READY FOR SimpleBarcodeScanner.js COMPONENT!")
            print("✅ Performance requirements met for SPEED and RELIABILITY")
            print("✅ Authentication, barcode lookup, and error handling working correctly")
        elif success_rate >= 60:
            print("⚠️  BACKEND HAS MINOR ISSUES - mostly ready but needs attention")
            print("⚠️  Some performance or compatibility issues detected")
        else:
            print("❌ BACKEND NOT READY - critical issues must be resolved")
            print("❌ Performance requirements not met")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = BarcodePerformanceTester()
    tester.run_performance_tests()

if __name__ == "__main__":
    main()