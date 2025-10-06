#!/usr/bin/env python3
"""
Debug PDF Content Analysis
"""

import asyncio
import aiohttp
import PyPDF2
from io import BytesIO

BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

async def debug_pdf_content():
    """Debug PDF content to understand structure"""
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
        
        # Get PDF
        async with session.get(f"{BACKEND_URL}/inventory-scans/export-pdf", headers=headers) as response:
            if response.status != 200:
                print(f"❌ PDF export failed: {response.status}")
                return
            
            pdf_content = await response.read()
            print(f"✅ PDF downloaded: {len(pdf_content)} bytes")
        
        # Analyze PDF
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        print(f"📄 PDF has {len(pdf_reader.pages)} pages")
        
        for i, page in enumerate(pdf_reader.pages):
            print(f"\n📋 PAGE {i+1} CONTENT:")
            print("-" * 50)
            page_text = page.extract_text()
            print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
            print("-" * 50)
            
            # Check for specific patterns
            if "Zone Number:" in page_text:
                zone_line = [line for line in page_text.split('\n') if 'Zone Number:' in line]
                print(f"🎯 Zone header found: {zone_line}")
            else:
                print("❌ No zone header found")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(debug_pdf_content())