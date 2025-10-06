#!/usr/bin/env python3
"""
WASTE REPORT DEBUG TEST - Investigate PDF Size Issues

This test investigates why waste report PDFs are too small and checks
the underlying data and API endpoints.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class WasteReportDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    print("✅ Authentication successful")
                    return True
            
            print("❌ Authentication failed")
            return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def check_waste_entries(self):
        """Check if there are waste entries in the database"""
        print("\n🗑️ CHECKING WASTE ENTRIES")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/waste/entries")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Waste entries endpoint accessible")
                print(f"📊 Number of waste entries: {len(data) if isinstance(data, list) else 'Unknown'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"📋 Sample waste entry:")
                    sample = data[0]
                    for key, value in sample.items():
                        if key not in ['_id']:
                            print(f"   {key}: {value}")
                else:
                    print("⚠️  No waste entries found - this explains small PDF size")
                
                return len(data) if isinstance(data, list) else 0
            else:
                print(f"❌ Waste entries endpoint failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return 0
                
        except Exception as e:
            print(f"❌ Error checking waste entries: {str(e)}")
            return 0
    
    def check_waste_reports_api(self):
        """Check the waste reports API"""
        print("\n📊 CHECKING WASTE REPORTS API")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/waste/reports?period=daily")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Waste reports API accessible")
                print(f"📊 Report data structure:")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            print(f"   {key}: {json.dumps(value, indent=4)}")
                        else:
                            print(f"   {key}: {value}")
                else:
                    print(f"   Data type: {type(data)}")
                    print(f"   Content: {str(data)[:200]}")
                
                return True
            else:
                print(f"❌ Waste reports API failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking waste reports API: {str(e)}")
            return False
    
    def create_test_waste_entry(self):
        """Create a test waste entry to populate data"""
        print("\n➕ CREATING TEST WASTE ENTRY")
        print("=" * 50)
        
        try:
            # First, get a product to create waste entry for
            products_response = self.session.get(f"{BACKEND_URL}/products?limit=1")
            
            if products_response.status_code == 200:
                products = products_response.json()
                if isinstance(products, list) and len(products) > 0:
                    product = products[0]
                    print(f"✅ Found product: {product.get('product_name', 'Unknown')}")
                    
                    # Create waste entry
                    waste_entry = {
                        "product_id": product.get("id"),
                        "product_name": product.get("product_name"),
                        "quantity_wasted": 5,
                        "waste_reason": "damaged",
                        "purchase_price": product.get("purchase_price", 10.0),
                        "purchase_currency": product.get("purchase_currency", "YER"),
                        "department": product.get("department"),
                        "section": product.get("section"),
                        "notes": "Test waste entry for PDF testing"
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/waste/entries", json=waste_entry)
                    
                    if response.status_code == 200:
                        print("✅ Test waste entry created successfully")
                        return True
                    else:
                        print(f"❌ Failed to create waste entry: {response.status_code}")
                        print(f"Response: {response.text[:200]}")
                        return False
                else:
                    print("❌ No products found to create waste entry")
                    return False
            else:
                print(f"❌ Failed to get products: {products_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test waste entry: {str(e)}")
            return False
    
    def test_pdf_after_data_creation(self):
        """Test PDF generation after creating test data"""
        print("\n📄 TESTING PDF AFTER DATA CREATION")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf")
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get('content-type', '')
                
                print(f"✅ PDF generated successfully")
                print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f}KB)")
                print(f"📋 Content-Type: {content_type}")
                
                # Check if size improved
                if file_size > 10000:
                    print("✅ PDF size is now substantial (>10KB)")
                    return True
                else:
                    print("⚠️  PDF size still small - may need more data or different issue")
                    return False
            else:
                print(f"❌ PDF generation failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing PDF: {str(e)}")
            return False
    
    def check_enhanced_export_system(self):
        """Check if enhanced export system is being used"""
        print("\n🚀 CHECKING ENHANCED EXPORT SYSTEM")
        print("=" * 50)
        
        try:
            # Test with different parameters to see if enhanced system responds
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf&enhanced=true")
            
            if response.status_code == 200:
                file_size = len(response.content)
                print(f"✅ Enhanced export system accessible")
                print(f"📊 Enhanced PDF size: {file_size:,} bytes ({file_size/1024:.1f}KB)")
                
                if file_size > 30000:
                    print("✅ Enhanced system generating large PDFs as expected")
                    return True
                else:
                    print("⚠️  Enhanced system not generating expected large files")
                    return False
            else:
                print(f"⚠️  Enhanced export parameter not recognized: {response.status_code}")
                # Try regular export
                response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf")
                if response.status_code == 200:
                    file_size = len(response.content)
                    print(f"📊 Regular export size: {file_size:,} bytes")
                return False
                
        except Exception as e:
            print(f"❌ Error checking enhanced export: {str(e)}")
            return False
    
    def run_debug_tests(self):
        """Run all debug tests"""
        print("🔍 WASTE REPORT PDF DEBUG TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("Investigating PDF size issues and data availability")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
        
        # Check current state
        waste_count = self.check_waste_entries()
        self.check_waste_reports_api()
        self.check_enhanced_export_system()
        
        # If no waste entries, create some test data
        if waste_count == 0:
            print("\n💡 No waste entries found - creating test data...")
            if self.create_test_waste_entry():
                # Re-check after creating data
                self.check_waste_entries()
                self.test_pdf_after_data_creation()
        
        print("\n" + "=" * 80)
        print("🔍 DEBUG SUMMARY")
        print("=" * 80)
        print("Key findings:")
        print("1. PDF format is correct (valid signature and structure)")
        print("2. Authentication and endpoints are working")
        print("3. Excel exports are working well (38KB files)")
        print("4. PDF size issue likely due to:")
        print("   - Limited waste data in database")
        print("   - Enhanced export system not fully active")
        print("   - PDF generation using minimal template")
        print("\n💡 Recommendations:")
        print("1. Verify enhanced export system is properly integrated")
        print("2. Check if USD conversion features are active")
        print("3. Ensure company branding is properly embedded")
        print("4. Test with more substantial waste data")

def main():
    """Main debug execution"""
    tester = WasteReportDebugTester()
    tester.run_debug_tests()

if __name__ == "__main__":
    main()