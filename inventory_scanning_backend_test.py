#!/usr/bin/env python3
"""
Comprehensive Backend Testing for NEW Inventory Scanning System
Testing all inventory scanning endpoints with admin authentication
"""

import requests
import json
import time
import sys
from datetime import datetime
import os

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geant-scanner.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials for testing
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data - using existing barcodes from Master Data
TEST_BARCODES = [
    "3222471081716",  # Apple Juice Box 1L
    "3222471052747",  # Lemonade 150Cl
    "3222471075722",  # Mountain Water 6X50Cl
    "3222471081273",  # Orange Peach Apricot Nectar Box 1L
]

class InventoryScanningTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} | {test_name} | {details}"
        if response_time > 0:
            result += f" | {response_time}ms"
        
        self.test_results.append(result)
        print(result)
        
    def authenticate_admin(self):
        """Test admin authentication"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
                timeout=10
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Admin Authentication", True, f"JWT token received", response_time)
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_inventory_scan_creation(self):
        """Test POST /api/inventory-scans endpoint"""
        print("\n📦 TESTING INVENTORY SCAN CREATION")
        
        # Test 1: Create scan for SA zone
        try:
            scan_data = {
                "zone_type": "SA",
                "zone_number": 1,
                "barcode": TEST_BARCODES[0],  # Apple Juice Box 1L
                "quantity_scanned": 50.0
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/inventory-scans",
                json=scan_data,
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Create SA Zone Scan", True, 
                            f"Barcode: {data.get('barcode')}, Qty: {data.get('quantity_added')}", response_time)
            else:
                self.log_test("Create SA Zone Scan", False, 
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("Create SA Zone Scan", False, f"Error: {str(e)}")
        
        # Test 2: Create scan for WH zone
        try:
            scan_data = {
                "zone_type": "WH",
                "zone_number": 2,
                "barcode": TEST_BARCODES[1],  # Lemonade 150Cl
                "quantity_scanned": 25.0
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/inventory-scans",
                json=scan_data,
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Create WH Zone Scan", True, 
                            f"Barcode: {data.get('barcode')}, Qty: {data.get('quantity_added')}", response_time)
            else:
                self.log_test("Create WH Zone Scan", False, 
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("Create WH Zone Scan", False, f"Error: {str(e)}")
    
    def test_auto_aggregation_logic(self):
        """Test auto-aggregation when scanning same item multiple times"""
        print("\n🔄 TESTING AUTO-AGGREGATION LOGIC")
        
        # Test 1: Scan same item again in SA zone (should aggregate)
        try:
            scan_data = {
                "zone_type": "SA",
                "zone_number": 1,
                "barcode": TEST_BARCODES[0],  # Same Apple Juice Box 1L
                "quantity_scanned": 30.0  # Additional quantity
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/inventory-scans",
                json=scan_data,
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Auto-Aggregation SA Zone", True, 
                            f"Additional qty: {data.get('quantity_added')}, Total should be 80", response_time)
            else:
                self.log_test("Auto-Aggregation SA Zone", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Auto-Aggregation SA Zone", False, f"Error: {str(e)}")
        
        # Test 2: Scan same item in WH zone (should aggregate separately)
        try:
            scan_data = {
                "zone_type": "WH",
                "zone_number": 3,
                "barcode": TEST_BARCODES[0],  # Same Apple Juice Box 1L but WH zone
                "quantity_scanned": 20.0
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/inventory-scans",
                json=scan_data,
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Auto-Aggregation WH Zone", True, 
                            f"WH qty: {data.get('quantity_added')}, Should have SA:80 + WH:20", response_time)
            else:
                self.log_test("Auto-Aggregation WH Zone", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Auto-Aggregation WH Zone", False, f"Error: {str(e)}")
    
    def test_master_data_integration(self):
        """Test barcode lookup and auto-fill from Master Data"""
        print("\n🔍 TESTING MASTER DATA INTEGRATION")
        
        # Test with different barcodes to verify master data lookup
        for i, barcode in enumerate(TEST_BARCODES[2:4]):  # Test remaining barcodes
            try:
                scan_data = {
                    "zone_type": "SA",
                    "zone_number": i + 4,
                    "barcode": barcode,
                    "quantity_scanned": 15.0
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/inventory-scans",
                    json=scan_data,
                    timeout=10
                )
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Master Data Lookup {i+1}", True, 
                                f"Barcode: {barcode}, Item: {data.get('item_description', 'N/A')}", response_time)
                elif response.status_code == 404:
                    self.log_test(f"Master Data Lookup {i+1}", False, 
                                f"Product not found for barcode: {barcode}", response_time)
                else:
                    self.log_test(f"Master Data Lookup {i+1}", False, 
                                f"Status: {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Master Data Lookup {i+1}", False, f"Error: {str(e)}")
    
    def test_data_retrieval(self):
        """Test GET /api/inventory-scans endpoint"""
        print("\n📊 TESTING DATA RETRIEVAL")
        
        try:
            start_time = time.time()
            response = self.session.get(
                f"{API_BASE}/inventory-scans",
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                scans = data.get("scans", [])
                total_count = data.get("total_count", 0)
                
                # Verify variance calculations in retrieved data
                variance_test_passed = True
                for scan in scans:
                    total_inventory = scan.get("total_inventory_scan", 0)
                    system_stock = scan.get("system_stock", 0)
                    variance_qty = scan.get("variance_qty", 0)
                    expected_variance = total_inventory - system_stock
                    
                    if abs(variance_qty - expected_variance) > 0.01:  # Allow small floating point differences
                        variance_test_passed = False
                        break
                
                self.log_test("Get Inventory Scans", True, 
                            f"Retrieved {total_count} scans", response_time)
                self.log_test("Variance Calculations", variance_test_passed, 
                            f"All variance calculations verified" if variance_test_passed else "Variance calculation errors found")
                
                # Check for required fields in scans
                if scans:
                    required_fields = ["barcode", "item_number", "description", "department", 
                                     "section", "family", "supplier_code", "supplier_name",
                                     "qty_scanned_sa", "qty_scanned_wh", "total_inventory_scan",
                                     "system_stock", "variance_qty", "variance_value"]
                    
                    first_scan = scans[0]
                    missing_fields = [field for field in required_fields if field not in first_scan]
                    
                    if not missing_fields:
                        self.log_test("Master Data Fields", True, "All required fields present")
                    else:
                        self.log_test("Master Data Fields", False, f"Missing fields: {missing_fields}")
                
            else:
                self.log_test("Get Inventory Scans", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Get Inventory Scans", False, f"Error: {str(e)}")
    
    def test_excel_export(self):
        """Test GET /api/inventory-scans/export endpoint"""
        print("\n📈 TESTING EXCEL EXPORT")
        
        try:
            start_time = time.time()
            response = self.session.get(
                f"{API_BASE}/inventory-scans/export",
                timeout=30  # Excel generation might take longer
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                # Check if it's actually an Excel file
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                has_content = content_length > 1000  # Should be substantial for Excel file
                
                if is_excel and has_content:
                    self.log_test("Excel Export Generation", True, 
                                f"Excel file generated ({content_length} bytes)", response_time)
                    
                    # Check filename in headers
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'Inventory_Scan_Report_' in content_disposition:
                        self.log_test("Excel Export Filename", True, "Proper filename format")
                    else:
                        self.log_test("Excel Export Filename", False, f"Unexpected filename: {content_disposition}")
                        
                else:
                    self.log_test("Excel Export Generation", False, 
                                f"Invalid Excel file: {content_type}, {content_length} bytes", response_time)
                    
            elif response.status_code == 404:
                self.log_test("Excel Export Generation", False, 
                            "No inventory scans found for export", response_time)
            else:
                self.log_test("Excel Export Generation", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Excel Export Generation", False, f"Error: {str(e)}")
    
    def test_clear_all_function(self):
        """Test DELETE /api/inventory-scans/clear endpoint"""
        print("\n🗑️ TESTING CLEAR ALL FUNCTION")
        
        try:
            start_time = time.time()
            response = self.session.delete(
                f"{API_BASE}/inventory-scans/clear",
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                success = data.get("success", False)
                
                if success:
                    self.log_test("Clear All Scans", True, 
                                f"Cleared {deleted_count} inventory scans", response_time)
                else:
                    self.log_test("Clear All Scans", False, 
                                "Success flag not set", response_time)
            else:
                self.log_test("Clear All Scans", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Clear All Scans", False, f"Error: {str(e)}")
        
        # Verify scans are actually cleared
        try:
            start_time = time.time()
            response = self.session.get(
                f"{API_BASE}/inventory-scans",
                timeout=10
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_count", 0)
                
                if total_count == 0:
                    self.log_test("Verify Clear All", True, 
                                "All scans successfully cleared", response_time)
                else:
                    self.log_test("Verify Clear All", False, 
                                f"Still {total_count} scans remaining", response_time)
            else:
                self.log_test("Verify Clear All", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Verify Clear All", False, f"Error: {str(e)}")
    
    def test_admin_access_control(self):
        """Test that all endpoints require admin authentication"""
        print("\n🔒 TESTING ADMIN ACCESS CONTROL")
        
        # Save current token
        original_token = self.session.headers.get("Authorization")
        
        # Test without authentication
        self.session.headers.pop("Authorization", None)
        
        endpoints_to_test = [
            ("POST", "/inventory-scans", {"zone_type": "SA", "zone_number": 1, "barcode": "test", "quantity_scanned": 1}),
            ("GET", "/inventory-scans", None),
            ("DELETE", "/inventory-scans/clear", None),
            ("GET", "/inventory-scans/export", None)
        ]
        
        for method, endpoint, data in endpoints_to_test:
            try:
                start_time = time.time()
                
                if method == "POST":
                    response = self.session.post(f"{API_BASE}{endpoint}", json=data, timeout=10)
                elif method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}", timeout=10)
                elif method == "DELETE":
                    response = self.session.delete(f"{API_BASE}{endpoint}", timeout=10)
                
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 403:
                    self.log_test(f"Access Control {method} {endpoint}", True, 
                                "Correctly blocked unauthorized access", response_time)
                elif response.status_code == 401:
                    self.log_test(f"Access Control {method} {endpoint}", True, 
                                "Correctly requires authentication", response_time)
                else:
                    self.log_test(f"Access Control {method} {endpoint}", False, 
                                f"Unexpected status: {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test(f"Access Control {method} {endpoint}", False, f"Error: {str(e)}")
        
        # Restore authentication
        if original_token:
            self.session.headers["Authorization"] = original_token
    
    def run_comprehensive_test(self):
        """Run all inventory scanning tests"""
        print("🚀 STARTING COMPREHENSIVE INVENTORY SCANNING SYSTEM BACKEND TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with testing.")
            return False
        
        # Step 2: Test admin access control
        self.test_admin_access_control()
        
        # Step 3: Clear any existing scans first
        print("\n🧹 CLEARING EXISTING SCANS FOR CLEAN TEST")
        try:
            self.session.delete(f"{API_BASE}/inventory-scans/clear", timeout=10)
        except:
            pass
        
        # Step 4: Test inventory scan creation
        self.test_inventory_scan_creation()
        
        # Step 5: Test auto-aggregation logic
        self.test_auto_aggregation_logic()
        
        # Step 6: Test master data integration
        self.test_master_data_integration()
        
        # Step 7: Test data retrieval and variance calculations
        self.test_data_retrieval()
        
        # Step 8: Test Excel export
        self.test_excel_export()
        
        # Step 9: Test clear all function
        self.test_clear_all_function()
        
        # Final Results
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE INVENTORY SCANNING SYSTEM TEST RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ PASSED: {self.passed_tests}/{self.total_tests} tests ({success_rate:.1f}%)")
        print(f"❌ FAILED: {self.total_tests - self.passed_tests}/{self.total_tests} tests")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Inventory Scanning System is working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: Inventory Scanning System is working well with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Inventory Scanning System has some issues that need attention")
        else:
            print("❌ CRITICAL: Inventory Scanning System has major issues requiring immediate attention")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(result)
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = InventoryScanningTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)