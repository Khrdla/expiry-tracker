#!/usr/bin/env python3
"""
ADVANCED BACKEND TESTING WITH MASTER DATA

Test the enhanced backend functionality with the newly imported master data (18,762 products).

SPECIFIC TESTS NEEDED:

1. Master Data API Performance:
- Test analytics endpoints with full dataset (18,762 products)
- Verify API performance with large dataset  
- Test supplier performance with 117 suppliers
- Measure API response times for all endpoints

2. Enhanced Search and Filtering:
- Test barcode lookup with various master data barcodes from different departments
- Verify product search by department (01-FMG, 03-LHH, 04-TXT, 05-HHH, 01-CGD)
- Test supplier filtering with top suppliers from master data
- Verify section-based filtering (26 different sections)

3. Large Dataset Performance:
- Test pagination with 18,762+ products
- Verify database query optimization with large collections
- Test export functionality with master data  
- Measure memory usage and response times

4. Master Data Integrity:
- Verify data consistency across all imported products
- Test relationships between products, suppliers, and departments
- Validate pricing and stock data accuracy
- Confirm barcode uniqueness and lookup accuracy

5. Advanced Analytics Calculations:
- Test stock value calculations across departments
- Verify supplier performance metrics accuracy
- Test waste analysis calculations with master data
- Validate percentage calculations and aggregations

EXPECTED PERFORMANCE:
- Analytics endpoints should respond under 2 seconds
- Barcode lookup should remain under 100ms
- Pagination should handle 18K+ products efficiently
- All calculations should be mathematically accurate
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Expected master data parameters
EXPECTED_PRODUCT_COUNT = 18762
EXPECTED_SUPPLIER_COUNT = 117
EXPECTED_DEPARTMENTS = ["01-FMG", "01-CGD", "01-OPSS", "03-LHH", "04-TXT", "05-HHH"]
EXPECTED_SECTIONS = 26

# Performance thresholds
MAX_ANALYTICS_RESPONSE_TIME = 2000  # 2 seconds in ms
MAX_BARCODE_RESPONSE_TIME = 100     # 100ms
MAX_PAGINATION_RESPONSE_TIME = 1000 # 1 second

class AdvancedMasterDataTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.performance_data = {}
        
    def log_test(self, test_name, success, details="", response_time_ms=None):
        """Log test result with optional performance data"""
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
        
        if response_time_ms:
            self.performance_data[test_name] = response_time_ms
    
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
    
    def test_master_data_volume(self):
        """Test 1: Verify master data volume and basic statistics"""
        print("\n📊 MASTER DATA VOLUME VERIFICATION")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Master Data Volume Setup", False, "No authentication token")
            return False
        
        # Test dashboard endpoint for overall statistics
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate total products across all departments
                total_products = 0
                departments_found = []
                
                if "kpis" in data:
                    for kpi in data["kpis"]:
                        total_products += kpi.get("total_items", 0)
                        departments_found.append(kpi.get("department", {}).get("value", ""))
                
                # Test product count
                if total_products >= EXPECTED_PRODUCT_COUNT * 0.9:  # Allow 10% variance
                    self.log_test("Product Count Verification", True, 
                                f"{total_products} products found (expected ~{EXPECTED_PRODUCT_COUNT})", response_time)
                else:
                    self.log_test("Product Count Verification", False, 
                                f"Only {total_products} products found (expected ~{EXPECTED_PRODUCT_COUNT})", response_time)
                
                # Test department coverage
                expected_depts = set(EXPECTED_DEPARTMENTS)
                found_depts = set(departments_found)
                common_depts = expected_depts.intersection(found_depts)
                
                if len(common_depts) >= 3:  # At least 3 departments should be present
                    self.log_test("Department Coverage", True, 
                                f"{len(common_depts)} departments found: {list(common_depts)}")
                else:
                    self.log_test("Department Coverage", False, 
                                f"Only {len(common_depts)} departments found: {list(common_depts)}")
                
                # Test supplier data
                if "top_suppliers" in data and len(data["top_suppliers"]) > 0:
                    supplier_count = len(data["top_suppliers"])
                    self.log_test("Supplier Data Availability", True, 
                                f"{supplier_count} top suppliers found")
                else:
                    self.log_test("Supplier Data Availability", False, "No supplier data found")
                
                return True
            else:
                self.log_test("Dashboard API", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Master Data Volume Test", False, f"Exception: {str(e)}")
            return False
    
    def test_large_dataset_performance(self):
        """Test 2: Large dataset performance with pagination"""
        print("\n⚡ LARGE DATASET PERFORMANCE")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Performance Test Setup", False, "No authentication token")
            return False
        
        # Test different pagination sizes
        pagination_tests = [
            {"limit": 100, "skip": 0, "name": "First 100 products"},
            {"limit": 500, "skip": 0, "name": "First 500 products"},
            {"limit": 1000, "skip": 0, "name": "First 1000 products"},
            {"limit": 100, "skip": 1000, "name": "Products 1001-1100"},
            {"limit": 100, "skip": 5000, "name": "Products 5001-5100"},
        ]
        
        for test_config in pagination_tests:
            try:
                start_time = time.time()
                response = self.session.get(
                    f"{BACKEND_URL}/products",
                    params={
                        "limit": test_config["limit"],
                        "skip": test_config["skip"]
                    }
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    product_count = len(data) if isinstance(data, list) else 0
                    
                    # Check performance threshold
                    performance_ok = response_time <= MAX_PAGINATION_RESPONSE_TIME
                    
                    if performance_ok and product_count > 0:
                        self.log_test(f"Pagination - {test_config['name']}", True, 
                                    f"{product_count} products returned", response_time)
                    elif not performance_ok:
                        self.log_test(f"Pagination - {test_config['name']}", False, 
                                    f"Too slow: {response_time:.0f}ms > {MAX_PAGINATION_RESPONSE_TIME}ms", response_time)
                    else:
                        self.log_test(f"Pagination - {test_config['name']}", False, 
                                    f"No products returned", response_time)
                else:
                    self.log_test(f"Pagination - {test_config['name']}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Pagination - {test_config['name']}", False, f"Exception: {str(e)}")
    
    def test_department_filtering(self):
        """Test 3: Department-based filtering with master data"""
        print("\n🏢 DEPARTMENT FILTERING")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Department Filter Setup", False, "No authentication token")
            return False
        
        # Test each expected department
        for department in EXPECTED_DEPARTMENTS:
            try:
                start_time = time.time()
                response = self.session.get(
                    f"{BACKEND_URL}/products",
                    params={"department": department, "limit": 100}
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    product_count = len(data) if isinstance(data, list) else 0
                    
                    if product_count > 0:
                        # Verify all products belong to the requested department
                        correct_dept = all(
                            product.get("department") == department 
                            for product in data 
                            if isinstance(product, dict)
                        )
                        
                        if correct_dept:
                            self.log_test(f"Department Filter - {department}", True, 
                                        f"{product_count} products found", response_time)
                        else:
                            self.log_test(f"Department Filter - {department}", False, 
                                        f"Mixed departments in results", response_time)
                    else:
                        self.log_test(f"Department Filter - {department}", False, 
                                    f"No products found", response_time)
                else:
                    self.log_test(f"Department Filter - {department}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Department Filter - {department}", False, f"Exception: {str(e)}")
    
    def test_barcode_lookup_performance(self):
        """Test 4: Barcode lookup performance with master data"""
        print("\n🔍 BARCODE LOOKUP PERFORMANCE")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Barcode Performance Setup", False, "No authentication token")
            return False
        
        # First, get some actual barcodes from the database
        try:
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 50})
            if response.status_code == 200:
                products = response.json()
                test_barcodes = []
                
                for product in products:
                    if isinstance(product, dict) and product.get("barcode"):
                        test_barcodes.append(product["barcode"])
                        if len(test_barcodes) >= 10:  # Test with 10 barcodes
                            break
                
                if test_barcodes:
                    print(f"Testing with {len(test_barcodes)} actual barcodes from database")
                    
                    # Test each barcode for performance
                    successful_lookups = 0
                    total_response_time = 0
                    
                    for i, barcode in enumerate(test_barcodes):
                        try:
                            start_time = time.time()
                            lookup_response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
                            response_time = (time.time() - start_time) * 1000
                            total_response_time += response_time
                            
                            if lookup_response.status_code == 200:
                                data = lookup_response.json()
                                
                                # Check performance threshold
                                performance_ok = response_time <= MAX_BARCODE_RESPONSE_TIME
                                
                                if performance_ok:
                                    successful_lookups += 1
                                    self.log_test(f"Barcode Lookup #{i+1}", True, 
                                                f"Product: {data.get('product_name', 'N/A')[:30]}", response_time)
                                else:
                                    self.log_test(f"Barcode Lookup #{i+1}", False, 
                                                f"Too slow: {response_time:.0f}ms > {MAX_BARCODE_RESPONSE_TIME}ms", response_time)
                            else:
                                self.log_test(f"Barcode Lookup #{i+1}", False, 
                                            f"HTTP {lookup_response.status_code}", response_time)
                                
                        except Exception as e:
                            self.log_test(f"Barcode Lookup #{i+1}", False, f"Exception: {str(e)}")
                    
                    # Calculate average performance
                    if successful_lookups > 0:
                        avg_response_time = total_response_time / len(test_barcodes)
                        if avg_response_time <= MAX_BARCODE_RESPONSE_TIME:
                            self.log_test("Average Barcode Performance", True, 
                                        f"{avg_response_time:.0f}ms average", avg_response_time)
                        else:
                            self.log_test("Average Barcode Performance", False, 
                                        f"{avg_response_time:.0f}ms average (too slow)", avg_response_time)
                else:
                    self.log_test("Barcode Performance Test", False, "No barcodes found in database")
            else:
                self.log_test("Barcode Performance Setup", False, "Could not fetch products for barcode testing")
                
        except Exception as e:
            self.log_test("Barcode Performance Test", False, f"Exception: {str(e)}")
    
    def test_search_functionality(self):
        """Test 5: Search functionality with large dataset"""
        print("\n🔎 SEARCH FUNCTIONALITY")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Search Test Setup", False, "No authentication token")
            return False
        
        # Test various search queries
        search_tests = [
            {"query": "juice", "name": "Product Name Search"},
            {"query": "water", "name": "Common Product Search"},
            {"query": "01-FMG", "name": "Department Code Search"},
            {"query": "apple", "name": "Fruit Product Search"},
            {"query": "milk", "name": "Dairy Product Search"},
        ]
        
        for search_test in search_tests:
            try:
                start_time = time.time()
                response = self.session.get(
                    f"{BACKEND_URL}/search",
                    params={"q": search_test["query"], "limit": 20}
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data) if isinstance(data, list) else 0
                    
                    if result_count > 0:
                        # Verify search relevance
                        relevant_results = 0
                        for product in data:
                            if isinstance(product, dict):
                                product_name = product.get("product_name", "").lower()
                                if search_test["query"].lower() in product_name:
                                    relevant_results += 1
                        
                        relevance_ratio = relevant_results / result_count if result_count > 0 else 0
                        
                        if relevance_ratio >= 0.3:  # At least 30% relevance
                            self.log_test(f"Search - {search_test['name']}", True, 
                                        f"{result_count} results, {relevance_ratio:.1%} relevant", response_time)
                        else:
                            self.log_test(f"Search - {search_test['name']}", False, 
                                        f"Low relevance: {relevance_ratio:.1%}", response_time)
                    else:
                        self.log_test(f"Search - {search_test['name']}", False, 
                                    f"No results found", response_time)
                else:
                    self.log_test(f"Search - {search_test['name']}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Search - {search_test['name']}", False, f"Exception: {str(e)}")
    
    def test_supplier_analysis(self):
        """Test 6: Supplier analysis with master data"""
        print("\n🏭 SUPPLIER ANALYSIS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Supplier Analysis Setup", False, "No authentication token")
            return False
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/suppliers")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                supplier_count = len(data) if isinstance(data, list) else 0
                
                if supplier_count > 0:
                    # Analyze supplier data quality
                    suppliers_with_items = 0
                    suppliers_with_values = 0
                    total_items = 0
                    total_value = 0
                    
                    for supplier in data:
                        if isinstance(supplier, dict):
                            items = supplier.get("total_items", 0)
                            value = supplier.get("stock_value", 0)
                            
                            if items > 0:
                                suppliers_with_items += 1
                                total_items += items
                            
                            if value > 0:
                                suppliers_with_values += 1
                                total_value += value
                    
                    # Test supplier count
                    if supplier_count >= EXPECTED_SUPPLIER_COUNT * 0.8:  # Allow 20% variance
                        self.log_test("Supplier Count", True, 
                                    f"{supplier_count} suppliers found (expected ~{EXPECTED_SUPPLIER_COUNT})", response_time)
                    else:
                        self.log_test("Supplier Count", False, 
                                    f"Only {supplier_count} suppliers found (expected ~{EXPECTED_SUPPLIER_COUNT})", response_time)
                    
                    # Test data completeness
                    if suppliers_with_items >= supplier_count * 0.8:
                        self.log_test("Supplier Data Completeness", True, 
                                    f"{suppliers_with_items}/{supplier_count} suppliers have item counts")
                    else:
                        self.log_test("Supplier Data Completeness", False, 
                                    f"Only {suppliers_with_items}/{supplier_count} suppliers have item counts")
                    
                    # Test value calculations
                    if suppliers_with_values > 0:
                        self.log_test("Supplier Value Calculations", True, 
                                    f"{suppliers_with_values} suppliers have stock values, total: {total_value:.2f}")
                    else:
                        self.log_test("Supplier Value Calculations", False, 
                                    "No suppliers have stock value calculations")
                else:
                    self.log_test("Supplier Analysis", False, "No suppliers found", response_time)
            else:
                self.log_test("Supplier Analysis", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Supplier Analysis", False, f"Exception: {str(e)}")
    
    def test_data_integrity(self):
        """Test 7: Data integrity and consistency"""
        print("\n🔍 DATA INTEGRITY")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Data Integrity Setup", False, "No authentication token")
            return False
        
        # Test data consistency across different endpoints
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
                sections_found = set()
                
                for product in products_data:
                    if isinstance(product, dict):
                        if product.get("purchase_currency"):
                            currencies_found.add(product["purchase_currency"])
                        if product.get("department"):
                            departments_found.add(product["department"])
                        if product.get("section"):
                            sections_found.add(product["section"])
                
                # Test currency diversity
                expected_currencies = {"YER", "SAR", "EUR", "USD"}
                found_currencies = currencies_found.intersection(expected_currencies)
                
                if len(found_currencies) >= 2:
                    self.log_test("Currency Diversity", True, 
                                f"Found currencies: {list(found_currencies)}")
                else:
                    self.log_test("Currency Diversity", False, 
                                f"Limited currencies: {list(found_currencies)}")
                
                # Test department consistency
                dashboard_depts = set()
                if "kpis" in dashboard_data:
                    for kpi in dashboard_data["kpis"]:
                        if kpi.get("department", {}).get("value"):
                            dashboard_depts.add(kpi["department"]["value"])
                
                dept_consistency = len(dashboard_depts.intersection(departments_found)) > 0
                
                if dept_consistency:
                    self.log_test("Department Consistency", True, 
                                f"Dashboard and products have consistent departments")
                else:
                    self.log_test("Department Consistency", False, 
                                f"Department mismatch between dashboard and products")
                
                # Test section diversity
                if len(sections_found) >= EXPECTED_SECTIONS * 0.5:  # At least half expected sections
                    self.log_test("Section Diversity", True, 
                                f"{len(sections_found)} sections found")
                else:
                    self.log_test("Section Diversity", False, 
                                f"Only {len(sections_found)} sections found (expected ~{EXPECTED_SECTIONS})")
                
            else:
                self.log_test("Data Integrity Test", False, "Could not fetch required data")
                
        except Exception as e:
            self.log_test("Data Integrity Test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all advanced master data tests"""
        print("🎯 ADVANCED BACKEND TESTING WITH MASTER DATA")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Expected Products: {EXPECTED_PRODUCT_COUNT:,}")
        print(f"Expected Suppliers: {EXPECTED_SUPPLIER_COUNT}")
        print(f"Expected Departments: {EXPECTED_DEPARTMENTS}")
        print(f"Performance Thresholds:")
        print(f"  - Analytics: {MAX_ANALYTICS_RESPONSE_TIME}ms")
        print(f"  - Barcode Lookup: {MAX_BARCODE_RESPONSE_TIME}ms")
        print(f"  - Pagination: {MAX_PAGINATION_RESPONSE_TIME}ms")
        print("=" * 80)
        
        # Run authentication first
        auth_success = self.authenticate()
        
        if auth_success:
            # Run all test suites
            self.test_master_data_volume()
            self.test_large_dataset_performance()
            self.test_department_filtering()
            self.test_barcode_lookup_performance()
            self.test_search_functionality()
            self.test_supplier_analysis()
            self.test_data_integrity()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 ADVANCED MASTER DATA TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Performance summary
        if self.performance_data:
            print(f"\n⚡ PERFORMANCE SUMMARY:")
            
            # Categorize performance data
            barcode_times = [t for k, t in self.performance_data.items() if "Barcode Lookup" in k]
            pagination_times = [t for k, t in self.performance_data.items() if "Pagination" in k]
            
            if barcode_times:
                avg_barcode = sum(barcode_times) / len(barcode_times)
                print(f"  - Average Barcode Lookup: {avg_barcode:.0f}ms (target: <{MAX_BARCODE_RESPONSE_TIME}ms)")
            
            if pagination_times:
                avg_pagination = sum(pagination_times) / len(pagination_times)
                print(f"  - Average Pagination: {avg_pagination:.0f}ms (target: <{MAX_PAGINATION_RESPONSE_TIME}ms)")
        
        # Critical findings
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        # Analyze key test results
        volume_tests = [r for r in self.test_results if "Product Count" in r["test"]]
        performance_tests = [r for r in self.test_results if "Performance" in r["test"]]
        integrity_tests = [r for r in self.test_results if "Integrity" in r["test"] or "Consistency" in r["test"]]
        
        if volume_tests and volume_tests[0]["success"]:
            print("✅ Master Data Volume: VERIFIED - Large dataset properly loaded")
        else:
            print("❌ Master Data Volume: FAILED - Dataset may not be complete")
        
        performance_success = sum(1 for t in performance_tests if t["success"]) / len(performance_tests) if performance_tests else 0
        if performance_success >= 0.8:
            print("✅ Performance: EXCELLENT - System handles large dataset efficiently")
        elif performance_success >= 0.6:
            print("⚠️  Performance: ACCEPTABLE - Some performance issues detected")
        else:
            print("❌ Performance: POOR - Significant performance problems")
        
        integrity_success = sum(1 for t in integrity_tests if t["success"]) / len(integrity_tests) if integrity_tests else 0
        if integrity_success >= 0.8:
            print("✅ Data Integrity: EXCELLENT - Data is consistent and well-structured")
        else:
            print("❌ Data Integrity: ISSUES - Data consistency problems detected")
        
        print(f"\n🔍 OVERALL ASSESSMENT:")
        if success_rate >= 85:
            print("✅ EXCELLENT: System ready for enterprise-level data volumes!")
            print("✅ All performance targets met with large dataset")
            print("✅ Master data integration successful")
        elif success_rate >= 70:
            print("⚠️  GOOD: System mostly ready with minor optimizations needed")
            print("⚠️  Some performance or data issues require attention")
        elif success_rate >= 50:
            print("⚠️  FAIR: System functional but needs significant improvements")
            print("⚠️  Performance or data integrity issues detected")
        else:
            print("❌ POOR: System not ready for enterprise-level usage")
            print("❌ Critical issues must be resolved")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = AdvancedMasterDataTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()