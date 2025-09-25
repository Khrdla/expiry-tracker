#!/usr/bin/env python3
"""
Focused Debug Test for Mirinda Excel Lookup Issue
Investigating why "mirinda" search returns "Lookup failed" instead of proper search results
"""

import requests
import sys
import json
import os
import pandas as pd
from datetime import datetime

class MirindaDebugTester:
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

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def login(self):
        """Login with admin credentials"""
        url = f"{self.api_url}/auth/login"
        data = {"username": self.admin_username, "password": self.admin_password}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                if 'access_token' in response_data:
                    self.token = response_data['access_token']
                    print(f"✅ Admin login successful: {self.token[:20]}...")
                    return True
            
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def test_excel_lookup_mirinda(self):
        """Test Excel lookup API with 'mirinda' query"""
        print("\n🔍 Testing Excel Lookup API with 'mirinda'")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        url = f"{self.api_url}/excel-lookup?query=mirinda"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.log_test("Excel Lookup - mirinda", True, "API call successful", response_data)
                    
                    # Check if product was found
                    found = response_data.get('found', False)
                    if found:
                        print(f"   ✅ Product found: {response_data.get('product_name')}")
                        print(f"   Department: {response_data.get('department')}")
                        print(f"   Supplier: {response_data.get('supplier')}")
                    else:
                        print(f"   ⚠️ No product found for 'mirinda'")
                        print(f"   Message: {response_data.get('message', 'No message')}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log_test("Excel Lookup - mirinda", False, f"Invalid JSON response: {str(e)}", response.text[:500])
                    return False
            else:
                self.log_test("Excel Lookup - mirinda", False, f"HTTP {response.status_code}", response.text[:500])
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Excel Lookup - mirinda", False, "Request timeout")
            return False
        except Exception as e:
            self.log_test("Excel Lookup - mirinda", False, f"Request error: {str(e)}")
            return False

    def test_excel_lookup_variations(self):
        """Test Excel lookup with different variations of mirinda"""
        variations = [
            "mirinda",
            "Mirinda", 
            "MIRINDA",
            "soft drink",
            "beverage",
            "orange",
            "soda"
        ]
        
        print(f"\n🔍 Testing Excel Lookup with {len(variations)} variations")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        results = {}
        
        for query in variations:
            url = f"{self.api_url}/excel-lookup?query={query}"
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        found = response_data.get('found', False)
                        product_name = response_data.get('product_name', 'N/A') if found else 'Not found'
                        
                        results[query] = {
                            'found': found,
                            'product_name': product_name,
                            'status': 'success'
                        }
                        
                        print(f"   {query}: {'✅ Found' if found else '⚠️ Not found'} - {product_name}")
                        
                    except json.JSONDecodeError:
                        results[query] = {'status': 'json_error', 'found': False}
                        print(f"   {query}: ❌ JSON decode error")
                else:
                    results[query] = {'status': f'http_{response.status_code}', 'found': False}
                    print(f"   {query}: ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                results[query] = {'status': f'error_{str(e)}', 'found': False}
                print(f"   {query}: ❌ Error: {str(e)}")
        
        # Log overall results
        successful_queries = sum(1 for r in results.values() if r.get('status') == 'success')
        found_products = sum(1 for r in results.values() if r.get('found', False))
        
        self.log_test("Excel Lookup Variations", True, 
                     f"{successful_queries}/{len(variations)} queries successful, {found_products} products found", 
                     results)
        
        return True

    def test_database_mirinda_search(self):
        """Search database for any Mirinda products"""
        print("\n🔍 Searching Database for Mirinda Products")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Test different search queries
        search_queries = [
            "mirinda",
            "Mirinda", 
            "MIRINDA",
            "orange",
            "soft",
            "drink",
            "beverage"
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        all_results = {}
        
        for query in search_queries:
            url = f"{self.api_url}/search?q={query}&limit=10"
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    try:
                        products = response.json()
                        if isinstance(products, list):
                            # Look for mirinda-related products
                            mirinda_products = []
                            for product in products:
                                product_name = product.get('product_name', '').lower()
                                if 'mirinda' in product_name or 'orange' in product_name:
                                    mirinda_products.append({
                                        'name': product.get('product_name'),
                                        'department': product.get('department'),
                                        'supplier': product.get('supplier'),
                                        'barcode': product.get('barcode')
                                    })
                            
                            all_results[query] = {
                                'total_results': len(products),
                                'mirinda_related': len(mirinda_products),
                                'products': mirinda_products
                            }
                            
                            print(f"   Query '{query}': {len(products)} total, {len(mirinda_products)} mirinda-related")
                            for product in mirinda_products:
                                print(f"      - {product['name']} ({product['department']})")
                        else:
                            all_results[query] = {'error': 'Invalid response format'}
                            print(f"   Query '{query}': ❌ Invalid response format")
                    except json.JSONDecodeError:
                        all_results[query] = {'error': 'JSON decode error'}
                        print(f"   Query '{query}': ❌ JSON decode error")
                else:
                    all_results[query] = {'error': f'HTTP {response.status_code}'}
                    print(f"   Query '{query}': ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                all_results[query] = {'error': str(e)}
                print(f"   Query '{query}': ❌ Error: {str(e)}")
        
        # Summary
        total_mirinda_products = sum(r.get('mirinda_related', 0) for r in all_results.values() if isinstance(r, dict))
        
        self.log_test("Database Mirinda Search", True, 
                     f"Found {total_mirinda_products} mirinda-related products across all queries", 
                     all_results)
        
        return True

    def test_excel_file_direct_check(self):
        """Check Excel file directly for Mirinda products"""
        print("\n📊 Checking Excel File Directly for Mirinda Products")
        
        excel_path = '/app/items_import_template.xlsx'
        
        try:
            if not os.path.exists(excel_path):
                self.log_test("Excel File Existence", False, f"Excel file not found at {excel_path}")
                return False
            
            print(f"   ✅ Excel file exists at {excel_path}")
            
            # Read Excel file
            df = pd.read_excel(excel_path)
            print(f"   📊 Excel file has {len(df)} rows and {len(df.columns)} columns")
            print(f"   📋 Columns: {list(df.columns)}")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Search for mirinda products
            mirinda_searches = [
                ('mirinda', 'Item Name'),
                ('Mirinda', 'Item Name'),
                ('MIRINDA', 'Item Name'),
                ('orange', 'Item Name'),
                ('soft', 'Item Name'),
                ('drink', 'Item Name')
            ]
            
            all_mirinda_products = []
            
            for search_term, column in mirinda_searches:
                if column in df.columns:
                    matches = df[df[column].str.contains(search_term, case=False, na=False)]
                    
                    print(f"   🔍 Search '{search_term}' in '{column}': {len(matches)} matches")
                    
                    for _, row in matches.iterrows():
                        product_info = {
                            'item_name': row.get('Item Name', 'N/A'),
                            'item_number': row.get('item Number', 'N/A'),
                            'department': row.get('Department', 'N/A'),
                            'supplier': row.get('Supplier', 'N/A'),
                            'barcode': row.get('Barcode', 'N/A')
                        }
                        
                        # Avoid duplicates
                        if product_info not in all_mirinda_products:
                            all_mirinda_products.append(product_info)
                            print(f"      - {product_info['item_name']} ({product_info['department']})")
                else:
                    print(f"   ⚠️ Column '{column}' not found in Excel file")
            
            # Summary
            print(f"\n   📊 Total unique Mirinda-related products found: {len(all_mirinda_products)}")
            
            self.log_test("Excel File Direct Check", True, 
                         f"Found {len(all_mirinda_products)} mirinda-related products in Excel file", 
                         {'total_products': len(all_mirinda_products), 'products': all_mirinda_products})
            
            return True
            
        except Exception as e:
            self.log_test("Excel File Direct Check", False, f"Error reading Excel file: {str(e)}")
            return False

    def test_api_error_logs(self):
        """Check for API error logs by testing edge cases"""
        print("\n🔍 Testing API Error Scenarios")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test various edge cases that might cause "Lookup failed"
        test_cases = [
            {"query": "", "description": "Empty query"},
            {"query": "   ", "description": "Whitespace only"},
            {"query": "mirinda", "description": "Original failing query"},
            {"query": "nonexistentproduct123456", "description": "Non-existent product"},
            {"query": "!@#$%", "description": "Special characters"},
            {"query": "a" * 1000, "description": "Very long query"}
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n   Test {i}: {description}")
            print(f"   Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            
            try:
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                url = f"{self.api_url}/excel-lookup?query={encoded_query}"
                
                response = requests.get(url, headers=headers, timeout=30)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        found = response_data.get('found', False)
                        message = response_data.get('message', 'No message')
                        
                        print(f"   Found: {found}")
                        print(f"   Message: {message}")
                        
                        if not found and query == "mirinda":
                            print(f"   🔍 CRITICAL: 'mirinda' query returned not found - this matches user report!")
                        
                    except json.JSONDecodeError:
                        print(f"   ❌ JSON decode error - response: {response.text[:200]}")
                        
                elif response.status_code == 500:
                    print(f"   ❌ Server error - this could be the 'Lookup failed' issue!")
                    print(f"   Response: {response.text[:200]}")
                    
                else:
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Request error: {str(e)}")
        
        return True

    def test_case_sensitivity(self):
        """Test if Excel lookup is case-sensitive"""
        print("\n🔍 Testing Case Sensitivity")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test with known products in different cases
        test_cases = [
            "orange",
            "Orange", 
            "ORANGE",
            "water",
            "Water",
            "WATER",
            "juice",
            "Juice",
            "JUICE"
        ]
        
        results = {}
        
        for query in test_cases:
            url = f"{self.api_url}/excel-lookup?query={query}"
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    found = response_data.get('found', False)
                    product_name = response_data.get('product_name', 'N/A') if found else None
                    
                    results[query] = {
                        'found': found,
                        'product_name': product_name
                    }
                    
                    print(f"   '{query}': {'✅ Found' if found else '❌ Not found'} - {product_name or 'N/A'}")
                else:
                    results[query] = {'found': False, 'error': f'HTTP {response.status_code}'}
                    print(f"   '{query}': ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                results[query] = {'found': False, 'error': str(e)}
                print(f"   '{query}': ❌ Error: {str(e)}")
        
        # Analyze case sensitivity
        base_words = ['orange', 'water', 'juice']
        case_sensitive_issues = []
        
        for base_word in base_words:
            variations = [base_word, base_word.capitalize(), base_word.upper()]
            found_counts = [results.get(v, {}).get('found', False) for v in variations]
            
            if not all(found_counts) and any(found_counts):
                case_sensitive_issues.append(base_word)
                print(f"   ⚠️ Case sensitivity issue detected for '{base_word}'")
        
        self.log_test("Case Sensitivity Test", True, 
                     f"Tested {len(test_cases)} variations, {len(case_sensitive_issues)} case sensitivity issues", 
                     results)
        
        return True

    def run_debug_tests(self):
        """Run all debug tests for mirinda lookup issue"""
        print("🔍 MIRINDA EXCEL LOOKUP DEBUG INVESTIGATION")
        print("=" * 60)
        print("Investigating why 'mirinda' search returns 'Lookup failed'")
        print("Expected: Product results or 'Product not found'")
        print("Actual: 'Lookup failed' error (red message)")
        print("=" * 60)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all debug tests
        print("\n1️⃣ TESTING EXCEL LOOKUP API WITH 'MIRINDA'")
        self.test_excel_lookup_mirinda()
        
        print("\n2️⃣ TESTING SIMILAR SEARCHES")
        self.test_excel_lookup_variations()
        
        print("\n3️⃣ CHECKING DATABASE FOR MIRINDA PRODUCTS")
        self.test_database_mirinda_search()
        
        print("\n4️⃣ TESTING EXCEL FILE ACCESS")
        self.test_excel_file_direct_check()
        
        print("\n5️⃣ CHECKING API ERROR LOGS")
        self.test_api_error_logs()
        
        print("\n6️⃣ TESTING CASE SENSITIVITY")
        self.test_case_sensitivity()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🔍 MIRINDA DEBUG INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        for result in self.test_results:
            if not result['success']:
                print(f"❌ {result['name']}: {result['details']}")
        
        print("\n📋 RECOMMENDATIONS:")
        print("1. Check backend logs for Excel lookup API errors")
        print("2. Verify Excel file contains Mirinda products")
        print("3. Test Excel file reading functionality")
        print("4. Check for case sensitivity issues")
        print("5. Verify API error handling")
        
        return True

if __name__ == "__main__":
    tester = MirindaDebugTester()
    tester.run_debug_tests()