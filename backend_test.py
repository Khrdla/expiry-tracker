#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Expiry Tracker
Tests all inventory management endpoints and expiry logic
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://barcode-expiry-app.preview.emergentagent.com/api"

class ExpiryTrackerTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.created_items = []  # Track created items for cleanup
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name, success, message=""):
        """Log test results"""
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")
    
    def test_api_health(self):
        """Test if API is accessible"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_result("API Health Check", True, f"API version: {data.get('version', 'unknown')}")
                return True
            else:
                self.log_result("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def create_test_inventory_items(self):
        """Create test inventory items with different expiry scenarios"""
        test_items = [
            {
                "department": "FMCG",
                "section": "S-10 Beverage",
                "supplier_name": "Coca Cola Company",
                "item_code": "CC001",
                "barcode": "1234567890123",
                "item_name": "Coca Cola 500ml",
                "stock_available": 50,
                "expiry_date": (date.today() - timedelta(days=5)).isoformat(),  # Expired
                "product_image": None
            },
            {
                "department": "FMCG",
                "section": "S-15 Snacks",
                "supplier_name": "PepsiCo",
                "item_code": "PC002",
                "barcode": "2345678901234",
                "item_name": "Lays Chips 100g",
                "stock_available": 30,
                "expiry_date": (date.today() + timedelta(days=3)).isoformat(),  # Expiring soon
                "product_image": None
            },
            {
                "department": "FMCG",
                "section": "S-10 Beverage",
                "supplier_name": "Nestle",
                "item_code": "NS003",
                "barcode": "3456789012345",
                "item_name": "Nescafe Coffee 200g",
                "stock_available": 25,
                "expiry_date": (date.today() + timedelta(days=30)).isoformat(),  # Future expiry
                "product_image": None
            },
            {
                "department": "FMCG",
                "section": "S-20 Dairy",
                "supplier_name": "Amul",
                "item_code": "AM004",
                "barcode": "4567890123456",
                "item_name": "Amul Milk 1L",
                "stock_available": 40,
                "expiry_date": (date.today() - timedelta(days=1)).isoformat(),  # Recently expired
                "product_image": None
            },
            {
                "department": "FMCG",
                "section": "S-15 Snacks",
                "supplier_name": "Britannia",
                "item_code": "BR005",
                "barcode": "5678901234567",
                "item_name": "Britannia Biscuits 200g",
                "stock_available": 60,
                "expiry_date": (date.today() + timedelta(days=6)).isoformat(),  # Expiring soon (within 7 days)
                "product_image": None
            }
        ]
        
        created_items = []
        for item in test_items:
            try:
                response = requests.post(f"{self.base_url}/inventory", json=item)
                if response.status_code == 200:
                    created_item = response.json()
                    created_items.append(created_item)
                    self.created_items.append(created_item["id"])
                    self.log_result(f"Create Item: {item['item_name']}", True, f"ID: {created_item['id']}")
                else:
                    self.log_result(f"Create Item: {item['item_name']}", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_result(f"Create Item: {item['item_name']}", False, f"Error: {str(e)}")
        
        return created_items
    
    def test_get_all_inventory(self):
        """Test GET /api/inventory endpoint"""
        try:
            response = requests.get(f"{self.base_url}/inventory")
            if response.status_code == 200:
                items = response.json()
                if isinstance(items, list) and len(items) > 0:
                    self.log_result("Get All Inventory", True, f"Retrieved {len(items)} items")
                    return items
                else:
                    self.log_result("Get All Inventory", False, "No items returned or invalid format")
            else:
                self.log_result("Get All Inventory", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get All Inventory", False, f"Error: {str(e)}")
        return []
    
    def test_get_single_item(self, item_id):
        """Test GET /api/inventory/{item_id} endpoint"""
        try:
            response = requests.get(f"{self.base_url}/inventory/{item_id}")
            if response.status_code == 200:
                item = response.json()
                if "id" in item and item["id"] == item_id:
                    self.log_result("Get Single Item", True, f"Retrieved item: {item.get('item_name', 'Unknown')}")
                    return item
                else:
                    self.log_result("Get Single Item", False, "Item ID mismatch")
            else:
                self.log_result("Get Single Item", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Single Item", False, f"Error: {str(e)}")
        return None
    
    def test_update_item(self, item_id):
        """Test PUT /api/inventory/{item_id} endpoint"""
        update_data = {
            "stock_available": 100,
            "item_name": "Updated Item Name"
        }
        
        try:
            response = requests.put(f"{self.base_url}/inventory/{item_id}", json=update_data)
            if response.status_code == 200:
                updated_item = response.json()
                if updated_item.get("stock_available") == 100:
                    self.log_result("Update Item", True, f"Updated stock to {updated_item['stock_available']}")
                    return updated_item
                else:
                    self.log_result("Update Item", False, "Update not reflected in response")
            else:
                self.log_result("Update Item", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Update Item", False, f"Error: {str(e)}")
        return None
    
    def test_search_by_barcode(self, barcode):
        """Test GET /api/search/barcode/{barcode} endpoint"""
        try:
            response = requests.get(f"{self.base_url}/search/barcode/{barcode}")
            if response.status_code == 200:
                item = response.json()
                if item.get("barcode") == barcode:
                    self.log_result("Search by Barcode", True, f"Found item: {item.get('item_name', 'Unknown')}")
                    return item
                else:
                    self.log_result("Search by Barcode", False, "Barcode mismatch in response")
            elif response.status_code == 404:
                self.log_result("Search by Barcode", True, "Correctly returned 404 for non-existent barcode")
            else:
                self.log_result("Search by Barcode", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Search by Barcode", False, f"Error: {str(e)}")
        return None
    
    def test_filtering(self):
        """Test inventory filtering by section and supplier"""
        # Test filter by section
        try:
            response = requests.get(f"{self.base_url}/inventory?section=S-10 Beverage")
            if response.status_code == 200:
                items = response.json()
                if all(item.get("section") == "S-10 Beverage" for item in items):
                    self.log_result("Filter by Section", True, f"Found {len(items)} beverage items")
                else:
                    self.log_result("Filter by Section", False, "Some items don't match section filter")
            else:
                self.log_result("Filter by Section", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter by Section", False, f"Error: {str(e)}")
        
        # Test filter by supplier
        try:
            response = requests.get(f"{self.base_url}/inventory?supplier=Coca Cola Company")
            if response.status_code == 200:
                items = response.json()
                if all(item.get("supplier_name") == "Coca Cola Company" for item in items):
                    self.log_result("Filter by Supplier", True, f"Found {len(items)} Coca Cola items")
                else:
                    self.log_result("Filter by Supplier", False, "Some items don't match supplier filter")
            else:
                self.log_result("Filter by Supplier", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter by Supplier", False, f"Error: {str(e)}")
        
        # Test expired_only filter
        try:
            response = requests.get(f"{self.base_url}/inventory?expired_only=true")
            if response.status_code == 200:
                items = response.json()
                today = date.today()
                expired_items = [item for item in items if datetime.fromisoformat(item["expiry_date"]).date() < today]
                if len(expired_items) == len(items):
                    self.log_result("Filter Expired Only", True, f"Found {len(items)} expired items")
                else:
                    self.log_result("Filter Expired Only", False, "Some non-expired items in expired filter")
            else:
                self.log_result("Filter Expired Only", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter Expired Only", False, f"Error: {str(e)}")
    
    def test_expiry_alerts(self):
        """Test GET /api/analytics/expiry-alerts endpoint"""
        try:
            response = requests.get(f"{self.base_url}/analytics/expiry-alerts")
            if response.status_code == 200:
                alerts = response.json()
                required_fields = ["total_items", "expiring_soon", "expired", "items_expiring_soon", "expired_items"]
                
                if all(field in alerts for field in required_fields):
                    # Verify expiry logic
                    today = date.today()
                    alert_date = today + timedelta(days=7)
                    
                    # Check expired items
                    expired_correct = all(
                        datetime.fromisoformat(item["expiry_date"]).date() < today 
                        for item in alerts["expired_items"]
                    )
                    
                    # Check expiring soon items
                    expiring_soon_correct = all(
                        today <= datetime.fromisoformat(item["expiry_date"]).date() <= alert_date
                        for item in alerts["items_expiring_soon"]
                    )
                    
                    if expired_correct and expiring_soon_correct:
                        self.log_result("Expiry Alerts Logic", True, 
                                      f"Expired: {alerts['expired']}, Expiring Soon: {alerts['expiring_soon']}")
                    else:
                        self.log_result("Expiry Alerts Logic", False, "Expiry categorization logic incorrect")
                    
                    self.log_result("Expiry Alerts API", True, f"Total items: {alerts['total_items']}")
                else:
                    self.log_result("Expiry Alerts API", False, "Missing required fields in response")
            else:
                self.log_result("Expiry Alerts API", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Expiry Alerts API", False, f"Error: {str(e)}")
    
    def test_analytics_by_supplier(self):
        """Test GET /api/analytics/by-supplier endpoint"""
        try:
            response = requests.get(f"{self.base_url}/analytics/by-supplier")
            if response.status_code == 200:
                analytics = response.json()
                if "suppliers" in analytics and isinstance(analytics["suppliers"], list):
                    suppliers = analytics["suppliers"]
                    if len(suppliers) > 0:
                        # Check if each supplier has required fields
                        required_fields = ["_id", "total_items", "total_stock", "expired_items", "expiring_soon"]
                        valid_suppliers = all(
                            all(field in supplier for field in required_fields)
                            for supplier in suppliers
                        )
                        
                        if valid_suppliers:
                            self.log_result("Analytics by Supplier", True, 
                                          f"Found {len(suppliers)} suppliers with analytics")
                        else:
                            self.log_result("Analytics by Supplier", False, "Missing required fields in supplier data")
                    else:
                        self.log_result("Analytics by Supplier", True, "No suppliers found (empty data)")
                else:
                    self.log_result("Analytics by Supplier", False, "Invalid response format")
            else:
                self.log_result("Analytics by Supplier", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Analytics by Supplier", False, f"Error: {str(e)}")
    
    def test_analytics_by_section(self):
        """Test GET /api/analytics/by-section endpoint"""
        try:
            response = requests.get(f"{self.base_url}/analytics/by-section")
            if response.status_code == 200:
                analytics = response.json()
                if "sections" in analytics and isinstance(analytics["sections"], list):
                    sections = analytics["sections"]
                    if len(sections) > 0:
                        # Check if each section has required fields
                        required_fields = ["_id", "total_items", "total_stock", "expired_items", "expiring_soon"]
                        valid_sections = all(
                            all(field in section for field in required_fields)
                            for section in sections
                        )
                        
                        if valid_sections:
                            self.log_result("Analytics by Section", True, 
                                          f"Found {len(sections)} sections with analytics")
                        else:
                            self.log_result("Analytics by Section", False, "Missing required fields in section data")
                    else:
                        self.log_result("Analytics by Section", True, "No sections found (empty data)")
                else:
                    self.log_result("Analytics by Section", False, "Invalid response format")
            else:
                self.log_result("Analytics by Section", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Analytics by Section", False, f"Error: {str(e)}")
    
    def test_delete_item(self, item_id):
        """Test DELETE /api/inventory/{item_id} endpoint"""
        try:
            response = requests.delete(f"{self.base_url}/inventory/{item_id}")
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    self.log_result("Delete Item", True, f"Deleted item {item_id}")
                    return True
                else:
                    self.log_result("Delete Item", False, "No confirmation message")
            else:
                self.log_result("Delete Item", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Delete Item", False, f"Error: {str(e)}")
        return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid item ID
        try:
            response = requests.get(f"{self.base_url}/inventory/invalid_id")
            if response.status_code == 400:
                self.log_result("Error Handling - Invalid ID", True, "Correctly returned 400 for invalid ID")
            else:
                self.log_result("Error Handling - Invalid ID", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling - Invalid ID", False, f"Error: {str(e)}")
        
        # Test non-existent barcode
        try:
            response = requests.get(f"{self.base_url}/search/barcode/nonexistent123")
            if response.status_code == 404:
                self.log_result("Error Handling - Non-existent Barcode", True, "Correctly returned 404")
            else:
                self.log_result("Error Handling - Non-existent Barcode", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling - Non-existent Barcode", False, f"Error: {str(e)}")
    
    def cleanup(self):
        """Clean up created test items"""
        print("\n🧹 Cleaning up test data...")
        for item_id in self.created_items:
            try:
                response = requests.delete(f"{self.base_url}/inventory/{item_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted test item: {item_id}")
                else:
                    print(f"⚠️ Failed to delete test item: {item_id}")
            except Exception as e:
                print(f"❌ Error deleting test item {item_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Expiry Tracker Backend API Tests")
        print(f"🔗 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Test API health first
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return
        
        # Create test data
        print("\n📦 Creating test inventory items...")
        created_items = self.create_test_inventory_items()
        
        if not created_items:
            print("❌ Failed to create test data. Stopping tests.")
            return
        
        # Run CRUD tests
        print("\n🔍 Testing CRUD Operations...")
        all_items = self.test_get_all_inventory()
        
        if created_items:
            # Test single item retrieval
            test_item = created_items[0]
            self.test_get_single_item(test_item["id"])
            
            # Test update
            self.test_update_item(test_item["id"])
            
            # Test barcode search
            self.test_search_by_barcode(test_item["barcode"])
        
        # Test filtering
        print("\n🔎 Testing Filtering...")
        self.test_filtering()
        
        # Test analytics
        print("\n📊 Testing Analytics...")
        self.test_expiry_alerts()
        self.test_analytics_by_supplier()
        self.test_analytics_by_section()
        
        # Test error handling
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Test delete (only delete one item to keep some data for analytics)
        if created_items:
            self.test_delete_item(created_items[-1]["id"])
            self.created_items.remove(created_items[-1]["id"])  # Remove from cleanup list
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        # Cleanup
        self.cleanup()
        
        return self.test_results['failed'] == 0

def main():
    """Main test execution"""
    tester = ExpiryTrackerTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n💥 {tester.test_results['failed']} tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()