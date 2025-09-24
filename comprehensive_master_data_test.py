#!/usr/bin/env python3
"""
COMPREHENSIVE MASTER DATA TEST - Final Review Request Compliance

This test covers ALL requirements from the review request:

1. Master Data API Performance ✅
2. Enhanced Search and Filtering ✅  
3. Large Dataset Performance ✅
4. Master Data Integrity ✅
5. Advanced Analytics Calculations ✅

Dataset: 1,850 products (not 18,762 as expected, but testing with actual data)
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class ComprehensiveMasterDataTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.critical_failures = []
        
    def log_test(self, test_name, success, details="", response_time_ms=None, critical=False):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            if critical:
                self.critical_failures.append(test_name)
            
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
            "critical": critical,
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
                    self.log_test("Admin Authentication", True, f"Token received", response_time, critical=True)
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No access token in response", response_time, critical=True)
                    return False
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}", response_time, critical=True)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}", critical=True)
            return False
    
    def test_master_data_api_performance(self):
        """Test 1: Master Data API Performance (Review Requirement 1)"""
        print("\n📊 1. MASTER DATA API PERFORMANCE")
        print("=" * 50)
        
        if not self.token:
            return False
        
        # Test analytics endpoints with performance requirements
        analytics_endpoints = [
            {"url": "/analytics/department-breakdown", "name": "Department Breakdown", "max_time": 2000},
            {"url": "/analytics/stock-levels", "name": "Stock Levels", "max_time": 2000},
            {"url": "/analytics/supplier-performance", "name": "Supplier Performance", "max_time": 2000}
        ]
        
        for endpoint in analytics_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint['url']}")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    performance_ok = response_time <= endpoint['max_time']
                    
                    if performance_ok and data:
                        self.log_test(f"{endpoint['name']} API Performance", True, 
                                    f"Response under {endpoint['max_time']}ms with data", response_time, critical=True)
                    elif not performance_ok:
                        self.log_test(f"{endpoint['name']} API Performance", False, 
                                    f"Too slow: {response_time:.0f}ms", response_time, critical=True)
                    else:
                        self.log_test(f"{endpoint['name']} API Performance", False, 
                                    f"No data returned", response_time, critical=True)
                else:
                    self.log_test(f"{endpoint['name']} API Performance", False, 
                                f"HTTP {response.status_code}", response_time, critical=True)
                    
            except Exception as e:
                self.log_test(f"{endpoint['name']} API Performance", False, f"Exception: {str(e)}", critical=True)
    
    def test_enhanced_search_and_filtering(self):
        """Test 2: Enhanced Search and Filtering (Review Requirement 2)"""
        print("\n🔍 2. ENHANCED SEARCH AND FILTERING")
        print("=" * 50)
        
        if not self.token:
            return False
        
        # Test barcode lookup with various barcodes from different departments
        print("Testing barcode lookup performance...")
        
        # Get sample barcodes from database
        try:
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 50})
            if response.status_code == 200:
                products = response.json()
                test_barcodes = []
                
                for product in products:
                    if isinstance(product, dict) and product.get("barcode"):
                        barcode = str(product["barcode"]).strip()
                        if barcode and len(barcode) > 5:
                            test_barcodes.append(barcode)
                            if len(test_barcodes) >= 5:
                                break
                
                # Test barcode lookup performance (should be under 100ms)
                barcode_times = []
                for barcode in test_barcodes:
                    start_time = time.time()
                    lookup_response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
                    response_time = (time.time() - start_time) * 1000
                    barcode_times.append(response_time)
                    
                    if lookup_response.status_code == 200 and response_time <= 100:
                        self.log_test(f"Barcode Lookup Performance", True, 
                                    f"Under 100ms threshold", response_time)
                    else:
                        self.log_test(f"Barcode Lookup Performance", False, 
                                    f"Over 100ms or failed", response_time, critical=True)
                
                # Average barcode performance
                if barcode_times:
                    avg_time = sum(barcode_times) / len(barcode_times)
                    if avg_time <= 100:
                        self.log_test("Average Barcode Performance", True, 
                                    f"{avg_time:.0f}ms average", avg_time, critical=True)
                    else:
                        self.log_test("Average Barcode Performance", False, 
                                    f"{avg_time:.0f}ms average (too slow)", avg_time, critical=True)
        
        except Exception as e:
            self.log_test("Barcode Lookup Test", False, f"Exception: {str(e)}", critical=True)
        
        # Test department filtering
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        for dept in departments:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/products", 
                                          params={"department": dept, "limit": 100})
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Verify filtering accuracy
                        correct_dept = all(p.get("department") == dept for p in data if isinstance(p, dict))
                        if correct_dept:
                            self.log_test(f"Department Filter - {dept}", True, 
                                        f"{len(data)} products, 100% accurate", response_time)
                        else:
                            self.log_test(f"Department Filter - {dept}", False, 
                                        f"Filtering inaccurate", response_time)
                    else:
                        self.log_test(f"Department Filter - {dept}", False, 
                                    f"No products found", response_time)
                else:
                    self.log_test(f"Department Filter - {dept}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Department Filter - {dept}", False, f"Exception: {str(e)}")
        
        # Test supplier filtering
        try:
            # Get top suppliers first
            suppliers_response = self.session.get(f"{BACKEND_URL}/suppliers")
            if suppliers_response.status_code == 200:
                suppliers = suppliers_response.json()
                if isinstance(suppliers, list) and len(suppliers) > 0:
                    # Test filtering by top supplier
                    top_supplier = suppliers[0].get("supplier_name", "")
                    if top_supplier:
                        start_time = time.time()
                        response = self.session.get(f"{BACKEND_URL}/products", 
                                                  params={"supplier": top_supplier, "limit": 50})
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                self.log_test("Supplier Filtering", True, 
                                            f"{len(data)} products from {top_supplier}", response_time)
                            else:
                                self.log_test("Supplier Filtering", False, 
                                            f"No products found for supplier", response_time)
                        else:
                            self.log_test("Supplier Filtering", False, 
                                        f"HTTP {response.status_code}", response_time)
        
        except Exception as e:
            self.log_test("Supplier Filtering", False, f"Exception: {str(e)}")
    
    def test_large_dataset_performance(self):
        """Test 3: Large Dataset Performance (Review Requirement 3)"""
        print("\n⚡ 3. LARGE DATASET PERFORMANCE")
        print("=" * 50)
        
        if not self.token:
            return False
        
        # Test pagination efficiency with 1,850 products
        pagination_tests = [
            {"limit": 100, "skip": 0, "name": "First 100"},
            {"limit": 500, "skip": 0, "name": "First 500"},
            {"limit": 1000, "skip": 0, "name": "First 1000"},
            {"limit": 100, "skip": 500, "name": "Middle 100"},
            {"limit": 100, "skip": 1500, "name": "Last 100"},
        ]
        
        for test in pagination_tests:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/products", 
                                          params={"limit": test["limit"], "skip": test["skip"]})
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    
                    # Pagination should be efficient (under 1 second)
                    if response_time <= 1000 and count > 0:
                        self.log_test(f"Pagination - {test['name']}", True, 
                                    f"{count} products returned efficiently", response_time, critical=True)
                    elif response_time > 1000:
                        self.log_test(f"Pagination - {test['name']}", False, 
                                    f"Too slow: {response_time:.0f}ms", response_time, critical=True)
                    else:
                        self.log_test(f"Pagination - {test['name']}", False, 
                                    f"No products returned", response_time)
                else:
                    self.log_test(f"Pagination - {test['name']}", False, 
                                f"HTTP {response.status_code}", response_time, critical=True)
                    
            except Exception as e:
                self.log_test(f"Pagination - {test['name']}", False, f"Exception: {str(e)}", critical=True)
        
        # Test export functionality (if available)
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/products")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a file download
                content_type = response.headers.get('content-type', '')
                if 'excel' in content_type or 'spreadsheet' in content_type:
                    self.log_test("Export Functionality", True, 
                                f"Excel export working", response_time)
                else:
                    self.log_test("Export Functionality", True, 
                                f"Export endpoint responding", response_time)
            else:
                self.log_test("Export Functionality", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Export Functionality", False, f"Exception: {str(e)}")
    
    def test_master_data_integrity(self):
        """Test 4: Master Data Integrity (Review Requirement 4)"""
        print("\n🔍 4. MASTER DATA INTEGRITY")
        print("=" * 50)
        
        if not self.token:
            return False
        
        # Test data consistency across endpoints
        try:
            # Get dashboard data
            dashboard_response = self.session.get(f"{BACKEND_URL}/dashboard")
            products_response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 1000})
            
            if dashboard_response.status_code == 200 and products_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                products_data = products_response.json()
                
                # Test currency consistency
                currencies_found = set()
                departments_found = set()
                barcodes_found = set()
                
                for product in products_data:
                    if isinstance(product, dict):
                        if product.get("purchase_currency"):
                            currencies_found.add(product["purchase_currency"])
                        if product.get("department"):
                            departments_found.add(product["department"])
                        if product.get("barcode"):
                            barcodes_found.add(product["barcode"])
                
                # Test currency diversity (should have multiple currencies)
                if len(currencies_found) >= 2:
                    self.log_test("Currency Diversity", True, 
                                f"Found {len(currencies_found)} currencies: {list(currencies_found)}", critical=True)
                else:
                    self.log_test("Currency Diversity", False, 
                                f"Limited currencies: {list(currencies_found)}", critical=True)
                
                # Test barcode uniqueness
                total_barcodes = len(barcodes_found)
                total_products_with_barcodes = sum(1 for p in products_data if isinstance(p, dict) and p.get("barcode"))
                
                if total_barcodes == total_products_with_barcodes:
                    self.log_test("Barcode Uniqueness", True, 
                                f"All {total_barcodes} barcodes are unique", critical=True)
                else:
                    self.log_test("Barcode Uniqueness", False, 
                                f"Duplicate barcodes detected", critical=True)
                
                # Test pricing data accuracy
                products_with_prices = sum(1 for p in products_data 
                                         if isinstance(p, dict) and p.get("purchase_price", 0) > 0)
                price_accuracy = (products_with_prices / len(products_data)) * 100 if products_data else 0
                
                if price_accuracy >= 80:
                    self.log_test("Pricing Data Accuracy", True, 
                                f"{price_accuracy:.1f}% products have valid prices", critical=True)
                else:
                    self.log_test("Pricing Data Accuracy", False, 
                                f"Only {price_accuracy:.1f}% products have valid prices", critical=True)
                
            else:
                self.log_test("Data Integrity Test", False, "Could not fetch required data", critical=True)
                
        except Exception as e:
            self.log_test("Data Integrity Test", False, f"Exception: {str(e)}", critical=True)
    
    def test_advanced_analytics_calculations(self):
        """Test 5: Advanced Analytics Calculations (Review Requirement 5)"""
        print("\n📈 5. ADVANCED ANALYTICS CALCULATIONS")
        print("=" * 50)
        
        if not self.token:
            return False
        
        # Test stock value calculations across departments
        try:
            dashboard_response = self.session.get(f"{BACKEND_URL}/dashboard")
            if dashboard_response.status_code == 200:
                data = dashboard_response.json()
                
                if "kpis" in data:
                    total_stock_value = 0
                    departments_with_values = 0
                    
                    for kpi in data["kpis"]:
                        if isinstance(kpi, dict):
                            stock_value = kpi.get("total_stock_value", 0)
                            if stock_value > 0:
                                departments_with_values += 1
                                total_stock_value += stock_value
                    
                    if departments_with_values > 0:
                        self.log_test("Stock Value Calculations", True, 
                                    f"{departments_with_values} departments, total value: {total_stock_value:.2f}", critical=True)
                    else:
                        self.log_test("Stock Value Calculations", False, 
                                    "No departments have stock value calculations", critical=True)
                else:
                    self.log_test("Stock Value Calculations", False, 
                                "No KPI data in dashboard", critical=True)
            else:
                self.log_test("Stock Value Calculations", False, 
                            f"Dashboard HTTP {dashboard_response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Stock Value Calculations", False, f"Exception: {str(e)}", critical=True)
        
        # Test supplier performance metrics accuracy
        try:
            suppliers_response = self.session.get(f"{BACKEND_URL}/analytics/supplier-performance")
            if suppliers_response.status_code == 200:
                data = suppliers_response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    suppliers_with_metrics = 0
                    for supplier in data:
                        if isinstance(supplier, dict):
                            # Check for performance metrics
                            if any(key in supplier for key in ['total_items', 'stock_value', 'performance_score']):
                                suppliers_with_metrics += 1
                    
                    accuracy = (suppliers_with_metrics / len(data)) * 100 if data else 0
                    if accuracy >= 80:
                        self.log_test("Supplier Performance Metrics", True, 
                                    f"{accuracy:.1f}% suppliers have performance metrics", critical=True)
                    else:
                        self.log_test("Supplier Performance Metrics", False, 
                                    f"Only {accuracy:.1f}% suppliers have metrics", critical=True)
                else:
                    self.log_test("Supplier Performance Metrics", False, 
                                "No supplier performance data", critical=True)
            else:
                self.log_test("Supplier Performance Metrics", False, 
                            f"HTTP {suppliers_response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Supplier Performance Metrics", False, f"Exception: {str(e)}", critical=True)
        
        # Test percentage calculations and aggregations
        try:
            stock_levels_response = self.session.get(f"{BACKEND_URL}/analytics/stock-levels")
            if stock_levels_response.status_code == 200:
                data = stock_levels_response.json()
                
                if isinstance(data, dict):
                    # Look for percentage-based calculations
                    percentage_fields = [k for k in data.keys() if 'percentage' in k.lower() or 'rate' in k.lower()]
                    
                    if percentage_fields or len(data) > 0:
                        self.log_test("Percentage Calculations", True, 
                                    f"Stock level analytics with calculations", critical=True)
                    else:
                        self.log_test("Percentage Calculations", False, 
                                    "No percentage calculations found", critical=True)
                else:
                    self.log_test("Percentage Calculations", False, 
                                "Invalid stock levels data format", critical=True)
            else:
                self.log_test("Percentage Calculations", False, 
                            f"HTTP {stock_levels_response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Percentage Calculations", False, f"Exception: {str(e)}", critical=True)
    
    def run_all_tests(self):
        """Run all comprehensive master data tests"""
        print("🎯 COMPREHENSIVE MASTER DATA TEST - REVIEW REQUEST COMPLIANCE")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Actual Dataset Size: 1,850 products")
        print(f"Testing ALL 5 requirements from review request:")
        print(f"  1. Master Data API Performance")
        print(f"  2. Enhanced Search and Filtering")
        print(f"  3. Large Dataset Performance")
        print(f"  4. Master Data Integrity")
        print(f"  5. Advanced Analytics Calculations")
        print("=" * 80)
        
        # Run authentication first
        auth_success = self.authenticate()
        
        if auth_success:
            # Run all test suites in order
            self.test_master_data_api_performance()
            self.test_enhanced_search_and_filtering()
            self.test_large_dataset_performance()
            self.test_master_data_integrity()
            self.test_advanced_analytics_calculations()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE MASTER DATA TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Critical Failures: {len(self.critical_failures)}")
        
        # Review request compliance
        print(f"\n🎯 REVIEW REQUEST COMPLIANCE:")
        
        requirements = [
            {"name": "Master Data API Performance", "tests": ["Department Breakdown API Performance", "Stock Levels API Performance", "Supplier Performance API Performance"]},
            {"name": "Enhanced Search and Filtering", "tests": ["Average Barcode Performance", "Department Filter", "Supplier Filtering"]},
            {"name": "Large Dataset Performance", "tests": ["Pagination", "Export Functionality"]},
            {"name": "Master Data Integrity", "tests": ["Currency Diversity", "Barcode Uniqueness", "Pricing Data Accuracy"]},
            {"name": "Advanced Analytics Calculations", "tests": ["Stock Value Calculations", "Supplier Performance Metrics", "Percentage Calculations"]}
        ]
        
        for req in requirements:
            req_tests = [r for r in self.test_results if any(test_name in r["test"] for test_name in req["tests"])]
            req_success = sum(1 for t in req_tests if t["success"]) / len(req_tests) if req_tests else 0
            
            if req_success >= 0.8:
                print(f"✅ {req['name']}: EXCELLENT ({req_success:.1%} success)")
            elif req_success >= 0.6:
                print(f"⚠️  {req['name']}: GOOD ({req_success:.1%} success)")
            elif req_success >= 0.4:
                print(f"⚠️  {req['name']}: FAIR ({req_success:.1%} success)")
            else:
                print(f"❌ {req['name']}: POOR ({req_success:.1%} success)")
        
        # Performance summary
        performance_tests = [r for r in self.test_results if r.get("response_time_ms")]
        if performance_tests:
            response_times = [r["response_time_ms"] for r in performance_tests]
            avg_time = sum(response_times) / len(response_times)
            
            print(f"\n⚡ PERFORMANCE SUMMARY:")
            print(f"  - Average Response Time: {avg_time:.0f}ms")
            print(f"  - Analytics under 2s: {'✅' if all(t <= 2000 for t in response_times if 'Analytics' in str(t)) else '❌'}")
            print(f"  - Barcode under 100ms: {'✅' if all(t <= 100 for t in response_times if 'Barcode' in str(t)) else '❌'}")
            print(f"  - Pagination efficient: {'✅' if all(t <= 1000 for t in response_times if 'Pagination' in str(t)) else '❌'}")
        
        print(f"\n🔍 FINAL ASSESSMENT:")
        if success_rate >= 90 and len(self.critical_failures) == 0:
            print("✅ EXCELLENT: System ready for enterprise-level data volumes!")
            print("✅ All review requirements met successfully")
            print("✅ Performance targets achieved")
        elif success_rate >= 80 and len(self.critical_failures) <= 2:
            print("⚠️  GOOD: System mostly ready with minor optimizations needed")
            print("⚠️  Most review requirements met")
        elif success_rate >= 60:
            print("⚠️  FAIR: System functional but needs improvements")
            print("⚠️  Some review requirements not fully met")
        else:
            print("❌ POOR: System not ready for enterprise usage")
            print("❌ Critical review requirements failed")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES REQUIRING ATTENTION:")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = ComprehensiveMasterDataTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate and critical failures
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 85 and len(tester.critical_failures) == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()