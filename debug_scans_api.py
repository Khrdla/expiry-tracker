#!/usr/bin/env python3
"""
Debug Inventory Scans API Response
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

async def debug_scans_api():
    """Debug inventory scans API response"""
    session = aiohttp.ClientSession()
    
    try:
        # Authenticate
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                print("❌ Authentication failed")
                return
            data = await response.json()
            auth_token = data.get("access_token")
            print("✅ Authentication successful")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get inventory scans
        async with session.get(f"{BACKEND_URL}/inventory-scans", headers=headers) as response:
            if response.status != 200:
                print(f"❌ API call failed: {response.status}")
                return
            
            scans_data = await response.json()
            print(f"✅ Retrieved {len(scans_data)} scan records")
            print(f"📄 Response type: {type(scans_data)}")
            
            if scans_data:
                print(f"📄 First record type: {type(scans_data[0])}")
                print(f"📄 First record: {json.dumps(scans_data[0], indent=2, default=str)}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(debug_scans_api())