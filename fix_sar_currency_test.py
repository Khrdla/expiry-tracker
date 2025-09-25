#!/usr/bin/env python3
"""
FIX SAR CURRENCY RATE TEST
==========================

The investigation revealed:
- Current SAR rate: 1.0 (causing 1:1 conversion)
- Expected SAR rate: 0.2667 (1 USD = 3.75 SAR)
- Base currency is set to "INVALID" with only "FAKE": 999 rate

This script will:
1. Update the currency settings with correct SAR rate
2. Test the fix with user's reported values
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class SARCurrencyFix:
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
        
    async def fix_currency_settings(self):
        """Fix currency settings with correct SAR rate"""
        try:
            self.test_results.append("\n🔧 FIXING CURRENCY SETTINGS")
            self.test_results.append("=" * 50)
            
            # Correct exchange rates (to USD)
            correct_rates = {
                "YER": 0.004,    # 1 USD = 250 YER, so 1 YER = 0.004 USD
                "SAR": 0.2667,   # 1 USD = 3.75 SAR, so 1 SAR = 0.2667 USD  
                "EUR": 1.10,     # 1 EUR = 1.10 USD
                "USD": 1.0       # Base rate
            }
            
            settings_update = {
                "base_currency": "USD",
                "exchange_rates": correct_rates,
                "last_updated": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            self.test_results.append(f"🔧 Updating with correct rates:")
            self.test_results.append(f"   YER: {correct_rates['YER']} (1 USD = 250 YER)")
            self.test_results.append(f"   SAR: {correct_rates['SAR']} (1 USD = 3.75 SAR)")
            self.test_results.append(f"   EUR: {correct_rates['EUR']} (1 EUR = 1.10 USD)")
            self.test_results.append(f"   USD: {correct_rates['USD']} (Base currency)")
            
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            async with self.session.put(
                f"{BACKEND_URL}/currency/settings", 
                json=settings_update,
                headers=headers
            ) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    self.test_results.append(f"✅ Currency Settings Updated: {status} OK")
                    self.test_results.append(f"📊 Response: {json.dumps(data, indent=2, default=str)}")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Currency Settings Update Failed: {status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Currency Settings Update Error: {str(e)}")
            return False
            
    async def verify_fix(self):
        """Verify the currency fix worked"""
        try:
            self.test_results.append("\n✅ VERIFYING CURRENCY FIX")
            self.test_results.append("=" * 50)
            
            # Get updated rates
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_rates = data.get("exchange_rates", {})
                    base_currency = data.get("base_currency", "Unknown")
                    
                    self.test_results.append(f"📊 Base Currency: {base_currency}")
                    self.test_results.append(f"📊 Updated Exchange Rates:")
                    for currency, rate in exchange_rates.items():
                        self.test_results.append(f"   {currency}: {rate}")
                        
                    # Check SAR rate specifically
                    sar_rate = exchange_rates.get("SAR")
                    if sar_rate is not None:
                        expected_sar_rate = 1 / 3.75  # 0.2667
                        
                        if abs(sar_rate - expected_sar_rate) < 0.01:
                            self.test_results.append(f"✅ SAR RATE FIXED: {sar_rate} ≈ {expected_sar_rate:.4f}")
                        else:
                            self.test_results.append(f"❌ SAR RATE STILL INCORRECT: {sar_rate} (Expected: {expected_sar_rate:.4f})")
                            
                        return sar_rate
                    else:
                        self.test_results.append("❌ SAR rate still not found")
                        return None
                else:
                    self.test_results.append(f"❌ Could not verify rates: {response.status}")
                    return None
                    
        except Exception as e:
            self.test_results.append(f"❌ Verification Error: {str(e)}")
            return None
            
    async def test_user_reported_values(self):
        """Test with user's exact reported values"""
        try:
            self.test_results.append("\n🧪 TESTING USER REPORTED VALUES")
            self.test_results.append("=" * 50)
            
            # Get current rates after fix
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_rates = data.get("exchange_rates", {})
                    sar_rate = exchange_rates.get("SAR", 1.0)
                    
                    # Test user's exact value: 369.36 SAR
                    user_sar_amount = 369.36
                    expected_usd = 98.50  # 369.36 ÷ 3.75 = 98.496
                    calculated_usd = user_sar_amount * sar_rate
                    
                    self.test_results.append(f"💰 User's Reported Value: {user_sar_amount} SAR")
                    self.test_results.append(f"💰 Expected USD: ${expected_usd}")
                    self.test_results.append(f"💰 Current SAR Rate: {sar_rate}")
                    self.test_results.append(f"💰 Calculated USD: ${calculated_usd:.2f}")
                    
                    if abs(calculated_usd - expected_usd) < 1.0:
                        self.test_results.append(f"✅ USER ISSUE FIXED: {user_sar_amount} SAR = ${calculated_usd:.2f} USD")
                        self.test_results.append(f"🎉 No more 1:1 conversion! Correct rate applied.")
                    else:
                        self.test_results.append(f"❌ USER ISSUE NOT FIXED:")
                        self.test_results.append(f"   Current: {user_sar_amount} SAR = ${calculated_usd:.2f} USD")
                        self.test_results.append(f"   Expected: {user_sar_amount} SAR = ${expected_usd} USD")
                        self.test_results.append(f"   Difference: ${abs(calculated_usd - expected_usd):.2f}")
                        
                    # Test additional values from review request
                    test_values = [
                        (375.00, 100.00),  # 375 SAR should be $100 USD
                        (750.00, 200.00),  # 750 SAR should be $200 USD
                        (1875.00, 500.00)  # 1875 SAR should be $500 USD
                    ]
                    
                    self.test_results.append(f"\n🧪 Additional Test Values:")
                    for sar_amount, expected_usd in test_values:
                        calculated_usd = sar_amount * sar_rate
                        status = "✅" if abs(calculated_usd - expected_usd) < 1.0 else "❌"
                        self.test_results.append(f"   {status} {sar_amount} SAR = ${calculated_usd:.2f} USD (Expected: ${expected_usd})")
                        
        except Exception as e:
            self.test_results.append(f"❌ User Values Test Error: {str(e)}")
            
    async def create_test_return_form(self):
        """Create a test return form with SAR currency to verify conversion"""
        try:
            self.test_results.append("\n📝 CREATING TEST RETURN FORM WITH SAR")
            self.test_results.append("=" * 50)
            
            test_return_form = {
                "reference_number": f"TEST-SAR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "product_code": "TEST-SAR-001",
                "product_name": "Test SAR Conversion Product",
                "barcode": "3222471081716",  # Use known barcode
                "supplier": "Test Supplier",
                "quantity": 1,
                "purchase_price": 369.36,  # User's exact reported amount
                "purchase_currency": "SAR",
                "reason_for_return": "Testing SAR currency conversion fix",
                "prepared_by_supervisor": "Imad Qejji",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "section_manager_approved": True,
                "notes": "Test form to verify SAR conversion: 369.36 SAR should equal $98.50 USD"
            }
            
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            async with self.session.post(
                f"{BACKEND_URL}/return-forms",
                json=test_return_form,
                headers=headers
            ) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    form_id = data.get("id")
                    self.test_results.append(f"✅ Test Return Form Created: {form_id}")
                    self.test_results.append(f"💰 Amount: 369.36 SAR (should convert to ~$98.50 USD)")
                    return form_id
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Return Form Creation Failed: {status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.test_results.append(f"❌ Return Form Creation Error: {str(e)}")
            return None
            
    async def run_fix_and_test(self):
        """Run complete SAR currency fix and verification"""
        try:
            self.test_results.append("🔧 SAR CURRENCY FIX AND TEST STARTED")
            self.test_results.append("=" * 60)
            self.test_results.append(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.test_results.append(f"🎯 Goal: Fix SAR rate from 1.0 to 0.2667")
            self.test_results.append(f"👤 Admin: {ADMIN_USERNAME}")
            
            await self.setup_session()
            
            # Step 1: Authenticate
            if not await self.authenticate():
                self.test_results.append("❌ FIX FAILED: Could not authenticate")
                return
                
            # Step 2: Fix currency settings
            if not await self.fix_currency_settings():
                self.test_results.append("❌ FIX FAILED: Could not update currency settings")
                return
                
            # Step 3: Verify the fix
            sar_rate = await self.verify_fix()
            if sar_rate is None:
                self.test_results.append("❌ FIX VERIFICATION FAILED")
                return
                
            # Step 4: Test with user's reported values
            await self.test_user_reported_values()
            
            # Step 5: Create test return form
            await self.create_test_return_form()
            
            self.test_results.append("\n" + "=" * 60)
            self.test_results.append("🏁 SAR CURRENCY FIX COMPLETED")
            self.test_results.append(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.test_results.append(f"❌ FIX ERROR: {str(e)}")
        finally:
            await self.cleanup_session()
            
    def print_results(self):
        """Print all test results"""
        print("\n".join(self.test_results))
        
    def get_summary(self):
        """Get fix summary"""
        failed_tests = [result for result in self.test_results if "❌" in result]
        passed_tests = [result for result in self.test_results if "✅" in result]
        fixed_issues = [result for result in self.test_results if "🎉" in result]
        
        summary = []
        summary.append(f"\n📊 SAR CURRENCY FIX SUMMARY:")
        summary.append(f"✅ Successful Operations: {len(passed_tests)}")
        summary.append(f"❌ Failed Operations: {len(failed_tests)}")
        summary.append(f"🎉 Issues Fixed: {len(fixed_issues)}")
        
        if fixed_issues:
            summary.append(f"\n🎉 ISSUES FIXED:")
            for fix in fixed_issues:
                summary.append(f"   {fix}")
                
        return "\n".join(summary)

async def main():
    """Main function to run SAR currency fix"""
    fixer = SARCurrencyFix()
    await fixer.run_fix_and_test()
    fixer.print_results()
    print(fixer.get_summary())

if __name__ == "__main__":
    asyncio.run(main())