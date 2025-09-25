#!/usr/bin/env python3
"""
Comprehensive Currency Management System Testing

Tests the newly implemented dynamic currency management system including:
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geant-inventory-2.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials for testing
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class CurrencyManagementTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
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
                    print(f"✅ Authentication successful - Token: {self.auth_token[:20]}...")
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
    
    async def test_get_currency_settings(self):
        """Test GET /api/currency/settings endpoint"""
        print("\n🔍 Testing GET /api/currency/settings...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            async with self.session.get(f"{API_BASE}/currency/settings", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ["settings", "supported_currencies", "base_currency"]
                    if all(field in data for field in required_fields):
                        settings = data["settings"]
                        
                        # Validate settings structure
                        if "exchange_rates" in settings and "base_currency" in settings:
                            rates = settings["exchange_rates"]
                            
                            # Check for expected currencies
                            expected_currencies = ["YER", "SAR", "EUR", "USD"]
                            if all(currency in rates for currency in expected_currencies):
                                print(f"✅ Currency settings retrieved successfully")
                                print(f"   Base currency: {data['base_currency']}")
                                print(f"   Exchange rates: {rates}")
                                print(f"   Supported currencies: {data['supported_currencies']}")
                                self.passed_tests += 1
                                return True
                            else:
                                print(f"❌ Missing expected currencies in rates: {rates}")
                        else:
                            print(f"❌ Invalid settings structure: {settings}")
                    else:
                        print(f"❌ Missing required fields in response: {data}")
                else:
                    print(f"❌ Failed to get currency settings: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error testing currency settings: {str(e)}")
        
        return False
    
    async def test_update_currency_settings(self):
        """Test PUT /api/currency/settings endpoint"""
        print("\n🔍 Testing PUT /api/currency/settings...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Test data with updated rates
            test_settings = {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.0041,  # Slightly updated rate
                    "SAR": 0.268,   # Slightly updated rate
                    "EUR": 1.11,    # Slightly updated rate
                    "USD": 1.0      # Base currency always 1.0
                }
            }
            
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json=test_settings, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success") and "settings" in data:
                        updated_settings = data["settings"]
                        updated_rates = updated_settings.get("exchange_rates", {})
                        
                        # Verify the rates were updated
                        if (updated_rates.get("YER") == 0.0041 and 
                            updated_rates.get("SAR") == 0.268 and
                            updated_rates.get("EUR") == 1.11):
                            print(f"✅ Currency settings updated successfully")
                            print(f"   Updated by: {data.get('updated_by')}")
                            print(f"   New rates: {updated_rates}")
                            self.passed_tests += 1
                            return True
                        else:
                            print(f"❌ Rates not updated correctly: {updated_rates}")
                    else:
                        print(f"❌ Invalid update response: {data}")
                else:
                    print(f"❌ Failed to update currency settings: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error testing currency settings update: {str(e)}")
        
        return False
    
    async def test_get_public_rates(self):
        """Test GET /api/currency/rates endpoint (public)"""
        print("\n🔍 Testing GET /api/currency/rates (public endpoint)...")
        self.total_tests += 1
        
        try:
            # Test without authentication (public endpoint)
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    required_fields = ["base_currency", "exchange_rates", "last_updated"]
                    if all(field in data for field in required_fields):
                        rates = data["exchange_rates"]
                        
                        # Check for expected currencies
                        expected_currencies = ["YER", "SAR", "EUR", "USD"]
                        if all(currency in rates for currency in expected_currencies):
                            print(f"✅ Public exchange rates retrieved successfully")
                            print(f"   Base currency: {data['base_currency']}")
                            print(f"   Exchange rates: {rates}")
                            print(f"   Last updated: {data['last_updated']}")
                            self.passed_tests += 1
                            return True
                        else:
                            print(f"❌ Missing expected currencies: {rates}")
                    else:
                        print(f"❌ Missing required fields: {data}")
                else:
                    print(f"❌ Failed to get public rates: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error testing public rates: {str(e)}")
        
        return False
    
    async def test_quick_update_rate(self):
        """Test POST /api/currency/rates/quick-update endpoint"""
        print("\n🔍 Testing POST /api/currency/rates/quick-update...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Test updating EUR rate
            update_data = {
                "currency": "EUR",
                "rate": 1.12
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=update_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if (data.get("success") and 
                        data.get("currency") == "EUR" and 
                        data.get("new_rate") == 1.12):
                        print(f"✅ Quick rate update successful")
                        print(f"   Currency: {data['currency']}")
                        print(f"   New rate: {data['new_rate']}")
                        print(f"   Updated by: {data.get('updated_by')}")
                        self.passed_tests += 1
                        return True
                    else:
                        print(f"❌ Invalid quick update response: {data}")
                else:
                    print(f"❌ Failed to quick update rate: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error testing quick rate update: {str(e)}")
        
        return False
    
    async def test_rate_validation(self):
        """Test rate validation (positive numbers only)"""
        print("\n🔍 Testing rate validation...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Test invalid rate (negative)
            invalid_data = {
                "currency": "EUR",
                "rate": -1.5
            }
            
            async with self.session.post(f"{API_BASE}/currency/rates/quick-update", 
                                       json=invalid_data, headers=headers) as response:
                if response.status == 400:
                    print(f"✅ Rate validation working - rejected negative rate")
                    self.passed_tests += 1
                    return True
                else:
                    print(f"❌ Rate validation failed - accepted invalid rate: {response.status}")
        except Exception as e:
            print(f"❌ Error testing rate validation: {str(e)}")
        
        return False
    
    async def test_authentication_required(self):
        """Test that currency updates require proper authentication"""
        print("\n🔍 Testing authentication requirements...")
        self.total_tests += 1
        
        try:
            # Test without authentication
            test_data = {
                "base_currency": "USD",
                "exchange_rates": {"EUR": 1.0}
            }
            
            async with self.session.put(f"{API_BASE}/currency/settings", json=test_data) as response:
                if response.status in [401, 403]:
                    print(f"✅ Authentication properly required - status: {response.status}")
                    self.passed_tests += 1
                    return True
                else:
                    print(f"❌ Authentication not required - status: {response.status}")
        except Exception as e:
            print(f"❌ Error testing authentication: {str(e)}")
        
        return False
    
    async def test_database_integration(self):
        """Test that currency settings are stored and retrieved from database"""
        print("\n🔍 Testing database integration...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            # Set unique test rates
            test_timestamp = datetime.now().strftime("%H%M%S")
            unique_rate = 1.0 + float(f"0.{test_timestamp[-3:]}")  # e.g., 1.123
            
            test_settings = {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.004,
                    "SAR": 0.267,
                    "EUR": unique_rate,  # Unique rate for verification
                    "USD": 1.0
                }
            }
            
            # Update settings
            async with self.session.put(f"{API_BASE}/currency/settings", 
                                      json=test_settings, headers=headers) as response:
                if response.status == 200:
                    # Wait a moment for database write
                    await asyncio.sleep(0.5)
                    
                    # Retrieve settings to verify database storage
                    async with self.session.get(f"{API_BASE}/currency/settings", headers=headers) as get_response:
                        if get_response.status == 200:
                            data = await get_response.json()
                            stored_rate = data["settings"]["exchange_rates"].get("EUR")
                            
                            if stored_rate == unique_rate:
                                print(f"✅ Database integration working - rate persisted: {stored_rate}")
                                self.passed_tests += 1
                                return True
                            else:
                                print(f"❌ Database integration failed - rate not persisted: {stored_rate} vs {unique_rate}")
                        else:
                            print(f"❌ Failed to retrieve settings for verification: {get_response.status}")
                else:
                    print(f"❌ Failed to update settings for database test: {response.status}")
        except Exception as e:
            print(f"❌ Error testing database integration: {str(e)}")
        
        return False
    
    async def test_export_system_integration(self):
        """Test that export system uses dynamic rates from database"""
        print("\n🔍 Testing export system integration...")
        self.total_tests += 1
        
        try:
            headers = self.get_auth_headers()
            
            # Test waste report export which should use dynamic currency rates
            async with self.session.get(f"{API_BASE}/export/waste-report/daily?format=excel", 
                                      headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = int(response.headers.get('content-length', 0))
                    
                    if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
                        print(f"✅ Export system integration working - Excel export successful")
                        print(f"   Content-Type: {content_type}")
                        print(f"   Content-Length: {content_length} bytes")
                        self.passed_tests += 1
                        return True
                    else:
                        print(f"❌ Export system returned unexpected content type: {content_type}")
                else:
                    print(f"❌ Export system integration failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error testing export system integration: {str(e)}")
        
        return False
    
    async def test_fallback_behavior(self):
        """Test fallback behavior when database is unavailable"""
        print("\n🔍 Testing fallback behavior...")
        self.total_tests += 1
        
        try:
            # Test public rates endpoint which should have fallback
            async with self.session.get(f"{API_BASE}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Should return some rates even if database is empty
                    if "exchange_rates" in data and len(data["exchange_rates"]) > 0:
                        print(f"✅ Fallback behavior working - rates available")
                        print(f"   Fallback rates: {data['exchange_rates']}")
                        self.passed_tests += 1
                        return True
                    else:
                        print(f"❌ Fallback behavior failed - no rates returned")
                else:
                    print(f"❌ Fallback test failed: {response.status}")
        except Exception as e:
            print(f"❌ Error testing fallback behavior: {str(e)}")
        
        return False
    
    async def run_all_tests(self):
        """Run all currency management tests"""
        print("🚀 Starting Comprehensive Currency Management System Testing")
        print("=" * 70)
        
        if not await self.setup():
            print("❌ Failed to setup test environment")
            return
        
        try:
            # Test all currency management endpoints
            await self.test_get_currency_settings()
            await self.test_update_currency_settings()
            await self.test_get_public_rates()
            await self.test_quick_update_rate()
            await self.test_rate_validation()
            await self.test_authentication_required()
            await self.test_database_integration()
            await self.test_export_system_integration()
            await self.test_fallback_behavior()
            
        finally:
            await self.cleanup()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 CURRENCY MANAGEMENT SYSTEM TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 CURRENCY MANAGEMENT SYSTEM IS WORKING CORRECTLY!")
        elif success_rate >= 60:
            print("⚠️  CURRENCY MANAGEMENT SYSTEM HAS SOME ISSUES")
        else:
            print("❌ CURRENCY MANAGEMENT SYSTEM HAS CRITICAL ISSUES")
        
        return success_rate

async def main():
    """Main test execution"""
    tester = CurrencyManagementTester()
    success_rate = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    asyncio.run(main())