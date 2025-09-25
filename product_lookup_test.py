#!/usr/bin/env python3
"""
Product Lookup Functionality Testing for Expiry Tracker
Focus: Testing all product lookup methods as requested in review
- Barcode API Test with sample barcode 3222471081716 (Apple Juice Box)
- Excel Lookup API Test with sample queries
- Product Search API Test
- Database Query Test
- Product API Test
"""

import requests
import sys
import json
from datetime import datetime

class ProductLookupTester:
    def __init__(self, base_url="https://geant-inventory-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials from review request
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"
        
        # Sample data from review request
        self.sample_barcode = "3222471081716"  # Apple Juice Box 1L
        self.sample_queries = ["Apple Juice", "Orange", "Water", "Lemonade"]

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def authenticate(self):
        """Authenticate with admin credentials"""
        print(f"\n🔐 AUTHENTICATION TEST")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={
                    "username": self.admin_username,
                    "password": self.admin_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"Successfully authenticated as {self.admin_username}"
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def test_barcode_lookup(self):
        """Test barcode lookup API with sample barcode"""
        print(f"\n🔍 BARCODE LOOKUP API TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Barcode Lookup", False, "No authentication token available")
            return
        
        try:
            # Test with sample barcode from review request
            response = requests.get(
                f"{self.api_url}/barcode/{self.sample_barcode}",
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                product_name = data.get('product_name', 'Unknown')
                department = data.get('department', 'Unknown')
                purchase_price = data.get('purchase_price', 0)
                purchase_currency = data.get('purchase_currency', 'Unknown')
                
                self.log_test(
                    f"Barcode Lookup ({self.sample_barcode})", 
                    True, 
                    f"Found: {product_name} | Dept: {department} | Price: {purchase_price} {purchase_currency}",
                    data
                )
                
                # Verify it's the expected Apple Juice Box
                if "apple" in product_name.lower() and "juice" in product_name.lower():
                    self.log_test(
                        "Apple Juice Box Verification", 
                        True, 
                        f"Confirmed Apple Juice product: {product_name}"
                    )
                else:
                    self.log_test(
                        "Apple Juice Box Verification", 
                        False, 
                        f"Expected Apple Juice but got: {product_name}"
                    )
                    
            elif response.status_code == 404:
                self.log_test(
                    f"Barcode Lookup ({self.sample_barcode})", 
                    False, 
                    "Product not found - barcode may not exist in database"
                )
            else:
                self.log_test(
                    f"Barcode Lookup ({self.sample_barcode})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Barcode Lookup", False, f"Exception: {str(e)}")

    def test_excel_lookup(self):
        """Test Excel lookup API with sample queries"""
        print(f"\n📊 EXCEL LOOKUP API TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Excel Lookup", False, "No authentication token available")
            return
        
        for query in self.sample_queries:
            try:
                response = requests.get(
                    f"{self.api_url}/excel-lookup",
                    params={'query': query},
                    headers={'Authorization': f'Bearer {self.token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    found = data.get('found', False)
                    
                    if found:
                        product_name = data.get('product_name', 'Unknown')
                        item_number = data.get('item_number', 'Unknown')
                        department = data.get('department', 'Unknown')
                        supplier = data.get('supplier', 'Unknown')
                        purchase_price = data.get('purchase_price', 0)
                        purchase_currency = data.get('purchase_currency', 'Unknown')
                        
                        self.log_test(
                            f"Excel Lookup ('{query}')", 
                            True, 
                            f"Found: {product_name} | Code: {item_number} | Dept: {department} | Supplier: {supplier} | Price: {purchase_price} {purchase_currency}",
                            data
                        )
                    else:
                        self.log_test(
                            f"Excel Lookup ('{query}')", 
                            False, 
                            f"No products found for query: {query}"
                        )
                else:
                    self.log_test(
                        f"Excel Lookup ('{query}')", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Excel Lookup ('{query}')", False, f"Exception: {str(e)}")

    def test_product_search(self):
        """Test product search API"""
        print(f"\n🔎 PRODUCT SEARCH API TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Product Search", False, "No authentication token available")
            return
        
        for query in self.sample_queries:
            try:
                response = requests.get(
                    f"{self.api_url}/search",
                    params={'q': query, 'limit': 5},
                    headers={'Authorization': f'Bearer {self.token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        self.log_test(
                            f"Product Search ('{query}')", 
                            True, 
                            f"Found {len(data)} products"
                        )
                        
                        # Show first result details
                        first_result = data[0]
                        product_name = first_result.get('product_name', 'Unknown')
                        department = first_result.get('department', 'Unknown')
                        supplier = first_result.get('supplier', 'Unknown')
                        
                        print(f"   First result: {product_name} | Dept: {department} | Supplier: {supplier}")
                        
                    else:
                        self.log_test(
                            f"Product Search ('{query}')", 
                            False, 
                            f"No search results found for: {query}"
                        )
                else:
                    self.log_test(
                        f"Product Search ('{query}')", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Product Search ('{query}')", False, f"Exception: {str(e)}")

    def test_products_api(self):
        """Test products API to verify products are accessible"""
        print(f"\n📦 PRODUCTS API TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Products API", False, "No authentication token available")
            return
        
        try:
            response = requests.get(
                f"{self.api_url}/products",
                params={'limit': 10},
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    self.log_test(
                        "Products API", 
                        True, 
                        f"Successfully retrieved {len(data)} products"
                    )
                    
                    # Check for products with barcodes
                    products_with_barcodes = [p for p in data if p.get('barcode')]
                    self.log_test(
                        "Products with Barcodes", 
                        len(products_with_barcodes) > 0, 
                        f"Found {len(products_with_barcodes)} products with barcodes out of {len(data)} total"
                    )
                    
                    # Show sample product details
                    if data:
                        sample_product = data[0]
                        product_name = sample_product.get('product_name', 'Unknown')
                        department = sample_product.get('department', 'Unknown')
                        barcode = sample_product.get('barcode', 'No barcode')
                        
                        print(f"   Sample product: {product_name} | Dept: {department} | Barcode: {barcode}")
                        
                else:
                    self.log_test(
                        "Products API", 
                        False, 
                        "Products API returned empty list - no products found"
                    )
            else:
                self.log_test(
                    "Products API", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Products API", False, f"Exception: {str(e)}")

    def test_database_verification(self):
        """Test database to verify products exist with proper barcode fields"""
        print(f"\n🗄️ DATABASE VERIFICATION TEST")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Database Verification", False, "No authentication token available")
            return
        
        try:
            # Test products endpoint with different filters
            response = requests.get(
                f"{self.api_url}/products",
                params={'limit': 100},
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    total_products = len(data)
                    products_with_barcodes = [p for p in data if p.get('barcode') and p.get('barcode').strip()]
                    products_with_names = [p for p in data if p.get('product_name') and p.get('product_name').strip()]
                    products_with_departments = [p for p in data if p.get('department') and p.get('department').strip()]
                    
                    self.log_test(
                        "Database Products Count", 
                        total_products > 0, 
                        f"Total products in database: {total_products}"
                    )
                    
                    self.log_test(
                        "Products with Barcodes", 
                        len(products_with_barcodes) > 0, 
                        f"{len(products_with_barcodes)} out of {total_products} products have barcodes"
                    )
                    
                    self.log_test(
                        "Products with Names", 
                        len(products_with_names) > 0, 
                        f"{len(products_with_names)} out of {total_products} products have names"
                    )
                    
                    self.log_test(
                        "Products with Departments", 
                        len(products_with_departments) > 0, 
                        f"{len(products_with_departments)} out of {total_products} products have departments"
                    )
                    
                    # Check for specific barcode
                    target_barcode_products = [p for p in data if p.get('barcode') == self.sample_barcode]
                    self.log_test(
                        f"Target Barcode ({self.sample_barcode}) in Database", 
                        len(target_barcode_products) > 0, 
                        f"Found {len(target_barcode_products)} products with target barcode"
                    )
                    
                    # Check for Apple Juice products
                    apple_juice_products = [p for p in data if p.get('product_name') and 'apple' in p.get('product_name', '').lower() and 'juice' in p.get('product_name', '').lower()]
                    self.log_test(
                        "Apple Juice Products in Database", 
                        len(apple_juice_products) > 0, 
                        f"Found {len(apple_juice_products)} Apple Juice products"
                    )
                    
                    if apple_juice_products:
                        for product in apple_juice_products[:3]:  # Show first 3
                            print(f"   Apple Juice: {product.get('product_name')} | Barcode: {product.get('barcode', 'No barcode')}")
                    
                else:
                    self.log_test(
                        "Database Verification", 
                        False, 
                        "Invalid response format from products API"
                    )
            else:
                self.log_test(
                    "Database Verification", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Database Verification", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all product lookup tests"""
        print("🧪 PRODUCT LOOKUP FUNCTIONALITY TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Sample barcode: {self.sample_barcode} (Apple Juice Box 1L)")
        print(f"Sample queries: {', '.join(self.sample_queries)}")
        print(f"Admin credentials: {self.admin_username}")
        
        # Run all tests
        if self.authenticate():
            self.test_barcode_lookup()
            self.test_excel_lookup()
            self.test_product_search()
            self.test_products_api()
            self.test_database_verification()
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        return self.tests_passed, self.tests_run

if __name__ == "__main__":
    tester = ProductLookupTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)