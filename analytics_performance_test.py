#!/usr/bin/env python3
"""
ANALYTICS ENDPOINTS PERFORMANCE TEST

Test the analytics endpoints mentioned in the review request:
- /api/analytics/department-breakdown
- /api/analytics/stock-levels  
- /api/analytics/supplier-performance

With the actual dataset of 1,850 products.
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://stock-genius-24.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Performance thresholds from review request
MAX_ANALYTICS_RESPONSE_TIME = 2000  # 2 seconds in ms

class AnalyticsPerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details="", response_time_ms=None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if response_time_ms:
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
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        print("\n🔐 AUTHENTICATION")
        print("=" * 50)
        
        try:
            start_time = time.time()
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Admin Authentication", True, f"Token received", response_time)
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No access token in response", response_time)
                    return False
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_department_breakdown_analytics(self):
        """Test /api/analytics/department-breakdown endpoint"""
        print("\n📊 DEPARTMENT BREAKDOWN ANALYTICS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Department Analytics Setup", False, "No authentication token")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check performance threshold
                performance_ok = response_time <= MAX_ANALYTICS_RESPONSE_TIME
                
                if performance_ok:
                    # Analyze response data
                    if isinstance(data, dict):
                        departments = data.get('departments', [])
                        total_products = data.get('total_products', 0)
                        
                        if departments and total_products > 0:
                            self.log_test("Department Breakdown API", True, 
                                        f"{len(departments)} departments, {total_products} total products", response_time)
                            
                            # Test data completeness
                            dept_with_data = sum(1 for dept in departments if dept.get('product_count', 0) > 0)
                            if dept_with_data > 0:
                                self.log_test("Department Data Completeness", True, 
                                            f"{dept_with_data}/{len(departments)} departments have products")
                            else:
                                self.log_test("Department Data Completeness", False, 
                                            "No departments have product counts")
                        else:
                            self.log_test("Department Breakdown API", False, 
                                        "Empty or invalid response data", response_time)
                    elif isinstance(data, list):
                        # Handle list response format
                        if len(data) > 0:
                            self.log_test("Department Breakdown API", True, 
                                        f"{len(data)} department entries returned", response_time)
                        else:
                            self.log_test("Department Breakdown API", False, 
                                        "Empty department list", response_time)
                    else:
                        self.log_test("Department Breakdown API", False, 
                                    f"Unexpected response format: {type(data)}", response_time)
                else:
                    self.log_test("Department Breakdown API", False, 
                                f"Too slow: {response_time:.0f}ms > {MAX_ANALYTICS_RESPONSE_TIME}ms", response_time)
            else:
                self.log_test("Department Breakdown API", False, 
                            f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_test("Department Breakdown API", False, f"Exception: {str(e)}")
    
    def test_stock_levels_analytics(self):
        """Test /api/analytics/stock-levels endpoint"""
        print("\n📈 STOCK LEVELS ANALYTICS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Stock Levels Setup", False, "No authentication token")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/stock-levels")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check performance threshold
                performance_ok = response_time <= MAX_ANALYTICS_RESPONSE_TIME
                
                if performance_ok:
                    # Analyze response data
                    if isinstance(data, dict):
                        # Look for stock level indicators
                        stock_categories = ['in_stock', 'low_stock', 'out_of_stock', 'expired', 'near_expiry']
                        found_categories = [cat for cat in stock_categories if cat in data]
                        
                        if found_categories:
                            total_items = sum(data.get(cat, 0) for cat in found_categories if isinstance(data.get(cat), (int, float)))
                            self.log_test("Stock Levels API", True, 
                                        f"Categories: {found_categories}, Total items: {total_items}", response_time)
                        else:
                            # Check for other data structures
                            if data:
                                self.log_test("Stock Levels API", True, 
                                            f"Response contains {len(data)} data points", response_time)
                            else:
                                self.log_test("Stock Levels API", False, 
                                            "Empty response data", response_time)
                    elif isinstance(data, list):
                        if len(data) > 0:
                            self.log_test("Stock Levels API", True, 
                                        f"{len(data)} stock level entries", response_time)
                        else:
                            self.log_test("Stock Levels API", False, 
                                        "Empty stock levels list", response_time)
                    else:
                        self.log_test("Stock Levels API", False, 
                                    f"Unexpected response format: {type(data)}", response_time)
                else:
                    self.log_test("Stock Levels API", False, 
                                f"Too slow: {response_time:.0f}ms > {MAX_ANALYTICS_RESPONSE_TIME}ms", response_time)
            else:
                self.log_test("Stock Levels API", False, 
                            f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_test("Stock Levels API", False, f"Exception: {str(e)}")
    
    def test_supplier_performance_analytics(self):
        """Test /api/analytics/supplier-performance endpoint"""
        print("\n🏭 SUPPLIER PERFORMANCE ANALYTICS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Supplier Performance Setup", False, "No authentication token")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/supplier-performance")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check performance threshold
                performance_ok = response_time <= MAX_ANALYTICS_RESPONSE_TIME
                
                if performance_ok:
                    # Analyze response data
                    if isinstance(data, dict):
                        suppliers = data.get('suppliers', [])
                        if suppliers:
                            # Analyze supplier data quality
                            suppliers_with_metrics = 0
                            total_suppliers = len(suppliers)
                            
                            for supplier in suppliers:
                                if isinstance(supplier, dict):
                                    # Check for performance metrics
                                    metrics = ['total_items', 'stock_value', 'out_of_stock_items', 'performance_score']
                                    if any(metric in supplier for metric in metrics):
                                        suppliers_with_metrics += 1
                            
                            self.log_test("Supplier Performance API", True, 
                                        f"{total_suppliers} suppliers, {suppliers_with_metrics} with metrics", response_time)
                            
                            # Test data completeness
                            completeness = (suppliers_with_metrics / total_suppliers * 100) if total_suppliers > 0 else 0
                            if completeness >= 80:
                                self.log_test("Supplier Metrics Completeness", True, 
                                            f"{completeness:.1f}% suppliers have performance metrics")
                            else:
                                self.log_test("Supplier Metrics Completeness", False, 
                                            f"Only {completeness:.1f}% suppliers have metrics")
                        else:
                            self.log_test("Supplier Performance API", False, 
                                        "No suppliers in response", response_time)
                    elif isinstance(data, list):
                        if len(data) > 0:
                            self.log_test("Supplier Performance API", True, 
                                        f"{len(data)} supplier performance entries", response_time)
                        else:
                            self.log_test("Supplier Performance API", False, 
                                        "Empty supplier performance list", response_time)
                    else:
                        self.log_test("Supplier Performance API", False, 
                                    f"Unexpected response format: {type(data)}", response_time)
                else:
                    self.log_test("Supplier Performance API", False, 
                                f"Too slow: {response_time:.0f}ms > {MAX_ANALYTICS_RESPONSE_TIME}ms", response_time)
            else:
                self.log_test("Supplier Performance API", False, 
                            f"HTTP {response.status_code}: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_test("Supplier Performance API", False, f"Exception: {str(e)}")
    
    def test_analytics_with_filters(self):
        """Test analytics endpoints with various filters"""
        print("\n🔍 ANALYTICS WITH FILTERS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Analytics Filters Setup", False, "No authentication token")
            return False
        
        # Test department filtering on analytics endpoints
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        for department in departments:
            # Test department breakdown with filter
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown", 
                                          params={"department": department})
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        self.log_test(f"Department Analytics Filter - {department}", True, 
                                    f"Filtered data returned", response_time)
                    else:
                        self.log_test(f"Department Analytics Filter - {department}", False, 
                                    f"No data for department", response_time)
                else:
                    self.log_test(f"Department Analytics Filter - {department}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Department Analytics Filter - {department}", False, f"Exception: {str(e)}")
        
        # Test date range filtering if supported
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/stock-levels", 
                                      params={"period": "weekly"})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.log_test("Stock Levels Period Filter", True, 
                            f"Weekly period filter accepted", response_time)
            else:
                self.log_test("Stock Levels Period Filter", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Stock Levels Period Filter", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all analytics performance tests"""
        print("🎯 ANALYTICS ENDPOINTS PERFORMANCE TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Dataset Size: 1,850 products")
        print(f"Performance Threshold: {MAX_ANALYTICS_RESPONSE_TIME}ms")
        print("Testing analytics endpoints from review request:")
        print("  - /api/analytics/department-breakdown")
        print("  - /api/analytics/stock-levels")
        print("  - /api/analytics/supplier-performance")
        print("=" * 80)
        
        # Run authentication first
        auth_success = self.authenticate()
        
        if auth_success:
            # Run all analytics tests
            self.test_department_breakdown_analytics()
            self.test_stock_levels_analytics()
            self.test_supplier_performance_analytics()
            self.test_analytics_with_filters()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 ANALYTICS PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Performance analysis
        analytics_tests = [r for r in self.test_results if "Analytics" in r["test"] and r.get("response_time_ms")]
        if analytics_tests:
            response_times = [r["response_time_ms"] for r in analytics_tests]
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\n⚡ ANALYTICS PERFORMANCE:")
            print(f"  - Average Response Time: {avg_time:.0f}ms")
            print(f"  - Fastest Response: {min_time:.0f}ms")
            print(f"  - Slowest Response: {max_time:.0f}ms")
            print(f"  - Performance Target: <{MAX_ANALYTICS_RESPONSE_TIME}ms")
            
            if max_time <= MAX_ANALYTICS_RESPONSE_TIME:
                print("  ✅ All analytics endpoints meet performance requirements")
            else:
                print("  ❌ Some analytics endpoints exceed performance threshold")
        
        print(f"\n🎯 REVIEW REQUEST COMPLIANCE:")
        
        # Check specific requirements from review request
        dept_breakdown_tests = [r for r in self.test_results if "Department Breakdown" in r["test"]]
        stock_levels_tests = [r for r in self.test_results if "Stock Levels" in r["test"]]
        supplier_perf_tests = [r for r in self.test_results if "Supplier Performance" in r["test"]]
        
        if dept_breakdown_tests and dept_breakdown_tests[0]["success"]:
            print("✅ Department Breakdown Analytics: WORKING")
        else:
            print("❌ Department Breakdown Analytics: FAILED")
        
        if stock_levels_tests and stock_levels_tests[0]["success"]:
            print("✅ Stock Levels Analytics: WORKING")
        else:
            print("❌ Stock Levels Analytics: FAILED")
        
        if supplier_perf_tests and supplier_perf_tests[0]["success"]:
            print("✅ Supplier Performance Analytics: WORKING")
        else:
            print("❌ Supplier Performance Analytics: FAILED")
        
        print(f"\n🔍 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            print("✅ EXCELLENT: All analytics endpoints working perfectly!")
            print("✅ Performance requirements met")
            print("✅ Ready for enterprise analytics usage")
        elif success_rate >= 75:
            print("⚠️  GOOD: Most analytics working with minor issues")
            print("⚠️  Some optimizations may be needed")
        elif success_rate >= 50:
            print("⚠️  FAIR: Analytics partially functional")
            print("⚠️  Significant improvements needed")
        else:
            print("❌ POOR: Analytics endpoints not working properly")
            print("❌ Critical issues must be resolved")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = AnalyticsPerformanceTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()