#!/usr/bin/env python3
"""
URGENT CURRENCY INVESTIGATION TEST
==================================

Testing SAR conversion rates as reported by user:
- User reports: 369.36 SAR showing as $369.36 USD (wrong 1:1 ratio)
- Expected: 369.36 SAR = $98.50 USD (369.36 ÷ 3.75 = 98.496)
- Correct rate: 1 USD = 3.75 SAR, so 1 SAR = 0.2667 USD

Admin credentials: imadqejji/066380531I
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class CurrencyInvestigationTest:
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
        
    async def test_currency_rates_api(self):
        """Test GET /api/currency/rates endpoint"""
        try:
            self.test_results.append("\n🔍 TESTING CURRENCY RATES API")
            self.test_results.append("=" * 50)
            
            async with self.session.get(f"{BACKEND_URL}/currency/rates") as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    self.test_results.append(f"✅ Currency Rates API: {status} OK")
                    
                    # Check base currency
                    base_currency = data.get("base_currency", "Unknown")
                    self.test_results.append(f"📊 Base Currency: {base_currency}")
                    
                    # Check exchange rates
                    exchange_rates = data.get("exchange_rates", {})
                    self.test_results.append(f"📊 Exchange Rates: {json.dumps(exchange_rates, indent=2)}")
                    
                    # Check SAR rate specifically
                    sar_rate = exchange_rates.get("SAR")
                    if sar_rate is not None:
                        self.test_results.append(f"🎯 SAR Rate: {sar_rate}")
                        
                        # Expected SAR rate should be 0.2667 (1 USD = 3.75 SAR)
                        expected_sar_rate = 1 / 3.75  # 0.2667
                        
                        if abs(sar_rate - expected_sar_rate) < 0.01:  # Allow small tolerance
                            self.test_results.append(f"✅ SAR RATE CORRECT: {sar_rate} ≈ {expected_sar_rate:.4f}")
                        else:
                            self.test_results.append(f"❌ SAR RATE INCORRECT: {sar_rate} (Expected: {expected_sar_rate:.4f})")
                            self.test_results.append(f"🚨 ISSUE IDENTIFIED: SAR rate is {sar_rate}, should be {expected_sar_rate:.4f}")
                    else:
                        self.test_results.append("❌ SAR rate not found in exchange rates")
                        
                    # Check last updated
                    last_updated = data.get("last_updated")
                    if last_updated:
                        self.test_results.append(f"📅 Last Updated: {last_updated}")
                        
                    return data
                    
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Currency Rates API Failed: {status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.test_results.append(f"❌ Currency Rates API Error: {str(e)}")
            return None
            
    async def test_currency_settings_api(self):
        """Test GET /api/currency/settings endpoint"""
        try:
            self.test_results.append("\n🔍 TESTING CURRENCY SETTINGS API")
            self.test_results.append("=" * 50)
            
            headers = self.get_auth_headers()
            async with self.session.get(f"{BACKEND_URL}/currency/settings", headers=headers) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    self.test_results.append(f"✅ Currency Settings API: {status} OK")
                    
                    settings = data.get("settings", {})
                    supported_currencies = data.get("supported_currencies", [])
                    base_currency = data.get("base_currency", "Unknown")
                    
                    self.test_results.append(f"📊 Supported Currencies: {supported_currencies}")
                    self.test_results.append(f"📊 Base Currency: {base_currency}")
                    self.test_results.append(f"📊 Settings: {json.dumps(settings, indent=2, default=str)}")
                    
                    return data
                    
                elif status == 401 or status == 403:
                    self.test_results.append(f"❌ Currency Settings API: Authentication required ({status})")
                    return None
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Currency Settings API Failed: {status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.test_results.append(f"❌ Currency Settings API Error: {str(e)}")
            return None
            
    async def test_sar_conversion_calculation(self):
        """Test SAR conversion with specific values from user report"""
        try:
            self.test_results.append("\n🔍 TESTING SAR CONVERSION CALCULATION")
            self.test_results.append("=" * 50)
            
            # Test values from user's screenshot
            test_amount_sar = 369.36
            expected_usd = 98.50  # 369.36 ÷ 3.75 = 98.496
            correct_sar_rate = 1 / 3.75  # 0.2667
            
            self.test_results.append(f"🧮 Test Amount: {test_amount_sar} SAR")
            self.test_results.append(f"🧮 Expected USD: ${expected_usd} USD")
            self.test_results.append(f"🧮 Correct SAR Rate: {correct_sar_rate:.4f}")
            
            # Get current rates from API
            rates_data = await self.test_currency_rates_api()
            if rates_data:
                exchange_rates = rates_data.get("exchange_rates", {})
                current_sar_rate = exchange_rates.get("SAR", 1.0)
                
                # Calculate conversion with current rate
                calculated_usd = test_amount_sar * current_sar_rate
                
                self.test_results.append(f"🧮 Current SAR Rate from API: {current_sar_rate}")
                self.test_results.append(f"🧮 Calculated USD: ${calculated_usd:.2f}")
                
                # Check if conversion is correct
                if abs(calculated_usd - expected_usd) < 1.0:  # Allow $1 tolerance
                    self.test_results.append(f"✅ SAR CONVERSION CORRECT: {test_amount_sar} SAR = ${calculated_usd:.2f} USD")
                else:
                    self.test_results.append(f"❌ SAR CONVERSION INCORRECT:")
                    self.test_results.append(f"   Current: {test_amount_sar} SAR = ${calculated_usd:.2f} USD")
                    self.test_results.append(f"   Expected: {test_amount_sar} SAR = ${expected_usd:.2f} USD")
                    self.test_results.append(f"   Difference: ${abs(calculated_usd - expected_usd):.2f}")
                    
                    if current_sar_rate == 1.0:
                        self.test_results.append(f"🚨 CRITICAL ISSUE: SAR rate is 1.0 (1:1 conversion) - This is the reported problem!")
                        
        except Exception as e:
            self.test_results.append(f"❌ SAR Conversion Test Error: {str(e)}")
            
    async def test_additional_sar_values(self):
        """Test additional SAR conversion values"""
        try:
            self.test_results.append("\n🔍 TESTING ADDITIONAL SAR VALUES")
            self.test_results.append("=" * 50)
            
            # Test the specific value mentioned in review request
            test_values = [
                375.00,  # Should be $100.00 USD (375 ÷ 3.75 = 100)
                369.36,  # User's reported value
                750.00,  # Should be $200.00 USD
                1875.00  # Should be $500.00 USD
            ]
            
            # Get current rates
            rates_data = await self.test_currency_rates_api()
            if rates_data:
                exchange_rates = rates_data.get("exchange_rates", {})
                current_sar_rate = exchange_rates.get("SAR", 1.0)
                
                for sar_amount in test_values:
                    expected_usd = sar_amount / 3.75
                    calculated_usd = sar_amount * current_sar_rate
                    
                    self.test_results.append(f"💰 {sar_amount} SAR:")
                    self.test_results.append(f"   Expected: ${expected_usd:.2f} USD")
                    self.test_results.append(f"   Current:  ${calculated_usd:.2f} USD")
                    
                    if abs(calculated_usd - expected_usd) < 1.0:
                        self.test_results.append(f"   ✅ CORRECT")
                    else:
                        self.test_results.append(f"   ❌ INCORRECT (Diff: ${abs(calculated_usd - expected_usd):.2f})")
                        
        except Exception as e:
            self.test_results.append(f"❌ Additional SAR Values Test Error: {str(e)}")
            
    async def run_investigation(self):
        """Run complete currency investigation"""
        try:
            self.test_results.append("🚨 URGENT CURRENCY INVESTIGATION STARTED")
            self.test_results.append("=" * 60)
            self.test_results.append(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.test_results.append(f"🎯 Focus: SAR conversion rate issue")
            self.test_results.append(f"👤 Admin: {ADMIN_USERNAME}")
            
            await self.setup_session()
            
            # Step 1: Authenticate
            if not await self.authenticate():
                self.test_results.append("❌ INVESTIGATION FAILED: Could not authenticate")
                return
                
            # Step 2: Test currency rates API
            await self.test_currency_rates_api()
            
            # Step 3: Test currency settings API  
            await self.test_currency_settings_api()
            
            # Step 4: Test SAR conversion calculation
            await self.test_sar_conversion_calculation()
            
            # Step 5: Test additional SAR values
            await self.test_additional_sar_values()
            
            self.test_results.append("\n" + "=" * 60)
            self.test_results.append("🏁 CURRENCY INVESTIGATION COMPLETED")
            self.test_results.append(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.test_results.append(f"❌ INVESTIGATION ERROR: {str(e)}")
        finally:
            await self.cleanup_session()
            
    def print_results(self):
        """Print all test results"""
        print("\n".join(self.test_results))
        
    def get_summary(self):
        """Get investigation summary"""
        failed_tests = [result for result in self.test_results if "❌" in result]
        passed_tests = [result for result in self.test_results if "✅" in result]
        critical_issues = [result for result in self.test_results if "🚨" in result]
        
        summary = []
        summary.append(f"\n📊 INVESTIGATION SUMMARY:")
        summary.append(f"✅ Passed Tests: {len(passed_tests)}")
        summary.append(f"❌ Failed Tests: {len(failed_tests)}")
        summary.append(f"🚨 Critical Issues: {len(critical_issues)}")
        
        if critical_issues:
            summary.append(f"\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                summary.append(f"   {issue}")
                
        return "\n".join(summary)

async def main():
    """Main function to run currency investigation"""
    investigator = CurrencyInvestigationTest()
    await investigator.run_investigation()
    investigator.print_results()
    print(investigator.get_summary())

if __name__ == "__main__":
    asyncio.run(main())