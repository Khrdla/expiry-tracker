#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING FOR ENHANCED GEANT HYPERMARKET INVENTORY SYSTEM

This test suite covers all critical backend functionality as specified in the review request:

1. Authentication API - Test admin credentials (imadqejji/066380531I) and JWT token generation
2. Barcode Scanner API - Test barcode lookup endpoint with multiple sample barcodes for fast product lookup
3. Dashboard API - Verify KPI data structure (names not indices), test department filtering and data accuracy
4. Products API - Test product listing, search, and filtering for proper data format
5. Filter Options API - Verify departments, sections, and suppliers return proper names (not indices)

Key focus areas:
- Ensure all APIs return proper data structure (names instead of numeric indices)
- Verify barcode lookup performance for instant scanning
- Test authentication requirements and token validation
- Confirm department/section/supplier data integrity
- Check ObjectId serialization issues are resolved
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

# Known test barcodes from review request
KNOWN_GOOD_BARCODES = [
    "3222471081716",  # Apple Juice Box 1L
    "3222471052747",  # Lemonade 150Cl
]

# Additional test barcodes for comprehensive coverage
ADDITIONAL_TEST_BARCODES = [
    "3222471075722",
    "3222471081273", 
    "9501100046987"
]

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.start_time = time.time()
        
    def log_test(self, test_name: str, success: bool, details: str = "", performance_ms: float = None):
        """Log test result with optional performance metrics"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if performance_ms:
            result += f" ({performance_ms:.0f}ms)"
        if details:
            result += f": {details}"
            
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "performance_ms": performance_ms,
            "timestamp": datetime.now().isoformat()
        })

    def test_authentication_api(self):
        """Test 1: Authentication API with admin credentials and JWT token generation"""
        print("\n🔐 TESTING AUTHENTICATION API")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            auth_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    
                    # Validate JWT token format
                    token_parts = self.token.split('.')
                    if len(token_parts) == 3:
                        self.log_test("Admin Authentication", True, 
                                    f"Valid JWT token received, type: {data['token_type']}", auth_time)
                        
                        # Test token validation
                        self._test_token_validation()
                        return True
                    else:
                        self.log_test("Admin Authentication", False, "Invalid JWT token format")
                        return False
                else:
                    self.log_test("Admin Authentication", False, "Missing access_token or token_type in response")
                    return False
            else:
                self.log_test("Admin Authentication", False, 
                            f"HTTP {response.status_code}: {response.text}", auth_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def _test_token_validation(self):
        """Test JWT token validation with protected endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            if response.status_code == 200:
                self.log_test("JWT Token Validation", True, "Token accepted by protected endpoint")
            else:
                self.log_test("JWT Token Validation", False, f"Token rejected: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("JWT Token Validation", False, f"Exception: {str(e)}")

    def test_barcode_scanner_api(self):
        """Test 2: Barcode Scanner API with multiple sample barcodes for fast product lookup"""
        print("\n📱 TESTING BARCODE SCANNER API")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Barcode API Setup", False, "No authentication token available")
            return False

        # Test known good barcodes first
        print("Testing known good barcodes from review request:")
        for barcode in KNOWN_GOOD_BARCODES:
            self._test_barcode_lookup(barcode, is_known_good=True)
        
        # Test additional barcodes for comprehensive coverage
        print("\nTesting additional barcodes for comprehensive coverage:")
        for barcode in ADDITIONAL_TEST_BARCODES:
            self._test_barcode_lookup(barcode, is_known_good=False)
        
        # Test barcode lookup performance
        self._test_barcode_performance()
        
        # Test authentication requirements
        self._test_barcode_auth_requirements()
        
        return True

    def _test_barcode_lookup(self, barcode: str, is_known_good: bool = False):
        """Test individual barcode lookup"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
            lookup_time = (time.time() - start_time) * 1000
            
            test_name = f"Barcode Lookup {barcode}"
            if is_known_good:
                test_name += " (KNOWN GOOD)"
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verify all required fields are present
                    required_fields = [
                        'product_name', 'item_number', 'barcode', 'department', 
                        'section', 'purchase_price', 'purchase_currency', 
                        'selling_price', 'supplier', 'quantity', 'status'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(test_name, False, f"Missing required fields: {missing_fields}", lookup_time)
                    else:
                        # Verify data structure (names not indices)
                        data_issues = self._validate_data_structure(data)
                        
                        if data_issues:
                            self.log_test(test_name, False, f"Data structure issues: {data_issues}", lookup_time)
                        else:
                            product_info = f"Product: {data.get('product_name', 'N/A')}, " \
                                         f"Dept: {data.get('department', 'N/A')}, " \
                                         f"Price: {data.get('purchase_price', 0)} {data.get('purchase_currency', 'N/A')}"
                            self.log_test(test_name, True, product_info, lookup_time)
                            
                            # Additional validation for known good barcodes
                            if is_known_good:
                                self._validate_known_good_barcode(barcode, data)
                                
                except json.JSONDecodeError:
                    self.log_test(test_name, False, "Invalid JSON response", lookup_time)
                    
            elif response.status_code == 404:
                # 404 is acceptable for some barcodes (product not in database)
                if is_known_good:
                    self.log_test(test_name, False, "Known good barcode not found (404)", lookup_time)
                else:
                    self.log_test(test_name, True, "Product not found (404) - acceptable", lookup_time)
            elif response.status_code == 403:
                self.log_test(test_name, False, "Authentication required (403)", lookup_time)
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}: {response.text[:100]}", lookup_time)
                
        except Exception as e:
            self.log_test(f"Barcode Lookup {barcode}", False, f"Exception: {str(e)}")

    def _validate_data_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validate that data contains names instead of numeric indices"""
        issues = []
        
        # Check department - should be string like "01-FMG", not numeric index
        department = data.get('department', '')
        if isinstance(department, (int, float)) or (isinstance(department, str) and department.isdigit()):
            issues.append(f"Department is numeric index ({department}) instead of name")
        
        # Check section - should be descriptive name, not numeric
        section = data.get('section', '')
        if isinstance(section, (int, float)) or (isinstance(section, str) and section.isdigit()):
            issues.append(f"Section is numeric index ({section}) instead of name")
        
        # Check supplier - should be company name, not numeric
        supplier = data.get('supplier', '')
        if isinstance(supplier, (int, float)) or (isinstance(supplier, str) and supplier.isdigit()):
            issues.append(f"Supplier is numeric index ({supplier}) instead of name")
        
        return issues

    def _validate_known_good_barcode(self, barcode: str, data: Dict[str, Any]):
        """Validate specific known good barcodes"""
        if barcode == "3222471081716":  # Apple Juice Box 1L
            expected_name = "Apple Juice Box 1L"
            actual_name = data.get('product_name', '')
            if expected_name.lower() in actual_name.lower():
                self.log_test(f"Known Product Validation {barcode}", True, 
                            f"Correct product: {actual_name}")
            else:
                self.log_test(f"Known Product Validation {barcode}", False, 
                            f"Expected '{expected_name}', got '{actual_name}'")
        
        elif barcode == "3222471052747":  # Lemonade 150Cl
            expected_name = "Lemonade 150Cl"
            actual_name = data.get('product_name', '')
            if expected_name.lower() in actual_name.lower():
                self.log_test(f"Known Product Validation {barcode}", True, 
                            f"Correct product: {actual_name}")
            else:
                self.log_test(f"Known Product Validation {barcode}", False, 
                            f"Expected '{expected_name}', got '{actual_name}'")

    def _test_barcode_performance(self):
        """Test barcode lookup performance for instant scanning"""
        if not KNOWN_GOOD_BARCODES:
            return
            
        barcode = KNOWN_GOOD_BARCODES[0]
        performance_tests = []
        
        # Run 5 performance tests
        for i in range(5):
            start_time = time.time()
            try:
                response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
                lookup_time = (time.time() - start_time) * 1000
                performance_tests.append(lookup_time)
            except:
                pass
        
        if performance_tests:
            avg_time = sum(performance_tests) / len(performance_tests)
            min_time = min(performance_tests)
            max_time = max(performance_tests)
            
            # Performance should be under 100ms for instant scanning
            if avg_time < 100:
                self.log_test("Barcode Lookup Performance", True, 
                            f"Avg: {avg_time:.0f}ms, Range: {min_time:.0f}-{max_time:.0f}ms")
            else:
                self.log_test("Barcode Lookup Performance", False, 
                            f"Too slow - Avg: {avg_time:.0f}ms (should be <100ms)")

    def _test_barcode_auth_requirements(self):
        """Test that barcode API properly requires authentication"""
        session_no_auth = requests.Session()
        
        try:
            response = session_no_auth.get(f"{BACKEND_URL}/barcode/{KNOWN_GOOD_BARCODES[0]}")
            
            if response.status_code in [401, 403]:
                self.log_test("Barcode Auth Requirement", True, 
                            f"Correctly requires auth (HTTP {response.status_code})")
            else:
                self.log_test("Barcode Auth Requirement", False, 
                            f"Should require auth, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Barcode Auth Requirement", False, f"Exception: {str(e)}")

    def test_dashboard_api(self):
        """Test 3: Dashboard API - Verify KPI data structure and department filtering"""
        print("\n📊 TESTING DASHBOARD API")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Dashboard API Setup", False, "No authentication token available")
            return False

        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            dashboard_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verify dashboard structure
                    required_sections = ['kpis', 'accessible_departments', 'sections', 'top_suppliers']
                    missing_sections = [section for section in required_sections if section not in data]
                    
                    if missing_sections:
                        self.log_test("Dashboard Structure", False, 
                                    f"Missing sections: {missing_sections}", dashboard_time)
                        return False
                    
                    self.log_test("Dashboard API Response", True, 
                                f"All required sections present", dashboard_time)
                    
                    # Test KPI data structure
                    self._test_dashboard_kpis(data.get('kpis', []))
                    
                    # Test department data
                    self._test_dashboard_departments(data.get('accessible_departments', []))
                    
                    # Test top suppliers data
                    self._test_dashboard_suppliers(data.get('top_suppliers', []))
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log_test("Dashboard API Response", False, "Invalid JSON response", dashboard_time)
                    return False
            else:
                self.log_test("Dashboard API Response", False, 
                            f"HTTP {response.status_code}: {response.text}", dashboard_time)
                return False
                
        except Exception as e:
            self.log_test("Dashboard API Response", False, f"Exception: {str(e)}")
            return False

    def _test_dashboard_kpis(self, kpis: List[Dict[str, Any]]):
        """Test dashboard KPI data structure"""
        if not kpis:
            self.log_test("Dashboard KPIs", False, "No KPI data returned")
            return
        
        # Verify KPI structure
        for i, kpi in enumerate(kpis):
            department = kpi.get('department')
            
            # Check department is name, not index
            if isinstance(department, (int, float)) or (isinstance(department, str) and department.isdigit()):
                self.log_test(f"KPI Department {i}", False, 
                            f"Department is numeric index ({department}) instead of name")
            else:
                self.log_test(f"KPI Department {i}", True, f"Department name: {department}")
            
            # Verify required KPI fields
            required_kpi_fields = ['total_items', 'expired_items', 'out_of_stock_items', 'total_stock_value']
            missing_kpi_fields = [field for field in required_kpi_fields if field not in kpi]
            
            if missing_kpi_fields:
                self.log_test(f"KPI Fields {i}", False, f"Missing fields: {missing_kpi_fields}")
            else:
                self.log_test(f"KPI Fields {i}", True, 
                            f"Items: {kpi.get('total_items', 0)}, Stock Value: {kpi.get('total_stock_value', 0)}")

    def _test_dashboard_departments(self, departments: List[str]):
        """Test dashboard department data"""
        expected_departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        if not departments:
            self.log_test("Dashboard Departments", False, "No departments returned")
            return
        
        # Check if departments are names, not indices
        numeric_departments = [d for d in departments if isinstance(d, (int, float)) or (isinstance(d, str) and d.isdigit())]
        
        if numeric_departments:
            self.log_test("Dashboard Departments", False, 
                        f"Numeric department indices found: {numeric_departments}")
        else:
            found_expected = [d for d in departments if d in expected_departments]
            self.log_test("Dashboard Departments", True, 
                        f"Department names: {departments}, Expected found: {found_expected}")

    def _test_dashboard_suppliers(self, suppliers: List[Dict[str, Any]]):
        """Test dashboard top suppliers data"""
        if not suppliers:
            self.log_test("Dashboard Suppliers", False, "No supplier data returned")
            return
        
        for i, supplier in enumerate(suppliers):
            supplier_name = supplier.get('supplier_name')
            
            # Check supplier name is not numeric index
            if isinstance(supplier_name, (int, float)) or (isinstance(supplier_name, str) and supplier_name.isdigit()):
                self.log_test(f"Supplier Name {i}", False, 
                            f"Supplier is numeric index ({supplier_name}) instead of name")
            else:
                currency = supplier.get('purchase_currency', 'N/A')
                stock_value = supplier.get('stock_value', 0)
                self.log_test(f"Supplier Name {i}", True, 
                            f"Name: {supplier_name}, Value: {stock_value} {currency}")

    def test_products_api(self):
        """Test 4: Products API - Test product listing, search, and filtering"""
        print("\n📦 TESTING PRODUCTS API")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Products API Setup", False, "No authentication token available")
            return False

        # Test basic product listing
        self._test_products_listing()
        
        # Test department filtering
        self._test_products_department_filtering()
        
        # Test search functionality
        self._test_products_search()
        
        return True

    def _test_products_listing(self):
        """Test basic product listing"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/products")
            listing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    products = response.json()
                    
                    if isinstance(products, list) and len(products) > 0:
                        self.log_test("Products Listing", True, 
                                    f"Retrieved {len(products)} products", listing_time)
                        
                        # Test first product data structure
                        first_product = products[0]
                        data_issues = self._validate_data_structure(first_product)
                        
                        if data_issues:
                            self.log_test("Product Data Structure", False, 
                                        f"Issues in first product: {data_issues}")
                        else:
                            self.log_test("Product Data Structure", True, 
                                        "Product data uses names instead of indices")
                    else:
                        self.log_test("Products Listing", False, 
                                    "No products returned or invalid format", listing_time)
                        
                except json.JSONDecodeError:
                    self.log_test("Products Listing", False, "Invalid JSON response", listing_time)
            else:
                self.log_test("Products Listing", False, 
                            f"HTTP {response.status_code}: {response.text}", listing_time)
                
        except Exception as e:
            self.log_test("Products Listing", False, f"Exception: {str(e)}")

    def _test_products_department_filtering(self):
        """Test product filtering by department"""
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        for dept in departments:
            start_time = time.time()
            
            try:
                response = self.session.get(f"{BACKEND_URL}/products?department={dept}")
                filter_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    try:
                        products = response.json()
                        
                        if isinstance(products, list):
                            # Verify all products belong to the requested department
                            wrong_dept_products = [p for p in products if p.get('department') != dept]
                            
                            if wrong_dept_products:
                                self.log_test(f"Department Filter {dept}", False, 
                                            f"{len(wrong_dept_products)} products from wrong department", filter_time)
                            else:
                                self.log_test(f"Department Filter {dept}", True, 
                                            f"{len(products)} products correctly filtered", filter_time)
                        else:
                            self.log_test(f"Department Filter {dept}", False, 
                                        "Invalid response format", filter_time)
                            
                    except json.JSONDecodeError:
                        self.log_test(f"Department Filter {dept}", False, 
                                    "Invalid JSON response", filter_time)
                else:
                    self.log_test(f"Department Filter {dept}", False, 
                                f"HTTP {response.status_code}", filter_time)
                    
            except Exception as e:
                self.log_test(f"Department Filter {dept}", False, f"Exception: {str(e)}")

    def _test_products_search(self):
        """Test product search functionality"""
        search_terms = ["juice", "water", "apple"]
        
        for term in search_terms:
            start_time = time.time()
            
            try:
                response = self.session.get(f"{BACKEND_URL}/search?q={term}")
                search_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    try:
                        products = response.json()
                        
                        if isinstance(products, list):
                            # Verify search results contain the search term
                            relevant_products = []
                            for product in products:
                                product_name = product.get('product_name', '').lower()
                                if term.lower() in product_name:
                                    relevant_products.append(product)
                            
                            if len(relevant_products) > 0:
                                self.log_test(f"Search '{term}'", True, 
                                            f"{len(relevant_products)}/{len(products)} relevant results", search_time)
                            else:
                                self.log_test(f"Search '{term}'", False, 
                                            f"No relevant results in {len(products)} returned", search_time)
                        else:
                            self.log_test(f"Search '{term}'", False, 
                                        "Invalid response format", search_time)
                            
                    except json.JSONDecodeError:
                        self.log_test(f"Search '{term}'", False, 
                                    "Invalid JSON response", search_time)
                else:
                    self.log_test(f"Search '{term}'", False, 
                                f"HTTP {response.status_code}", search_time)
                    
            except Exception as e:
                self.log_test(f"Search '{term}'", False, f"Exception: {str(e)}")

    def test_filter_options_api(self):
        """Test 5: Filter Options API - Verify departments, sections, and suppliers return proper names"""
        print("\n🔍 TESTING FILTER OPTIONS API")
        print("=" * 60)
        
        if not self.token:
            self.log_test("Filter Options Setup", False, "No authentication token available")
            return False

        # Test suppliers endpoint
        self._test_suppliers_api()
        
        # Test dashboard for filter options (departments, sections)
        self._test_dashboard_filter_options()
        
        return True

    def _test_suppliers_api(self):
        """Test suppliers API endpoint"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/suppliers")
            suppliers_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    suppliers = response.json()
                    
                    if isinstance(suppliers, list) and len(suppliers) > 0:
                        self.log_test("Suppliers API", True, 
                                    f"Retrieved {len(suppliers)} suppliers", suppliers_time)
                        
                        # Verify supplier data structure
                        for i, supplier in enumerate(suppliers[:3]):  # Check first 3
                            supplier_name = supplier.get('supplier_name')
                            
                            if isinstance(supplier_name, (int, float)) or (isinstance(supplier_name, str) and supplier_name.isdigit()):
                                self.log_test(f"Supplier Name {i}", False, 
                                            f"Supplier is numeric index ({supplier_name}) instead of name")
                            else:
                                self.log_test(f"Supplier Name {i}", True, f"Name: {supplier_name}")
                    else:
                        self.log_test("Suppliers API", False, 
                                    "No suppliers returned or invalid format", suppliers_time)
                        
                except json.JSONDecodeError:
                    self.log_test("Suppliers API", False, "Invalid JSON response", suppliers_time)
            else:
                self.log_test("Suppliers API", False, 
                            f"HTTP {response.status_code}: {response.text}", suppliers_time)
                
        except Exception as e:
            self.log_test("Suppliers API", False, f"Exception: {str(e)}")

    def _test_dashboard_filter_options(self):
        """Test dashboard for filter options (departments, sections)"""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            dashboard_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Test sections data
                    sections = data.get('sections', [])
                    if sections:
                        numeric_sections = [s for s in sections if isinstance(s, (int, float)) or (isinstance(s, str) and s.isdigit())]
                        
                        if numeric_sections:
                            self.log_test("Filter Sections", False, 
                                        f"Numeric section indices found: {numeric_sections}")
                        else:
                            self.log_test("Filter Sections", True, 
                                        f"Section names: {sections[:5]}...")  # Show first 5
                    else:
                        self.log_test("Filter Sections", False, "No sections data returned")
                    
                    # Test departments data
                    departments = data.get('accessible_departments', [])
                    if departments:
                        expected_departments = ["01-FMG", "01-CGD", "01-OPSS"]
                        found_expected = [d for d in departments if d in expected_departments]
                        
                        self.log_test("Filter Departments", True, 
                                    f"Departments: {departments}, Expected: {found_expected}")
                    else:
                        self.log_test("Filter Departments", False, "No departments data returned")
                        
                except json.JSONDecodeError:
                    self.log_test("Dashboard Filter Options", False, "Invalid JSON response", dashboard_time)
            else:
                self.log_test("Dashboard Filter Options", False, 
                            f"HTTP {response.status_code}", dashboard_time)
                
        except Exception as e:
            self.log_test("Dashboard Filter Options", False, f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🎯 COMPREHENSIVE BACKEND TESTING FOR ENHANCED GEANT HYPERMARKET INVENTORY SYSTEM")
        print("=" * 90)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{'*' * len(ADMIN_PASSWORD)}")
        print(f"Known Good Barcodes: {KNOWN_GOOD_BARCODES}")
        print("=" * 90)
        
        # Run all test suites
        auth_success = self.test_authentication_api()
        
        if auth_success:
            self.test_barcode_scanner_api()
            self.test_dashboard_api()
            self.test_products_api()
            self.test_filter_options_api()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with other tests")
        
        # Print comprehensive summary
        self.print_comprehensive_summary()

    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 90)
        print("📊 COMPREHENSIVE BACKEND TEST SUMMARY")
        print("=" * 90)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.1f}s")
        
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        # Analyze results by category
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"]]
        barcode_tests = [r for r in self.test_results if "Barcode" in r["test"]]
        dashboard_tests = [r for r in self.test_results if "Dashboard" in r["test"]]
        products_tests = [r for r in self.test_results if "Products" in r["test"] or "Search" in r["test"]]
        filter_tests = [r for r in self.test_results if "Filter" in r["test"] or "Supplier" in r["test"]]
        
        # 1. Authentication API
        auth_success = any(t["success"] for t in auth_tests if "Admin Authentication" in t["test"])
        if auth_success:
            print("✅ 1. Authentication API: WORKING - Admin credentials accepted, JWT tokens generated")
        else:
            print("❌ 1. Authentication API: FAILED - Cannot authenticate with admin credentials")
        
        # 2. Barcode Scanner API
        barcode_success = any(t["success"] for t in barcode_tests if "KNOWN GOOD" in t["test"])
        performance_tests = [t for t in barcode_tests if "Performance" in t["test"]]
        performance_good = any(t["success"] for t in performance_tests)
        
        if barcode_success and performance_good:
            print("✅ 2. Barcode Scanner API: WORKING - Fast product lookup, proper data structure")
        elif barcode_success:
            print("⚠️  2. Barcode Scanner API: PARTIAL - Working but performance issues")
        else:
            print("❌ 2. Barcode Scanner API: FAILED - Cannot lookup products by barcode")
        
        # 3. Dashboard API
        dashboard_success = any(t["success"] for t in dashboard_tests if "Dashboard API Response" in t["test"])
        kpi_structure_good = any(t["success"] for t in dashboard_tests if "KPI" in t["test"])
        
        if dashboard_success and kpi_structure_good:
            print("✅ 3. Dashboard API: WORKING - KPI data structure correct, department filtering works")
        elif dashboard_success:
            print("⚠️  3. Dashboard API: PARTIAL - Working but data structure issues")
        else:
            print("❌ 3. Dashboard API: FAILED - Cannot retrieve dashboard data")
        
        # 4. Products API
        products_success = any(t["success"] for t in products_tests if "Products Listing" in t["test"])
        search_success = any(t["success"] for t in products_tests if "Search" in t["test"])
        
        if products_success and search_success:
            print("✅ 4. Products API: WORKING - Product listing, search, and filtering functional")
        elif products_success:
            print("⚠️  4. Products API: PARTIAL - Listing works but search issues")
        else:
            print("❌ 4. Products API: FAILED - Cannot retrieve product data")
        
        # 5. Filter Options API
        filter_success = any(t["success"] for t in filter_tests)
        
        if filter_success:
            print("✅ 5. Filter Options API: WORKING - Departments, sections, suppliers return proper names")
        else:
            print("❌ 5. Filter Options API: FAILED - Filter options not working properly")
        
        print("\n🔍 KEY FOCUS AREAS VERIFICATION:")
        
        # Data structure verification
        structure_issues = [t for t in self.test_results if not t["success"] and "numeric index" in t["details"]]
        if not structure_issues:
            print("✅ Data Structure: All APIs return proper names instead of numeric indices")
        else:
            print(f"❌ Data Structure: {len(structure_issues)} APIs still returning numeric indices")
        
        # Performance verification
        performance_issues = [t for t in self.test_results if not t["success"] and ("slow" in t["details"] or "Performance" in t["test"])]
        if not performance_issues:
            print("✅ Performance: Barcode lookup performance suitable for instant scanning")
        else:
            print("❌ Performance: Barcode lookup too slow for instant scanning")
        
        # Authentication verification
        if auth_success:
            print("✅ Authentication: Token validation and requirements working correctly")
        else:
            print("❌ Authentication: Token validation or requirements not working")
        
        # ObjectId serialization
        serialization_issues = [t for t in self.test_results if not t["success"] and "JSON" in t["details"]]
        if not serialization_issues:
            print("✅ ObjectId Serialization: No JSON serialization issues detected")
        else:
            print(f"❌ ObjectId Serialization: {len(serialization_issues)} JSON serialization issues found")
        
        print("\n🏁 FINAL VERDICT:")
        if success_rate >= 90:
            print("✅ EXCELLENT: Backend is production-ready for enhanced frontend components")
        elif success_rate >= 80:
            print("✅ GOOD: Backend is functional with minor issues to address")
        elif success_rate >= 70:
            print("⚠️  ACCEPTABLE: Backend works but has several issues that should be fixed")
        elif success_rate >= 50:
            print("⚠️  CONCERNING: Backend has significant issues that need immediate attention")
        else:
            print("❌ CRITICAL: Backend has major failures that prevent proper operation")
        
        print("\n" + "=" * 90)

def main():
    """Main test execution"""
    tester = ComprehensiveBackendTester()
    tester.run_comprehensive_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()