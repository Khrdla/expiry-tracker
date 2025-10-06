#!/usr/bin/env python3
"""
USD Conversion Testing for Waste Reports
Focus on verifying USD conversion is working correctly
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geant-scanner.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

async def test_usd_conversion():
    """Test USD conversion functionality in waste reports"""
    
    # Setup session
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
    
    try:
        # Authenticate
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        async with session.post(f"{API_BASE}/auth/login", json=login_data) as response:
            if response.status != 200:
                print("❌ Authentication failed")
                return
            
            data = await response.json()
            auth_token = data.get('access_token')
            session.headers.update({'Authorization': f'Bearer {auth_token}'})
            print("✅ Authentication successful")
        
        # Test 1: Check if enhanced_export_system module exists
        print("\n🔍 Testing Enhanced Export System")
        
        # Test waste report export with different currencies
        test_currencies = ["YER", "SAR", "EUR"]
        
        for currency in test_currencies:
            print(f"\n📊 Testing {currency} currency handling...")
            
            # Create a test waste entry with specific currency
            test_entry = {
                "product_id": f"test-{currency.lower()}-product",
                "product_name": f"Test Product {currency}",
                "quantity_wasted": 10,
                "purchase_price": 100.0 if currency == "YER" else (50.0 if currency == "SAR" else 25.0),
                "purchase_currency": currency,
                "waste_reason": "testing_usd_conversion",
                "department": "01-FMG"
            }
            
            # Try to create waste entry
            try:
                async with session.post(f"{API_BASE}/waste/entries", json=test_entry) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        print(f"✅ Created test waste entry for {currency}")
                        
                        # Check if USD conversion is mentioned in response
                        if 'usd' in str(result).lower():
                            print(f"✅ USD conversion detected in {currency} waste entry response")
                        else:
                            print(f"⚠️ No USD conversion detected in {currency} waste entry response")
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create {currency} waste entry: {response.status} - {error_text}")
            except Exception as e:
                print(f"❌ Exception creating {currency} waste entry: {str(e)}")
        
        # Test 2: Check waste reports for USD conversion
        print(f"\n📈 Testing Waste Report USD Conversion...")
        
        try:
            async with session.get(f"{API_BASE}/waste/reports?period=daily") as response:
                if response.status == 200:
                    report_data = await response.json()
                    print(f"✅ Waste reports API working")
                    
                    # Check for USD conversion in report data
                    report_str = str(report_data).lower()
                    if 'usd' in report_str:
                        print("✅ USD conversion found in waste reports API")
                    else:
                        print("⚠️ No USD conversion found in waste reports API")
                    
                    # Check for currency totals
                    if 'currency_totals' in report_str:
                        print("✅ Currency totals found in waste reports")
                    else:
                        print("⚠️ No currency totals found in waste reports")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Waste reports API failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Exception testing waste reports: {str(e)}")
        
        # Test 3: Check Excel export for USD conversion
        print(f"\n📊 Testing Excel Export USD Conversion...")
        
        try:
            async with session.get(f"{API_BASE}/export/waste-report/daily?format=excel") as response:
                if response.status == 200:
                    content = await response.read()
                    print(f"✅ Waste report Excel export successful - {len(content)} bytes")
                    
                    # Check if it's using enhanced export system
                    if len(content) > 30000:  # Enhanced system typically generates larger files
                        print("✅ Large file size suggests enhanced export system is working")
                    else:
                        print("⚠️ Small file size suggests fallback system might be used")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Excel export failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Exception testing Excel export: {str(e)}")
        
        # Test 4: Check if enhanced_export_system.py exists and is accessible
        print(f"\n🔧 Testing Enhanced Export System Module...")
        
        try:
            # Try to access a simple endpoint that might use the enhanced system
            async with session.get(f"{API_BASE}/export/return-forms") as response:
                if response.status == 200:
                    content = await response.read()
                    content_type = response.headers.get('content-type', '')
                    
                    if 'spreadsheet' in content_type and len(content) > 30000:
                        print("✅ Enhanced export system appears to be working (large structured files)")
                    else:
                        print("⚠️ May be using fallback export system")
                        
                else:
                    print(f"❌ Return forms export failed: {response.status}")
        except Exception as e:
            print(f"❌ Exception testing enhanced export system: {str(e)}")
        
        # Test 5: Check for specific USD conversion rates
        print(f"\n💱 Testing Currency Conversion Rates...")
        
        # Expected conversion rates from enhanced_export_system.py:
        # YER: 0.004 (250 YER = 1 USD)
        # SAR: 0.267 (3.75 SAR = 1 USD)  
        # EUR: 1.10 (1 EUR = 1.10 USD)
        
        test_conversions = [
            ("YER", 1000, 4.0),    # 1000 YER should be ~4 USD
            ("SAR", 100, 26.7),    # 100 SAR should be ~26.7 USD
            ("EUR", 100, 110.0)    # 100 EUR should be ~110 USD
        ]
        
        for currency, amount, expected_usd in test_conversions:
            print(f"Expected conversion: {amount} {currency} = ~{expected_usd} USD")
        
        print("\n💡 Note: USD conversion verification requires examining the actual Excel/PDF content")
        print("The enhanced export system should show both original currency and USD amounts")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_usd_conversion())