#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Expiry Tracker
Tests all critical API endpoints after major ObjectId serialization fixes
Focus: Authentication, Products API, Dashboard, Filters, Currency handling
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class ExpiryTrackerAPITester:
    def __init__(self, base_url="https://smartinventory-10.preview.emergentagent.com"):
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

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)

            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - server may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic API health"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_login(self):
        """Test login with admin credentials from review request"""
        success, response = self.run_test(
            "Admin Login (imadqejji)",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password}
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Admin token obtained: {self.token[:20]}...")
            return True
        else:
            print(f"   ❌ Admin login failed: {response}")
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            self.log_test("Get Current User", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        if success and isinstance(response, dict):
            self.user_data = response
            print(f"   👤 User: {response.get('username')} (Admin: {response.get('is_admin')})")
        
        return success

    def test_get_products(self):
        """Test getting products list - PRIORITY HIGH (just fixed ObjectId issues)"""
        success, response = self.run_test(
            "Get Products List (50 default)",
            "GET",
            "products",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   📦 Found {len(response)} products")
            if len(response) > 0:
                product = response[0]
                print(f"   Sample product: {product.get('product_name', 'Unknown')}")
                print(f"   Department: {product.get('department', 'Unknown')}")
                print(f"   Currency: {product.get('purchase_currency', 'Unknown')}")
                # Store first product for further testing
                self.sample_product = product
                
                # Verify ObjectId serialization is working (no ObjectId strings)
                product_str = json.dumps(product)
                if "ObjectId" in product_str:
                    self.log_test("ObjectId Serialization Check", False, "ObjectId found in response")
                    return False
                else:
                    self.log_test("ObjectId Serialization Check", True, "No ObjectId serialization issues")
        
        return success

    def test_products_department_filtering(self):
        """Test department filtering for products - verify 01-FMG, 01-CGD, 01-OPSS"""
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        all_success = True
        
        for dept in departments:
            success, response = self.run_test(
                f"Get Products - Department {dept}",
                "GET",
                f"products?department={dept}",
                200
            )
            
            if success and isinstance(response, list):
                print(f"   📂 Department {dept}: {len(response)} products")
                if len(response) > 0:
                    # Verify all products belong to this department
                    for product in response[:3]:  # Check first 3
                        if product.get('department') != dept:
                            self.log_test(f"Department Filter {dept}", False, f"Product has wrong department: {product.get('department')}")
                            all_success = False
                            break
            else:
                all_success = False
        
        return all_success

    def test_dashboard_api(self):
        """Test dashboard API - should show KPIs for all departments"""
        success, response = self.run_test(
            "Dashboard API",
            "GET",
            "dashboard",
            200
        )
        
        if success and isinstance(response, dict):
            kpis = response.get('kpis', [])
            print(f"   📊 Dashboard KPIs for {len(kpis)} departments")
            
            # Verify expected departments are present
            dept_names = [kpi.get('department') for kpi in kpis]
            expected_depts = ["01-FMG", "01-CGD", "01-OPSS"]
            
            for dept in expected_depts:
                if dept not in dept_names:
                    self.log_test("Dashboard Department Coverage", False, f"Missing department: {dept}")
                    return False
            
            # Check currency handling in stock values
            for kpi in kpis:
                dept = kpi.get('department')
                stock_value = kpi.get('total_stock_value', 0)
                print(f"   💰 {dept}: Stock value {stock_value}")
            
            # Verify top suppliers have currency info
            top_suppliers = response.get('top_suppliers', [])
            print(f"   🏢 Top suppliers: {len(top_suppliers)}")
            for supplier in top_suppliers[:3]:
                currency = supplier.get('purchase_currency', 'Unknown')
                print(f"   Supplier {supplier.get('supplier_name')}: {currency}")
        
        return success

    def test_filters_api(self):
        """Test filters API - should return department/section options"""
        success, response = self.run_test(
            "Filters API",
            "GET",
            "filters",
            200
        )
        
        if success and isinstance(response, dict):
            departments = response.get('departments', [])
            sections = response.get('sections', [])
            suppliers = response.get('suppliers', [])
            
            print(f"   🔍 Filters: {len(departments)} departments, {len(sections)} sections, {len(suppliers)} suppliers")
            
            # Verify expected departments
            dept_values = [d.get('value') for d in departments]
            expected_depts = ["01-FMG", "01-CGD", "01-OPSS"]
            
            for dept in expected_depts:
                if dept not in dept_values:
                    self.log_test("Filters Department Options", False, f"Missing department option: {dept}")
                    return False
            
            print(f"   ✅ All expected departments present in filters")
        
        return success

    def test_debug_endpoint(self):
        """Test debug endpoint - should return 5 sample products"""
        success, response = self.run_test(
            "Test Products Debug Endpoint",
            "GET",
            "test-products",
            200
        )
        
        if success and isinstance(response, dict):
            count = response.get('count', 0)
            products = response.get('products', [])
            print(f"   🔧 Debug endpoint: {count} products returned")
            
            if count > 0 and len(products) > 0:
                sample = products[0]
                print(f"   Sample: {sample.get('product_name')} - {sample.get('department')}")
                print(f"   Currency: {sample.get('purchase_currency')}")
        
        return success

    def test_search_functionality(self):
        """Test search functionality - critical for the review"""
        # Test text search
        success1, response1 = self.run_test(
            "Search by Text (Samsung)",
            "GET",
            "search?q=Samsung&limit=10",
            200
        )
        
        if success1 and isinstance(response1, list):
            print(f"   🔍 Text search found {len(response1)} results")
        
        # Test barcode search
        success2, response2 = self.run_test(
            "Search by Barcode",
            "GET",
            "search?q=1234567890123&limit=10",
            200
        )
        
        if success2 and isinstance(response2, list):
            print(f"   📱 Barcode search found {len(response2)} results")
        
        # Test direct barcode lookup
        success3, response3 = self.run_test(
            "Direct Barcode Lookup",
            "GET",
            "products/barcode/1234567890123",
            200
        )
        
        if success3:
            print(f"   ✅ Direct barcode lookup successful")
        else:
            print(f"   ⚠️ Direct barcode lookup failed (may be expected if barcode doesn't exist)")
        
        return success1 and success2

    def test_suppliers_endpoint(self):
        """Test suppliers endpoint"""
        success, response = self.run_test(
            "Get Suppliers",
            "GET",
            "suppliers",
            200
        )
        
        if success and isinstance(response, dict) and 'suppliers' in response:
            suppliers = response['suppliers']
            print(f"   🏢 Found {len(suppliers)} suppliers")
            if suppliers:
                print(f"   Sample suppliers: {suppliers[:3]}")
        
        return success

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if success and isinstance(response, dict):
            departments = response.get('departments', [])
            sections = response.get('sections', [])
            print(f"   📂 Found {len(departments)} departments, {len(sections)} sections")
        
        return success

    def test_kpi_endpoints(self):
        """Test KPI endpoints"""
        success1, response1 = self.run_test(
            "Get Enhanced KPI",
            "GET",
            "kpi/enhanced",
            200
        )
        
        if success1 and isinstance(response1, dict):
            print(f"   📊 KPI data: {response1.get('total_products', 0)} total products")
        
        success2, response2 = self.run_test(
            "Get Donut Chart Data",
            "GET",
            "kpi/donut-chart",
            200
        )
        
        return success1 and success2

    def test_out_of_stock_endpoint(self):
        """Test out-of-stock products endpoint"""
        success, response = self.run_test(
            "Get Out of Stock Products",
            "GET",
            "products/out-of-stock",
            200
        )
        
        if success and isinstance(response, dict):
            products = response.get('out_of_stock_products', [])
            print(f"   📉 Found {len(products)} out-of-stock products")
        
        return success

    def test_export_functionality(self):
        """Test export functionality"""
        # Test Excel export
        success1, response1 = self.run_test(
            "Export Excel",
            "GET",
            "export/excel",
            200
        )
        
        # Test template download
        success2, response2 = self.run_test(
            "Download Template",
            "GET",
            "export/template",
            200
        )
        
        return success1 and success2

    def test_supplier_dashboard(self):
        """Test supplier dashboard endpoint"""
        success, response = self.run_test(
            "Supplier Dashboard",
            "GET",
            "suppliers/dashboard",
            200
        )
        
        if success and isinstance(response, dict):
            suppliers_data = response.get('suppliers_summary', [])
            print(f"   📈 Supplier dashboard: {len(suppliers_data)} suppliers with data")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("=" * 60)
        
        # Core connectivity tests
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
            
        if not self.test_get_current_user():
            print("❌ User authentication failed - stopping tests")
            return False
        
        # Core functionality tests
        self.test_get_products()
        self.test_search_functionality()  # Critical for review
        self.test_suppliers_endpoint()
        self.test_categories_endpoint()
        self.test_kpi_endpoints()
        self.test_out_of_stock_endpoint()
        self.test_export_functionality()
        self.test_supplier_dashboard()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 BACKEND TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ExpiryTrackerAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())