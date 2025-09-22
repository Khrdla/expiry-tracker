#!/usr/bin/env python3
"""
MASTER DATA PERFORMANCE TEST - Focused on actual dataset analysis

This test focuses on analyzing the actual master data that has been imported
and testing performance with the real dataset size and structure.
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://stock-genius-24.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class MasterDataPerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.dataset_stats = {}
        
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
    
    def analyze_dataset_size(self):
        """Analyze the actual dataset size and structure"""
        print("\n📊 DATASET ANALYSIS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Dataset Analysis Setup", False, "No authentication token")
            return False
        
        try:
            # Test different pagination sizes to estimate total dataset size
            test_limits = [100, 500, 1000, 2000, 5000]
            actual_counts = []
            
            for limit in test_limits:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/products", params={"limit": limit})
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    actual_counts.append(count)
                    
                    self.log_test(f"Dataset Size Test (limit={limit})", True, 
                                f"{count} products returned", response_time)
                    
                    # If we get less than requested, we've hit the limit
                    if count < limit:
                        estimated_total = count
                        self.dataset_stats['estimated_total_products'] = estimated_total
                        self.log_test("Total Dataset Size", True, 
                                    f"Estimated {estimated_total:,} total products")
                        break
                else:
                    self.log_test(f"Dataset Size Test (limit={limit})", False, 
                                f"HTTP {response.status_code}", response_time)
            
            # Test pagination at different offsets to verify large dataset handling
            if 'estimated_total_products' in self.dataset_stats:
                total = self.dataset_stats['estimated_total_products']
                
                # Test pagination at 25%, 50%, 75% of dataset
                test_offsets = [
                    int(total * 0.25),
                    int(total * 0.5),
                    int(total * 0.75)
                ]
                
                for offset in test_offsets:
                    if offset < total - 100:  # Ensure we have at least 100 items to fetch
                        start_time = time.time()
                        response = self.session.get(f"{BACKEND_URL}/products", 
                                                  params={"skip": offset, "limit": 100})
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            data = response.json()
                            count = len(data) if isinstance(data, list) else 0
                            
                            if count > 0:
                                self.log_test(f"Deep Pagination (offset={offset})", True, 
                                            f"{count} products at {offset/total:.0%} of dataset", response_time)
                            else:
                                self.log_test(f"Deep Pagination (offset={offset})", False, 
                                            f"No products returned at offset {offset}", response_time)
                        else:
                            self.log_test(f"Deep Pagination (offset={offset})", False, 
                                        f"HTTP {response.status_code}", response_time)
            
            return True
            
        except Exception as e:
            self.log_test("Dataset Analysis", False, f"Exception: {str(e)}")
            return False
    
    def analyze_data_distribution(self):
        """Analyze data distribution across departments, suppliers, etc."""
        print("\n📈 DATA DISTRIBUTION ANALYSIS")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Distribution Analysis Setup", False, "No authentication token")
            return False
        
        try:
            # Get a large sample of products to analyze distribution
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 2000})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                products = response.json()
                if isinstance(products, list) and len(products) > 0:
                    
                    # Analyze departments
                    departments = {}
                    suppliers = {}
                    sections = {}
                    currencies = {}
                    
                    for product in products:
                        if isinstance(product, dict):
                            # Department analysis
                            dept = product.get("department", "Unknown")
                            departments[dept] = departments.get(dept, 0) + 1
                            
                            # Supplier analysis
                            supplier = product.get("supplier", "Unknown")
                            suppliers[supplier] = suppliers.get(supplier, 0) + 1
                            
                            # Section analysis
                            section = product.get("section", "Unknown")
                            sections[section] = sections.get(section, 0) + 1
                            
                            # Currency analysis
                            currency = product.get("purchase_currency", "Unknown")
                            currencies[currency] = currencies.get(currency, 0) + 1
                    
                    # Store statistics
                    self.dataset_stats.update({
                        'departments': departments,
                        'suppliers': suppliers,
                        'sections': sections,
                        'currencies': currencies,
                        'sample_size': len(products)
                    })
                    
                    # Report findings
                    self.log_test("Data Distribution Analysis", True, 
                                f"Analyzed {len(products)} products", response_time)
                    
                    self.log_test("Department Distribution", True, 
                                f"{len(departments)} departments: {list(departments.keys())}")
                    
                    self.log_test("Supplier Distribution", True, 
                                f"{len(suppliers)} suppliers found")
                    
                    self.log_test("Section Distribution", True, 
                                f"{len(sections)} sections found")
                    
                    self.log_test("Currency Distribution", True, 
                                f"Currencies: {list(currencies.keys())}")
                    
                    return True
                else:
                    self.log_test("Data Distribution Analysis", False, 
                                "No products returned or invalid format", response_time)
                    return False
            else:
                self.log_test("Data Distribution Analysis", False, 
                            f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Data Distribution Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_department_performance(self):
        """Test performance of department-based queries"""
        print("\n🏢 DEPARTMENT PERFORMANCE TESTING")
        print("=" * 50)
        
        if not self.token or 'departments' not in self.dataset_stats:
            self.log_test("Department Performance Setup", False, "No data available")
            return False
        
        # Test each department found in the dataset
        for department, count in self.dataset_stats['departments'].items():
            if department != "Unknown" and count > 0:
                try:
                    start_time = time.time()
                    response = self.session.get(f"{BACKEND_URL}/products", 
                                              params={"department": department, "limit": 500})
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        returned_count = len(data) if isinstance(data, list) else 0
                        
                        # Verify department filtering accuracy
                        correct_dept_count = 0
                        for product in data:
                            if isinstance(product, dict) and product.get("department") == department:
                                correct_dept_count += 1
                        
                        accuracy = (correct_dept_count / returned_count * 100) if returned_count > 0 else 0
                        
                        if accuracy >= 95:  # 95% accuracy threshold
                            self.log_test(f"Department Filter - {department}", True, 
                                        f"{returned_count} products, {accuracy:.1f}% accurate", response_time)
                        else:
                            self.log_test(f"Department Filter - {department}", False, 
                                        f"Low accuracy: {accuracy:.1f}%", response_time)
                    else:
                        self.log_test(f"Department Filter - {department}", False, 
                                    f"HTTP {response.status_code}", response_time)
                        
                except Exception as e:
                    self.log_test(f"Department Filter - {department}", False, f"Exception: {str(e)}")
    
    def test_barcode_performance_with_real_data(self):
        """Test barcode lookup performance with actual barcodes from dataset"""
        print("\n🔍 BARCODE PERFORMANCE WITH REAL DATA")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Barcode Performance Setup", False, "No authentication token")
            return False
        
        try:
            # Get products with barcodes
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 100})
            if response.status_code == 200:
                products = response.json()
                test_barcodes = []
                
                # Collect barcodes from different departments
                for product in products:
                    if isinstance(product, dict) and product.get("barcode"):
                        barcode = str(product["barcode"]).strip()
                        if barcode and barcode != "0" and len(barcode) > 5:
                            test_barcodes.append({
                                'barcode': barcode,
                                'product_name': product.get('product_name', 'Unknown'),
                                'department': product.get('department', 'Unknown')
                            })
                            if len(test_barcodes) >= 15:  # Test with 15 barcodes
                                break
                
                if test_barcodes:
                    print(f"Testing barcode lookup with {len(test_barcodes)} real barcodes")
                    
                    successful_lookups = 0
                    total_response_time = 0
                    response_times = []
                    
                    for i, barcode_info in enumerate(test_barcodes):
                        barcode = barcode_info['barcode']
                        expected_name = barcode_info['product_name']
                        
                        try:
                            start_time = time.time()
                            lookup_response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
                            response_time = (time.time() - start_time) * 1000
                            total_response_time += response_time
                            response_times.append(response_time)
                            
                            if lookup_response.status_code == 200:
                                data = lookup_response.json()
                                returned_name = data.get('product_name', '')
                                
                                # Verify the correct product was returned
                                name_match = expected_name.lower() in returned_name.lower() or returned_name.lower() in expected_name.lower()
                                
                                if name_match and response_time <= 100:  # Under 100ms
                                    successful_lookups += 1
                                    self.log_test(f"Barcode Lookup #{i+1}", True, 
                                                f"Found: {returned_name[:30]}", response_time)
                                elif not name_match:
                                    self.log_test(f"Barcode Lookup #{i+1}", False, 
                                                f"Wrong product returned", response_time)
                                else:
                                    self.log_test(f"Barcode Lookup #{i+1}", False, 
                                                f"Too slow: {response_time:.0f}ms", response_time)
                            else:
                                self.log_test(f"Barcode Lookup #{i+1}", False, 
                                            f"HTTP {lookup_response.status_code}", response_time)
                                
                        except Exception as e:
                            self.log_test(f"Barcode Lookup #{i+1}", False, f"Exception: {str(e)}")
                    
                    # Performance summary
                    if response_times:
                        avg_time = sum(response_times) / len(response_times)
                        min_time = min(response_times)
                        max_time = max(response_times)
                        
                        self.log_test("Barcode Performance Summary", True, 
                                    f"Avg: {avg_time:.0f}ms, Min: {min_time:.0f}ms, Max: {max_time:.0f}ms")
                        
                        # Success rate
                        success_rate = (successful_lookups / len(test_barcodes)) * 100
                        if success_rate >= 80:
                            self.log_test("Barcode Success Rate", True, f"{success_rate:.1f}% success rate")
                        else:
                            self.log_test("Barcode Success Rate", False, f"Only {success_rate:.1f}% success rate")
                else:
                    self.log_test("Barcode Performance Test", False, "No valid barcodes found in dataset")
            else:
                self.log_test("Barcode Performance Setup", False, "Could not fetch products for barcode testing")
                
        except Exception as e:
            self.log_test("Barcode Performance Test", False, f"Exception: {str(e)}")
    
    def test_search_performance(self):
        """Test search performance with various queries"""
        print("\n🔎 SEARCH PERFORMANCE")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Search Performance Setup", False, "No authentication token")
            return False
        
        # Test search with different query types
        search_queries = [
            {"query": "water", "type": "common_product"},
            {"query": "juice", "type": "beverage"},
            {"query": "milk", "type": "dairy"},
            {"query": "bread", "type": "bakery"},
            {"query": "apple", "type": "fruit"},
            {"query": "chocolate", "type": "confectionery"}
        ]
        
        for search_test in search_queries:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/search", 
                                          params={"q": search_test["query"], "limit": 50})
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data) if isinstance(data, list) else 0
                    
                    if result_count > 0:
                        # Check search relevance
                        relevant_count = 0
                        for product in data:
                            if isinstance(product, dict):
                                product_name = product.get("product_name", "").lower()
                                if search_test["query"].lower() in product_name:
                                    relevant_count += 1
                        
                        relevance = (relevant_count / result_count) * 100 if result_count > 0 else 0
                        
                        if relevance >= 50 and response_time <= 500:  # 50% relevance, under 500ms
                            self.log_test(f"Search - {search_test['type']}", True, 
                                        f"{result_count} results, {relevance:.1f}% relevant", response_time)
                        elif relevance < 50:
                            self.log_test(f"Search - {search_test['type']}", False, 
                                        f"Low relevance: {relevance:.1f}%", response_time)
                        else:
                            self.log_test(f"Search - {search_test['type']}", False, 
                                        f"Too slow: {response_time:.0f}ms", response_time)
                    else:
                        self.log_test(f"Search - {search_test['type']}", False, 
                                    f"No results for '{search_test['query']}'", response_time)
                else:
                    self.log_test(f"Search - {search_test['type']}", False, 
                                f"HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Search - {search_test['type']}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all master data performance tests"""
        print("🎯 MASTER DATA PERFORMANCE TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing actual dataset size and performance")
        print("=" * 80)
        
        # Run authentication first
        auth_success = self.authenticate()
        
        if auth_success:
            # Run all test suites
            self.analyze_dataset_size()
            self.analyze_data_distribution()
            self.test_department_performance()
            self.test_barcode_performance_with_real_data()
            self.test_search_performance()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 MASTER DATA PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Dataset statistics
        if self.dataset_stats:
            print(f"\n📊 DATASET STATISTICS:")
            if 'estimated_total_products' in self.dataset_stats:
                print(f"  - Total Products: {self.dataset_stats['estimated_total_products']:,}")
            if 'departments' in self.dataset_stats:
                print(f"  - Departments: {len(self.dataset_stats['departments'])}")
                for dept, count in self.dataset_stats['departments'].items():
                    print(f"    • {dept}: {count:,} products")
            if 'suppliers' in self.dataset_stats:
                print(f"  - Suppliers: {len(self.dataset_stats['suppliers'])}")
            if 'sections' in self.dataset_stats:
                print(f"  - Sections: {len(self.dataset_stats['sections'])}")
            if 'currencies' in self.dataset_stats:
                print(f"  - Currencies: {list(self.dataset_stats['currencies'].keys())}")
        
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if success_rate >= 85:
            print("✅ EXCELLENT: System handles master data efficiently")
            print("✅ Ready for enterprise-level usage")
        elif success_rate >= 70:
            print("⚠️  GOOD: System mostly ready with minor optimizations needed")
        elif success_rate >= 50:
            print("⚠️  FAIR: System functional but needs improvements")
        else:
            print("❌ POOR: System needs significant optimization")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = MasterDataPerformanceTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()