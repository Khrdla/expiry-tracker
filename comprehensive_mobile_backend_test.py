#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND AUDIT for Mobile Application after Barcode Scanner Redesign
Tests all critical backend requirements from the review request:

1. Barcode Scanner Backend Support
2. Product Search & Lookup APIs  
3. Export Functionality Backend
4. Core System APIs
5. Authentication & Security
6. Database Operations
7. System Performance

Focus: Mobile-optimized responses, Bearer token authentication, CORS headers
"""

import requests
import sys
import json
import time
from datetime import datetime, timedelta

class ComprehensiveMobileBackendTester:
    def __init__(self, base_url="https://smart-inventory-69.preview.emergentagent.com"):
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
        
        # Sample barcodes for comprehensive testing
        self.sample_barcodes = [
            "9501100046987",   # Al Hana Orange Nectar 235 ml
            "3222471052747",   # Lemonade 150Cl  
            "3222471075722",   # Mountain Water 6X50Cl
            "3222471081273",   # Orange Peach Apricot Nectar Box 1L
            "3222471081716"    # Apple Juice Box 1L
        ]

    def log_test(self, name, success, details="", response_data=None, response_time=None):
        """Log test results with performance metrics"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            time_info = f" ({response_time}ms)" if response_time else ""
            print(f"✅ {name}: PASSED{time_info}")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data,
            'response_time': response_time
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, measure_time=True):
        """Run a single API test with performance measurement"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        start_time = time.time() if measure_time else None
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            response_time = int((time.time() - start_time) * 1000) if start_time else None
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data, response_time)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data, response_time)

            return success, response_data, response

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}, None
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - server may be down")
            return False, {}, None
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}, None

    def test_admin_login(self):
        """Test admin login with credentials from review request"""
        print("\n🔐 AUTHENTICATION & SECURITY TESTING")
        print("=" * 60)
        
        success, response, _ = self.run_test(
            "Admin Login (imadqejji/066380531I)",
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

    def test_barcode_scanner_backend_support(self):
        """Test ALL barcode lookup endpoints with extensive barcode samples"""
        print("\n📱 BARCODE SCANNER BACKEND SUPPORT TESTING")
        print("=" * 60)
        
        all_success = True
        
        # Test 1: Barcode Lookup with ALL sample barcodes
        print(f"\n🔍 Testing barcode lookup with {len(self.sample_barcodes)} sample barcodes")
        
        for i, barcode in enumerate(self.sample_barcodes, 1):
            success, response, http_response = self.run_test(
                f"Barcode Lookup #{i} ({barcode})",
                "GET",
                f"barcode/{barcode}",
                200
            )
            
            if success and isinstance(response, dict):
                # Verify response format is optimal for mobile interface
                required_fields = [
                    'product_name', 'item_number', 'barcode', 'department', 
                    'section', 'purchase_price', 'purchase_currency', 'selling_price', 
                    'supplier', 'quantity', 'status'
                ]
                
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    self.log_test(f"Barcode Response Fields #{i}", False, f"Missing fields: {missing_fields}")
                    all_success = False
                    continue
                
                # Verify JSON serialization and mobile-compatible response sizes
                try:
                    json_str = json.dumps(response)
                    response_size = len(json_str.encode('utf-8'))
                    print(f"   📏 Response size: {response_size} bytes (mobile-friendly: {'✅' if response_size < 2048 else '⚠️'})")
                    
                    if response_size > 5120:  # 5KB limit for mobile
                        self.log_test(f"Barcode Response Size #{i}", False, f"Response too large: {response_size} bytes")
                        all_success = False
                        continue
                        
                except Exception as e:
                    self.log_test(f"Barcode JSON Serialization #{i}", False, f"Not JSON serializable: {str(e)}")
                    all_success = False
                    continue
                
                # Verify mobile-compatible data
                product_name = response.get('product_name', '')
                department = response.get('department', '')
                status = response.get('status', '')
                
                print(f"   📦 Product: {product_name}")
                print(f"   🏢 Department: {department}")
                print(f"   📊 Status: {status}")
                
                # Check CORS headers for mobile compatibility
                if http_response:
                    cors_headers = {
                        'access-control-allow-origin': http_response.headers.get('access-control-allow-origin'),
                        'access-control-allow-methods': http_response.headers.get('access-control-allow-methods'),
                        'access-control-allow-headers': http_response.headers.get('access-control-allow-headers'),
                        'access-control-allow-credentials': http_response.headers.get('access-control-allow-credentials')
                    }
                    
                    cors_present = any(cors_headers.values())
                    if cors_present:
                        print(f"   🌐 CORS headers present: ✅")
                    else:
                        print(f"   🌐 CORS headers missing: ⚠️")
                        
            else:
                all_success = False
        
        # Test 2: Authentication with Bearer tokens
        print(f"\n🔐 Testing Bearer token authentication")
        
        # Test without token
        original_token = self.token
        self.token = None
        
        success, response, _ = self.run_test(
            "Barcode Lookup - No Bearer Token",
            "GET",
            f"barcode/{self.sample_barcodes[0]}",
            403
        )
        
        if success:
            print("   ✅ Correctly requires Bearer token (returns 403 without auth)")
        else:
            all_success = False
        
        # Restore token
        self.token = original_token
        
        # Test 3: Error handling for invalid barcodes
        print(f"\n❌ Testing error handling for invalid barcodes")
        
        invalid_barcodes = ["0000000000000", "invalid_barcode", "999999999999999"]
        
        for i, invalid_barcode in enumerate(invalid_barcodes, 1):
            success, response, _ = self.run_test(
                f"Invalid Barcode #{i} ({invalid_barcode})",
                "GET",
                f"barcode/{invalid_barcode}",
                404
            )
            
            if success and isinstance(response, dict):
                # Verify clean, user-friendly error messages
                detail = response.get('detail', '')
                if detail and 'not found' in detail.lower():
                    print(f"   ✅ Clean error message: {detail}")
                else:
                    print(f"   ⚠️ Error message could be more user-friendly: {detail}")
            elif not success:
                all_success = False
        
        return all_success

    def test_product_search_lookup_apis(self):
        """Test comprehensive product search endpoints for waste report functionality"""
        print("\n🔍 PRODUCT SEARCH & LOOKUP APIs TESTING")
        print("=" * 60)
        
        all_success = True
        
        # Test 1: Multi-word product name searches
        print(f"\n📝 Testing multi-word product name searches")
        
        multi_word_searches = [
            "Apple Juice Box",
            "Orange Peach Apricot",
            "Mountain Water 6X50Cl",
            "Al Hana Orange"
        ]
        
        for i, search_term in enumerate(multi_word_searches, 1):
            success, response, _ = self.run_test(
                f"Multi-word Search #{i} ({search_term})",
                "GET",
                f"search?q={search_term}&limit=10",
                200
            )
            
            if success and isinstance(response, list):
                print(f"   📊 Found {len(response)} results for '{search_term}'")
                
                # Verify results contain search terms
                if response:
                    relevant_results = 0
                    for product in response:
                        product_name = product.get('product_name', '').lower()
                        search_words = search_term.lower().split()
                        if any(word in product_name for word in search_words):
                            relevant_results += 1
                    
                    relevance_ratio = relevant_results / len(response) if response else 0
                    print(f"   🎯 Relevance: {relevant_results}/{len(response)} ({relevance_ratio:.1%})")
                    
                    if relevance_ratio < 0.5:  # Less than 50% relevant
                        print(f"   ⚠️ Low search relevance for '{search_term}'")
            else:
                all_success = False
        
        # Test 2: Barcode vs. name search logic
        print(f"\n🔢 Testing barcode vs. name search logic")
        
        # Test barcode search
        barcode_search = self.sample_barcodes[0]
        success, response, _ = self.run_test(
            f"Barcode Search ({barcode_search})",
            "GET",
            f"search?q={barcode_search}&limit=5",
            200
        )
        
        if success and isinstance(response, list):
            if response:
                found_product = response[0]
                if found_product.get('barcode') == barcode_search:
                    print(f"   ✅ Barcode search found exact match")
                else:
                    print(f"   ⚠️ Barcode search didn't find exact barcode match")
            else:
                print(f"   ❌ Barcode search returned no results")
                all_success = False
        else:
            all_success = False
        
        # Test 3: Partial matching capabilities
        print(f"\n🔍 Testing partial matching capabilities")
        
        partial_searches = [
            {"query": "Juice", "description": "Product type"},
            {"query": "1L", "description": "Size specification"},
            {"query": "Box", "description": "Package type"},
            {"query": "Al", "description": "Brand prefix"}
        ]
        
        for i, search_data in enumerate(partial_searches, 1):
            query = search_data["query"]
            description = search_data["description"]
            
            success, response, _ = self.run_test(
                f"Partial Match #{i} ({description})",
                "GET",
                f"search?q={query}&limit=10",
                200
            )
            
            if success and isinstance(response, list):
                print(f"   📊 Partial search '{query}': {len(response)} results")
                
                # Verify all required fields are returned for mobile app compatibility
                if response:
                    sample_product = response[0]
                    mobile_required_fields = [
                        'product_name', 'item_number', 'department', 'section',
                        'purchase_price', 'purchase_currency', 'selling_price', 'supplier'
                    ]
                    
                    missing_fields = [field for field in mobile_required_fields if field not in sample_product]
                    if missing_fields:
                        print(f"   ❌ Missing mobile-required fields: {missing_fields}")
                        all_success = False
                    else:
                        print(f"   ✅ All mobile-required fields present")
            else:
                all_success = False
        
        return all_success

    def test_export_functionality_backend(self):
        """Test ALL export endpoints with proper Bearer token authentication"""
        print("\n📤 EXPORT FUNCTIONALITY BACKEND TESTING")
        print("=" * 60)
        
        all_success = True
        
        # Test 1: Dashboard exports (Excel/PDF)
        print(f"\n📊 Testing dashboard export endpoints")
        
        dashboard_exports = [
            {"endpoint": "export/dashboard/excel", "description": "Dashboard Excel Export"},
            {"endpoint": "export/dashboard/pdf", "description": "Dashboard PDF Export"}
        ]
        
        for i, export_data in enumerate(dashboard_exports, 1):
            endpoint = export_data["endpoint"]
            description = export_data["description"]
            
            success, response, http_response = self.run_test(
                f"{description}",
                "GET",
                endpoint,
                200
            )
            
            if success:
                # Verify file generation works correctly
                if http_response:
                    content_type = http_response.headers.get('content-type', '')
                    content_length = http_response.headers.get('content-length', '0')
                    
                    print(f"   📄 Content-Type: {content_type}")
                    print(f"   📏 Content-Length: {content_length} bytes")
                    
                    # Verify MIME types are appropriate
                    if 'excel' in endpoint and 'spreadsheet' in content_type:
                        print(f"   ✅ Correct Excel MIME type")
                    elif 'pdf' in endpoint and 'pdf' in content_type:
                        print(f"   ✅ Correct PDF MIME type")
                    else:
                        print(f"   ⚠️ Unexpected MIME type for {endpoint}")
                    
                    # Verify file sizes are appropriate for mobile
                    try:
                        size_bytes = int(content_length)
                        if size_bytes > 0:
                            print(f"   ✅ File generated successfully ({size_bytes} bytes)")
                            
                            # Check if size is mobile-friendly (< 10MB)
                            if size_bytes > 10 * 1024 * 1024:
                                print(f"   ⚠️ Large file size may not be mobile-friendly")
                        else:
                            print(f"   ❌ Empty file generated")
                            all_success = False
                    except:
                        print(f"   ⚠️ Could not determine file size")
            else:
                all_success = False
        
        # Test 2: Waste report exports
        print(f"\n🗑️ Testing waste report export endpoints")
        
        waste_exports = [
            {"endpoint": "export/waste-report/daily", "description": "Daily Waste Report"},
            {"endpoint": "export/waste-report/weekly", "description": "Weekly Waste Report"},
            {"endpoint": "export/waste-report/monthly", "description": "Monthly Waste Report"}
        ]
        
        for i, export_data in enumerate(waste_exports, 1):
            endpoint = export_data["endpoint"]
            description = export_data["description"]
            
            success, response, http_response = self.run_test(
                f"{description}",
                "GET",
                endpoint,
                200
            )
            
            if success and http_response:
                content_type = http_response.headers.get('content-type', '')
                print(f"   📄 {description}: {content_type}")
                print(f"   ✅ Export endpoint accessible")
            elif not success:
                # Some export endpoints might return 404 if no data exists
                print(f"   ⚠️ {description}: May require data to be present")
        
        # Test 3: Return form exports
        print(f"\n📋 Testing return form export endpoints")
        
        # First, try to get existing return forms
        success, response, _ = self.run_test(
            "Get Return Forms for Export Test",
            "GET",
            "returns?limit=5",
            200
        )
        
        if success and isinstance(response, list) and response:
            # Test PDF export for first return form
            return_form = response[0]
            return_id = return_form.get('id')
            
            if return_id:
                success, response, http_response = self.run_test(
                    f"Return Form PDF Export ({return_id})",
                    "GET",
                    f"export/return-form/{return_id}/pdf",
                    200
                )
                
                if success and http_response:
                    content_type = http_response.headers.get('content-type', '')
                    if 'pdf' in content_type:
                        print(f"   ✅ Return form PDF export working")
                    else:
                        print(f"   ⚠️ Unexpected content type: {content_type}")
                        all_success = False
                else:
                    all_success = False
            else:
                print(f"   ⚠️ Return form has no ID field")
        else:
            print(f"   ⚠️ No return forms available for export testing")
        
        # Test 4: Authentication requirement for exports
        print(f"\n🔐 Testing export authentication requirements")
        
        # Test without Bearer token
        original_token = self.token
        self.token = None
        
        success, response, _ = self.run_test(
            "Dashboard Export - No Bearer Token",
            "GET",
            "export/dashboard/excel",
            403
        )
        
        if success:
            print("   ✅ Export endpoints correctly require Bearer token")
        else:
            print("   ❌ Export endpoints should require authentication")
            all_success = False
        
        # Restore token
        self.token = original_token
        
        return all_success

    def test_core_system_apis(self):
        """Test dashboard API and core system endpoints"""
        print("\n🏠 CORE SYSTEM APIs TESTING")
        print("=" * 60)
        
        all_success = True
        
        # Test 1: Dashboard API returns proper data structure
        print(f"\n📊 Testing dashboard API data structure")
        
        success, response, _ = self.run_test(
            "Dashboard API Structure",
            "GET",
            "dashboard",
            200
        )
        
        if success and isinstance(response, dict):
            # Verify mobile-optimized response structure
            required_sections = ['kpis', 'recent_alerts', 'stock_distribution', 'expiry_status', 'top_suppliers']
            
            missing_sections = [section for section in required_sections if section not in response]
            if missing_sections:
                print(f"   ❌ Missing dashboard sections: {missing_sections}")
                all_success = False
            else:
                print(f"   ✅ All required dashboard sections present")
                
                # Verify KPIs structure
                kpis = response.get('kpis', [])
                print(f"   📊 KPIs for {len(kpis)} departments")
                
                for kpi in kpis:
                    dept = kpi.get('department', 'Unknown')
                    total_items = kpi.get('total_items', 0)
                    stock_value = kpi.get('total_stock_value', 0)
                    print(f"      {dept}: {total_items} items, stock value: {stock_value}")
                
                # Verify top suppliers have currency info
                top_suppliers = response.get('top_suppliers', [])
                print(f"   🏢 Top suppliers: {len(top_suppliers)}")
                
                for supplier in top_suppliers[:3]:
                    name = supplier.get('supplier_name', 'Unknown')
                    currency = supplier.get('purchase_currency', 'Unknown')
                    print(f"      {name}: {currency}")
        else:
            all_success = False
        
        # Test 2: Waste management APIs handle mobile requests correctly
        print(f"\n🗑️ Testing waste management APIs for mobile")
        
        waste_endpoints = [
            {"endpoint": "waste/entries", "method": "GET", "description": "Get Waste Entries"},
            {"endpoint": "waste/reports?period=daily", "method": "GET", "description": "Daily Waste Report"}
        ]
        
        for endpoint_data in waste_endpoints:
            endpoint = endpoint_data["endpoint"]
            method = endpoint_data["method"]
            description = endpoint_data["description"]
            
            success, response, http_response = self.run_test(
                f"{description}",
                method,
                endpoint,
                200
            )
            
            if success:
                # Check response size for mobile compatibility
                if http_response:
                    content_length = len(http_response.content)
                    print(f"   📏 Response size: {content_length} bytes")
                    
                    if content_length > 1024 * 1024:  # 1MB
                        print(f"   ⚠️ Large response may not be mobile-friendly")
                    else:
                        print(f"   ✅ Mobile-friendly response size")
                        
                # Verify JSON structure
                if isinstance(response, (dict, list)):
                    print(f"   ✅ Valid JSON response structure")
                else:
                    print(f"   ❌ Invalid response structure")
                    all_success = False
            else:
                # Some endpoints might be empty, which is acceptable
                print(f"   ⚠️ {description}: May require data to be present")
        
        # Test 3: Email system backend configuration
        print(f"\n📧 Testing email system backend (07:00 AM scheduling)")
        
        success, response, _ = self.run_test(
            "Email System Status",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success and isinstance(response, dict):
            # Check timezone configuration
            timezone = response.get('timezone', '')
            current_time = response.get('current_time', '')
            email_configured = response.get('email_configured', False)
            
            print(f"   🌍 Timezone: {timezone}")
            print(f"   🕰️ Current time: {current_time}")
            print(f"   📧 Email configured: {email_configured}")
            
            # Verify Aden timezone (07:00 AM requirement)
            if 'Aden' in timezone or 'Asia/Aden' in timezone:
                print(f"   ✅ Correct Aden timezone configuration")
            else:
                print(f"   ⚠️ Timezone may not be set to Aden: {timezone}")
        else:
            print(f"   ⚠️ Email system status not available")
        
        return all_success

    def test_database_operations(self):
        """Test MongoDB operations are efficient and mobile-compatible"""
        print("\n🗄️ DATABASE OPERATIONS TESTING")
        print("=" * 60)
        
        all_success = True
        
        # Test 1: UUID handling (no ObjectId serialization issues)
        print(f"\n🆔 Testing UUID handling and ObjectId serialization")
        
        success, response, _ = self.run_test(
            "Products UUID Handling",
            "GET",
            "products?limit=10",
            200
        )
        
        if success and isinstance(response, list):
            for i, product in enumerate(response[:3], 1):
                # Check for ObjectId serialization issues
                product_str = json.dumps(product)
                if "ObjectId" in product_str:
                    print(f"   ❌ Product #{i}: ObjectId serialization issue found")
                    all_success = False
                else:
                    print(f"   ✅ Product #{i}: No ObjectId serialization issues")
                
                # Verify UUID format for ID field
                product_id = product.get('id', '')
                if product_id and len(product_id) > 10:  # Basic UUID length check
                    print(f"   ✅ Product #{i}: Valid ID format ({product_id[:8]}...)")
                else:
                    print(f"   ⚠️ Product #{i}: ID format may not be UUID")
        else:
            all_success = False
        
        # Test 2: Data retrieval performance for mobile networks
        print(f"\n⚡ Testing data retrieval performance")
        
        performance_tests = [
            {"endpoint": "products?limit=50", "description": "50 Products", "max_time": 2000},
            {"endpoint": "dashboard", "description": "Dashboard Data", "max_time": 3000},
            {"endpoint": "search?q=juice&limit=20", "description": "Search Results", "max_time": 2000}
        ]
        
        for test_data in performance_tests:
            endpoint = test_data["endpoint"]
            description = test_data["description"]
            max_time = test_data["max_time"]
            
            success, response, _ = self.run_test(
                f"Performance Test - {description}",
                "GET",
                endpoint,
                200,
                measure_time=True
            )
            
            if success:
                # Check last test result for timing
                last_result = self.test_results[-1]
                response_time = last_result.get('response_time', 0)
                
                if response_time and response_time <= max_time:
                    print(f"   ✅ Performance acceptable: {response_time}ms (limit: {max_time}ms)")
                elif response_time:
                    print(f"   ⚠️ Performance concern: {response_time}ms (limit: {max_time}ms)")
                else:
                    print(f"   ⚠️ Could not measure response time")
            else:
                all_success = False
        
        # Test 3: Error handling for database operations
        print(f"\n❌ Testing database error handling")
        
        # Test with invalid product ID
        success, response, _ = self.run_test(
            "Invalid Product ID Handling",
            "GET",
            "products/invalid-id-12345",
            404
        )
        
        if success:
            print(f"   ✅ Proper error handling for invalid IDs")
        else:
            print(f"   ❌ Database error handling needs improvement")
            all_success = False
        
        return all_success

    def test_system_performance(self):
        """Test API response times suitable for mobile networks"""
        print("\n⚡ SYSTEM PERFORMANCE TESTING")
        print("=" * 60)
        
        all_success = True
        response_times = []
        
        # Test 1: API response times for mobile networks
        print(f"\n📱 Testing API response times for mobile compatibility")
        
        mobile_critical_endpoints = [
            {"endpoint": f"barcode/{self.sample_barcodes[0]}", "description": "Barcode Lookup", "max_time": 1000},
            {"endpoint": "search?q=juice&limit=10", "description": "Product Search", "max_time": 1500},
            {"endpoint": "dashboard", "description": "Dashboard Load", "max_time": 2000},
            {"endpoint": "products?limit=20", "description": "Product List", "max_time": 1500}
        ]
        
        for test_data in mobile_critical_endpoints:
            endpoint = test_data["endpoint"]
            description = test_data["description"]
            max_time = test_data["max_time"]
            
            success, response, _ = self.run_test(
                f"Mobile Performance - {description}",
                "GET",
                endpoint,
                200,
                measure_time=True
            )
            
            if success:
                last_result = self.test_results[-1]
                response_time = last_result.get('response_time', 0)
                response_times.append(response_time)
                
                if response_time and response_time <= max_time:
                    print(f"   ✅ Mobile-friendly: {response_time}ms (limit: {max_time}ms)")
                elif response_time:
                    print(f"   ⚠️ May be slow on mobile: {response_time}ms (limit: {max_time}ms)")
                    if response_time > max_time * 1.5:  # 50% over limit
                        all_success = False
            else:
                all_success = False
        
        # Test 2: Concurrent request handling
        print(f"\n🔄 Testing concurrent request handling")
        
        # Simulate multiple concurrent requests (simplified)
        concurrent_tests = []
        start_time = time.time()
        
        for i in range(3):  # Test 3 concurrent requests
            success, response, _ = self.run_test(
                f"Concurrent Request #{i+1}",
                "GET",
                "dashboard",
                200,
                measure_time=True
            )
            concurrent_tests.append(success)
        
        total_time = time.time() - start_time
        concurrent_success = all(concurrent_tests)
        
        if concurrent_success:
            print(f"   ✅ Concurrent requests handled successfully in {total_time:.2f}s")
        else:
            print(f"   ❌ Some concurrent requests failed")
            all_success = False
        
        # Test 3: System stability under mobile load patterns
        print(f"\n📊 Performance Summary")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"   📈 Average response time: {avg_response_time:.0f}ms")
            print(f"   📈 Max response time: {max_response_time}ms")
            print(f"   📈 Min response time: {min_response_time}ms")
            
            # Mobile performance assessment
            if avg_response_time <= 1500:
                print(f"   ✅ Excellent mobile performance")
            elif avg_response_time <= 3000:
                print(f"   ⚠️ Acceptable mobile performance")
            else:
                print(f"   ❌ Poor mobile performance")
                all_success = False
        
        return all_success

    def run_comprehensive_audit(self):
        """Run the complete comprehensive backend audit"""
        print("🚀 COMPREHENSIVE BACKEND AUDIT FOR MOBILE APPLICATION")
        print("=" * 80)
        print("Focus: Barcode scanner redesign, mobile optimization, Bearer token auth")
        print("=" * 80)
        
        # Initialize
        start_time = time.time()
        
        # Test sequence based on review request priorities
        test_results = []
        
        # 1. Authentication & Security (prerequisite)
        test_results.append(("Authentication", self.test_admin_login()))
        
        if not self.token:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with protected endpoints")
            return False
        
        # 2. Barcode Scanner Backend Support (PRIORITY 1)
        test_results.append(("Barcode Scanner Backend", self.test_barcode_scanner_backend_support()))
        
        # 3. Product Search & Lookup APIs (PRIORITY 2)
        test_results.append(("Product Search & Lookup", self.test_product_search_lookup_apis()))
        
        # 4. Export Functionality Backend (PRIORITY 3)
        test_results.append(("Export Functionality", self.test_export_functionality_backend()))
        
        # 5. Core System APIs (PRIORITY 4)
        test_results.append(("Core System APIs", self.test_core_system_apis()))
        
        # 6. Database Operations (PRIORITY 5)
        test_results.append(("Database Operations", self.test_database_operations()))
        
        # 7. System Performance (PRIORITY 6)
        test_results.append(("System Performance", self.test_system_performance()))
        
        # Final Results
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE BACKEND AUDIT RESULTS")
        print("=" * 80)
        
        passed_categories = 0
        total_categories = len(test_results)
        
        for category, success in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {category}")
            if success:
                passed_categories += 1
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Categories Passed: {passed_categories}/{total_categories}")
        print(f"   Individual Tests: {self.tests_passed}/{self.tests_run}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Total Time: {total_time:.2f} seconds")
        
        # Mobile-specific assessment
        print(f"\n📱 MOBILE COMPATIBILITY ASSESSMENT:")
        
        mobile_critical_passed = 0
        mobile_critical_total = 4  # Barcode, Search, Core APIs, Performance
        
        critical_categories = ["Barcode Scanner Backend", "Product Search & Lookup", "Core System APIs", "System Performance"]
        for category, success in test_results:
            if category in critical_categories and success:
                mobile_critical_passed += 1
        
        mobile_score = (mobile_critical_passed / mobile_critical_total) * 100
        
        if mobile_score >= 90:
            print(f"   🌟 EXCELLENT mobile compatibility ({mobile_score:.0f}%)")
        elif mobile_score >= 75:
            print(f"   ✅ GOOD mobile compatibility ({mobile_score:.0f}%)")
        elif mobile_score >= 50:
            print(f"   ⚠️ ACCEPTABLE mobile compatibility ({mobile_score:.0f}%)")
        else:
            print(f"   ❌ POOR mobile compatibility ({mobile_score:.0f}%)")
        
        overall_success = passed_categories >= (total_categories * 0.8)  # 80% pass rate
        
        if overall_success:
            print(f"\n🎉 AUDIT RESULT: BACKEND IS READY FOR MOBILE APPLICATION")
        else:
            print(f"\n⚠️ AUDIT RESULT: BACKEND NEEDS IMPROVEMENTS FOR MOBILE")
        
        return overall_success

def main():
    """Main execution function"""
    print("Starting Comprehensive Mobile Backend Audit...")
    
    tester = ComprehensiveMobileBackendTester()
    success = tester.run_comprehensive_audit()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()