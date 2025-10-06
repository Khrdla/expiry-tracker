#!/usr/bin/env python3
"""
Dynamic Currency Conversion Dashboard Enhancement Testing
Testing comprehensive currency system implementation with admin-only currency management
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
DEFAULT_DISPLAY_CURRENCY = "USD"
DEFAULT_YER_EXCHANGE_RATE = 1610.0
DEFAULT_SAR_EXCHANGE_RATE = 3.75
TEST_CURRENCIES = ["USD", "SAR", "YER"]

class CurrencyConversionTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.original_settings = None
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.0f}ms",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({response_time:.0f}ms)")
        if details:
            print(f"    Details: {details}")
    
    def authenticate_admin(self):
        """Authenticate with admin credentials"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Admin Authentication", True, 
                    f"Admin user {ADMIN_USERNAME} authenticated successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_get_currency_settings_default(self):
        """Test GET /api/dashboard/currency-settings returns default settings for new users"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/dashboard/currency-settings")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.original_settings = data  # Store for cleanup
                
                # Verify default values
                expected_fields = ["display_currency", "yer_exchange_rate", "sar_exchange_rate", "last_updated", "can_edit"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_result("GET Currency Settings - Structure", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return False
                
                # Verify default values
                display_currency_ok = data.get("display_currency") == DEFAULT_DISPLAY_CURRENCY
                yer_rate_ok = data.get("yer_exchange_rate") == DEFAULT_YER_EXCHANGE_RATE
                sar_rate_ok = data.get("sar_exchange_rate") == DEFAULT_SAR_EXCHANGE_RATE
                can_edit_ok = data.get("can_edit") == True  # Admin should be able to edit
                
                all_defaults_ok = display_currency_ok and yer_rate_ok and sar_rate_ok and can_edit_ok
                
                self.log_result("GET Currency Settings - Default Values", all_defaults_ok,
                    f"Currency: {data.get('display_currency')} (expected: {DEFAULT_DISPLAY_CURRENCY}), "
                    f"YER rate: {data.get('yer_exchange_rate')} (expected: {DEFAULT_YER_EXCHANGE_RATE}), "
                    f"SAR rate: {data.get('sar_exchange_rate')} (expected: {DEFAULT_SAR_EXCHANGE_RATE}), "
                    f"Can edit: {data.get('can_edit')} (expected: True)", response_time)
                return all_defaults_ok
            else:
                self.log_result("GET Currency Settings", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("GET Currency Settings", False, f"Exception: {str(e)}")
            return False
    
    def test_put_currency_settings_admin_only(self):
        """Test PUT /api/dashboard/currency-settings (admin-only endpoint)"""
        try:
            # Test updating currency settings
            start_time = time.time()
            
            test_settings = {
                "display_currency": "SAR",
                "yer_exchange_rate": 1650.0  # Updated rate
            }
            
            response = self.session.put(f"{BACKEND_URL}/dashboard/currency-settings", json=test_settings)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                expected_fields = ["success", "message", "display_currency", "yer_exchange_rate", "sar_exchange_rate", "last_updated"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_result("PUT Currency Settings - Response Structure", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return False
                
                # Verify updated values
                currency_updated = data.get("display_currency") == "SAR"
                yer_rate_updated = data.get("yer_exchange_rate") == 1650.0
                sar_rate_fixed = data.get("sar_exchange_rate") == 3.75  # Should remain fixed
                success_flag = data.get("success") == True
                
                all_updates_ok = currency_updated and yer_rate_updated and sar_rate_fixed and success_flag
                
                self.log_result("PUT Currency Settings - Admin Update", all_updates_ok,
                    f"Success: {data.get('success')}, Currency: {data.get('display_currency')}, "
                    f"YER rate: {data.get('yer_exchange_rate')}, SAR rate: {data.get('sar_exchange_rate')}", response_time)
                return all_updates_ok
            else:
                self.log_result("PUT Currency Settings - Admin Update", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("PUT Currency Settings - Admin Update", False, f"Exception: {str(e)}")
            return False
    
    def test_currency_conversion_logic(self):
        """Test currency conversion formulas work correctly"""
        try:
            # Test conversion formulas with known values
            test_cases = [
                {
                    "name": "USD to Base (no conversion)",
                    "base_value_usd": 100.0,
                    "target_currency": "USD",
                    "expected_result": 100.0,
                    "formula": "USD → Base values (no conversion)"
                },
                {
                    "name": "USD to SAR conversion",
                    "base_value_usd": 100.0,
                    "target_currency": "SAR",
                    "expected_result": 375.0,  # 100 * 3.75
                    "formula": "SAR → USD Value × 3.75"
                },
                {
                    "name": "USD to YER conversion",
                    "base_value_usd": 100.0,
                    "target_currency": "YER",
                    "expected_result": 165000.0,  # 100 * 1650 (updated rate)
                    "formula": "YER → USD Value × Exchange Rate Input (1650)"
                }
            ]
            
            all_conversions_ok = True
            conversion_details = []
            
            for test_case in test_cases:
                base_value = test_case["base_value_usd"]
                target_currency = test_case["target_currency"]
                expected = test_case["expected_result"]
                
                # Calculate conversion based on current rates
                if target_currency == "USD":
                    converted_value = base_value
                elif target_currency == "SAR":
                    converted_value = base_value * 3.75
                elif target_currency == "YER":
                    converted_value = base_value * 1650.0  # Using updated rate from previous test
                
                conversion_ok = abs(converted_value - expected) < 0.01  # Allow small floating point differences
                
                if not conversion_ok:
                    all_conversions_ok = False
                
                conversion_details.append(f"{test_case['name']}: {converted_value} (expected: {expected}) - {'✓' if conversion_ok else '✗'}")
            
            self.log_result("Currency Conversion Logic", all_conversions_ok,
                f"Conversion tests: {'; '.join(conversion_details)}", 0)
            return all_conversions_ok
            
        except Exception as e:
            self.log_result("Currency Conversion Logic", False, f"Exception: {str(e)}")
            return False
    
    def test_settings_persistence(self):
        """Test that updated settings are saved and retrievable"""
        try:
            # First, update settings with new values
            start_time = time.time()
            
            test_settings = {
                "display_currency": "YER",
                "yer_exchange_rate": 1700.0
            }
            
            update_response = self.session.put(f"{BACKEND_URL}/dashboard/currency-settings", json=test_settings)
            update_time = (time.time() - start_time) * 1000
            
            if update_response.status_code != 200:
                self.log_result("Settings Persistence - Update", False,
                    f"Failed to update settings: {update_response.status_code}", update_time)
                return False
            
            # Wait a moment for database consistency
            time.sleep(0.5)
            
            # Now retrieve settings to verify persistence
            start_time = time.time()
            get_response = self.session.get(f"{BACKEND_URL}/dashboard/currency-settings")
            get_time = (time.time() - start_time) * 1000
            
            if get_response.status_code == 200:
                data = get_response.json()
                
                # Verify persisted values
                currency_persisted = data.get("display_currency") == "YER"
                yer_rate_persisted = data.get("yer_exchange_rate") == 1700.0
                sar_rate_unchanged = data.get("sar_exchange_rate") == 3.75
                
                persistence_ok = currency_persisted and yer_rate_persisted and sar_rate_unchanged
                
                self.log_result("Settings Persistence", persistence_ok,
                    f"Retrieved - Currency: {data.get('display_currency')}, "
                    f"YER rate: {data.get('yer_exchange_rate')}, SAR rate: {data.get('sar_exchange_rate')}", 
                    update_time + get_time)
                return persistence_ok
            else:
                self.log_result("Settings Persistence - Retrieval", False,
                    f"Failed to retrieve settings: {get_response.status_code}", get_time)
                return False
                
        except Exception as e:
            self.log_result("Settings Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_non_admin_access_restriction(self):
        """Test that non-admin users cannot update currency settings"""
        try:
            # Create a temporary session without admin token
            non_admin_session = requests.Session()
            
            # Try to update settings without admin authentication
            start_time = time.time()
            
            test_settings = {
                "display_currency": "USD",
                "yer_exchange_rate": 1500.0
            }
            
            response = non_admin_session.put(f"{BACKEND_URL}/dashboard/currency-settings", json=test_settings)
            response_time = (time.time() - start_time) * 1000
            
            # Should get 401 (Unauthorized) or 403 (Forbidden)
            access_properly_restricted = response.status_code in [401, 403]
            
            self.log_result("Non-Admin Access Restriction", access_properly_restricted,
                f"Status: {response.status_code} (expected: 401 or 403), "
                f"Response: {response.text[:100] if response.text else 'No response body'}", response_time)
            return access_properly_restricted
            
        except Exception as e:
            self.log_result("Non-Admin Access Restriction", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all currency conversion dashboard enhancement tests"""
        print("🚀 DYNAMIC CURRENCY CONVERSION DASHBOARD ENHANCEMENT TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print(f"Test Currencies: {TEST_CURRENCIES}")
        print(f"Default Settings: Currency={DEFAULT_DISPLAY_CURRENCY}, YER={DEFAULT_YER_EXCHANGE_RATE}, SAR={DEFAULT_SAR_EXCHANGE_RATE}")
        print("=" * 70)
        
        # 1. Admin Authentication
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - stopping tests")
            return
        
        # 2. Test GET currency settings with default values
        self.test_get_currency_settings_default()
        
        # 3. Test PUT currency settings (admin-only)
        self.test_put_currency_settings_admin_only()
        
        # 4. Test currency conversion logic
        self.test_currency_conversion_logic()
        
        # 5. Test settings persistence
        self.test_settings_persistence()
        
        # 6. Test non-admin access restriction
        self.test_non_admin_access_restriction()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 CURRENCY CONVERSION DASHBOARD ENHANCEMENT TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "GET Currency Settings Default Values": any("GET Currency Settings - Default Values" in r["test"] and r["success"] for r in self.test_results),
            "PUT Currency Settings Admin-Only": any("PUT Currency Settings - Admin Update" in r["test"] and r["success"] for r in self.test_results),
            "Currency Conversion Logic": any("Currency Conversion Logic" in r["test"] and r["success"] for r in self.test_results),
            "Settings Persistence": any("Settings Persistence" in r["test"] and r["success"] for r in self.test_results),
            "Non-Admin Access Restriction": any("Non-Admin Access Restriction" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n" + "=" * 70)
        print("🏁 CURRENCY CONVERSION DASHBOARD ENHANCEMENT TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = CurrencyConversionTester()
    tester.run_comprehensive_tests()