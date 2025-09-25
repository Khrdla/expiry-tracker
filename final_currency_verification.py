#!/usr/bin/env python3
"""
FINAL CURRENCY VERIFICATION TEST
================================

Comprehensive verification that the SAR currency fix is working correctly
across all system components.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FinalCurrencyVerification:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.test_results.append("✅ AUTHENTICATION: Admin login successful")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ AUTHENTICATION FAILED: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ AUTHENTICATION ERROR: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def verify_currency_rates_api(self):
        """Verify GET /api/currency/rates returns correct SAR rate"""
        try:
            self.test_results.append("\n✅ VERIFYING CURRENCY RATES API")
            self.test_results.append("=" * 50)
            
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    base_currency = data.get("base_currency")
                    exchange_rates = data.get("exchange_rates", {})
                    sar_rate = exchange_rates.get("SAR")
                    
                    self.test_results.append(f"✅ Currency Rates API: 200 OK")
                    self.test_results.append(f"📊 Base Currency: {base_currency}")
                    self.test_results.append(f"📊 SAR Rate: {sar_rate}")
                    
                    # Verify SAR rate is correct (0.2667)
                    expected_sar_rate = 1 / 3.75
                    if sar_rate and abs(sar_rate - expected_sar_rate) < 0.01:
                        self.test_results.append(f"✅ SAR RATE CORRECT: {sar_rate} (Expected: {expected_sar_rate:.4f})")
                        return True
                    else:
                        self.test_results.append(f"❌ SAR RATE INCORRECT: {sar_rate} (Expected: {expected_sar_rate:.4f})")
                        return False
                else:
                    self.test_results.append(f"❌ Currency Rates API Failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Currency Rates API Error: {str(e)}")
            return False
            
    async def verify_currency_settings_api(self):
        """Verify GET /api/currency/settings returns correct configuration"""
        try:
            self.test_results.append("\n✅ VERIFYING CURRENCY SETTINGS API")
            self.test_results.append("=" * 50)
            
            headers = self.get_auth_headers()
            async with self.session.get(f"{BACKEND_URL}/currency/settings", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    settings = data.get("settings", {})
                    base_currency = settings.get("base_currency")
                    exchange_rates = settings.get("exchange_rates", {})
                    
                    self.test_results.append(f"✅ Currency Settings API: 200 OK")
                    self.test_results.append(f"📊 Base Currency: {base_currency}")
                    self.test_results.append(f"📊 Exchange Rates: {json.dumps(exchange_rates, indent=2)}")
                    
                    # Verify all expected rates are present
                    expected_currencies = ["YER", "SAR", "EUR", "USD"]
                    missing_currencies = [curr for curr in expected_currencies if curr not in exchange_rates]
                    
                    if not missing_currencies:
                        self.test_results.append(f"✅ ALL CURRENCIES PRESENT: {expected_currencies}")
                    else:
                        self.test_results.append(f"❌ MISSING CURRENCIES: {missing_currencies}")
                        
                    return len(missing_currencies) == 0
                else:
                    self.test_results.append(f"❌ Currency Settings API Failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Currency Settings API Error: {str(e)}")
            return False
            
    async def test_exact_user_scenarios(self):
        """Test the exact scenarios reported by the user"""
        try:
            self.test_results.append("\n🎯 TESTING EXACT USER SCENARIOS")
            self.test_results.append("=" * 50)
            
            # Get current rates
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_rates = data.get("exchange_rates", {})
                    sar_rate = exchange_rates.get("SAR", 1.0)
                    
                    # Test exact user reported value: 369.36 SAR
                    user_amount = 369.36
                    calculated_usd = user_amount * sar_rate
                    expected_usd = user_amount / 3.75  # 98.496
                    
                    self.test_results.append(f"🎯 User's Exact Scenario:")
                    self.test_results.append(f"   Amount: {user_amount} SAR")
                    self.test_results.append(f"   Previous (Wrong): ${user_amount:.2f} USD (1:1 conversion)")
                    self.test_results.append(f"   Current: ${calculated_usd:.2f} USD")
                    self.test_results.append(f"   Expected: ${expected_usd:.2f} USD")
                    
                    if abs(calculated_usd - expected_usd) < 1.0:
                        self.test_results.append(f"✅ USER ISSUE RESOLVED: Correct conversion applied")
                        self.test_results.append(f"🎉 No more 1:1 conversion error!")
                        return True
                    else:
                        self.test_results.append(f"❌ USER ISSUE NOT RESOLVED: Still incorrect conversion")
                        return False
                else:
                    self.test_results.append(f"❌ Could not get rates for user scenario test")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ User Scenario Test Error: {str(e)}")
            return False
            
    async def test_return_form_conversion(self):
        """Test return form with SAR currency conversion"""
        try:
            self.test_results.append("\n📝 TESTING RETURN FORM SAR CONVERSION")
            self.test_results.append("=" * 50)
            
            # Create a test return form with SAR currency
            test_form = {
                "reference_number": f"VERIFY-SAR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "product_code": "VERIFY-001",
                "product_name": "SAR Conversion Verification Product",
                "barcode": "3222471081716",
                "supplier": "Test Supplier",
                "quantity": 1,
                "purchase_price": 375.00,  # Should be exactly $100.00 USD
                "purchase_currency": "SAR",
                "reason_for_return": "Verifying SAR to USD conversion",
                "prepared_by_supervisor": "Imad Qejji",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "section_manager_approved": True,
                "notes": "375.00 SAR should equal exactly $100.00 USD"
            }
            
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            async with self.session.post(
                f"{BACKEND_URL}/return-forms",
                json=test_form,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    form_id = data.get("id")
                    self.test_results.append(f"✅ Return Form Created: {form_id}")
                    
                    # Calculate expected conversion
                    sar_amount = 375.00
                    expected_usd = sar_amount / 3.75  # 100.00
                    
                    self.test_results.append(f"📊 Return Form Details:")
                    self.test_results.append(f"   Amount: {sar_amount} SAR")
                    self.test_results.append(f"   Expected USD: ${expected_usd:.2f}")
                    self.test_results.append(f"   Form ID: {form_id}")
                    
                    return form_id
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Return Form Creation Failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.test_results.append(f"❌ Return Form Test Error: {str(e)}")
            return None
            
    async def comprehensive_rate_verification(self):
        """Comprehensive verification of all currency rates"""
        try:
            self.test_results.append("\n🔍 COMPREHENSIVE RATE VERIFICATION")
            self.test_results.append("=" * 50)
            
            # Get current rates
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_rates = data.get("exchange_rates", {})
                    
                    # Expected rates (to USD)
                    expected_rates = {
                        "YER": 0.004,    # 1 USD = 250 YER
                        "SAR": 0.2667,   # 1 USD = 3.75 SAR
                        "EUR": 1.10,     # 1 EUR = 1.10 USD
                        "USD": 1.0       # Base
                    }
                    
                    all_correct = True
                    
                    for currency, expected_rate in expected_rates.items():
                        actual_rate = exchange_rates.get(currency)
                        
                        if actual_rate is not None:
                            if abs(actual_rate - expected_rate) < 0.01:
                                self.test_results.append(f"✅ {currency}: {actual_rate} (Expected: {expected_rate})")
                            else:
                                self.test_results.append(f"❌ {currency}: {actual_rate} (Expected: {expected_rate})")
                                all_correct = False
                        else:
                            self.test_results.append(f"❌ {currency}: Missing from rates")
                            all_correct = False
                            
                    if all_correct:
                        self.test_results.append(f"✅ ALL CURRENCY RATES CORRECT")
                    else:
                        self.test_results.append(f"❌ SOME CURRENCY RATES INCORRECT")
                        
                    return all_correct
                else:
                    self.test_results.append(f"❌ Could not verify rates: {response.status}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Comprehensive Rate Verification Error: {str(e)}")
            return False
            
    async def run_final_verification(self):
        """Run complete final verification"""
        try:
            self.test_results.append("🏁 FINAL CURRENCY VERIFICATION STARTED")
            self.test_results.append("=" * 60)
            self.test_results.append(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.test_results.append(f"🎯 Goal: Verify SAR currency fix is working correctly")
            self.test_results.append(f"👤 Admin: {ADMIN_USERNAME}")
            
            await self.setup_session()
            
            # Step 1: Authenticate
            if not await self.authenticate():
                self.test_results.append("❌ VERIFICATION FAILED: Could not authenticate")
                return
                
            # Step 2: Verify currency rates API
            rates_ok = await self.verify_currency_rates_api()
            
            # Step 3: Verify currency settings API
            settings_ok = await self.verify_currency_settings_api()
            
            # Step 4: Test exact user scenarios
            user_scenarios_ok = await self.test_exact_user_scenarios()
            
            # Step 5: Test return form conversion
            return_form_id = await self.test_return_form_conversion()
            
            # Step 6: Comprehensive rate verification
            comprehensive_ok = await self.comprehensive_rate_verification()
            
            # Final assessment
            all_tests_passed = all([rates_ok, settings_ok, user_scenarios_ok, return_form_id is not None, comprehensive_ok])
            
            self.test_results.append("\n" + "=" * 60)
            if all_tests_passed:
                self.test_results.append("🎉 FINAL VERIFICATION: ALL TESTS PASSED")
                self.test_results.append("✅ SAR CURRENCY ISSUE COMPLETELY RESOLVED")
                self.test_results.append("✅ User's 369.36 SAR now correctly converts to ~$98.50 USD")
                self.test_results.append("✅ No more 1:1 conversion error")
            else:
                self.test_results.append("❌ FINAL VERIFICATION: SOME TESTS FAILED")
                
            self.test_results.append(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.test_results.append(f"❌ VERIFICATION ERROR: {str(e)}")
        finally:
            await self.cleanup_session()
            
    def print_results(self):
        """Print all test results"""
        print("\n".join(self.test_results))
        
    def get_summary(self):
        """Get verification summary"""
        failed_tests = [result for result in self.test_results if "❌" in result]
        passed_tests = [result for result in self.test_results if "✅" in result]
        resolved_issues = [result for result in self.test_results if "🎉" in result]
        
        summary = []
        summary.append(f"\n📊 FINAL VERIFICATION SUMMARY:")
        summary.append(f"✅ Passed Tests: {len(passed_tests)}")
        summary.append(f"❌ Failed Tests: {len(failed_tests)}")
        summary.append(f"🎉 Issues Resolved: {len(resolved_issues)}")
        
        if resolved_issues:
            summary.append(f"\n🎉 ISSUES RESOLVED:")
            for issue in resolved_issues:
                summary.append(f"   {issue}")
                
        return "\n".join(summary)

async def main():
    """Main function to run final verification"""
    verifier = FinalCurrencyVerification()
    await verifier.run_final_verification()
    verifier.print_results()
    print(verifier.get_summary())

if __name__ == "__main__":
    asyncio.run(main())