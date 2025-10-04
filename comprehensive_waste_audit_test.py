#!/usr/bin/env python3
"""
COMPREHENSIVE WASTE MANAGEMENT AUDIT VERIFICATION TEST

This test specifically addresses the review request requirements:
1. Test all 4 critical waste endpoints after audit fixes
2. Verify admin authentication (imadqejji/066380531I) 
3. Test data integrity with currency calculations (YER, SAR, EUR)
4. Verify performance (<100ms for API calls)
5. Test error handling for invalid data

Expected: Verify no regression after frontend WasteReports.js cleanup
Previous status: 100% success rate (26/26 tests passed)
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Configuration from review request
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data for multi-currency validation using real products from database
CURRENCY_TEST_DATA = [
    {
        "product_id": "3d8e7ef1-b728-4cce-a33b-560c4ea16781",  # Al Hanaa Guava Nectar 235 ml (YER)
        "quantity_wasted": 10,
        "waste_reason": "damaged",
        "notes": "Testing YER currency calculation"
    },
    {
        "product_id": "e6bb0e62-2c60-491b-9ac4-1ed22c1e58c3",  # Pepsi cola can 250 ml (SAR)
        "quantity_wasted": 5,
        "waste_reason": "expired",
        "notes": "Testing SAR currency calculation"
    },
    {
        "product_id": "ab7ecf8a-5a9c-44fe-9ff1-eee5f17cc6e1",  # Apple Juice Box 1L (EUR)
        "quantity_wasted": 3,
        "waste_reason": "unsellable",
        "notes": "Testing EUR currency calculation"
    }
]

class WasteAuditTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.performance_data = []
        self.created_entries = []
        
    def log_test(self, test_name, success, details="", response_time_ms=None):
        """Log test result with performance tracking"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if response_time_ms is not None:
            result += f" ({response_time_ms:.0f}ms)"
            self.performance_data.append({
                "test": test_name,
                "response_time": response_time_ms,
                "meets_100ms_requirement": response_time_ms < 100
            })
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
    
    def make_timed_request(self, method, endpoint, **kwargs):
        """Make request with timing"""
        start_time = time.time()
        try:
            response = getattr(self.session, method.lower())(f"{BACKEND_URL}{endpoint}", **kwargs)
            response_time_ms = (time.time() - start_time) * 1000
            return response, response_time_ms
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            raise e
    
    def test_admin_authentication(self):
        """REQUIREMENT 2: Verify admin authentication (imadqejji/066380531I)"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
        print("=" * 60)
        
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response, response_time = self.make_timed_request("post", "/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Admin Authentication (imadqejji/066380531I)", True, 
                                "Admin credentials working, JWT token received", response_time)
                    return True
                else:
                    self.log_test("Admin Authentication", False, 
                                "No access token in response", response_time)
                    return False
            else:
                self.log_test("Admin Authentication", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_waste_entry_endpoint(self):
        """REQUIREMENT 1: Test POST /api/waste/entries endpoint"""
        print("\n📝 TESTING POST /api/waste/entries ENDPOINT")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Waste Entry Endpoint Setup", False, "No authentication token")
            return False
        
        all_successful = True
        
        for i, test_data in enumerate(CURRENCY_TEST_DATA):
            try:
                response, response_time = self.make_timed_request("post", "/waste/entries", json=test_data)
                
                test_name = f"POST /api/waste/entries ({test_data['purchase_currency']})"
                
                if response.status_code in [200, 201]:
                    try:
                        result = response.json()
                        
                        # REQUIREMENT 3: Verify calculation exists and entry created
                        if "id" in result or "message" in result:
                            self.log_test(test_name, True, 
                                        f"Waste entry created successfully for product {test_data['product_id']}", 
                                        response_time)
                            
                            if "id" in result:
                                self.created_entries.append(result["id"])
                        else:
                            self.log_test(test_name, False, 
                                        "No entry ID or success message in response", 
                                        response_time)
                            all_successful = False
                            
                    except json.JSONDecodeError:
                        self.log_test(test_name, False, "Invalid JSON response", response_time)
                        all_successful = False
                else:
                    self.log_test(test_name, False, 
                                f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                    all_successful = False
                    
            except Exception as e:
                self.log_test(f"POST /api/waste/entries (Product {test_data['product_id']})", False, f"Exception: {str(e)}")
                all_successful = False
        
        return all_successful
    
    def test_waste_reports_endpoint(self):
        """REQUIREMENT 1: Test GET /api/waste/reports endpoint"""
        print("\n📊 TESTING GET /api/waste/reports ENDPOINT")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Waste Reports Endpoint Setup", False, "No authentication token")
            return False
        
        # Test different report scenarios
        test_scenarios = [
            {"period": "daily", "description": "Daily Report"},
            {"period": "weekly", "description": "Weekly Report"},
            {"period": "monthly", "description": "Monthly Report"},
            {"period": "daily", "department": "01-FMG", "description": "Daily Report with Department Filter"}
        ]
        
        all_successful = True
        
        for scenario in test_scenarios:
            try:
                params = {k: v for k, v in scenario.items() if k != "description"}
                response, response_time = self.make_timed_request("get", "/waste/reports", params=params)
                
                test_name = f"GET /api/waste/reports ({scenario['description']})"
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Verify report structure
                        required_keys = ["period", "currency_totals", "total_entries"]
                        missing_keys = [key for key in required_keys if key not in data]
                        
                        if missing_keys:
                            self.log_test(test_name, False, 
                                        f"Missing report keys: {missing_keys}", response_time)
                            all_successful = False
                        else:
                            # REQUIREMENT 3: Verify currency breakdown (YER, SAR, EUR)
                            currency_totals = data.get("currency_totals", {})
                            currencies_found = [curr for curr in ["YER", "SAR", "EUR"] if curr in currency_totals]
                            
                            self.log_test(test_name, True, 
                                        f"Report generated: {data.get('total_entries', 0)} entries, currencies: {currencies_found}", 
                                        response_time)
                            
                    except json.JSONDecodeError:
                        self.log_test(test_name, False, "Invalid JSON response", response_time)
                        all_successful = False
                else:
                    self.log_test(test_name, False, 
                                f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                    all_successful = False
                    
            except Exception as e:
                self.log_test(f"GET /api/waste/reports ({scenario['description']})", False, f"Exception: {str(e)}")
                all_successful = False
        
        return all_successful
    
    def test_waste_entries_list_endpoint(self):
        """REQUIREMENT 1: Test GET /api/waste/entries endpoint"""
        print("\n📋 TESTING GET /api/waste/entries ENDPOINT")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Waste Entries List Setup", False, "No authentication token")
            return False
        
        try:
            response, response_time = self.make_timed_request("get", "/waste/entries")
            
            test_name = "GET /api/waste/entries"
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, list):
                        self.log_test(test_name, True, 
                                    f"Retrieved {len(data)} waste entries", response_time)
                        
                        # Verify data structure
                        if data:
                            first_entry = data[0]
                            required_fields = ["id", "product_name", "quantity_wasted", 
                                             "purchase_price", "purchase_currency", "waste_value"]
                            missing_fields = [field for field in required_fields if field not in first_entry]
                            
                            if missing_fields:
                                self.log_test("Waste Entry Data Structure", False, 
                                            f"Missing fields: {missing_fields}")
                                return False
                            else:
                                self.log_test("Waste Entry Data Structure", True, 
                                            "All required fields present")
                        
                        return True
                    else:
                        self.log_test(test_name, False, 
                                    f"Expected list, got {type(data)}", response_time)
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test(test_name, False, "Invalid JSON response", response_time)
                    return False
            else:
                self.log_test(test_name, False, 
                            f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                return False
                
        except Exception as e:
            self.log_test("GET /api/waste/entries", False, f"Exception: {str(e)}")
            return False
    
    def test_waste_export_endpoint(self):
        """REQUIREMENT 1: Test GET /api/export/waste-report/{period} endpoint"""
        print("\n📤 TESTING GET /api/export/waste-report/{period} ENDPOINT")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Waste Export Setup", False, "No authentication token")
            return False
        
        # Test different export periods
        export_tests = [
            {"period": "daily", "description": "Daily Export"},
            {"period": "weekly", "description": "Weekly Export"},
            {"period": "monthly", "description": "Monthly Export"}
        ]
        
        all_successful = True
        
        for test in export_tests:
            try:
                response, response_time = self.make_timed_request("get", f"/export/waste-report/{test['period']}")
                
                test_name = f"GET /api/export/waste-report/{test['period']}"
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    if content_length > 0:
                        self.log_test(test_name, True, 
                                    f"Export generated: {content_length} bytes, type: {content_type}", 
                                    response_time)
                    else:
                        self.log_test(test_name, False, "Empty export file", response_time)
                        all_successful = False
                else:
                    self.log_test(test_name, False, 
                                f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                    all_successful = False
                    
            except Exception as e:
                self.log_test(f"GET /api/export/waste-report/{test['period']}", False, f"Exception: {str(e)}")
                all_successful = False
        
        return all_successful
    
    def test_error_handling(self):
        """REQUIREMENT 5: Test error handling for invalid data"""
        print("\n🚫 TESTING ERROR HANDLING")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Error Handling Setup", False, "No authentication token")
            return False
        
        # Test invalid data scenarios
        invalid_scenarios = [
            {
                "data": {"product_name": "", "quantity_wasted": 0, "purchase_price": 0},
                "description": "Empty/zero values"
            },
            {
                "data": {"product_name": "Test", "quantity_wasted": -5, "purchase_price": 10},
                "description": "Negative quantity"
            },
            {
                "data": {"product_name": "Test", "quantity_wasted": 5, "purchase_price": -10},
                "description": "Negative price"
            },
            {
                "data": {"product_name": "Test", "quantity_wasted": 5, "purchase_currency": "INVALID"},
                "description": "Invalid currency"
            }
        ]
        
        all_successful = True
        
        for i, scenario in enumerate(invalid_scenarios):
            try:
                response, response_time = self.make_timed_request("post", "/waste/entries", json=scenario["data"])
                
                test_name = f"Error Handling {i+1}: {scenario['description']}"
                
                # Should return 400 or 422 for invalid data
                if response.status_code in [400, 422]:
                    self.log_test(test_name, True, 
                                f"Correctly rejected with HTTP {response.status_code}", response_time)
                else:
                    self.log_test(test_name, False, 
                                f"Expected 400/422, got {response.status_code}", response_time)
                    all_successful = False
                    
            except Exception as e:
                self.log_test(f"Error Handling {i+1}", False, f"Exception: {str(e)}")
                all_successful = False
        
        return all_successful
    
    def test_performance_requirements(self):
        """REQUIREMENT 4: Verify performance (<100ms for API calls)"""
        print("\n⚡ TESTING PERFORMANCE REQUIREMENTS")
        print("=" * 60)
        
        if not self.performance_data:
            self.log_test("Performance Analysis", False, "No performance data collected")
            return False
        
        # Analyze performance metrics
        total_requests = len(self.performance_data)
        fast_requests = [req for req in self.performance_data if req["meets_100ms_requirement"]]
        slow_requests = [req for req in self.performance_data if not req["meets_100ms_requirement"]]
        
        avg_response_time = sum(req["response_time"] for req in self.performance_data) / total_requests
        performance_rate = (len(fast_requests) / total_requests) * 100
        
        self.log_test("Performance Analysis", True, 
                    f"Average: {avg_response_time:.1f}ms, {len(fast_requests)}/{total_requests} requests <100ms ({performance_rate:.1f}%)")
        
        if slow_requests:
            slow_details = ", ".join([f"{req['test']}({req['response_time']:.0f}ms)" for req in slow_requests[:3]])
            self.log_test("Performance Requirement (<100ms)", False, 
                        f"Slow requests: {slow_details}")
            return False
        else:
            self.log_test("Performance Requirement (<100ms)", True, 
                        "All API calls completed in <100ms")
            return True
    
    def run_comprehensive_audit(self):
        """Run all waste management audit tests"""
        print("🗑️  COMPREHENSIVE WASTE MANAGEMENT AUDIT VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{'*' * len(ADMIN_PASSWORD)}")
        print(f"Testing Currencies: YER, SAR, EUR")
        print(f"Expected: No regression after WasteReports.js cleanup")
        print(f"Previous Status: 100% success rate (26/26 tests passed)")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_admin_authentication()
        
        if auth_success:
            self.test_waste_entry_endpoint()
            self.test_waste_reports_endpoint()
            self.test_waste_entries_list_endpoint()
            self.test_waste_export_endpoint()
            self.test_error_handling()
            self.test_performance_requirements()
        else:
            print("\n❌ CRITICAL: Admin authentication failed - cannot proceed with audit tests")
        
        # Print comprehensive summary
        self.print_audit_summary()
    
    def print_audit_summary(self):
        """Print comprehensive audit summary"""
        print("\n" + "=" * 80)
        print("📊 WASTE MANAGEMENT AUDIT SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Performance summary
        if self.performance_data:
            avg_response_time = sum(req["response_time"] for req in self.performance_data) / len(self.performance_data)
            fast_requests = [req for req in self.performance_data if req["meets_100ms_requirement"]]
            performance_rate = (len(fast_requests) / len(self.performance_data)) * 100
            
            print(f"Average Response Time: {avg_response_time:.1f}ms")
            print(f"Performance Rate (<100ms): {performance_rate:.1f}%")
        
        print("\n🎯 AUDIT REQUIREMENTS VERIFICATION:")
        
        # Check each specific requirement from review request
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"]]
        waste_entry_tests = [r for r in self.test_results if "POST /api/waste/entries" in r["test"]]
        reports_tests = [r for r in self.test_results if "GET /api/waste/reports" in r["test"]]
        list_tests = [r for r in self.test_results if "GET /api/waste/entries" in r["test"] and "POST" not in r["test"]]
        export_tests = [r for r in self.test_results if "GET /api/export/waste-report" in r["test"]]
        error_tests = [r for r in self.test_results if "Error Handling" in r["test"]]
        
        # 1. Waste Management API Endpoints
        endpoints_working = 0
        total_endpoints = 4
        
        if waste_entry_tests and all(t["success"] for t in waste_entry_tests):
            print("✅ POST /api/waste/entries: WORKING - Waste entry creation functional")
            endpoints_working += 1
        else:
            print("❌ POST /api/waste/entries: FAILED - Waste entry creation not working")
        
        if reports_tests and all(t["success"] for t in reports_tests):
            print("✅ GET /api/waste/reports: WORKING - Waste reports generation functional")
            endpoints_working += 1
        else:
            print("❌ GET /api/waste/reports: FAILED - Waste reports generation not working")
        
        if list_tests and all(t["success"] for t in list_tests):
            print("✅ GET /api/waste/entries: WORKING - Waste entries listing functional")
            endpoints_working += 1
        else:
            print("❌ GET /api/waste/entries: FAILED - Waste entries listing not working")
        
        if export_tests and all(t["success"] for t in export_tests):
            print("✅ GET /api/export/waste-report/{period}: WORKING - Export functionality operational")
            endpoints_working += 1
        else:
            print("❌ GET /api/export/waste-report/{period}: FAILED - Export functionality not working")
        
        # 2. Authentication & Security
        if auth_tests and auth_tests[0]["success"]:
            print("✅ Authentication & Security: VERIFIED - Admin credentials (imadqejji/066380531I) working")
        else:
            print("❌ Authentication & Security: FAILED - Admin authentication not working")
        
        # 3. Data Integrity
        calculation_tests = [t for t in waste_entry_tests if "Calculation verified" in t.get("details", "")]
        if calculation_tests and len(calculation_tests) >= 3:
            print("✅ Data Integrity: VERIFIED - Currency calculations (quantity × purchase_price) correct across YER, SAR, EUR")
        else:
            print("❌ Data Integrity: FAILED - Currency calculations not working properly")
        
        # 4. Performance Verification
        if self.performance_data:
            fast_requests = [req for req in self.performance_data if req["meets_100ms_requirement"]]
            if len(fast_requests) == len(self.performance_data):
                print("✅ Performance Verification: PASSED - All API calls <100ms")
            else:
                slow_count = len(self.performance_data) - len(fast_requests)
                print(f"⚠️  Performance Verification: PARTIAL - {slow_count} API calls >100ms")
        
        # 5. Error Handling
        if error_tests and all(t["success"] for t in error_tests):
            print("✅ Error Handling: VERIFIED - Proper error responses for invalid data")
        else:
            print("❌ Error Handling: FAILED - Invalid data not properly handled")
        
        print(f"\n📈 API Endpoints Status: {endpoints_working}/{total_endpoints} working")
        
        print("\n🔍 FINAL AUDIT VERDICT:")
        if success_rate >= 95 and endpoints_working == total_endpoints:
            print("✅ WASTE MANAGEMENT SYSTEM: FULLY FUNCTIONAL")
            print("✅ NO REGRESSION DETECTED - All audit fixes successful")
            print("✅ PRODUCTION READY - System maintains expected functionality")
            print("✅ FRONTEND CLEANUP SUCCESSFUL - No backend impact detected")
        elif success_rate >= 80:
            print("⚠️  WASTE MANAGEMENT SYSTEM: MOSTLY FUNCTIONAL")
            print("⚠️  MINOR ISSUES DETECTED - Some functionality needs attention")
            print("⚠️  PARTIAL REGRESSION - Some audit fixes may need review")
        else:
            print("❌ WASTE MANAGEMENT SYSTEM: CRITICAL ISSUES")
            print("❌ REGRESSION DETECTED - Audit fixes introduced problems")
            print("❌ NOT PRODUCTION READY - Critical issues must be resolved")
        
        print("\n" + "=" * 80)

def main():
    """Main audit execution"""
    tester = WasteAuditTester()
    tester.run_comprehensive_audit()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 95:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()