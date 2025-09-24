#!/usr/bin/env python3
"""
FILTERS API DEBUG TEST - Why are departments showing as "Department 1", "Department 2"?

This test specifically debugs the filters API issue where departments, sections, 
and suppliers are showing as numeric indices instead of actual names after new data upload.

Test Coverage:
1. Test Filters API endpoint and examine exact response structure
2. Check raw data in database for departments, sections, suppliers
3. Validate data types (strings, numbers, objects, arrays)
4. Sample products check to examine field values
5. Compare expected vs actual filter data

Admin credentials: imadqejji/066380531I
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FiltersDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.debug_data = {}
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
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
                    self.log_test("Admin Login", True, f"Token received successfully")
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
    
    def test_filters_api_endpoint(self):
        """Test 2: Call /api/filters endpoint and examine exact response structure"""
        print("\n🔍 TESTING FILTERS API ENDPOINT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Filters API Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/filters")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.debug_data['filters_response'] = data
                    
                    print(f"\n📋 FILTERS API RESPONSE STRUCTURE:")
                    print(json.dumps(data, indent=2))
                    
                    # Check if filters endpoint exists and what it returns
                    if isinstance(data, dict):
                        departments = data.get('departments', [])
                        sections = data.get('sections', [])
                        suppliers = data.get('suppliers', [])
                        
                        self.log_test("Filters API Response", True, f"Departments: {len(departments)}, Sections: {len(sections)}, Suppliers: {len(suppliers)}")
                        
                        # Examine department data structure
                        if departments:
                            print(f"\n🏢 DEPARTMENTS DATA:")
                            for i, dept in enumerate(departments[:5]):  # Show first 5
                                print(f"  [{i}] {dept} (Type: {type(dept).__name__})")
                                
                        # Examine sections data structure  
                        if sections:
                            print(f"\n📂 SECTIONS DATA:")
                            for i, section in enumerate(sections[:5]):  # Show first 5
                                print(f"  [{i}] {section} (Type: {type(section).__name__})")
                                
                        # Examine suppliers data structure
                        if suppliers:
                            print(f"\n🏭 SUPPLIERS DATA:")
                            for i, supplier in enumerate(suppliers[:5]):  # Show first 5
                                print(f"  [{i}] {supplier} (Type: {type(supplier).__name__})")
                        
                        return True
                    else:
                        self.log_test("Filters API Response", False, f"Unexpected response type: {type(data)}")
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test("Filters API Response", False, "Invalid JSON response")
                    return False
                    
            elif response.status_code == 404:
                self.log_test("Filters API Endpoint", False, "Filters endpoint not found (404) - may not be implemented")
                return False
            else:
                self.log_test("Filters API Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Filters API Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_dashboard_api_for_filter_data(self):
        """Test 3: Check dashboard API for department/section data"""
        print("\n📊 TESTING DASHBOARD API FOR FILTER DATA")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Dashboard API Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.debug_data['dashboard_response'] = data
                    
                    # Extract department information from KPIs
                    kpis = data.get('kpis', [])
                    departments_from_kpis = []
                    
                    print(f"\n📈 DASHBOARD KPI DEPARTMENTS:")
                    for kpi in kpis:
                        dept = kpi.get('department')
                        departments_from_kpis.append(dept)
                        print(f"  Department: {dept} (Type: {type(dept).__name__})")
                        print(f"    Total Items: {kpi.get('total_items', 0)}")
                        print(f"    Stock Value: {kpi.get('total_stock_value', 0)}")
                    
                    # Check sections from dashboard
                    sections = data.get('sections', [])
                    print(f"\n📂 DASHBOARD SECTIONS:")
                    for i, section in enumerate(sections[:10]):  # Show first 10
                        print(f"  [{i}] {section} (Type: {type(section).__name__})")
                    
                    # Check top suppliers
                    top_suppliers = data.get('top_suppliers', [])
                    print(f"\n🏭 DASHBOARD TOP SUPPLIERS:")
                    for supplier in top_suppliers[:5]:  # Show first 5
                        supplier_name = supplier.get('supplier_name')
                        print(f"  Supplier: {supplier_name} (Type: {type(supplier_name).__name__})")
                        print(f"    Total Items: {supplier.get('total_items', 0)}")
                        print(f"    Currency: {supplier.get('purchase_currency', 'N/A')}")
                    
                    self.log_test("Dashboard Filter Data", True, f"Found {len(departments_from_kpis)} departments, {len(sections)} sections, {len(top_suppliers)} suppliers")
                    return True
                        
                except json.JSONDecodeError:
                    self.log_test("Dashboard API Response", False, "Invalid JSON response")
                    return False
                    
            else:
                self.log_test("Dashboard API", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard API", False, f"Exception: {str(e)}")
            return False
    
    def test_sample_products_data(self):
        """Test 4: Get sample products and examine department/section/supplier field values"""
        print("\n📦 TESTING SAMPLE PRODUCTS DATA")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Products API Setup", False, "No authentication token available")
            return False
            
        try:
            # Get first 10 products to examine their data structure
            response = self.session.get(f"{BACKEND_URL}/products?limit=10")
            
            if response.status_code == 200:
                try:
                    products = response.json()
                    self.debug_data['sample_products'] = products
                    
                    if isinstance(products, list) and products:
                        print(f"\n📋 SAMPLE PRODUCTS DATA ANALYSIS:")
                        print(f"Total products retrieved: {len(products)}")
                        
                        # Analyze department field values
                        departments_found = set()
                        sections_found = set()
                        suppliers_found = set()
                        
                        for i, product in enumerate(products):
                            dept = product.get('department')
                            section = product.get('section')
                            supplier = product.get('supplier')
                            
                            departments_found.add(dept)
                            sections_found.add(section)
                            suppliers_found.add(supplier)
                            
                            if i < 3:  # Show details for first 3 products
                                print(f"\n  Product {i+1}: {product.get('product_name', 'N/A')}")
                                print(f"    Department: '{dept}' (Type: {type(dept).__name__})")
                                print(f"    Section: '{section}' (Type: {type(section).__name__})")
                                print(f"    Supplier: '{supplier}' (Type: {type(supplier).__name__})")
                                print(f"    Item Number: {product.get('item_number', 'N/A')}")
                                print(f"    Barcode: {product.get('barcode', 'N/A')}")
                        
                        print(f"\n🔍 UNIQUE VALUES FOUND:")
                        print(f"  Departments: {sorted(list(departments_found))}")
                        print(f"  Sections: {sorted(list(sections_found))}")
                        print(f"  Suppliers: {sorted(list(suppliers_found))[:10]}")  # Show first 10 suppliers
                        
                        # Check if we're seeing the problematic "Department 1", "Department 2" pattern
                        problematic_depts = [d for d in departments_found if d and ("Department " in str(d) and str(d).replace("Department ", "").isdigit())]
                        if problematic_depts:
                            self.log_test("Problematic Department Names", False, f"Found: {problematic_depts}")
                        else:
                            self.log_test("Department Names Format", True, "No 'Department X' pattern found")
                        
                        self.log_test("Sample Products Data", True, f"Analyzed {len(products)} products")
                        return True
                    else:
                        self.log_test("Sample Products Data", False, "No products returned or invalid format")
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test("Products API Response", False, "Invalid JSON response")
                    return False
                    
            else:
                self.log_test("Products API", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Products API", False, f"Exception: {str(e)}")
            return False
    
    def test_products_with_department_filter(self):
        """Test 5: Test products API with department filtering to see actual values"""
        print("\n🔍 TESTING PRODUCTS WITH DEPARTMENT FILTERING")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Department Filter Setup", False, "No authentication token available")
            return False
        
        # Test with expected department codes
        expected_departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        for dept in expected_departments:
            try:
                response = self.session.get(f"{BACKEND_URL}/products?department={dept}&limit=5")
                
                if response.status_code == 200:
                    try:
                        products = response.json()
                        
                        if isinstance(products, list):
                            print(f"\n🏢 DEPARTMENT '{dept}' FILTER RESULTS:")
                            print(f"  Products found: {len(products)}")
                            
                            if products:
                                # Show first product details
                                first_product = products[0]
                                print(f"  Sample Product: {first_product.get('product_name', 'N/A')}")
                                print(f"  Department Field: '{first_product.get('department', 'N/A')}'")
                                print(f"  Section Field: '{first_product.get('section', 'N/A')}'")
                                print(f"  Supplier Field: '{first_product.get('supplier', 'N/A')}'")
                                
                                self.log_test(f"Department Filter {dept}", True, f"Found {len(products)} products")
                            else:
                                self.log_test(f"Department Filter {dept}", False, "No products found")
                        else:
                            self.log_test(f"Department Filter {dept}", False, "Invalid response format")
                            
                    except json.JSONDecodeError:
                        self.log_test(f"Department Filter {dept}", False, "Invalid JSON response")
                        
                else:
                    self.log_test(f"Department Filter {dept}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Department Filter {dept}", False, f"Exception: {str(e)}")
    
    def test_search_functionality(self):
        """Test 6: Test search functionality to see how it handles department data"""
        print("\n🔍 TESTING SEARCH FUNCTIONALITY")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Search Setup", False, "No authentication token available")
            return False
            
        try:
            # Search for a common term
            response = self.session.get(f"{BACKEND_URL}/search?q=product&limit=5")
            
            if response.status_code == 200:
                try:
                    products = response.json()
                    
                    if isinstance(products, list) and products:
                        print(f"\n🔍 SEARCH RESULTS ANALYSIS:")
                        print(f"Products found: {len(products)}")
                        
                        for i, product in enumerate(products[:3]):  # Show first 3
                            print(f"\n  Search Result {i+1}:")
                            print(f"    Product: {product.get('product_name', 'N/A')}")
                            print(f"    Department: '{product.get('department', 'N/A')}'")
                            print(f"    Section: '{product.get('section', 'N/A')}'")
                            print(f"    Supplier: '{product.get('supplier', 'N/A')}'")
                        
                        self.log_test("Search Functionality", True, f"Found {len(products)} products")
                    else:
                        self.log_test("Search Functionality", False, "No search results")
                        
                except json.JSONDecodeError:
                    self.log_test("Search API Response", False, "Invalid JSON response")
                    
            else:
                self.log_test("Search API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Search API", False, f"Exception: {str(e)}")
    
    def analyze_filter_data_issue(self):
        """Analyze the collected data to identify the root cause of the filter issue"""
        print("\n🔬 ANALYZING FILTER DATA ISSUE")
        print("=" * 50)
        
        # Check if we have the necessary data
        if not self.debug_data:
            print("❌ No debug data collected - cannot analyze issue")
            return
        
        print("\n📊 ROOT CAUSE ANALYSIS:")
        
        # Check if filters API exists
        if 'filters_response' in self.debug_data:
            filters_data = self.debug_data['filters_response']
            print("✅ Filters API endpoint exists and returns data")
            
            # Analyze the structure
            if isinstance(filters_data, dict):
                departments = filters_data.get('departments', [])
                if departments:
                    print(f"  Departments in filters: {departments}")
                    # Check if these are the problematic "Department 1" style names
                    problematic = [d for d in departments if isinstance(d, str) and "Department " in d and d.replace("Department ", "").isdigit()]
                    if problematic:
                        print(f"  ❌ ISSUE FOUND: Problematic department names: {problematic}")
                    else:
                        print(f"  ✅ Department names look correct: {departments}")
        else:
            print("❌ Filters API endpoint not found or not working")
        
        # Check dashboard data
        if 'dashboard_response' in self.debug_data:
            dashboard_data = self.debug_data['dashboard_response']
            kpis = dashboard_data.get('kpis', [])
            if kpis:
                dept_names = [kpi.get('department') for kpi in kpis]
                print(f"  Dashboard departments: {dept_names}")
        
        # Check sample products data
        if 'sample_products' in self.debug_data:
            products = self.debug_data['sample_products']
            if products:
                unique_depts = set(p.get('department') for p in products)
                unique_sections = set(p.get('section') for p in products)
                unique_suppliers = set(p.get('supplier') for p in products if p.get('supplier'))
                
                print(f"  Product departments: {sorted(list(unique_depts))}")
                print(f"  Product sections: {sorted(list(unique_sections))}")
                print(f"  Product suppliers (sample): {sorted(list(unique_suppliers))[:5]}")
                
                # Check for the specific issue pattern
                problematic_depts = [d for d in unique_depts if d and "Department " in str(d) and str(d).replace("Department ", "").isdigit()]
                if problematic_depts:
                    print(f"  ❌ CRITICAL ISSUE: Products have problematic department names: {problematic_depts}")
                    print(f"  🔍 This suggests the data import process is storing indices instead of actual department names")
                else:
                    print(f"  ✅ Product department names appear to be correct")
        
        print("\n💡 RECOMMENDATIONS:")
        print("1. Check the data import/upload process")
        print("2. Verify that department/section/supplier fields are being stored as names, not indices")
        print("3. Check if there's a mapping issue between numeric codes and display names")
        print("4. Verify the filters API implementation returns actual names, not indices")
    
    def run_all_tests(self):
        """Run all filters debug tests"""
        print("🔍 FILTERS API DEBUG TEST - Why departments showing as 'Department 1', 'Department 2'?")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("Issue: Departments, sections, suppliers showing as numeric indices instead of names")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            self.test_filters_api_endpoint()
            self.test_dashboard_api_for_filter_data()
            self.test_sample_products_data()
            self.test_products_with_department_filter()
            self.test_search_functionality()
            self.analyze_filter_data_issue()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with filters debug tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 FILTERS DEBUG TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 FILTERS API ISSUE DIAGNOSIS:")
        
        # Provide diagnosis based on test results
        auth_tests = [r for r in self.test_results if "Admin Login" in r["test"]]
        filter_tests = [r for r in self.test_results if "Filter" in r["test"] or "Department" in r["test"]]
        
        if auth_tests and auth_tests[0]["success"]:
            print("✅ Authentication: WORKING - Can access backend APIs")
        else:
            print("❌ Authentication: FAILED - Cannot access backend APIs")
            return
        
        # Check for specific issues found
        problematic_dept_tests = [r for r in self.test_results if "Problematic Department" in r["test"]]
        if problematic_dept_tests:
            if not problematic_dept_tests[0]["success"]:
                print("❌ ISSUE CONFIRMED: Found 'Department X' pattern in product data")
                print("🔍 ROOT CAUSE: Data import process is storing indices instead of actual names")
            else:
                print("✅ Department names appear to be in correct format")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check the Excel import process - ensure department names are preserved")
        print("2. Verify database contains actual department names (01-FMG, 01-CGD, 01-OPSS)")
        print("3. Check if filters API implementation needs to be created/fixed")
        print("4. Ensure frontend is not converting names to indices during display")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = FiltersDebugTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()