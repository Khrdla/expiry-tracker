#!/usr/bin/env python3
"""
Focused Backend Testing for Critical Issues Found in Comprehensive Audit
"""

import requests
import json
import time

class FocusedBackendTester:
    def __init__(self, base_url="https://smart-inventory-69.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"

    def login(self):
        """Get fresh authentication token"""
        response = requests.post(f"{self.api_url}/auth/login", 
                               json={"username": self.admin_username, "password": self.admin_password})
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            print(f"✅ Login successful, token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_barcode_database_issue(self):
        """Test why barcode 9501100046987 is not found"""
        print("\n🔍 INVESTIGATING BARCODE DATABASE ISSUE")
        print("=" * 50)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # 1. Search for the barcode in search endpoint
        print("1. Testing search endpoint for barcode 9501100046987...")
        response = requests.get(f"{self.api_url}/search?q=9501100046987&limit=5", headers=headers)
        print(f"   Search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Search results: {len(data)} items")
            for item in data:
                print(f"     - {item.get('product_name', 'Unknown')}: barcode={item.get('barcode', 'None')}")
        
        # 2. Search for "Al Hana Orange" (the expected product name)
        print("\n2. Testing search for 'Al Hana Orange'...")
        response = requests.get(f"{self.api_url}/search?q=Al Hana Orange&limit=10", headers=headers)
        print(f"   Search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Search results: {len(data)} items")
            for item in data:
                barcode = item.get('barcode', 'None')
                print(f"     - {item.get('product_name', 'Unknown')}: barcode={barcode}")
                if barcode == '9501100046987':
                    print(f"       ✅ FOUND! This product has the missing barcode")
        
        # 3. Search for "Orange Nectar" 
        print("\n3. Testing search for 'Orange Nectar'...")
        response = requests.get(f"{self.api_url}/search?q=Orange Nectar&limit=10", headers=headers)
        print(f"   Search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Search results: {len(data)} items")
            for item in data:
                barcode = item.get('barcode', 'None')
                print(f"     - {item.get('product_name', 'Unknown')}: barcode={barcode}")
                if barcode == '9501100046987':
                    print(f"       ✅ FOUND! This product has the missing barcode")
        
        # 4. Get all products from 01-FMG department (where this barcode should be)
        print("\n4. Testing products from 01-FMG department...")
        response = requests.get(f"{self.api_url}/products?department=01-FMG&limit=50", headers=headers)
        print(f"   Products status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   01-FMG products: {len(data)} items")
            
            found_barcode = False
            for item in data:
                barcode = item.get('barcode', '')
                if barcode == '9501100046987':
                    print(f"       ✅ FOUND BARCODE! Product: {item.get('product_name', 'Unknown')}")
                    print(f"          Department: {item.get('department', 'Unknown')}")
                    print(f"          Section: {item.get('section', 'Unknown')}")
                    found_barcode = True
                    break
            
            if not found_barcode:
                print(f"       ❌ Barcode 9501100046987 not found in 01-FMG products")
                # Show some sample barcodes from this department
                print(f"       Sample barcodes from 01-FMG:")
                for item in data[:5]:
                    barcode = item.get('barcode', 'None')
                    if barcode and barcode != 'None':
                        print(f"         - {item.get('product_name', 'Unknown')}: {barcode}")

    def test_cors_headers(self):
        """Test CORS headers configuration"""
        print("\n🌐 TESTING CORS HEADERS")
        print("=" * 30)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test CORS headers on various endpoints
        endpoints = [
            "dashboard",
            "products?limit=5",
            "barcode/3222471052747"
        ]
        
        for endpoint in endpoints:
            print(f"\nTesting CORS on /{endpoint}...")
            response = requests.get(f"{self.api_url}/{endpoint}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            cors_headers = {}
            for header, value in response.headers.items():
                if 'access-control' in header.lower():
                    cors_headers[header] = value
            
            if cors_headers:
                print(f"   ✅ CORS headers present:")
                for header, value in cors_headers.items():
                    print(f"     {header}: {value}")
            else:
                print(f"   ❌ No CORS headers found")

    def test_product_endpoint_method(self):
        """Test why GET /api/products/{id} returns 405"""
        print("\n🔧 TESTING PRODUCT ENDPOINT METHODS")
        print("=" * 40)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # First get a valid product ID
        response = requests.get(f"{self.api_url}/products?limit=1", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                product_id = data[0].get('id')
                print(f"Testing with product ID: {product_id}")
                
                # Test GET method
                response = requests.get(f"{self.api_url}/products/{product_id}", headers=headers)
                print(f"   GET /api/products/{product_id}: {response.status_code}")
                
                if response.status_code == 405:
                    print(f"   ❌ GET method not allowed - this endpoint may not exist")
                    print(f"   ℹ️  Individual product retrieval may need to use search or products list")
                elif response.status_code == 200:
                    print(f"   ✅ GET method works")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
        else:
            print(f"   ❌ Could not get product list to test individual product endpoint")

    def test_working_barcodes(self):
        """Test the barcodes that are working to confirm functionality"""
        print("\n✅ TESTING WORKING BARCODES")
        print("=" * 35)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        working_barcodes = [
            "3222471052747",   # Lemonade 150Cl
            "3222471075722",   # Mountain Water 6X50Cl
            "3222471081273",   # Orange Peach Apricot Nectar Box 1L
            "3222471081716"    # Apple Juice Box 1L
        ]
        
        for barcode in working_barcodes:
            print(f"\nTesting barcode: {barcode}")
            response = requests.get(f"{self.api_url}/barcode/{barcode}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Product: {data.get('product_name', 'Unknown')}")
                print(f"      Department: {data.get('department', 'Unknown')}")
                print(f"      Status: {data.get('status', 'Unknown')}")
                
                # Check response size
                response_size = len(json.dumps(data).encode('utf-8'))
                print(f"      Response size: {response_size} bytes")
                
                # Check required fields
                required_fields = [
                    'product_name', 'item_number', 'barcode', 'department', 
                    'section', 'purchase_price', 'purchase_currency', 'selling_price', 
                    'supplier', 'quantity', 'status'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"      ❌ Missing fields: {missing_fields}")
                else:
                    print(f"      ✅ All required fields present")
            else:
                print(f"   ❌ Failed with status {response.status_code}")

    def test_export_functionality_details(self):
        """Test export functionality in detail"""
        print("\n📤 TESTING EXPORT FUNCTIONALITY DETAILS")
        print("=" * 45)
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test successful exports
        successful_exports = [
            {"endpoint": "export/dashboard/excel", "name": "Dashboard Excel"},
            {"endpoint": "export/dashboard/pdf", "name": "Dashboard PDF"},
            {"endpoint": "export/waste-report/daily", "name": "Daily Waste Report"},
            {"endpoint": "export/waste-report/weekly", "name": "Weekly Waste Report"}
        ]
        
        for export_data in successful_exports:
            endpoint = export_data["endpoint"]
            name = export_data["name"]
            
            print(f"\nTesting {name}...")
            response = requests.get(f"{self.api_url}/{endpoint}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '0')
                
                print(f"   ✅ Export successful")
                print(f"      Content-Type: {content_type}")
                print(f"      Content-Length: {content_length} bytes")
                
                # Check if it's the right file type
                if 'excel' in endpoint and 'spreadsheet' in content_type:
                    print(f"      ✅ Correct Excel MIME type")
                elif 'pdf' in endpoint and 'pdf' in content_type:
                    print(f"      ✅ Correct PDF MIME type")
                else:
                    print(f"      ⚠️  MIME type check: expected file type for {endpoint}")
            else:
                print(f"   ❌ Export failed")
        
        # Test the failing monthly export
        print(f"\nTesting Monthly Waste Report (known to fail)...")
        response = requests.get(f"{self.api_url}/export/waste-report/monthly", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                print(f"   ❌ Expected failure - Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   ❌ Expected failure - Non-JSON error response")

    def run_focused_tests(self):
        """Run all focused tests"""
        print("🎯 FOCUSED BACKEND TESTING - CRITICAL ISSUES")
        print("=" * 60)
        
        if not self.login():
            return False
        
        # Run focused tests
        self.test_barcode_database_issue()
        self.test_cors_headers()
        self.test_product_endpoint_method()
        self.test_working_barcodes()
        self.test_export_functionality_details()
        
        print("\n" + "=" * 60)
        print("🏁 FOCUSED TESTING COMPLETE")
        print("=" * 60)
        
        return True

def main():
    tester = FocusedBackendTester()
    tester.run_focused_tests()

if __name__ == "__main__":
    main()