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
            "../health",  # Use /health endpoint instead of /api/
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
        """Test search functionality with real product data"""
        # Test general search
        success1, response1 = self.run_test(
            "Search Products (general)",
            "GET",
            "search?q=product&limit=10",
            200
        )
        
        if success1 and isinstance(response1, list):
            print(f"   🔍 General search found {len(response1)} results")
        
        return success1

    def test_currency_display(self):
        """Test currency display - CRITICAL for review (YER/SAR/EUR)"""
        # Get products and check currency fields
        success, response = self.run_test(
            "Currency Display Check",
            "GET",
            "products?limit=20",
            200
        )
        
        if success and isinstance(response, list):
            currencies_found = set()
            for product in response:
                currency = product.get('purchase_currency')
                if currency:
                    currencies_found.add(currency)
            
            print(f"   💱 Currencies found: {list(currencies_found)}")
            
            # Check if we have the expected currencies from imported data
            expected_currencies = {'YER', 'SAR', 'EUR'}
            found_expected = currencies_found.intersection(expected_currencies)
            
            if found_expected:
                print(f"   ✅ Found expected currencies: {found_expected}")
                return True
            else:
                self.log_test("Currency Display", False, f"Expected YER/SAR/EUR, found: {currencies_found}")
                return False
        
        return False

    def get_sample_barcodes(self):
        """Get sample barcodes from database for testing"""
        # Sample barcodes from different departments based on actual data
        return [
            {"barcode": "9501100046987", "department": "01-FMG", "product_name": "Al Hana Orange Nectar 235 ml"},
            {"barcode": "3222471052747", "department": "01-CGD", "product_name": "Lemonade 150Cl"},
            {"barcode": "3222471075722", "department": "01-CGD", "product_name": "Mountain Water 6X50Cl"},
            {"barcode": "3222471081273", "department": "01-CGD", "product_name": "Orange Peach Apricot Nectar Box 1L"},
            {"barcode": "3222471081716", "department": "01-CGD", "product_name": "Apple Juice Box 1L"}
        ]

    def test_barcode_lookup_valid(self):
        """Test barcode lookup with valid barcodes - NEW FUNCTIONALITY"""
        sample_barcodes = self.get_sample_barcodes()
        all_success = True
        
        print(f"\n🔍 Testing barcode lookup with {len(sample_barcodes)} sample barcodes")
        
        for i, barcode_data in enumerate(sample_barcodes, 1):
            barcode = barcode_data["barcode"]
            expected_product = barcode_data["product_name"]
            expected_dept = barcode_data["department"]
            
            success, response = self.run_test(
                f"Barcode Lookup #{i} ({barcode})",
                "GET",
                f"barcode/{barcode}",
                200
            )
            
            if success and isinstance(response, dict):
                # Verify response contains expected fields
                required_fields = ['product_name', 'item_number', 'barcode', 'department', 
                                 'section', 'purchase_price', 'purchase_currency', 'selling_price', 
                                 'supplier', 'quantity', 'status']
                
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    self.log_test(f"Barcode Response Fields #{i}", False, f"Missing fields: {missing_fields}")
                    all_success = False
                    continue
                
                # Verify product matches expected
                actual_product = response.get('product_name', '')
                actual_dept = response.get('department', '')
                
                if actual_product != expected_product:
                    self.log_test(f"Barcode Product Match #{i}", False, f"Expected '{expected_product}', got '{actual_product}'")
                    all_success = False
                    continue
                
                if actual_dept != expected_dept:
                    self.log_test(f"Barcode Department Match #{i}", False, f"Expected '{expected_dept}', got '{actual_dept}'")
                    all_success = False
                    continue
                
                # Verify ObjectId serialization
                response_str = str(response)
                if "ObjectId" in response_str:
                    self.log_test(f"Barcode ObjectId Serialization #{i}", False, "ObjectId found in barcode response")
                    all_success = False
                    continue
                
                # Verify status calculation
                status = response.get('status')
                if not status:
                    self.log_test(f"Barcode Status Calculation #{i}", False, "No status field in response")
                    all_success = False
                    continue
                
                print(f"   ✅ Barcode {barcode}: {actual_product} ({actual_dept}) - Status: {status}")
                
            else:
                all_success = False
        
        return all_success

    def test_barcode_lookup_invalid(self):
        """Test barcode lookup with invalid barcodes"""
        invalid_barcodes = [
            "0000000000000",  # Non-existent barcode
            "invalid_barcode",  # Invalid format
            "999999999999999",  # Another non-existent
            "",  # Empty barcode
        ]
        
        all_success = True
        
        for i, barcode in enumerate(invalid_barcodes, 1):
            success, response = self.run_test(
                f"Invalid Barcode #{i} ({barcode or 'empty'})",
                "GET",
                f"barcode/{barcode}",
                404
            )
            
            if success:
                print(f"   ✅ Invalid barcode '{barcode}' correctly returned 404")
            else:
                all_success = False
        
        return all_success

    def test_barcode_authentication(self):
        """Test barcode endpoint requires authentication"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Barcode Endpoint - No Auth",
            "GET",
            "barcode/9501100046987",
            403  # FastAPI returns 403 for missing auth, not 401
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ Barcode endpoint correctly requires authentication")
            return True
        else:
            self.log_test("Barcode Authentication", False, "Barcode endpoint should require authentication")
            return False

    def test_barcode_department_access(self):
        """Test barcode endpoint respects department access control"""
        # This test assumes admin user has access to all departments
        # In a real scenario, we'd test with department-specific users
        
        sample_barcodes = self.get_sample_barcodes()
        
        # Test that admin can access products from all departments
        departments_accessed = set()
        
        for barcode_data in sample_barcodes[:3]:  # Test first 3
            barcode = barcode_data["barcode"]
            expected_dept = barcode_data["department"]
            
            success, response = self.run_test(
                f"Barcode Dept Access ({expected_dept})",
                "GET",
                f"barcode/{barcode}",
                200
            )
            
            if success and isinstance(response, dict):
                actual_dept = response.get('department')
                departments_accessed.add(actual_dept)
        
        # Verify we can access multiple departments
        if len(departments_accessed) > 1:
            print(f"   ✅ Admin can access products from departments: {departments_accessed}")
            return True
        else:
            self.log_test("Barcode Department Access", False, f"Only accessed departments: {departments_accessed}")
            return False

    def test_barcode_response_format(self):
        """Test barcode response format and data integrity"""
        barcode = "9501100046987"  # Known good barcode
        
        success, response = self.run_test(
            "Barcode Response Format",
            "GET",
            f"barcode/{barcode}",
            200
        )
        
        if success and isinstance(response, dict):
            # Check required fields are present and have correct types
            field_checks = {
                'product_name': str,
                'item_number': str,
                'barcode': str,
                'department': str,
                'section': str,
                'purchase_price': (int, float),
                'purchase_currency': str,
                'selling_price': (int, float),
                'supplier': str,
                'quantity': (int, float),
                'status': str
            }
            
            all_valid = True
            for field, expected_type in field_checks.items():
                if field not in response:
                    self.log_test("Barcode Response Format", False, f"Missing field: {field}")
                    return False
                
                value = response[field]
                if value is not None and not isinstance(value, expected_type):
                    self.log_test("Barcode Response Format", False, f"Field {field} has wrong type: {type(value)}, expected {expected_type}")
                    all_valid = False
            
            # Check that barcode in response matches requested barcode
            if response.get('barcode') != barcode:
                self.log_test("Barcode Response Format", False, f"Response barcode {response.get('barcode')} doesn't match requested {barcode}")
                return False
            
            # Verify no ObjectId or other non-serializable objects
            try:
                import json
                json.dumps(response)
                print("   ✅ Barcode response is JSON serializable")
            except Exception as e:
                self.log_test("Barcode Response Format", False, f"Response not JSON serializable: {str(e)}")
                return False
            
            if all_valid:
                print("   ✅ All required fields present with correct types")
                return True
        
        return False

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
        """Run all backend tests focused on review requirements"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("Focus: Authentication, Products API, Dashboard, Filters, Currency")
        print("=" * 70)
        
        # Core connectivity and authentication tests
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return False
            
        if not self.test_login():
            print("❌ Admin login failed - stopping tests")
            return False
        
        # PRIORITY HIGH - Critical endpoints from review request
        print("\n🔥 PRIORITY HIGH TESTS (from review request)")
        print("-" * 50)
        
        # Products API (just fixed ObjectId issues)
        self.test_get_products()
        self.test_products_department_filtering()
        
        # Dashboard API (should show KPIs for all departments)
        self.test_dashboard_api()
        
        # Filters API (should return department/section options)
        self.test_filters_api()
        
        # Debug endpoint
        self.test_debug_endpoint()
        
        # Currency display testing (CRITICAL)
        self.test_currency_display()
        
        # NEW BARCODE SCANNER FUNCTIONALITY TESTS (PRIORITY HIGH)
        print("\n🔍 BARCODE SCANNER FUNCTIONALITY TESTS (NEW)")
        print("-" * 50)
        self.test_barcode_lookup_valid()
        self.test_barcode_lookup_invalid()
        self.test_barcode_authentication()
        self.test_barcode_department_access()
        self.test_barcode_response_format()
        
        # Additional functionality tests
        print("\n📋 ADDITIONAL FUNCTIONALITY TESTS")
        print("-" * 40)
        self.test_search_functionality()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 BACKEND TEST RESULTS")
        print("=" * 70)
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
        
        # Summary for main agent
        print(f"\n📋 SUMMARY FOR MAIN AGENT:")
        print(f"✅ Authentication: {'WORKING' if self.token else 'FAILED'}")
        
        products_working = any(test['name'].startswith('Get Products') and test['success'] for test in self.test_results)
        print(f"✅ Products API: {'WORKING' if products_working else 'FAILED'}")
        
        dashboard_working = any(test['name'] == 'Dashboard API' and test['success'] for test in self.test_results)
        print(f"✅ Dashboard API: {'WORKING' if dashboard_working else 'FAILED'}")
        
        filters_working = any(test['name'] == 'Filters API' and test['success'] for test in self.test_results)
        print(f"✅ Filters API: {'WORKING' if filters_working else 'FAILED'}")
        
        currency_working = any(test['name'] == 'Currency Display Check' and test['success'] for test in self.test_results)
        print(f"💱 Currency Display: {'WORKING' if currency_working else 'NEEDS ATTENTION'}")
        
        # NEW: Barcode functionality summary
        barcode_tests = [test for test in self.test_results if 'Barcode' in test['name']]
        barcode_passed = sum(1 for test in barcode_tests if test['success'])
        barcode_total = len(barcode_tests)
        
        if barcode_total > 0:
            barcode_working = barcode_passed == barcode_total
            print(f"🔍 Barcode Scanner API: {'WORKING' if barcode_working else 'FAILED'} ({barcode_passed}/{barcode_total} tests passed)")
        else:
            print(f"🔍 Barcode Scanner API: NOT TESTED")
        
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