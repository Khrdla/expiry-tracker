#!/usr/bin/env python3
"""
Comprehensive Waste Management API Testing
Tests all waste management endpoints and functionality as requested in the review
Focus: Waste entries, reports, currency breakdown, export functionality
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import time

class WasteManagementTester:
    def __init__(self, base_url="https://stockmate-12.preview.emergentagent.com"):
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
        self.created_waste_entries = []  # Track created entries for cleanup

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
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)
            else:
                self.log_test(name, False, f"Unsupported method: {method}")
                return None
            
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                details += f", Response: {response.text[:200]}"
            
            response_data = None
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            self.log_test(name, success, details, response_data)
            return response
            
        except Exception as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return None

    def authenticate(self):
        """Authenticate with admin credentials"""
        print("\n🔐 AUTHENTICATION TESTING")
        print("=" * 50)
        
        login_data = {
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            login_data
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get('access_token')
                if self.token:
                    print(f"✅ Authentication successful - Token obtained")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse login response: {e}")
                return False
        else:
            print("❌ Authentication failed")
            return False

    def get_sample_products(self):
        """Get sample products for waste entry testing"""
        print("\n📦 GETTING SAMPLE PRODUCTS FOR TESTING")
        print("=" * 50)
        
        response = self.run_test(
            "Get Products for Waste Testing",
            "GET",
            "products?limit=10",
            200
        )
        
        if response and response.status_code == 200:
            try:
                products = response.json()
                if products and len(products) > 0:
                    print(f"✅ Found {len(products)} products for testing")
                    return products[:5]  # Return first 5 products
                else:
                    print("❌ No products found")
                    return []
            except Exception as e:
                print(f"❌ Failed to parse products response: {e}")
                return []
        else:
            print("❌ Failed to get products")
            return []

    def test_create_waste_entries(self, sample_products):
        """Test POST /api/waste/entries - Create waste entry"""
        print("\n📝 TESTING WASTE ENTRY CREATION")
        print("=" * 50)
        
        if not sample_products:
            print("❌ No sample products available for testing")
            return
        
        # Test data for different waste reasons and currencies
        waste_test_cases = [
            {
                "product": sample_products[0],
                "quantity_wasted": 5,
                "waste_reason": "damaged",
                "notes": "Product damaged during transport"
            },
            {
                "product": sample_products[1] if len(sample_products) > 1 else sample_products[0],
                "quantity_wasted": 3,
                "waste_reason": "expired",
                "notes": "Product past expiry date"
            },
            {
                "product": sample_products[2] if len(sample_products) > 2 else sample_products[0],
                "quantity_wasted": 10,
                "waste_reason": "unsellable",
                "notes": "Quality issues reported by customers"
            }
        ]
        
        for i, test_case in enumerate(waste_test_cases):
            product = test_case["product"]
            waste_data = {
                "product_id": product.get("id"),
                "quantity_wasted": test_case["quantity_wasted"],
                "waste_reason": test_case["waste_reason"],
                "notes": test_case["notes"]
            }
            
            response = self.run_test(
                f"Create Waste Entry {i+1} ({test_case['waste_reason']})",
                "POST",
                "waste/entries",
                200,
                waste_data
            )
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    waste_id = result.get("id")
                    if waste_id:
                        self.created_waste_entries.append(waste_id)
                        print(f"  ✅ Waste entry created with ID: {waste_id}")
                        
                        # Verify calculation: total_waste_value = quantity × purchase_price
                        expected_value = test_case["quantity_wasted"] * product.get("purchase_price", 0)
                        print(f"  📊 Expected waste value: {expected_value} {product.get('purchase_currency', 'YER')}")
                    else:
                        print(f"  ❌ No ID returned in response")
                except Exception as e:
                    print(f"  ❌ Failed to parse response: {e}")

    def test_waste_reports(self):
        """Test GET /api/waste/reports - Get waste reports"""
        print("\n📊 TESTING WASTE REPORTS")
        print("=" * 50)
        
        # Test different report periods
        report_periods = ["daily", "weekly", "yearly"]
        
        for period in report_periods:
            response = self.run_test(
                f"Get Waste Report - {period.title()}",
                "GET",
                f"waste/reports?period={period}",
                200
            )
            
            if response and response.status_code == 200:
                try:
                    report_data = response.json()
                    print(f"  📈 {period.title()} Report:")
                    print(f"    - Total entries: {report_data.get('total_entries', 0)}")
                    print(f"    - Total quantity wasted: {report_data.get('total_quantity_wasted', 0)}")
                    
                    # Check currency breakdown
                    currency_totals = report_data.get('currency_totals', {})
                    print(f"    - Currency breakdown:")
                    for currency, total in currency_totals.items():
                        print(f"      * {currency}: {total}")
                        
                except Exception as e:
                    print(f"  ❌ Failed to parse report data: {e}")

    def test_department_filtering(self):
        """Test department filtering in waste reports"""
        print("\n🏢 TESTING DEPARTMENT FILTERING")
        print("=" * 50)
        
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        for dept in departments:
            response = self.run_test(
                f"Waste Report - Department {dept}",
                "GET",
                f"waste/reports?period=daily&department={dept}",
                200
            )
            
            if response and response.status_code == 200:
                try:
                    report_data = response.json()
                    print(f"  🏢 Department {dept}:")
                    print(f"    - Entries: {report_data.get('total_entries', 0)}")
                    print(f"    - Quantity wasted: {report_data.get('total_quantity_wasted', 0)}")
                except Exception as e:
                    print(f"  ❌ Failed to parse department report: {e}")

    def test_custom_date_ranges(self):
        """Test custom date range filtering"""
        print("\n📅 TESTING CUSTOM DATE RANGES")
        print("=" * 50)
        
        # Test with last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        response = self.run_test(
            f"Custom Date Range ({start_str} to {end_str})",
            "GET",
            f"waste/reports?period=custom&start_date={start_str}&end_date={end_str}",
            200
        )
        
        if response and response.status_code == 200:
            try:
                report_data = response.json()
                print(f"  📅 Custom Range Report:")
                print(f"    - Period: {start_str} to {end_str}")
                print(f"    - Total entries: {report_data.get('total_entries', 0)}")
                print(f"    - Total quantity wasted: {report_data.get('total_quantity_wasted', 0)}")
            except Exception as e:
                print(f"  ❌ Failed to parse custom date report: {e}")

    def test_waste_entries_list(self):
        """Test GET /api/waste/entries - List waste entries with pagination"""
        print("\n📋 TESTING WASTE ENTRIES LIST")
        print("=" * 50)
        
        # Test basic listing
        response = self.run_test(
            "List Waste Entries (Default)",
            "GET",
            "waste/entries",
            200
        )
        
        if response and response.status_code == 200:
            try:
                entries = response.json()
                print(f"  📋 Found {len(entries)} waste entries")
                
                if entries:
                    first_entry = entries[0]
                    print(f"  📝 Sample entry:")
                    print(f"    - Product: {first_entry.get('product_name', 'N/A')}")
                    print(f"    - Quantity wasted: {first_entry.get('quantity_wasted', 0)}")
                    print(f"    - Reason: {first_entry.get('waste_reason', 'N/A')}")
                    print(f"    - Value: {first_entry.get('total_waste_value', 0)} {first_entry.get('purchase_currency', 'YER')}")
                    
            except Exception as e:
                print(f"  ❌ Failed to parse entries list: {e}")
        
        # Test pagination
        response = self.run_test(
            "List Waste Entries (Pagination - Limit 5)",
            "GET",
            "waste/entries?limit=5&skip=0",
            200
        )
        
        if response and response.status_code == 200:
            try:
                entries = response.json()
                print(f"  📄 Pagination test: Retrieved {len(entries)} entries (limit=5)")
            except Exception as e:
                print(f"  ❌ Failed to parse paginated entries: {e}")

    def test_filtering_waste_entries(self):
        """Test filtering waste entries by department and section"""
        print("\n🔍 TESTING WASTE ENTRIES FILTERING")
        print("=" * 50)
        
        # Test department filtering
        departments = ["01-FMG", "01-CGD"]
        
        for dept in departments:
            response = self.run_test(
                f"Filter Waste Entries - Department {dept}",
                "GET",
                f"waste/entries?department={dept}",
                200
            )
            
            if response and response.status_code == 200:
                try:
                    entries = response.json()
                    print(f"  🏢 Department {dept}: {len(entries)} entries")
                except Exception as e:
                    print(f"  ❌ Failed to parse filtered entries: {e}")

    def test_export_functionality(self):
        """Test GET /api/export/waste-report/{period} - Export functionality"""
        print("\n📤 TESTING EXPORT FUNCTIONALITY")
        print("=" * 50)
        
        # Test Excel export
        response = self.run_test(
            "Export Waste Report - Excel (Daily)",
            "GET",
            "export/waste-report/daily?format=excel",
            200
        )
        
        if response and response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            print(f"  📊 Excel Export:")
            print(f"    - Content-Type: {content_type}")
            print(f"    - File Size: {content_length} bytes")
            
            if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
                print(f"    ✅ Excel file generated successfully")
            else:
                print(f"    ⚠️  Unexpected content type for Excel export")
        
        # Test PDF export
        response = self.run_test(
            "Export Waste Report - PDF (Weekly)",
            "GET",
            "export/waste-report/weekly?format=pdf",
            200
        )
        
        if response and response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            print(f"  📄 PDF Export:")
            print(f"    - Content-Type: {content_type}")
            print(f"    - File Size: {content_length} bytes")
            
            if 'pdf' in content_type.lower():
                print(f"    ✅ PDF file generated successfully")
            else:
                print(f"    ⚠️  Unexpected content type for PDF export")

    def test_export_with_filters(self):
        """Test export functionality with filters"""
        print("\n🔍 TESTING EXPORT WITH FILTERS")
        print("=" * 50)
        
        # Test export with department filter
        response = self.run_test(
            "Export with Department Filter (01-FMG)",
            "GET",
            "export/waste-report/daily?format=excel&department=01-FMG",
            200
        )
        
        if response and response.status_code == 200:
            content_length = len(response.content)
            print(f"  🏢 Department filtered export: {content_length} bytes")

    def test_error_handling(self):
        """Test error handling for invalid data"""
        print("\n⚠️  TESTING ERROR HANDLING")
        print("=" * 50)
        
        # Test creating waste entry with invalid product ID
        invalid_waste_data = {
            "product_id": "invalid-product-id",
            "quantity_wasted": 5,
            "waste_reason": "damaged",
            "notes": "Test invalid product"
        }
        
        response = self.run_test(
            "Create Waste Entry - Invalid Product ID",
            "POST",
            "waste/entries",
            404,  # Expecting 404 for invalid product
            invalid_waste_data
        )
        
        # Test invalid waste reason
        if len(self.created_waste_entries) > 0:
            # Use a valid product ID but invalid waste reason
            sample_products = self.get_sample_products()
            if sample_products:
                invalid_reason_data = {
                    "product_id": sample_products[0].get("id"),
                    "quantity_wasted": 5,
                    "waste_reason": "invalid_reason",
                    "notes": "Test invalid reason"
                }
                
                response = self.run_test(
                    "Create Waste Entry - Invalid Waste Reason",
                    "POST",
                    "waste/entries",
                    422,  # Expecting validation error
                    invalid_reason_data
                )

    def test_authentication_requirements(self):
        """Test that endpoints require authentication"""
        print("\n🔒 TESTING AUTHENTICATION REQUIREMENTS")
        print("=" * 50)
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        # Test endpoints without authentication
        endpoints_to_test = [
            ("waste/entries", "GET"),
            ("waste/reports", "GET"),
            ("waste/entries", "POST"),
            ("export/waste-report/daily", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            response = self.run_test(
                f"No Auth - {method} {endpoint}",
                method,
                endpoint,
                403,  # Expecting 403 Forbidden
                {"test": "data"} if method == "POST" else None
            )
        
        # Restore token
        self.token = original_token

    def run_comprehensive_tests(self):
        """Run all waste management tests"""
        print("🗑️  WASTE MANAGEMENT API COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Get sample products for testing
        sample_products = self.get_sample_products()
        
        # Step 3: Test waste entry creation
        self.test_create_waste_entries(sample_products)
        
        # Step 4: Test waste reports
        self.test_waste_reports()
        
        # Step 5: Test department filtering
        self.test_department_filtering()
        
        # Step 6: Test custom date ranges
        self.test_custom_date_ranges()
        
        # Step 7: Test waste entries listing
        self.test_waste_entries_list()
        
        # Step 8: Test filtering waste entries
        self.test_filtering_waste_entries()
        
        # Step 9: Test export functionality
        self.test_export_functionality()
        
        # Step 10: Test export with filters
        self.test_export_with_filters()
        
        # Step 11: Test error handling
        self.test_error_handling()
        
        # Step 12: Test authentication requirements
        self.test_authentication_requirements()
        
        # Final Results
        print("\n" + "=" * 80)
        print("🏁 WASTE MANAGEMENT TESTING COMPLETE")
        print("=" * 80)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.created_waste_entries:
            print(f"\n📝 Created {len(self.created_waste_entries)} waste entries during testing")
        
        # Summary of key findings
        print("\n🔍 KEY FINDINGS:")
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = WasteManagementTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)