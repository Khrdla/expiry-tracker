#!/usr/bin/env python3
"""
Barcode Database Check - List all barcodes that exist in the Geant Hypermarket database
This script connects to the database and retrieves all products with valid barcodes
for testing the barcode scanner with real data.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# Load environment variables
load_dotenv('/app/backend/.env')

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'inventory_db')

# API configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class BarcodeChecker:
    def __init__(self):
        self.client = None
        self.db = None
        self.auth_token = None
        
    async def connect_database(self):
        """Connect to MongoDB database"""
        try:
            print("🔌 Connecting to MongoDB database...")
            self.client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.client[DB_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to database: {str(e)}")
            return False
    
    def authenticate_api(self):
        """Authenticate with the API to get access token"""
        try:
            print("🔐 Authenticating with API...")
            
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                print("✅ Successfully authenticated with API")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def get_products_with_barcodes_db(self):
        """Get all products with barcodes directly from database"""
        try:
            print("📊 Querying database for products with barcodes...")
            
            # Query products that have non-empty barcodes
            query = {
                "barcode": {
                    "$exists": True,
                    "$ne": None,
                    "$ne": "",
                    "$regex": "^.+$"  # At least one character
                }
            }
            
            products_cursor = self.db.products.find(query)
            products = []
            
            async for product in products_cursor:
                if product.get('barcode') and str(product.get('barcode')).strip():
                    products.append({
                        'barcode': str(product.get('barcode')).strip(),
                        'product_name': product.get('product_name', 'Unknown'),
                        'department': product.get('department', 'Unknown'),
                        'section': product.get('section', 'Unknown'),
                        'supplier': product.get('supplier', 'Unknown'),
                        'purchase_price': product.get('purchase_price', 0),
                        'purchase_currency': product.get('purchase_currency', 'YER'),
                        'quantity': product.get('quantity', 0)
                    })
            
            print(f"✅ Found {len(products)} products with valid barcodes in database")
            return products
            
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return []
    
    def test_barcode_api(self, barcode):
        """Test a specific barcode with the API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{BACKEND_URL}/barcode/{barcode}", headers=headers)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 404:
                return False, "Product not found"
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"Request error: {str(e)}"
    
    async def run_comprehensive_check(self):
        """Run comprehensive barcode database check"""
        print("=" * 80)
        print("🏪 GEANT HYPERMARKET - BARCODE DATABASE CHECK")
        print("=" * 80)
        print(f"📅 Check performed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Connect to database
        if not await self.connect_database():
            return
        
        # Step 2: Authenticate with API
        if not self.authenticate_api():
            print("⚠️  API authentication failed, but continuing with database check...")
        
        # Step 3: Get products with barcodes from database
        products = await self.get_products_with_barcodes_db()
        
        if not products:
            print("❌ No products with barcodes found in database!")
            return
        
        # Step 4: Display results
        print("\n" + "=" * 80)
        print("📋 BARCODE INVENTORY SUMMARY")
        print("=" * 80)
        print(f"Total products with barcodes: {len(products)}")
        
        # Group by department
        dept_counts = {}
        for product in products:
            dept = product['department']
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        print("\nProducts by Department:")
        for dept, count in dept_counts.items():
            print(f"  • {dept}: {count} products")
        
        # Step 5: Display sample barcodes for testing
        print("\n" + "=" * 80)
        print("🔍 SAMPLE BARCODES FOR TESTING (First 20)")
        print("=" * 80)
        
        sample_products = products[:20]  # Get first 20 for testing
        
        for i, product in enumerate(sample_products, 1):
            print(f"\n{i:2d}. BARCODE: {product['barcode']}")
            print(f"    Product: {product['product_name']}")
            print(f"    Department: {product['department']}")
            print(f"    Section: {product['section']}")
            print(f"    Supplier: {product['supplier']}")
            print(f"    Price: {product['purchase_price']} {product['purchase_currency']}")
            print(f"    Stock: {product['quantity']} units")
            
            # Test with API if authenticated
            if self.auth_token:
                success, result = self.test_barcode_api(product['barcode'])
                if success:
                    print(f"    ✅ API Test: WORKING")
                else:
                    print(f"    ❌ API Test: {result}")
        
        # Step 6: Additional recommendations
        print("\n" + "=" * 80)
        print("💡 TESTING RECOMMENDATIONS")
        print("=" * 80)
        
        # Find products with different characteristics for comprehensive testing
        eur_products = [p for p in products if p['purchase_currency'] == 'EUR'][:3]
        sar_products = [p for p in products if p['purchase_currency'] == 'SAR'][:3]
        yer_products = [p for p in products if p['purchase_currency'] == 'YER'][:3]
        
        print("\n🔸 RECOMMENDED TEST BARCODES BY CURRENCY:")
        
        if eur_products:
            print("\n  EUR Products:")
            for product in eur_products:
                print(f"    • {product['barcode']} - {product['product_name']}")
        
        if sar_products:
            print("\n  SAR Products:")
            for product in sar_products:
                print(f"    • {product['barcode']} - {product['product_name']}")
        
        if yer_products:
            print("\n  YER Products:")
            for product in yer_products:
                print(f"    • {product['barcode']} - {product['product_name']}")
        
        # Find products by department
        print("\n🔸 RECOMMENDED TEST BARCODES BY DEPARTMENT:")
        
        for dept in ['01-FMG', '01-CGD', '01-OPSS']:
            dept_products = [p for p in products if p['department'] == dept][:2]
            if dept_products:
                print(f"\n  {dept}:")
                for product in dept_products:
                    print(f"    • {product['barcode']} - {product['product_name']}")
        
        # Step 7: Export full list
        print("\n" + "=" * 80)
        print("📄 COMPLETE BARCODE LIST")
        print("=" * 80)
        
        print(f"\nAll {len(products)} barcodes found in database:")
        print("\nBARCODE | PRODUCT NAME | DEPARTMENT | CURRENCY")
        print("-" * 80)
        
        for product in products:
            barcode = product['barcode']
            name = product['product_name'][:30] + "..." if len(product['product_name']) > 30 else product['product_name']
            dept = product['department']
            currency = product['purchase_currency']
            print(f"{barcode:<15} | {name:<32} | {dept:<10} | {currency}")
        
        print("\n" + "=" * 80)
        print("✅ BARCODE DATABASE CHECK COMPLETED")
        print("=" * 80)
        print("📱 You can now test your barcode scanner with any of the above barcodes!")
        print("🎯 All listed barcodes exist in the database and should return product details.")
        print("=" * 80)
        
        # Close database connection
        if self.client:
            self.client.close()

async def main():
    """Main function to run the barcode check"""
    checker = BarcodeChecker()
    await checker.run_comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main())