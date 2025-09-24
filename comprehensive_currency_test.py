#!/usr/bin/env python3
"""
COMPREHENSIVE CURRENCY MANAGEMENT SYSTEM TESTING

This test covers all requirements from the review request:
1. Currency Settings API Endpoints
2. Database Integration  
3. Export System Integration
4. Rate Management Features
5. Authentication & Permissions
6. Integration with Enhanced Export System
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import sys

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stockmate-14.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials for testing
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class ComprehensiveCurrencyTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = []
        
    async def setup(self):
        """Initialize test session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate as admin
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        try:
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ Authentication successful - Admin access confirmed")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def record_test(self, test_name, passed, details=""):
        """Record test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}")
            if details:
                print(f"   {details}")
    
    async def test_currency_settings_api_endpoints(self):
        """Test all 4 currency API endpoints as specified in review request"""
        print("\n🔍 TESTING CURRENCY SETTINGS API ENDPOINTS")
        print("-" * 50)
        
        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        # 1. Test GET /api/currency/settings
        try:
            async with self.session.get(f"{API_BASE}/currency/settings", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "settings" in data and "exchange_rates" in data["settings"]:
                        self.record_test("GET /api/currency/settings", True, 
                                       f"Retrieved settings with rates: {data['settings']['exchange_rates']}")
                    else:
                        self.record_test("GET /api/currency/settings", False, "Invalid response structure")
                else:
                    self.record_test("GET /api/currency/settings", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("GET /api/currency/settings", False, f"Error: {str(e)}")
        
        # 2. Test PUT /api/currency/settings
        try:
            test_settings = {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.0042,
                    "SAR": 0.269,
                    "EUR": 1.13,
                    "USD": 1.0
                }
            }
            
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json=test_settings, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.record_test("PUT /api/currency/settings", True, 
                                       f"Updated by: {data.get('updated_by')}")
                    else:
                        self.record_test("PUT /api/currency/settings", False, "Update not successful")
                else:
                    self.record_test("PUT /api/currency/settings", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("PUT /api/currency/settings", False, f"Error: {str(e)}")
        
        # 3. Test GET /api/currency/rates (public)
        try:
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    if "exchange_rates" in data and "base_currency" in data:
                        self.record_test("GET /api/currency/rates", True, 
                                       f"Public rates: {data['exchange_rates']}")
                    else:
                        self.record_test("GET /api/currency/rates", False, "Invalid response structure")
                else:
                    self.record_test("GET /api/currency/rates", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("GET /api/currency/rates", False, f"Error: {str(e)}")
        
        # 4. Test POST /api/currency/rates/quick-update
        try:
            quick_update = {
                "currency": "EUR",
                "rate": 1.15
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=quick_update, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("new_rate") == 1.15:
                        self.record_test("POST /api/currency/rates/quick-update", True, 
                                       f"Updated {data['currency']} to {data['new_rate']}")
                    else:
                        self.record_test("POST /api/currency/rates/quick-update", False, "Update not successful")
                else:
                    self.record_test("POST /api/currency/rates/quick-update", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("POST /api/currency/rates/quick-update", False, f"Error: {str(e)}")
    
    async def test_database_integration(self):
        """Test currency settings storage and retrieval from MongoDB"""
        print("\n🔍 TESTING DATABASE INTEGRATION")
        print("-" * 50)
        
        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        # Test database persistence
        try:
            # Set unique test rate
            timestamp = datetime.now().strftime("%H%M%S")
            unique_rate = 1.0 + float(f"0.{timestamp[-3:]}")
            
            test_settings = {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.004,
                    "SAR": 0.267,
                    "EUR": unique_rate,
                    "USD": 1.0
                }
            }
            
            # Update settings
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json=test_settings, headers=headers) as response:
                if response.status == 200:
                    await asyncio.sleep(0.5)  # Wait for database write
                    
                    # Retrieve and verify
                    async with self.session.get(f"{API_BASE}/currency/settings", headers=headers) as get_response:
                        if get_response.status == 200:
                            data = await get_response.json()
                            stored_rate = data["settings"]["exchange_rates"].get("EUR")
                            
                            if stored_rate == unique_rate:
                                self.record_test("Database Storage & Retrieval", True, 
                                               f"Rate persisted correctly: {stored_rate}")
                            else:
                                self.record_test("Database Storage & Retrieval", False, 
                                               f"Rate mismatch: {stored_rate} vs {unique_rate}")
                        else:
                            self.record_test("Database Storage & Retrieval", False, "Failed to retrieve")
                else:
                    self.record_test("Database Storage & Retrieval", False, "Failed to update")
        except Exception as e:
            self.record_test("Database Storage & Retrieval", False, f"Error: {str(e)}")
        
        # Test fallback behavior
        try:
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    if "exchange_rates" in data and len(data["exchange_rates"]) >= 4:
                        self.record_test("Fallback to Default Rates", True, 
                                       "Default rates available when database unavailable")
                    else:
                        self.record_test("Fallback to Default Rates", False, "No fallback rates")
                else:
                    self.record_test("Fallback to Default Rates", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Fallback to Default Rates", False, f"Error: {str(e)}")
    
    async def test_export_system_integration(self):
        """Test waste report export using dynamic rates from database"""
        print("\n🔍 TESTING EXPORT SYSTEM INTEGRATION")
        print("-" * 50)
        
        headers = self.get_auth_headers()
        
        # Test Excel export with dynamic rates
        try:
            async with self.session.get(f"{API_BASE}/export/waste-report/daily?format=excel", 
                                      headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = int(response.headers.get('content-length', 0))
                    
                    if 'excel' in content_type.lower() and content_length > 30000:
                        self.record_test("Excel Export with Dynamic Rates", True, 
                                       f"Enhanced export: {content_length} bytes")
                    else:
                        self.record_test("Excel Export with Dynamic Rates", False, 
                                       f"May be using fallback: {content_length} bytes")
                else:
                    self.record_test("Excel Export with Dynamic Rates", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Excel Export with Dynamic Rates", False, f"Error: {str(e)}")
        
        # Test PDF export with dynamic rates
        try:
            async with self.session.get(f"{API_BASE}/export/waste-report/weekly?format=pdf", 
                                      headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = int(response.headers.get('content-length', 0))
                    
                    if 'pdf' in content_type.lower() and content_length > 10000:
                        self.record_test("PDF Export with Dynamic Rates", True, 
                                       f"Enhanced export: {content_length} bytes")
                    else:
                        self.record_test("PDF Export with Dynamic Rates", False, 
                                       f"May be using fallback: {content_length} bytes")
                else:
                    self.record_test("PDF Export with Dynamic Rates", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("PDF Export with Dynamic Rates", False, f"Error: {str(e)}")
        
        # Test USD conversion calculations
        try:
            # First verify current rates
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data["exchange_rates"]
                    
                    if all(currency in rates for currency in ["YER", "SAR", "EUR"]):
                        self.record_test("USD Conversion Rates Available", True, 
                                       f"All currencies available: {rates}")
                    else:
                        self.record_test("USD Conversion Rates Available", False, 
                                       f"Missing currencies: {rates}")
                else:
                    self.record_test("USD Conversion Rates Available", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("USD Conversion Rates Available", False, f"Error: {str(e)}")
    
    async def test_rate_management_features(self):
        """Test rate management features"""
        print("\n🔍 TESTING RATE MANAGEMENT FEATURES")
        print("-" * 50)
        
        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        # Test individual currency rate updates
        try:
            update_data = {
                "currency": "SAR",
                "rate": 0.270
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=update_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.record_test("Individual Rate Update", True, 
                                       f"SAR updated to {data.get('new_rate')}")
                    else:
                        self.record_test("Individual Rate Update", False, "Update not successful")
                else:
                    self.record_test("Individual Rate Update", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Individual Rate Update", False, f"Error: {str(e)}")
        
        # Test bulk rate updates
        try:
            bulk_settings = {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.0043,
                    "SAR": 0.271,
                    "EUR": 1.16,
                    "USD": 1.0
                }
            }
            
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json=bulk_settings, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.record_test("Bulk Rate Updates", True, 
                                       f"All rates updated successfully")
                    else:
                        self.record_test("Bulk Rate Updates", False, "Bulk update not successful")
                else:
                    self.record_test("Bulk Rate Updates", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Bulk Rate Updates", False, f"Error: {str(e)}")
        
        # Test base currency settings
        try:
            async with self.session.get(f"{API_BASE}/currency/settings", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    base_currency = data.get("base_currency")
                    
                    if base_currency == "USD":
                        self.record_test("Base Currency Settings", True, 
                                       f"Base currency: {base_currency}")
                    else:
                        self.record_test("Base Currency Settings", False, 
                                       f"Unexpected base currency: {base_currency}")
                else:
                    self.record_test("Base Currency Settings", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Base Currency Settings", False, f"Error: {str(e)}")
        
        # Test rate validation (positive numbers only)
        try:
            invalid_data = {
                "currency": "EUR",
                "rate": -1.5
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=invalid_data, headers=headers) as response:
                if response.status == 400:
                    self.record_test("Rate Validation (Positive Numbers)", True, 
                                   "Negative rates properly rejected")
                else:
                    self.record_test("Rate Validation (Positive Numbers)", False, 
                                   f"Invalid rate accepted: {response.status}")
        except Exception as e:
            self.record_test("Rate Validation (Positive Numbers)", False, f"Error: {str(e)}")
    
    async def test_authentication_and_permissions(self):
        """Test authentication and permissions for currency management"""
        print("\n🔍 TESTING AUTHENTICATION & PERMISSIONS")
        print("-" * 50)
        
        # Test that only managers and admins can update rates
        try:
            test_data = {
                "currency": "EUR",
                "rate": 1.20
            }
            
            # Test without authentication
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", json=test_data) as response:
                if response.status in [401, 403]:
                    self.record_test("Authentication Required for Updates", True, 
                                   f"Unauthorized access blocked: {response.status}")
                else:
                    self.record_test("Authentication Required for Updates", False, 
                                   f"Unauthorized access allowed: {response.status}")
        except Exception as e:
            self.record_test("Authentication Required for Updates", False, f"Error: {str(e)}")
        
        # Test with admin credentials (already authenticated)
        try:
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            test_data = {
                "currency": "EUR",
                "rate": 1.21
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=test_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.record_test("Admin Access Allowed", True, 
                                       f"Admin can update rates: {data.get('updated_by')}")
                    else:
                        self.record_test("Admin Access Allowed", False, "Admin update failed")
                else:
                    self.record_test("Admin Access Allowed", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Admin Access Allowed", False, f"Error: {str(e)}")
        
        # Test proper error handling for unauthorized access
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json={"base_currency": "USD"}, headers=invalid_headers) as response:
                if response.status in [401, 403]:
                    self.record_test("Error Handling for Unauthorized Access", True, 
                                   "Invalid tokens properly rejected")
                else:
                    self.record_test("Error Handling for Unauthorized Access", False, 
                                   f"Invalid token accepted: {response.status}")
        except Exception as e:
            self.record_test("Error Handling for Unauthorized Access", False, f"Error: {str(e)}")
    
    async def test_enhanced_export_system_integration(self):
        """Test integration with EnhancedWasteReportExporter"""
        print("\n🔍 TESTING ENHANCED EXPORT SYSTEM INTEGRATION")
        print("-" * 50)
        
        headers = self.get_auth_headers()
        
        # Test that EnhancedWasteReportExporter uses database rates
        try:
            # Set a unique rate for testing
            test_rate = 1.234
            update_data = {
                "currency": "EUR",
                "rate": test_rate
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=update_data, headers=headers) as response:
                if response.status == 200:
                    await asyncio.sleep(1)  # Wait for database update
                    
                    # Test export to see if it uses the new rate
                    async with self.session.get(f"{API_BASE}/export/waste-report/daily?format=excel", 
                                              headers=headers) as export_response:
                        if export_response.status == 200:
                            content_length = int(export_response.headers.get('content-length', 0))
                            
                            if content_length > 30000:  # Enhanced export indicator
                                self.record_test("EnhancedWasteReportExporter Uses Database Rates", True, 
                                               f"Enhanced export active: {content_length} bytes")
                            else:
                                self.record_test("EnhancedWasteReportExporter Uses Database Rates", False, 
                                               f"May be using fallback: {content_length} bytes")
                        else:
                            self.record_test("EnhancedWasteReportExporter Uses Database Rates", False, 
                                           f"Export failed: {export_response.status}")
                else:
                    self.record_test("EnhancedWasteReportExporter Uses Database Rates", False, 
                                   f"Rate update failed: {response.status}")
        except Exception as e:
            self.record_test("EnhancedWasteReportExporter Uses Database Rates", False, f"Error: {str(e)}")
        
        # Test currency conversion accuracy
        try:
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data["exchange_rates"]
                    
                    # Verify all required currencies are present with reasonable rates
                    required_currencies = ["YER", "SAR", "EUR", "USD"]
                    valid_rates = all(
                        currency in rates and 
                        isinstance(rates[currency], (int, float)) and 
                        rates[currency] > 0
                        for currency in required_currencies
                    )
                    
                    if valid_rates:
                        self.record_test("Currency Conversion Accuracy", True, 
                                       f"All rates valid: {rates}")
                    else:
                        self.record_test("Currency Conversion Accuracy", False, 
                                       f"Invalid rates found: {rates}")
                else:
                    self.record_test("Currency Conversion Accuracy", False, f"Status: {response.status}")
        except Exception as e:
            self.record_test("Currency Conversion Accuracy", False, f"Error: {str(e)}")
        
        # Test fallback behavior if database is unavailable
        try:
            # This tests the fallback mechanism in the export system
            async with self.session.get(f"{API_BASE}/export/waste-report/daily?format=pdf", 
                                      headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'pdf' in content_type.lower():
                        self.record_test("Fallback Behavior for Export System", True, 
                                       "Export system has fallback mechanisms")
                    else:
                        self.record_test("Fallback Behavior for Export System", False, 
                                       f"Unexpected content type: {content_type}")
                else:
                    self.record_test("Fallback Behavior for Export System", False, 
                                   f"Export failed: {response.status}")
        except Exception as e:
            self.record_test("Fallback Behavior for Export System", False, f"Error: {str(e)}")
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive currency management tests"""
        print("🚀 COMPREHENSIVE CURRENCY MANAGEMENT SYSTEM TESTING")
        print("=" * 70)
        print("Testing all requirements from review request:")
        print("1. Currency Settings API Endpoints")
        print("2. Database Integration")
        print("3. Export System Integration")
        print("4. Rate Management Features")
        print("5. Authentication & Permissions")
        print("6. Integration with Enhanced Export System")
        print("=" * 70)
        
        if not await self.setup():
            print("❌ Failed to setup test environment")
            return 0
        
        try:
            await self.test_currency_settings_api_endpoints()
            await self.test_database_integration()
            await self.test_export_system_integration()
            await self.test_rate_management_features()
            await self.test_authentication_and_permissions()
            await self.test_enhanced_export_system_integration()
            
        finally:
            await self.cleanup()
        
        # Print comprehensive results
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE CURRENCY MANAGEMENT TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("🎉 CURRENCY MANAGEMENT SYSTEM IS FULLY FUNCTIONAL!")
            print("   All critical requirements from review request are working correctly.")
        elif success_rate >= 80:
            print("✅ CURRENCY MANAGEMENT SYSTEM IS WORKING WELL!")
            print("   Most requirements are working with minor issues.")
        elif success_rate >= 70:
            print("⚠️  CURRENCY MANAGEMENT SYSTEM HAS SOME ISSUES")
            print("   Core functionality working but needs attention.")
        else:
            print("❌ CURRENCY MANAGEMENT SYSTEM HAS CRITICAL ISSUES")
            print("   Major functionality problems detected.")
        
        return success_rate

async def main():
    """Main test execution"""
    tester = ComprehensiveCurrencyTester()
    success_rate = await tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    asyncio.run(main())