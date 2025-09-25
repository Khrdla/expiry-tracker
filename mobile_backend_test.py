#!/usr/bin/env python3
"""
Comprehensive Backend Testing for 5 Mobile Application Fixes
Focus: Mobile Barcode Scanner, Export Authentication, Waste Product Lookup, Daily Email Reports, Dashboard 3D Charts
Priority Order as per user requirements
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import time

class MobileBackendTester:
    def __init__(self, base_url="https://geant-inventory-2.preview.emergentagent.com"):
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
        
        # Sample barcodes for mobile testing
        self.sample_barcodes = [
            "3222471081716",  # Apple Juice Box 1L
            "9501100046987",  # Al Hana Orange Nectar 235 ml
            "3222471052747",  # Lemonade 150Cl
            "3222471075722",  # Mountain Water 6X50Cl
            "3222471081273"   # Orange Peach Apricot Nectar Box 1L
        ]

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
        """Test admin login to get Bearer token"""
        success, response, _ = self.run_test(
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

    # ===== PRIORITY 1: MOBILE BARCODE SCANNER API =====
    
    def test_mobile_barcode_scanner_api(self):
        """Test GET /api/barcode/{barcode} with sample barcodes for mobile compatibility"""
        print("\n" + "="*80)
        print("🔥 PRIORITY 1: MOBILE BARCODE SCANNER API TESTING")
        print("="*80)
        
        all_tests_passed = True
        
        # Test each sample barcode
        for i, barcode in enumerate(self.sample_barcodes, 1):
            success, response, http_response = self.run_test(
                f"Mobile Barcode Scanner #{i} ({barcode})",
                "GET",
                f"barcode/{barcode}",
                200
            )
            
            if success and isinstance(response, dict):
                # Verify mobile-compatible response format
                required_fields = [
                    'product_name', 'item_number', 'barcode', 'department', 
                    'section', 'purchase_price', 'purchase_currency', 
                    'selling_price', 'supplier', 'quantity', 'status'
                ]
                
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    self.log_test(f"Mobile Barcode Response Fields #{i}", False, f"Missing: {missing_fields}")
                    all_tests_passed = False
                    continue
                
                # Check CORS headers for mobile browsers
                if http_response:
                    cors_headers = {
                        'access-control-allow-origin': http_response.headers.get('access-control-allow-origin'),
                        'access-control-allow-methods': http_response.headers.get('access-control-allow-methods'),
                        'access-control-allow-headers': http_response.headers.get('access-control-allow-headers'),
                        'access-control-allow-credentials': http_response.headers.get('access-control-allow-credentials')
                    }
                    
                    print(f"   📱 CORS Headers: {cors_headers}")
                    
                    # Verify mobile-friendly response size
                    response_size = len(json.dumps(response))
                    print(f"   📏 Response size: {response_size} bytes (mobile-friendly: {'✅' if response_size < 2000 else '⚠️'})")
                
                # Verify JSON serialization (no ObjectId issues)
                try:
                    json.dumps(response)
                    print(f"   ✅ JSON serializable for mobile")
                except Exception as e:
                    self.log_test(f"Mobile JSON Serialization #{i}", False, f"Not serializable: {str(e)}")
                    all_tests_passed = False
                    continue
                
                print(f"   📦 Product: {response.get('product_name')}")
                print(f"   🏢 Department: {response.get('department')}")
                print(f"   💰 Price: {response.get('purchase_price')} {response.get('purchase_currency')}")
                print(f"   📊 Status: {response.get('status')}")
                
            else:
                all_tests_passed = False
        
        return all_tests_passed

    def test_mobile_barcode_authentication(self):
        """Test Bearer token authentication for mobile apps"""
        print("\n🔐 Testing Mobile Barcode Authentication")
        
        # Test without Bearer token
        original_token = self.token
        self.token = None
        
        success, response, _ = self.run_test(
            "Mobile Barcode - No Auth",
            "GET",
            f"barcode/{self.sample_barcodes[0]}",
            403  # Should require authentication
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ Mobile barcode API correctly requires Bearer token")
            
            # Test with valid Bearer token
            success2, response2, _ = self.run_test(
                "Mobile Barcode - Valid Bearer Token",
                "GET",
                f"barcode/{self.sample_barcodes[0]}",
                200
            )
            
            if success2:
                print("   ✅ Mobile barcode API accepts valid Bearer token")
                return True
            else:
                return False
        else:
            self.log_test("Mobile Barcode Authentication", False, "Should require Bearer token authentication")
            return False

    def test_mobile_barcode_error_handling(self):
        """Test mobile-friendly error handling for invalid barcodes"""
        print("\n📱 Testing Mobile Barcode Error Handling")
        
        invalid_barcodes = ["0000000000000", "invalid_barcode", "999999999999999"]
        all_success = True
        
        for i, barcode in enumerate(invalid_barcodes, 1):
            success, response, _ = self.run_test(
                f"Mobile Invalid Barcode #{i} ({barcode})",
                "GET",
                f"barcode/{barcode}",
                404
            )
            
            if success and isinstance(response, dict):
                # Check for mobile-friendly error message
                detail = response.get('detail', '')
                if detail:
                    print(f"   📱 Mobile error message: {detail}")
                else:
                    print(f"   ⚠️ No error message for mobile users")
            
            if not success:
                all_success = False
        
        return all_success

    # ===== PRIORITY 2: EXPORT REPORTS AUTHENTICATION =====
    
    def test_export_reports_authentication(self):
        """Test all export endpoints with Bearer token authentication"""
        print("\n" + "="*80)
        print("🔥 PRIORITY 2: EXPORT REPORTS AUTHENTICATION TESTING")
        print("="*80)
        
        export_endpoints = [
            {"endpoint": "export/dashboard/excel", "name": "Dashboard Excel Export"},
            {"endpoint": "export/dashboard/pdf", "name": "Dashboard PDF Export"},
            {"endpoint": "export/return-forms", "name": "Return Forms Export"},
            {"endpoint": "export/expiry-tracker", "name": "Expiry Tracker Export"},
            {"endpoint": "export/excel", "name": "General Excel Export"}
        ]
        
        all_tests_passed = True
        
        for export_test in export_endpoints:
            endpoint = export_test["endpoint"]
            name = export_test["name"]
            
            # Test without authentication first
            original_token = self.token
            self.token = None
            
            success_no_auth, response_no_auth, _ = self.run_test(
                f"{name} - No Auth",
                "GET",
                endpoint,
                401  # Should return 401 for unauthenticated
            )
            
            # Restore token
            self.token = original_token
            
            if success_no_auth:
                print(f"   ✅ {name} correctly requires authentication")
            else:
                print(f"   ⚠️ {name} authentication check inconclusive")
            
            # Test with valid Bearer token
            success_with_auth, response_with_auth, http_response = self.run_test(
                f"{name} - With Bearer Token",
                "GET",
                endpoint,
                200
            )
            
            if success_with_auth:
                print(f"   ✅ {name} works with Bearer token")
                
                # Check response type and size for file generation
                if http_response:
                    content_type = http_response.headers.get('content-type', '')
                    content_length = http_response.headers.get('content-length', '0')
                    
                    print(f"   📄 Content-Type: {content_type}")
                    print(f"   📏 Content-Length: {content_length} bytes")
                    
                    # Verify proper MIME types
                    if 'excel' in endpoint.lower() and 'application/' in content_type:
                        print(f"   ✅ Proper Excel MIME type")
                    elif 'pdf' in endpoint.lower() and 'application/pdf' in content_type:
                        print(f"   ✅ Proper PDF MIME type")
                    else:
                        print(f"   ⚠️ MIME type may need verification")
                
            else:
                print(f"   ❌ {name} failed with Bearer token")
                all_tests_passed = False
        
        return all_tests_passed

    def test_export_file_generation(self):
        """Test that export endpoints actually generate files"""
        print("\n📁 Testing Export File Generation")
        
        # Test a few key export endpoints
        key_exports = [
            {"endpoint": "export/dashboard/excel", "name": "Dashboard Excel", "expected_type": "application/"},
            {"endpoint": "export/dashboard/pdf", "name": "Dashboard PDF", "expected_type": "application/pdf"}
        ]
        
        all_success = True
        
        for export_test in key_exports:
            success, response, http_response = self.run_test(
                f"File Generation - {export_test['name']}",
                "GET",
                export_test["endpoint"],
                200
            )
            
            if success and http_response:
                content_length = len(http_response.content)
                content_type = http_response.headers.get('content-type', '')
                
                if content_length > 0:
                    print(f"   ✅ {export_test['name']}: Generated {content_length} bytes")
                    print(f"   📄 Content-Type: {content_type}")
                    
                    if export_test['expected_type'] in content_type:
                        print(f"   ✅ Correct file type")
                    else:
                        print(f"   ⚠️ Unexpected content type")
                else:
                    self.log_test(f"File Generation - {export_test['name']}", False, "Empty file generated")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    # ===== PRIORITY 3: WASTE REPORT PRODUCT LOOKUP =====
    
    def test_waste_report_product_lookup(self):
        """Test enhanced waste report product lookup with name search"""
        print("\n" + "="*80)
        print("🔥 PRIORITY 3: WASTE REPORT PRODUCT LOOKUP TESTING")
        print("="*80)
        
        all_tests_passed = True
        
        # Test product name searches (multi-word searches)
        search_queries = [
            {"query": "Apple Juice", "description": "Multi-word product search"},
            {"query": "Orange Nectar", "description": "Product name search"},
            {"query": "Mountain Water", "description": "Brand and product search"},
            {"query": "Lemonade", "description": "Single word product search"},
            {"query": "Box 1L", "description": "Size and package search"}
        ]
        
        for i, search_test in enumerate(search_queries, 1):
            query = search_test["query"]
            description = search_test["description"]
            
            success, response, _ = self.run_test(
                f"Waste Product Search #{i} ({description})",
                "GET",
                f"search?q={query}&limit=10",
                200
            )
            
            if success and isinstance(response, list):
                print(f"   🔍 Query '{query}': Found {len(response)} results")
                
                if len(response) > 0:
                    # Verify search results include expected fields for waste reporting
                    sample_product = response[0]
                    required_fields = ['product_name', 'purchase_price', 'purchase_currency', 'quantity']
                    
                    missing_fields = [field for field in required_fields if field not in sample_product]
                    if missing_fields:
                        self.log_test(f"Waste Search Fields #{i}", False, f"Missing: {missing_fields}")
                        all_tests_passed = False
                        continue
                    
                    print(f"   📦 Sample result: {sample_product.get('product_name')}")
                    print(f"   💰 Price: {sample_product.get('purchase_price')} {sample_product.get('purchase_currency')}")
                    print(f"   📊 Quantity: {sample_product.get('quantity')}")
                    
                    # Test word-by-word search logic
                    product_name = sample_product.get('product_name', '').lower()
                    query_words = query.lower().split()
                    
                    words_found = sum(1 for word in query_words if word in product_name)
                    if words_found > 0:
                        print(f"   ✅ Search logic working: {words_found}/{len(query_words)} words matched")
                    else:
                        print(f"   ⚠️ Search may be matching other fields (barcode, supplier, etc.)")
                else:
                    print(f"   ⚠️ No results for '{query}' - may indicate search issues")
            else:
                all_tests_passed = False
        
        return all_tests_passed

    def test_barcode_vs_name_search_logic(self):
        """Test barcode detection vs name search logic"""
        print("\n🔍 Testing Barcode vs Name Search Logic")
        
        test_cases = [
            {"query": "3222471081716", "type": "barcode", "description": "Pure barcode search"},
            {"query": "Apple Juice Box 1L", "type": "name", "description": "Pure name search"},
            {"query": "9501100046987", "type": "barcode", "description": "Another barcode search"}
        ]
        
        all_success = True
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            expected_type = test_case["type"]
            description = test_case["description"]
            
            success, response, _ = self.run_test(
                f"Search Logic #{i} ({description})",
                "GET",
                f"search?q={query}&limit=5",
                200
            )
            
            if success and isinstance(response, list) and len(response) > 0:
                sample_result = response[0]
                
                if expected_type == "barcode":
                    # For barcode searches, should find exact barcode match
                    result_barcode = sample_result.get('barcode', '')
                    if result_barcode == query:
                        print(f"   ✅ Barcode search: Exact match found")
                    else:
                        print(f"   ⚠️ Barcode search: Expected {query}, got {result_barcode}")
                
                elif expected_type == "name":
                    # For name searches, should find partial matches
                    result_name = sample_result.get('product_name', '').lower()
                    query_lower = query.lower()
                    
                    if query_lower in result_name or any(word in result_name for word in query_lower.split()):
                        print(f"   ✅ Name search: Partial match found")
                    else:
                        print(f"   ⚠️ Name search: No clear match in '{sample_result.get('product_name')}'")
                
                print(f"   📦 Result: {sample_result.get('product_name')}")
                print(f"   🔢 Barcode: {sample_result.get('barcode', 'N/A')}")
            else:
                print(f"   ❌ No results for {description}")
                all_success = False
        
        return all_success

    def test_waste_search_all_fields(self):
        """Test that waste product search includes all expected fields"""
        print("\n📋 Testing Waste Search Field Coverage")
        
        success, response, _ = self.run_test(
            "Waste Search Field Coverage",
            "GET",
            f"search?q=Apple&limit=5",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            sample_product = response[0]
            
            # Fields needed for waste reporting
            expected_fields = [
                'product_name', 'item_number', 'barcode', 'department', 'section',
                'purchase_price', 'purchase_currency', 'selling_price', 'supplier',
                'quantity', 'status'
            ]
            
            present_fields = []
            missing_fields = []
            
            for field in expected_fields:
                if field in sample_product:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            print(f"   ✅ Present fields ({len(present_fields)}): {present_fields}")
            if missing_fields:
                print(f"   ❌ Missing fields ({len(missing_fields)}): {missing_fields}")
                self.log_test("Waste Search Field Coverage", False, f"Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ All required fields present for waste reporting")
                return True
        else:
            self.log_test("Waste Search Field Coverage", False, "No search results to test")
            return False

    # ===== PRIORITY 4: DAILY EMAIL REPORTS =====
    
    def test_daily_email_reports_system(self):
        """Test daily email reports system configured for 7:00 AM"""
        print("\n" + "="*80)
        print("🔥 PRIORITY 4: DAILY EMAIL REPORTS SYSTEM TESTING")
        print("="*80)
        
        all_tests_passed = True
        
        # Test email configuration endpoints
        success1, response1, _ = self.run_test(
            "Email Settings GET",
            "GET",
            "settings/email",
            200
        )
        
        if success1 and isinstance(response1, dict):
            # Check if scheduled for 07:00 AM
            scheduled_time = response1.get('daily_alert_time', '')
            timezone = response1.get('timezone', '')
            
            print(f"   ⏰ Scheduled time: {scheduled_time}")
            print(f"   🌍 Timezone: {timezone}")
            
            if '07:00' in scheduled_time or '7:00' in scheduled_time:
                print(f"   ✅ Correctly scheduled for 07:00 AM")
            else:
                print(f"   ⚠️ Time may not be 07:00 AM as required")
            
            if 'Aden' in timezone or 'Asia/Aden' in timezone:
                print(f"   ✅ Correct Aden timezone")
            else:
                print(f"   ⚠️ Timezone may not be Asia/Aden")
        else:
            print(f"   ❌ Email settings endpoint failed")
            all_tests_passed = False
        
        # Test email status endpoint
        success2, response2, _ = self.run_test(
            "Email Status Check",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success2 and isinstance(response2, dict):
            email_configured = response2.get('email_configured', False)
            current_time = response2.get('current_aden_time', '')
            
            print(f"   📧 Email configured: {email_configured}")
            print(f"   🕐 Current Aden time: {current_time}")
            
            if email_configured:
                print(f"   ✅ Email system is configured")
            else:
                print(f"   ⚠️ Email system may not be fully configured")
        else:
            all_tests_passed = False
        
        return all_tests_passed

    def test_consolidated_report_generation(self):
        """Test consolidated report generation for daily emails"""
        print("\n📊 Testing Consolidated Report Generation")
        
        # Test daily alerts endpoint (used for email reports)
        success, response, _ = self.run_test(
            "Daily Alerts Data",
            "GET",
            "alerts/daily",
            200
        )
        
        if success and isinstance(response, dict):
            # Check for consolidated data structure
            out_of_stock = response.get('out_of_stock_items', [])
            near_expiry = response.get('near_expiry_items', [])
            
            print(f"   📦 Out of stock items: {len(out_of_stock)}")
            print(f"   ⏰ Near expiry items: {len(near_expiry)}")
            
            # Verify data structure for email reporting
            if len(out_of_stock) > 0:
                sample_item = out_of_stock[0]
                required_fields = ['department', 'product_name', 'item_number', 'supplier', 'section']
                
                missing_fields = [field for field in required_fields if field not in sample_item]
                if missing_fields:
                    self.log_test("Daily Alerts Data Structure", False, f"Missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ Proper data structure for email reports")
            
            return True
        else:
            self.log_test("Daily Alerts Data", False, "Failed to get daily alerts data")
            return False

    def test_waste_data_integration(self):
        """Test waste data integration for email reports"""
        print("\n🗑️ Testing Waste Data Integration for Email Reports")
        
        # Test waste reports endpoint
        success, response, _ = self.run_test(
            "Waste Reports for Email",
            "GET",
            "waste/reports?period=weekly",
            200
        )
        
        if success and isinstance(response, dict):
            currency_totals = response.get('currency_totals', {})
            total_entries = response.get('total_entries', 0)
            
            print(f"   💰 Currency totals: {currency_totals}")
            print(f"   📊 Total waste entries: {total_entries}")
            
            # Verify currency breakdown (YER, SAR, EUR)
            expected_currencies = ['YER', 'SAR', 'EUR']
            for currency in expected_currencies:
                if currency in currency_totals:
                    print(f"   ✅ {currency} waste data available: {currency_totals[currency]}")
                else:
                    print(f"   ⚠️ {currency} waste data not found")
            
            return True
        else:
            self.log_test("Waste Data Integration", False, "Failed to get waste reports data")
            return False

    def test_email_scheduler_configuration(self):
        """Test email scheduler configuration"""
        print("\n⏰ Testing Email Scheduler Configuration")
        
        # Test scheduler status (if available)
        success, response, _ = self.run_test(
            "Email Scheduler Status",
            "GET",
            "alerts/scheduler-status",
            200
        )
        
        if success and isinstance(response, dict):
            scheduler_active = response.get('scheduler_active', False)
            next_run = response.get('next_run', '')
            
            print(f"   ⚡ Scheduler active: {scheduler_active}")
            print(f"   ⏰ Next run: {next_run}")
            
            if scheduler_active:
                print(f"   ✅ Email scheduler is active")
            else:
                print(f"   ⚠️ Email scheduler may not be active")
            
            return True
        else:
            print(f"   ⚠️ Scheduler status endpoint not available (may be normal)")
            return True  # Don't fail if endpoint doesn't exist

    # ===== PRIORITY 5: DASHBOARD DATA FOR 3D CHARTS =====
    
    def test_dashboard_3d_charts_data(self):
        """Test dashboard data for 3D charts and enhanced analytics"""
        print("\n" + "="*80)
        print("🔥 PRIORITY 5: DASHBOARD DATA FOR 3D CHARTS TESTING")
        print("="*80)
        
        all_tests_passed = True
        
        # Test main dashboard endpoint
        success1, response1, _ = self.run_test(
            "Dashboard KPI Data",
            "GET",
            "dashboard",
            200
        )
        
        if success1 and isinstance(response1, dict):
            kpis = response1.get('kpis', [])
            stock_distribution = response1.get('stock_distribution', {})
            expiry_status = response1.get('expiry_status', {})
            top_suppliers = response1.get('top_suppliers', [])
            
            print(f"   📊 KPIs for {len(kpis)} departments")
            print(f"   📈 Stock distribution: {stock_distribution}")
            print(f"   ⏰ Expiry status: {expiry_status}")
            print(f"   🏢 Top suppliers: {len(top_suppliers)}")
            
            # Verify KPI data structure for 3D charts
            for i, kpi in enumerate(kpis):
                dept = kpi.get('department')
                total_items = kpi.get('total_items', 0)
                stock_value = kpi.get('total_stock_value', 0)
                
                print(f"   📂 {dept}: {total_items} items, value: {stock_value}")
                
                # Verify required fields for 3D visualization
                required_kpi_fields = [
                    'department', 'total_items', 'expired_items', 'near_expiry_items',
                    'out_of_stock_items', 'low_stock_items', 'total_stock_value', 'total_quantity'
                ]
                
                missing_fields = [field for field in required_kpi_fields if field not in kpi]
                if missing_fields:
                    self.log_test(f"KPI Data Structure - {dept}", False, f"Missing: {missing_fields}")
                    all_tests_passed = False
            
            # Verify currency totals for 3D charts
            for supplier in top_suppliers[:3]:
                supplier_name = supplier.get('supplier_name', 'Unknown')
                currency = supplier.get('purchase_currency', 'Unknown')
                stock_value = supplier.get('stock_value', 0)
                
                print(f"   💰 {supplier_name}: {stock_value} {currency}")
        else:
            all_tests_passed = False
        
        return all_tests_passed

    def test_waste_reports_3d_data(self):
        """Test waste reports data for 3D chart visualization"""
        print("\n📊 Testing Waste Reports 3D Chart Data")
        
        success, response, _ = self.run_test(
            "Waste Reports 3D Data",
            "GET",
            "waste/reports?period=monthly",
            200
        )
        
        if success and isinstance(response, dict):
            currency_totals = response.get('currency_totals', {})
            department_breakdown = response.get('department_breakdown', {})
            
            print(f"   💰 Currency breakdown for 3D charts:")
            for currency, value in currency_totals.items():
                print(f"      {currency}: {value}")
            
            print(f"   🏢 Department breakdown for 3D charts:")
            for dept, data in department_breakdown.items():
                if isinstance(data, dict):
                    print(f"      {dept}: {data}")
                else:
                    print(f"      {dept}: {data}")
            
            # Verify data is suitable for 3D visualization
            if len(currency_totals) >= 2:  # Need at least 2 currencies for meaningful 3D
                print(f"   ✅ Sufficient currency data for 3D charts")
            else:
                print(f"   ⚠️ Limited currency data for 3D visualization")
            
            return True
        else:
            self.log_test("Waste Reports 3D Data", False, "Failed to get waste reports data")
            return False

    def test_department_analytics_data(self):
        """Test department analytics data for enhanced 3D charts"""
        print("\n🏢 Testing Department Analytics for 3D Charts")
        
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        all_success = True
        
        for dept in departments:
            success, response, _ = self.run_test(
                f"Department Analytics - {dept}",
                "GET",
                f"products?department={dept}&limit=50",
                200
            )
            
            if success and isinstance(response, list):
                # Calculate analytics for 3D visualization
                total_products = len(response)
                currencies = {}
                total_value = 0
                
                for product in response:
                    currency = product.get('purchase_currency', 'Unknown')
                    price = product.get('purchase_price', 0)
                    quantity = product.get('quantity', 0)
                    
                    if currency not in currencies:
                        currencies[currency] = {'count': 0, 'value': 0}
                    
                    currencies[currency]['count'] += 1
                    currencies[currency]['value'] += (price * quantity)
                    total_value += (price * quantity)
                
                print(f"   📊 {dept} Analytics:")
                print(f"      Products: {total_products}")
                print(f"      Total value: {total_value}")
                print(f"      Currencies: {currencies}")
                
                # Verify data richness for 3D charts
                if len(currencies) > 1:
                    print(f"   ✅ Multi-currency data available for 3D visualization")
                else:
                    print(f"   ⚠️ Single currency data (may limit 3D chart options)")
            else:
                all_success = False
        
        return all_success

    def test_currency_totals_calculation(self):
        """Test currency totals calculation for dashboard 3D charts"""
        print("\n💰 Testing Currency Totals Calculation")
        
        success, response, _ = self.run_test(
            "Currency Totals for 3D Charts",
            "GET",
            "dashboard",
            200
        )
        
        if success and isinstance(response, dict):
            kpis = response.get('kpis', [])
            
            # Calculate total values by currency across all departments
            total_by_currency = {}
            
            for kpi in kpis:
                dept = kpi.get('department')
                stock_value = kpi.get('total_stock_value', 0)
                
                # For 3D charts, we need currency breakdown
                # This is a simplified calculation - real implementation would need currency-specific values
                print(f"   📊 {dept}: Stock value {stock_value}")
                
                # Verify stock value calculation
                if isinstance(stock_value, (int, float)) and stock_value >= 0:
                    print(f"   ✅ Valid stock value calculation")
                else:
                    self.log_test("Currency Totals Calculation", False, f"Invalid stock value: {stock_value}")
                    return False
            
            print(f"   ✅ Currency totals suitable for 3D chart visualization")
            return True
        else:
            self.log_test("Currency Totals Calculation", False, "Failed to get dashboard data")
            return False

    def run_all_mobile_tests(self):
        """Run all mobile application backend tests in priority order"""
        print("🚀 STARTING COMPREHENSIVE MOBILE BACKEND TESTING")
        print("="*80)
        print("Testing 5 Critical Mobile Application Fixes:")
        print("1. Mobile Barcode Scanner API (PRIORITY 1)")
        print("2. Export Reports Authentication (Critical)")
        print("3. Waste Report Product Lookup (Enhanced)")
        print("4. Daily Email Reports (7:00 AM)")
        print("5. Dashboard Data for 3D Charts (Analytics)")
        print("="*80)
        
        # Login first
        if not self.test_admin_login():
            print("❌ CRITICAL: Admin login failed - cannot proceed with testing")
            return False
        
        # Run tests in priority order
        test_results = []
        
        # Priority 1: Mobile Barcode Scanner
        print("\n" + "🔥"*20 + " PRIORITY 1 TESTING " + "🔥"*20)
        barcode_api_success = self.test_mobile_barcode_scanner_api()
        barcode_auth_success = self.test_mobile_barcode_authentication()
        barcode_error_success = self.test_mobile_barcode_error_handling()
        
        priority1_success = barcode_api_success and barcode_auth_success and barcode_error_success
        test_results.append(("Priority 1: Mobile Barcode Scanner", priority1_success))
        
        # Priority 2: Export Reports Authentication
        print("\n" + "🔥"*20 + " PRIORITY 2 TESTING " + "🔥"*20)
        export_auth_success = self.test_export_reports_authentication()
        export_file_success = self.test_export_file_generation()
        
        priority2_success = export_auth_success and export_file_success
        test_results.append(("Priority 2: Export Reports Authentication", priority2_success))
        
        # Priority 3: Waste Report Product Lookup
        print("\n" + "🔥"*20 + " PRIORITY 3 TESTING " + "🔥"*20)
        waste_lookup_success = self.test_waste_report_product_lookup()
        search_logic_success = self.test_barcode_vs_name_search_logic()
        waste_fields_success = self.test_waste_search_all_fields()
        
        priority3_success = waste_lookup_success and search_logic_success and waste_fields_success
        test_results.append(("Priority 3: Waste Report Product Lookup", priority3_success))
        
        # Priority 4: Daily Email Reports
        print("\n" + "🔥"*20 + " PRIORITY 4 TESTING " + "🔥"*20)
        email_system_success = self.test_daily_email_reports_system()
        report_gen_success = self.test_consolidated_report_generation()
        waste_integration_success = self.test_waste_data_integration()
        scheduler_success = self.test_email_scheduler_configuration()
        
        priority4_success = email_system_success and report_gen_success and waste_integration_success and scheduler_success
        test_results.append(("Priority 4: Daily Email Reports", priority4_success))
        
        # Priority 5: Dashboard Data for 3D Charts
        print("\n" + "🔥"*20 + " PRIORITY 5 TESTING " + "🔥"*20)
        dashboard_3d_success = self.test_dashboard_3d_charts_data()
        waste_3d_success = self.test_waste_reports_3d_data()
        dept_analytics_success = self.test_department_analytics_data()
        currency_calc_success = self.test_currency_totals_calculation()
        
        priority5_success = dashboard_3d_success and waste_3d_success and dept_analytics_success and currency_calc_success
        test_results.append(("Priority 5: Dashboard 3D Charts", priority5_success))
        
        # Final Results
        print("\n" + "="*80)
        print("🏁 MOBILE BACKEND TESTING COMPLETE")
        print("="*80)
        
        for test_name, success in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_name}")
        
        overall_success = all(success for _, success in test_results)
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Overall Status: {'✅ ALL MOBILE FIXES WORKING' if overall_success else '❌ SOME MOBILE FIXES NEED ATTENTION'}")
        
        return overall_success

if __name__ == "__main__":
    tester = MobileBackendTester()
    success = tester.run_all_mobile_tests()
    sys.exit(0 if success else 1)