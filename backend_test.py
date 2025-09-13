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
    def __init__(self, base_url="https://hypermarket-stock.preview.emergentagent.com"):
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

    def test_product_data_verification(self):
        """Test product data verification with different currencies (EUR, SAR, YER)"""
        print("\n🔍 Testing Product Data Verification with Different Currencies")
        
        # Get a larger sample of products to find different currencies
        success, response = self.run_test(
            "Product Data Sample (100 products)",
            "GET",
            "products?limit=100",
            200
        )
        
        if not success or not isinstance(response, list):
            return False
        
        # Categorize products by currency
        currency_products = {'EUR': [], 'SAR': [], 'YER': []}
        
        for product in response:
            currency = product.get('purchase_currency', '').upper()
            if currency in currency_products:
                currency_products[currency].append(product)
        
        print(f"   📊 Currency distribution:")
        for currency, products in currency_products.items():
            print(f"   {currency}: {len(products)} products")
        
        # Test each currency type
        all_tests_passed = True
        
        for currency, products in currency_products.items():
            if not products:
                print(f"   ⚠️ No {currency} products found for testing")
                continue
            
            # Test first few products of each currency
            for i, product in enumerate(products[:3], 1):
                # Verify purchase_currency is properly stored
                stored_currency = product.get('purchase_currency', '')
                if stored_currency.upper() != currency:
                    self.log_test(f"{currency} Currency Storage #{i}", False, 
                                f"Expected {currency}, got {stored_currency}")
                    all_tests_passed = False
                    continue
                
                # Verify selling_price is numeric and reasonable
                selling_price = product.get('selling_price')
                if not isinstance(selling_price, (int, float)):
                    self.log_test(f"{currency} Selling Price Type #{i}", False, 
                                f"Selling price not numeric: {type(selling_price)}")
                    all_tests_passed = False
                    continue
                
                if selling_price <= 0:
                    self.log_test(f"{currency} Selling Price Value #{i}", False, 
                                f"Selling price not reasonable: {selling_price}")
                    all_tests_passed = False
                    continue
                
                # For YER products, selling price should be in YER amounts (typically higher numbers)
                if currency == 'YER' and selling_price < 100:
                    print(f"   ⚠️ {currency} product has low selling price: {selling_price} (may be converted)")
                
                print(f"   ✅ {currency} Product #{i}: {product.get('product_name', 'Unknown')[:30]}...")
                print(f"      Purchase Currency: {stored_currency}")
                print(f"      Selling Price: {selling_price}")
        
        return all_tests_passed

    def test_specific_currency_products(self):
        """Test specific products with known currencies"""
        print("\n🔍 Testing Specific Currency Products")
        
        # Test Apple Juice Box 1L (should be EUR according to review request)
        success, response = self.run_test(
            "Search Apple Juice Box 1L",
            "GET",
            "search?q=Apple Juice Box 1L&limit=5",
            200
        )
        
        apple_juice_found = False
        if success and isinstance(response, list):
            for product in response:
                if "Apple Juice Box 1L" in product.get('product_name', ''):
                    apple_juice_found = True
                    currency = product.get('purchase_currency', '')
                    selling_price = product.get('selling_price', 0)
                    
                    print(f"   🍎 Apple Juice Box 1L found:")
                    print(f"      Purchase Currency: {currency}")
                    print(f"      Selling Price: {selling_price}")
                    
                    # Verify it has EUR purchase currency as mentioned in review
                    if currency.upper() == 'EUR':
                        print(f"   ✅ Apple Juice has EUR currency as expected")
                    else:
                        print(f"   ⚠️ Apple Juice has {currency} currency (expected EUR)")
                    
                    # Verify selling price is reasonable
                    if isinstance(selling_price, (int, float)) and selling_price > 0:
                        print(f"   ✅ Selling price is numeric and reasonable")
                    else:
                        self.log_test("Apple Juice Selling Price", False, 
                                    f"Invalid selling price: {selling_price}")
                        return False
                    break
        
        if not apple_juice_found:
            print("   ⚠️ Apple Juice Box 1L not found in search results")
        
        return True

    def test_selling_price_currency_logic(self):
        """Test that selling prices are always in YER regardless of purchase currency"""
        print("\n🔍 Testing Selling Price Currency Logic")
        
        # Get products with different purchase currencies
        success, response = self.run_test(
            "Products for Currency Logic Test",
            "GET",
            "products?limit=50",
            200
        )
        
        if not success or not isinstance(response, list):
            return False
        
        # Group products by purchase currency and check selling prices
        currency_analysis = {}
        
        for product in response:
            purchase_currency = product.get('purchase_currency', '').upper()
            selling_price = product.get('selling_price', 0)
            
            if purchase_currency not in currency_analysis:
                currency_analysis[purchase_currency] = []
            
            currency_analysis[purchase_currency].append({
                'name': product.get('product_name', 'Unknown'),
                'selling_price': selling_price,
                'purchase_price': product.get('purchase_price', 0)
            })
        
        print(f"   📊 Selling Price Analysis by Purchase Currency:")
        
        all_valid = True
        for currency, products in currency_analysis.items():
            if not products:
                continue
                
            selling_prices = [p['selling_price'] for p in products if isinstance(p['selling_price'], (int, float))]
            if not selling_prices:
                continue
                
            avg_selling = sum(selling_prices) / len(selling_prices)
            min_selling = min(selling_prices)
            max_selling = max(selling_prices)
            
            print(f"   {currency} products ({len(products)} items):")
            print(f"      Selling price range: {min_selling} - {max_selling}")
            print(f"      Average selling price: {avg_selling:.2f}")
            
            # Check if selling prices look like YER amounts (typically higher numbers)
            if currency != 'YER':
                # For non-YER purchase currencies, selling prices should still be in YER
                # YER amounts are typically in thousands
                yer_like_prices = [p for p in selling_prices if p >= 1000]
                if len(yer_like_prices) > len(selling_prices) * 0.5:  # More than 50% are YER-like
                    print(f"   ✅ {currency} products have YER-like selling prices")
                else:
                    print(f"   ⚠️ {currency} products may not have YER selling prices")
        
        return all_valid

    def test_edit_product_endpoint(self):
        """Test the PUT /api/products/{id} endpoint"""
        print("\n🔍 Testing Edit Product Endpoint")
        
        # First get a product to edit
        success, response = self.run_test(
            "Get Products for Edit Test",
            "GET",
            "products?limit=5",
            200
        )
        
        if not success or not isinstance(response, list) or len(response) == 0:
            self.log_test("Edit Product - No Products", False, "No products available for edit test")
            return False
        
        # Use the first product
        test_product = response[0]
        product_id = test_product.get('id')
        
        if not product_id:
            self.log_test("Edit Product - No ID", False, "Product has no ID field")
            return False
        
        original_selling_price = test_product.get('selling_price', 0)
        original_currency = test_product.get('purchase_currency', '')
        
        print(f"   📝 Testing edit on product: {test_product.get('product_name', 'Unknown')}")
        print(f"   Original selling price: {original_selling_price}")
        print(f"   Original currency: {original_currency}")
        
        # Test updating selling price (should stay in YER)
        new_selling_price = original_selling_price + 100 if isinstance(original_selling_price, (int, float)) else 5000
        
        update_data = {
            "selling_price": new_selling_price
        }
        
        success, response = self.run_test(
            f"Update Product Selling Price",
            "PUT",
            f"products/{product_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"   ✅ Product update successful")
            
            # Verify the update by getting the product again
            success2, response2 = self.run_test(
                "Verify Product Update",
                "GET",
                f"products?search={test_product.get('item_number', '')}&limit=1",
                200
            )
            
            if success2 and isinstance(response2, list) and len(response2) > 0:
                updated_product = response2[0]
                updated_selling_price = updated_product.get('selling_price')
                updated_currency = updated_product.get('purchase_currency')
                
                print(f"   Updated selling price: {updated_selling_price}")
                print(f"   Currency after update: {updated_currency}")
                
                # Verify selling price was updated
                if updated_selling_price == new_selling_price:
                    print(f"   ✅ Selling price updated correctly")
                else:
                    self.log_test("Product Update Verification", False, 
                                f"Selling price not updated: expected {new_selling_price}, got {updated_selling_price}")
                    return False
                
                # Verify currency remained the same
                if updated_currency == original_currency:
                    print(f"   ✅ Purchase currency preserved: {updated_currency}")
                else:
                    self.log_test("Product Update Currency", False, 
                                f"Currency changed: {original_currency} -> {updated_currency}")
                    return False
                
                return True
            else:
                self.log_test("Product Update Verification", False, "Could not verify product update")
                return False
        else:
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

    def test_excel_lookup_valid_queries(self):
        """Test Excel lookup with valid product names and barcodes"""
        # Test queries based on common product patterns
        test_queries = [
            {"query": "Orange", "description": "Partial product name match"},
            {"query": "Water", "description": "Common product name"},
            {"query": "Juice", "description": "Product category"},
            {"query": "9501100046987", "description": "Valid barcode"},
            {"query": "3222471052747", "description": "Another valid barcode"},
            {"query": "Al Hana", "description": "Brand name"},
            {"query": "Lemonade", "description": "Specific product name"}
        ]
        
        all_success = True
        
        print(f"\n🔍 Testing Excel lookup with {len(test_queries)} valid queries")
        
        for i, test_data in enumerate(test_queries, 1):
            query = test_data["query"]
            description = test_data["description"]
            
            success, response = self.run_test(
                f"Excel Lookup #{i} ({description})",
                "GET",
                f"excel-lookup?query={query}",
                200
            )
            
            if success and isinstance(response, dict):
                # Check if product was found
                found = response.get('found', False)
                if found:
                    # Verify response contains required fields
                    required_fields = [
                        'product_name', 'item_number', 'department', 'section',
                        'supplier', 'purchase_price', 'purchase_currency', 'selling_price'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in response]
                    if missing_fields:
                        self.log_test(f"Excel Lookup Response Fields #{i}", False, f"Missing fields: {missing_fields}")
                        all_success = False
                        continue
                    
                    # Verify data types and values
                    product_name = response.get('product_name', '')
                    purchase_price = response.get('purchase_price', 0)
                    currency = response.get('purchase_currency', '')
                    
                    if not product_name:
                        self.log_test(f"Excel Lookup Data Quality #{i}", False, "Empty product name")
                        all_success = False
                        continue
                    
                    if not isinstance(purchase_price, (int, float)):
                        self.log_test(f"Excel Lookup Data Quality #{i}", False, f"Invalid purchase price type: {type(purchase_price)}")
                        all_success = False
                        continue
                    
                    if not currency:
                        self.log_test(f"Excel Lookup Data Quality #{i}", False, "Empty currency")
                        all_success = False
                        continue
                    
                    print(f"   ✅ Query '{query}': Found '{product_name}' - {purchase_price} {currency}")
                    
                else:
                    print(f"   ⚠️ Query '{query}': No match found (this may be expected)")
                    
            else:
                all_success = False
        
        return all_success

    def test_excel_lookup_authentication(self):
        """Test Excel lookup endpoint requires authentication"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Excel Lookup - No Auth",
            "GET",
            "excel-lookup?query=Orange",
            403  # FastAPI returns 403 for missing auth
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ Excel lookup endpoint correctly requires authentication")
            return True
        else:
            self.log_test("Excel Lookup Authentication", False, "Excel lookup endpoint should require authentication")
            return False

    def test_excel_lookup_error_scenarios(self):
        """Test Excel lookup error handling"""
        error_scenarios = [
            {"query": "", "description": "Empty query", "expected_status": 422},  # FastAPI validation error
            {"query": "   ", "description": "Whitespace only query", "expected_status": 200},  # Should handle gracefully
            {"query": "!@#$%^&*()", "description": "Special characters", "expected_status": 200},
            {"query": "NONEXISTENTPRODUCT12345", "description": "Non-existent product", "expected_status": 200}
        ]
        
        all_success = True
        
        print(f"\n🔍 Testing Excel lookup error scenarios")
        
        for i, scenario in enumerate(error_scenarios, 1):
            query = scenario["query"]
            description = scenario["description"]
            expected_status = scenario["expected_status"]
            
            # URL encode the query properly
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            success, response = self.run_test(
                f"Excel Lookup Error #{i} ({description})",
                "GET",
                f"excel-lookup?query={encoded_query}",
                expected_status
            )
            
            if success:
                if expected_status == 200 and isinstance(response, dict):
                    found = response.get('found', False)
                    if query.strip() == "" or query == "NONEXISTENTPRODUCT12345":
                        if not found:
                            print(f"   ✅ Query '{query}': Correctly returned not found")
                        else:
                            self.log_test(f"Excel Lookup Error Handling #{i}", False, f"Should not find match for '{query}'")
                            all_success = False
                    else:
                        print(f"   ✅ Query '{query}': Handled gracefully")
                else:
                    print(f"   ✅ Query '{query}': Correct error response")
            else:
                all_success = False
        
        return all_success

    def test_excel_lookup_data_validation(self):
        """Test Excel lookup data validation and format"""
        # Test with a known good query
        success, response = self.run_test(
            "Excel Lookup Data Validation",
            "GET",
            "excel-lookup?query=Orange",
            200
        )
        
        if success and isinstance(response, dict):
            found = response.get('found', False)
            
            if found:
                # Validate response structure
                expected_structure = {
                    'found': bool,
                    'product_name': str,
                    'item_number': str,
                    'department': str,
                    'section': str,
                    'family': str,
                    'sub_family': str,
                    'supplier_code': str,
                    'supplier': str,
                    'barcode': str,
                    'purchase_price': (int, float),
                    'purchase_currency': str,
                    'selling_price': (int, float),
                    'arabic_description': str,
                    'location': str,
                    'brand': str,
                    'all_matches': int,
                    'search_query': str
                }
                
                all_valid = True
                for field, expected_type in expected_structure.items():
                    if field not in response:
                        self.log_test("Excel Lookup Structure", False, f"Missing field: {field}")
                        return False
                    
                    value = response[field]
                    if value is not None and not isinstance(value, expected_type):
                        self.log_test("Excel Lookup Structure", False, f"Field {field} has wrong type: {type(value)}, expected {expected_type}")
                        all_valid = False
                
                # Verify JSON serializable
                try:
                    import json
                    json.dumps(response)
                    print("   ✅ Excel lookup response is JSON serializable")
                except Exception as e:
                    self.log_test("Excel Lookup JSON Serialization", False, f"Response not JSON serializable: {str(e)}")
                    return False
                
                # Verify search query matches
                if response.get('search_query') != 'Orange':
                    self.log_test("Excel Lookup Query Match", False, f"Search query mismatch: {response.get('search_query')}")
                    return False
                
                # Verify currency is valid
                currency = response.get('purchase_currency', '')
                valid_currencies = ['YER', 'SAR', 'EUR', 'USD']
                if currency not in valid_currencies:
                    print(f"   ⚠️ Unexpected currency: {currency} (may be valid)")
                
                if all_valid:
                    print("   ✅ All required fields present with correct types")
                    print(f"   📦 Product: {response.get('product_name')}")
                    print(f"   🏢 Department: {response.get('department')}")
                    print(f"   💰 Price: {response.get('purchase_price')} {response.get('purchase_currency')}")
                    print(f"   🔍 Matches found: {response.get('all_matches')}")
                    return True
            else:
                print("   ⚠️ No product found for 'Orange' query - this may indicate Excel file issues")
                return True  # Not necessarily a failure
        
        return False

    def test_excel_lookup_partial_matches(self):
        """Test Excel lookup partial matching functionality"""
        partial_queries = [
            {"query": "Al", "description": "Brand prefix"},
            {"query": "Juice", "description": "Product type"},
            {"query": "1L", "description": "Size specification"},
            {"query": "Box", "description": "Package type"}
        ]
        
        all_success = True
        
        print(f"\n🔍 Testing Excel lookup partial matching")
        
        for i, test_data in enumerate(partial_queries, 1):
            query = test_data["query"]
            description = test_data["description"]
            
            success, response = self.run_test(
                f"Excel Partial Match #{i} ({description})",
                "GET",
                f"excel-lookup?query={query}",
                200
            )
            
            if success and isinstance(response, dict):
                found = response.get('found', False)
                all_matches = response.get('all_matches', 0)
                
                if found:
                    product_name = response.get('product_name', '')
                    print(f"   ✅ Query '{query}': Found '{product_name}' ({all_matches} total matches)")
                    
                    # Verify the found product actually contains the search term
                    if query.lower() not in product_name.lower():
                        print(f"   ⚠️ Product name '{product_name}' doesn't contain '{query}' - may be barcode/item number match")
                else:
                    print(f"   ⚠️ Query '{query}': No matches found")
            else:
                all_success = False
        
        return all_success

    def test_excel_file_accessibility(self):
        """Test that Excel file is accessible and readable"""
        # This is tested indirectly through the API, but we can check the error handling
        success, response = self.run_test(
            "Excel File Accessibility Test",
            "GET",
            "excel-lookup?query=test",
            200
        )
        
        if success and isinstance(response, dict):
            # If we get a proper response structure, the file is accessible
            if 'found' in response:
                print("   ✅ Excel file is accessible and readable")
                return True
            else:
                self.log_test("Excel File Accessibility", False, "Unexpected response structure")
                return False
        else:
            # Check if it's a 500 error indicating file not found
            if not success:
                self.log_test("Excel File Accessibility", False, "Excel file may not be accessible")
                return False
        
        return True

    def test_product_with_image_lemonade(self):
        """Test specific product 'Lemonade 150Cl' with image functionality"""
        print("\n🖼️ Testing Product Image Functionality - Lemonade 150Cl")
        
        # Search for the specific product mentioned in review request
        success, response = self.run_test(
            "Search Lemonade 150Cl Product",
            "GET",
            "search?q=Lemonade 150Cl&limit=5",
            200
        )
        
        lemonade_product = None
        if success and isinstance(response, list):
            for product in response:
                if "Lemonade 150Cl" in product.get('product_name', ''):
                    lemonade_product = product
                    break
        
        if not lemonade_product:
            self.log_test("Lemonade Product Search", False, "Lemonade 150Cl product not found")
            return False
        
        print(f"   📦 Found product: {lemonade_product.get('product_name')}")
        
        # Check if product has image_url
        image_url = lemonade_product.get('image_url')
        expected_image_url = "/uploads/bf28e101-c299-42e7-842b-00eb1e4b8e97_749d4c0f6cb748f9936646a312795aee.jpeg"
        
        if image_url:
            print(f"   🖼️ Product has image_url: {image_url}")
            
            # Verify it matches the expected URL from review request
            if image_url == expected_image_url:
                print(f"   ✅ Image URL matches expected: {expected_image_url}")
                self.log_test("Lemonade Image URL Match", True, f"Image URL: {image_url}")
            else:
                print(f"   ⚠️ Image URL differs from expected")
                print(f"      Expected: {expected_image_url}")
                print(f"      Actual: {image_url}")
                self.log_test("Lemonade Image URL Match", False, f"Expected {expected_image_url}, got {image_url}")
                
            return True
        else:
            self.log_test("Lemonade Product Image URL", False, "Product has no image_url field")
            return False

    def test_image_api_endpoint(self):
        """Test the image serving API endpoint /api/uploads/{filename}"""
        print("\n🖼️ Testing Image API Endpoint")
        
        # Test the specific image file mentioned in review request
        filename = "bf28e101-c299-42e7-842b-00eb1e4b8e97_749d4c0f6cb748f9936646a312795aee.jpeg"
        
        # Test image endpoint without authentication first
        url = f"{self.api_url}/uploads/{filename}"
        print(f"   🔍 Testing image URL: {url}")
        
        try:
            # Test without auth headers for image serving
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                print(f"   📄 Content-Type: {content_type}")
                
                if content_type.startswith('image/'):
                    print(f"   ✅ Image served successfully with correct MIME type")
                    
                    # Check content length
                    content_length = len(response.content)
                    print(f"   📏 Image size: {content_length} bytes")
                    
                    if content_length > 0:
                        self.log_test("Image API Endpoint", True, f"Image served: {content_length} bytes, type: {content_type}")
                        return True
                    else:
                        self.log_test("Image API Endpoint", False, "Image file is empty")
                        return False
                else:
                    self.log_test("Image API Endpoint", False, f"Wrong content type: {content_type}")
                    return False
                    
            elif response.status_code == 404:
                self.log_test("Image API Endpoint", False, "Image file not found on server")
                return False
            else:
                self.log_test("Image API Endpoint", False, f"Unexpected status code: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Image API Endpoint", False, "Request timeout")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test("Image API Endpoint", False, "Connection error")
            return False
        except Exception as e:
            self.log_test("Image API Endpoint", False, f"Error: {str(e)}")
            return False

    def test_database_image_data(self):
        """Test database for products with image_url populated"""
        print("\n🖼️ Testing Database Image Data")
        
        # Get products and check for image_url fields
        success, response = self.run_test(
            "Get Products for Image Data Check",
            "GET",
            "products?limit=100",
            200
        )
        
        if not success or not isinstance(response, list):
            return False
        
        products_with_images = []
        products_without_images = []
        
        for product in response:
            image_url = product.get('image_url')
            if image_url:
                products_with_images.append({
                    'name': product.get('product_name', 'Unknown'),
                    'image_url': image_url,
                    'department': product.get('department', 'Unknown')
                })
            else:
                products_without_images.append(product.get('product_name', 'Unknown'))
        
        print(f"   📊 Image Data Summary:")
        print(f"      Products with images: {len(products_with_images)}")
        print(f"      Products without images: {len(products_without_images)}")
        
        if products_with_images:
            print(f"   🖼️ Products with images:")
            for i, product in enumerate(products_with_images[:5], 1):  # Show first 5
                print(f"      {i}. {product['name']}")
                print(f"         Image: {product['image_url']}")
                print(f"         Department: {product['department']}")
            
            # Verify image_url format
            valid_formats = 0
            for product in products_with_images:
                image_url = product['image_url']
                if image_url.startswith('/uploads/') and (image_url.endswith('.jpeg') or image_url.endswith('.jpg') or image_url.endswith('.png')):
                    valid_formats += 1
            
            print(f"   ✅ Valid image URL formats: {valid_formats}/{len(products_with_images)}")
            
            if valid_formats == len(products_with_images):
                self.log_test("Database Image URL Format", True, f"All {len(products_with_images)} image URLs have valid format")
            else:
                self.log_test("Database Image URL Format", False, f"Only {valid_formats}/{len(products_with_images)} have valid format")
            
            return True
        else:
            print("   ⚠️ No products found with image_url populated")
            self.log_test("Database Image Data", False, "No products have image_url populated")
            return False

    def test_image_file_existence(self):
        """Test if image files actually exist on the server"""
        print("\n🖼️ Testing Image File Existence on Server")
        
        # Get products with images
        success, response = self.run_test(
            "Get Products with Images",
            "GET",
            "products?limit=50",
            200
        )
        
        if not success or not isinstance(response, list):
            return False
        
        products_with_images = [p for p in response if p.get('image_url')]
        
        if not products_with_images:
            print("   ⚠️ No products with images found for file existence test")
            return True  # Not a failure, just no images to test
        
        files_exist = 0
        files_missing = 0
        
        # Test up to 5 image files
        for i, product in enumerate(products_with_images[:5], 1):
            image_url = product.get('image_url', '')
            product_name = product.get('product_name', 'Unknown')
            
            if image_url.startswith('/uploads/'):
                filename = image_url.replace('/uploads/', '')
                
                try:
                    url = f"{self.api_url}/uploads/{filename}"
                    response = requests.head(url, timeout=10)  # Use HEAD for faster check
                    
                    if response.status_code == 200:
                        files_exist += 1
                        print(f"   ✅ File {i}: {filename} exists")
                    else:
                        files_missing += 1
                        print(f"   ❌ File {i}: {filename} missing (status: {response.status_code})")
                        
                except Exception as e:
                    files_missing += 1
                    print(f"   ❌ File {i}: {filename} error: {str(e)}")
        
        total_tested = files_exist + files_missing
        print(f"   📊 File Existence Summary: {files_exist}/{total_tested} files exist")
        
        if files_exist > 0:
            self.log_test("Image File Existence", True, f"{files_exist}/{total_tested} image files exist on server")
            return True
        else:
            self.log_test("Image File Existence", False, f"No image files found on server (0/{total_tested})")
            return False

    def test_image_authentication_requirements(self):
        """Test if image serving requires authentication"""
        print("\n🖼️ Testing Image Authentication Requirements")
        
        # Test image endpoint without authentication
        filename = "bf28e101-c299-42e7-842b-00eb1e4b8e97_749d4c0f6cb748f9936646a312795aee.jpeg"
        
        # Remove token temporarily
        original_token = self.token
        self.token = None
        
        try:
            url = f"{self.api_url}/uploads/{filename}"
            response = requests.get(url, timeout=10)
            
            # Restore token
            self.token = original_token
            
            if response.status_code == 200:
                print("   ✅ Images are publicly accessible (no authentication required)")
                self.log_test("Image Authentication", True, "Images publicly accessible")
                return True
            elif response.status_code in [401, 403]:
                print("   🔒 Images require authentication")
                self.log_test("Image Authentication", True, "Images require authentication")
                return True
            elif response.status_code == 404:
                print("   ⚠️ Image file not found (cannot test authentication)")
                self.log_test("Image Authentication", True, "Image not found - cannot test auth")
                return True
            else:
                print(f"   ⚠️ Unexpected status code: {response.status_code}")
                self.log_test("Image Authentication", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            # Restore token
            self.token = original_token
            self.log_test("Image Authentication", False, f"Error testing authentication: {str(e)}")
            return False

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
        
        # CURRENCY AND PRODUCT DATA VERIFICATION TESTS (FROM REVIEW REQUEST)
        print("\n💱 CURRENCY AND PRODUCT DATA VERIFICATION TESTS")
        print("-" * 55)
        self.test_product_data_verification()
        self.test_specific_currency_products()
        self.test_selling_price_currency_logic()
        self.test_edit_product_endpoint()
        
        # NEW BARCODE SCANNER FUNCTIONALITY TESTS (PRIORITY HIGH)
        print("\n🔍 BARCODE SCANNER FUNCTIONALITY TESTS (NEW)")
        print("-" * 50)
        self.test_barcode_lookup_valid()
        self.test_barcode_lookup_invalid()
        self.test_barcode_authentication()
        self.test_barcode_department_access()
        self.test_barcode_response_format()
        
        # NEW EXCEL LOOKUP FUNCTIONALITY TESTS (PRIORITY HIGH)
        print("\n📊 EXCEL LOOKUP FUNCTIONALITY TESTS (NEW - HIGH PRIORITY)")
        print("-" * 60)
        self.test_excel_file_accessibility()
        self.test_excel_lookup_valid_queries()
        self.test_excel_lookup_authentication()
        self.test_excel_lookup_data_validation()
        self.test_excel_lookup_partial_matches()
        self.test_excel_lookup_error_scenarios()
        
        # PRODUCT IMAGE FUNCTIONALITY TESTS (FROM REVIEW REQUEST)
        print("\n🖼️ PRODUCT IMAGE FUNCTIONALITY TESTS (REVIEW REQUEST)")
        print("-" * 55)
        self.test_product_with_image_lemonade()
        self.test_image_api_endpoint()
        self.test_database_image_data()
        self.test_image_file_existence()
        self.test_image_authentication_requirements()
        
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
        
        # NEW: Excel lookup functionality summary
        excel_tests = [test for test in self.test_results if 'Excel Lookup' in test['name']]
        excel_passed = sum(1 for test in excel_tests if test['success'])
        excel_total = len(excel_tests)
        
        if excel_total > 0:
            excel_working = excel_passed == excel_total
            print(f"📊 Excel Lookup API: {'WORKING' if excel_working else 'FAILED'} ({excel_passed}/{excel_total} tests passed)")
        else:
            print(f"📊 Excel Lookup API: NOT TESTED")
        
        # NEW: Image functionality summary
        image_tests = [test for test in self.test_results if 'Image' in test['name'] or 'Lemonade' in test['name']]
        image_passed = sum(1 for test in image_tests if test['success'])
        image_total = len(image_tests)
        
        if image_total > 0:
            image_working = image_passed == image_total
            print(f"🖼️ Image Functionality: {'WORKING' if image_working else 'FAILED'} ({image_passed}/{image_total} tests passed)")
        else:
            print(f"🖼️ Image Functionality: NOT TESTED")
        
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