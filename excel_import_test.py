#!/usr/bin/env python3
"""
Excel Import Functionality Testing for Expiry Tracker
Tests the new Excel Import endpoints added in Settings
Focus: POST /api/system/import-excel and GET /api/system/import-template
"""

import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime

class ExcelImportTester:
    def __init__(self, base_url="https://return-manager-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials
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

    def login(self):
        """Login to get authentication token"""
        print("🔐 Logging in as admin...")
        
        login_data = {
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def test_excel_template_download(self):
        """Test GET /api/system/import-template endpoint"""
        print("\n📥 Testing Excel Template Download")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(
                f"{self.api_url}/system/import-template",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Check Content-Type header
                content_type = response.headers.get('Content-Type', '')
                if 'spreadsheet' in content_type or 'excel' in content_type:
                    print(f"   ✅ Correct Content-Type: {content_type}")
                else:
                    print(f"   ⚠️ Content-Type: {content_type}")
                
                # Check Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    print(f"   ✅ Proper download header: {content_disposition}")
                else:
                    print(f"   ⚠️ Content-Disposition: {content_disposition}")
                
                # Check file size
                content_length = len(response.content)
                if content_length > 5000:  # Should be at least 5KB for Excel with data
                    print(f"   ✅ Template file size: {content_length} bytes")
                    self.log_test("Excel Template Download", True, f"File size: {content_length} bytes")
                    
                    # Try to read as Excel to verify it's valid
                    try:
                        excel_data = pd.read_excel(io.BytesIO(response.content), sheet_name=None)
                        sheets = list(excel_data.keys())
                        print(f"   ✅ Valid Excel file with sheets: {sheets}")
                        
                        # Check if it has Instructions sheet
                        if 'Instructions' in sheets:
                            print("   ✅ Instructions sheet found")
                            instructions_df = excel_data['Instructions']
                            print(f"   📋 Instructions has {len(instructions_df)} rows")
                        
                        # Check if it has Products sheet with sample data
                        if 'Products' in sheets:
                            print("   ✅ Products sheet found")
                            products_df = excel_data['Products']
                            print(f"   📦 Sample products: {len(products_df)} rows")
                            
                            # Verify required columns
                            required_columns = [
                                'product_name', 'department', 'section', 'family', 'sub_family',
                                'supplier', 'purchase_price', 'purchase_currency'
                            ]
                            
                            missing_columns = []
                            for col in required_columns:
                                if col not in products_df.columns:
                                    missing_columns.append(col)
                            
                            if not missing_columns:
                                print("   ✅ All required columns present in template")
                            else:
                                print(f"   ❌ Missing columns: {missing_columns}")
                                self.log_test("Template Required Columns", False, f"Missing: {missing_columns}")
                                return False
                        
                        return True
                        
                    except Exception as e:
                        print(f"   ❌ Invalid Excel file: {str(e)}")
                        self.log_test("Excel Template Validation", False, f"Invalid Excel: {str(e)}")
                        return False
                else:
                    print(f"   ❌ File too small: {content_length} bytes")
                    self.log_test("Excel Template Download", False, f"File too small: {content_length} bytes")
                    return False
            else:
                print(f"   ❌ Download failed: {response.status_code}")
                self.log_test("Excel Template Download", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Template download error: {str(e)}")
            self.log_test("Excel Template Download", False, str(e))
            return False

    def create_test_excel_file(self, scenario="valid"):
        """Create test Excel file for different scenarios"""
        if scenario == "valid":
            data = {
                'product_name': ['Test Apple Juice', 'Test Bread Loaf', 'Test Milk Carton'],
                'department': ['01-CGD', '01-FMG', '01-FMG'],
                'section': ['S010 - Beverage', 'S016 - Bakery', 'S015 - Dairy'],
                'family': ['Beverages', 'Bakery', 'Dairy'],
                'sub_family': ['Fruit Juices', 'Bread', 'Milk'],
                'supplier': ['Test Supplier A', 'Test Supplier B', 'Test Supplier C'],
                'purchase_price': [2.50, 1.25, 3.00],
                'purchase_currency': ['EUR', 'YER', 'SAR'],
                'item_number': ['TEST001', 'TEST002', 'TEST003'],
                'barcode': [f'TEST{datetime.now().microsecond}001', f'TEST{datetime.now().microsecond}002', f'TEST{datetime.now().microsecond}003'],
                'selling_price': [350, 175, 420],
                'quantity': [50, 100, 75]
            }
        elif scenario == "invalid_department":
            data = {
                'product_name': ['Test Product'],
                'department': ['INVALID-DEPT'],  # Invalid department
                'section': ['Test Section'],
                'family': ['Test Family'],
                'sub_family': ['Test Sub'],
                'supplier': ['Test Supplier'],
                'purchase_price': [10.0],
                'purchase_currency': ['YER']
            }
        elif scenario == "invalid_currency":
            data = {
                'product_name': ['Test Product'],
                'department': ['01-FMG'],
                'section': ['Test Section'],
                'family': ['Test Family'],
                'sub_family': ['Test Sub'],
                'supplier': ['Test Supplier'],
                'purchase_price': [10.0],
                'purchase_currency': ['INVALID']  # Invalid currency
            }
        elif scenario == "missing_columns":
            data = {
                'product_name': ['Test Product'],
                'department': ['01-FMG']
                # Missing required columns
            }
        elif scenario == "duplicate_barcode":
            # First create a product with a known barcode, then try to import duplicate
            data = {
                'product_name': ['Duplicate Test Product'],
                'department': ['01-FMG'],
                'section': ['Test Section'],
                'family': ['Test Family'],
                'sub_family': ['Test Sub'],
                'supplier': ['Test Supplier'],
                'purchase_price': [10.0],
                'purchase_currency': ['YER'],
                'barcode': ['9501100046987']  # This barcode likely exists in the system
            }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)
        
        output.seek(0)
        return output.getvalue()

    def test_excel_import_valid_data(self):
        """Test Excel import with valid data"""
        print("\n✅ Testing Excel Import with Valid Data")
        
        try:
            # Create valid test Excel file
            excel_data = self.create_test_excel_file("valid")
            
            headers = {'Authorization': f'Bearer {self.token}'}
            files = {'file': ('test_products.xlsx', excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = requests.post(
                f"{self.api_url}/system/import-excel",
                headers=headers,
                files=files,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Import successful: {response.status_code}")
                
                # Check response format
                expected_fields = ['message', 'import_summary', 'status']
                for field in expected_fields:
                    if field not in result:
                        print(f"   ❌ Missing field in response: {field}")
                        self.log_test("Excel Import Response Format", False, f"Missing {field}")
                        return False
                
                # Check import summary
                import_summary = result.get('import_summary', {})
                required_summary_fields = ['total_rows', 'successful_imports', 'failed_imports', 'errors', 'imported_products']
                
                for field in required_summary_fields:
                    if field not in import_summary:
                        print(f"   ❌ Missing summary field: {field}")
                        self.log_test("Excel Import Summary Format", False, f"Missing {field}")
                        return False
                
                # Print statistics
                total_rows = import_summary.get('total_rows', 0)
                successful = import_summary.get('successful_imports', 0)
                failed = import_summary.get('failed_imports', 0)
                
                print(f"   📊 Import Statistics:")
                print(f"      Total rows: {total_rows}")
                print(f"      Successful: {successful}")
                print(f"      Failed: {failed}")
                print(f"      Success rate: {(successful/total_rows)*100:.1f}%" if total_rows > 0 else "N/A")
                
                # Check imported products
                imported_products = import_summary.get('imported_products', [])
                if imported_products:
                    print(f"   📦 Imported products:")
                    for product in imported_products[:3]:  # Show first 3
                        print(f"      - Row {product.get('row')}: {product.get('product_name')} ({product.get('department')})")
                
                # Check for errors
                errors = import_summary.get('errors', [])
                if errors:
                    print(f"   ⚠️ Import errors:")
                    for error in errors[:3]:  # Show first 3
                        print(f"      - {error}")
                
                self.log_test("Excel Import Valid Data", True, f"Imported {successful}/{total_rows} products")
                return True
                
            else:
                print(f"   ❌ Import failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                self.log_test("Excel Import Valid Data", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Import test error: {str(e)}")
            self.log_test("Excel Import Valid Data", False, str(e))
            return False

    def test_excel_import_authentication(self):
        """Test Excel import requires admin authentication"""
        print("\n🔐 Testing Excel Import Authentication")
        
        # Test without authentication
        excel_data = self.create_test_excel_file("valid")
        files = {'file': ('test_products.xlsx', excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        response = requests.post(
            f"{self.api_url}/system/import-excel",
            files=files,
            timeout=30
        )
        
        if response.status_code in [401, 403]:
            print(f"   ✅ Correctly requires authentication: {response.status_code}")
            self.log_test("Excel Import Authentication", True, f"HTTP {response.status_code}")
            return True
        else:
            print(f"   ❌ Should require authentication, got: {response.status_code}")
            self.log_test("Excel Import Authentication", False, f"HTTP {response.status_code}")
            return False

    def test_excel_import_file_validation(self):
        """Test Excel import file format validation"""
        print("\n📋 Testing Excel Import File Validation")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test with non-Excel file
        text_data = b"This is not an Excel file"
        files = {'file': ('test.txt', text_data, 'text/plain')}
        
        response = requests.post(
            f"{self.api_url}/system/import-excel",
            headers=headers,
            files=files,
            timeout=30
        )
        
        if response.status_code == 400:
            result = response.json()
            detail = result.get('detail', '')
            if 'Excel' in detail or '.xlsx' in detail or '.xls' in detail:
                print(f"   ✅ Correctly rejects non-Excel files: {detail}")
                self.log_test("Excel Import File Validation", True, detail)
                return True
        
        print(f"   ❌ Should reject non-Excel files, got: {response.status_code}")
        self.log_test("Excel Import File Validation", False, f"HTTP {response.status_code}")
        return False

    def test_excel_import_invalid_scenarios(self):
        """Test Excel import with various invalid data scenarios"""
        print("\n❌ Testing Excel Import Invalid Data Scenarios")
        
        scenarios = [
            {"name": "Invalid Department", "scenario": "invalid_department"},
            {"name": "Invalid Currency", "scenario": "invalid_currency"},
            {"name": "Missing Required Columns", "scenario": "missing_columns"},
            {"name": "Duplicate Barcode", "scenario": "duplicate_barcode"}
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        all_success = True
        
        for test_scenario in scenarios:
            print(f"\n   🧪 Testing: {test_scenario['name']}")
            
            try:
                excel_data = self.create_test_excel_file(test_scenario['scenario'])
                files = {'file': (f"test_{test_scenario['scenario']}.xlsx", excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                response = requests.post(
                    f"{self.api_url}/system/import-excel",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 400:
                    result = response.json()
                    detail = result.get('detail', '')
                    print(f"      ✅ Correctly rejected: {detail}")
                elif response.status_code == 200:
                    # Check if it was handled gracefully with errors in the response
                    result = response.json()
                    import_summary = result.get('import_summary', {})
                    failed_imports = import_summary.get('failed_imports', 0)
                    errors = import_summary.get('errors', [])
                    
                    if failed_imports > 0 or errors:
                        print(f"      ✅ Handled gracefully with {failed_imports} failures")
                        if errors:
                            print(f"      Error: {errors[0]}")
                    else:
                        print(f"      ⚠️ Unexpected success - may need review")
                else:
                    print(f"      ❌ Unexpected response: {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                print(f"      ❌ Test error: {str(e)}")
                all_success = False
        
        self.log_test("Excel Import Invalid Scenarios", all_success, "Tested multiple invalid scenarios")
        return all_success

    def run_all_tests(self):
        """Run all Excel Import tests"""
        print("🚀 Starting Excel Import Functionality Testing")
        print("Focus: NEW EXCEL IMPORT ENDPOINTS IN SETTINGS")
        print("=" * 70)
        
        # Login first
        if not self.login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Test 1: Excel Template Download
        print("\n📥 EXCEL TEMPLATE DOWNLOAD TESTING")
        print("-" * 50)
        self.test_excel_template_download()
        
        # Test 2: Authentication Requirements
        print("\n🔐 EXCEL IMPORT AUTHENTICATION TESTING")
        print("-" * 50)
        self.test_excel_import_authentication()
        
        # Test 3: File Format Validation
        print("\n📋 EXCEL IMPORT FILE VALIDATION TESTING")
        print("-" * 50)
        self.test_excel_import_file_validation()
        
        # Test 4: Valid Data Import
        print("\n✅ EXCEL IMPORT VALID DATA TESTING")
        print("-" * 50)
        self.test_excel_import_valid_data()
        
        # Test 5: Invalid Data Scenarios
        print("\n❌ EXCEL IMPORT INVALID DATA TESTING")
        print("-" * 50)
        self.test_excel_import_invalid_scenarios()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 EXCEL IMPORT TEST RESULTS")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        # Show successful tests
        successful_tests = [test for test in self.test_results if test['success']]
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS ({len(successful_tests)}):")
            for test in successful_tests:
                print(f"   - {test['name']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ExcelImportTester()
    
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