#!/usr/bin/env python3
"""
Multi-Item Investigation Test
Investigating how the backend handles multi-item vs single-item return forms
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class MultiItemInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def create_single_item_form(self):
        """Create traditional single-item return form"""
        single_item_data = {
            "reference_number": f"RTN-SINGLE-{int(time.time())}",
            "product_code": "TEST-001",
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 50,
            "purchase_price": 3.75,
            "purchase_currency": "SAR",
            "supplier": "ExtenC",
            "reason_for_return": "Quality issue",
            "selected_supervisor": "Mahmoud Badr",
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            "supervisor_approved": True,
            "supervisor_signature": "Mahmoud_Badr_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "Imad_Qejji_signature",
            "section_manager_timestamp": datetime.now().isoformat()
        }
        
        response = self.session.post(f"{BACKEND_URL}/return-forms", json=single_item_data)
        
        if response.status_code == 200:
            data = response.json()
            form_id = data.get("id")
            print(f"✅ Single-item form created: {form_id}")
            return form_id
        else:
            print(f"❌ Single-item form creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def create_multi_item_form(self):
        """Create new multi-item return form"""
        multi_item_data = {
            "reference_number": f"RTN-MULTI-{int(time.time())}",
            "supplier": "ExtenC",
            "selected_supervisor": "Mahmoud Badr",
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            "reason_for_return": "Mixed FOC and normal items return",
            "supervisor_approved": True,
            "supervisor_signature": "Mahmoud_Badr_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "Imad_Qejji_signature",
            "section_manager_timestamp": datetime.now().isoformat(),
            
            # Multi-item structure
            "items": [
                {
                    "product_name": "Apple Juice Box 1L",
                    "barcode": "3222471081716",
                    "quantity": 50,
                    "price": 3.75,
                    "currency": "SAR",
                    "is_foc": False,
                    "foc_reason": "",
                    "total_value": 187.50
                },
                {
                    "product_name": "Orange Juice Box 1L",
                    "barcode": "3222471081717", 
                    "quantity": 25,
                    "price": 0,
                    "currency": "SAR",
                    "is_foc": True,
                    "foc_reason": "Promotional sample",
                    "total_value": 0
                }
            ],
            
            # Item summary
            "item_summary": {
                "total_items": 2,
                "total_quantity": 75,
                "normal_quantity": 50,
                "foc_quantity": 25,
                "total_value": 187.50,
                "currency": "SAR"
            }
        }
        
        response = self.session.post(f"{BACKEND_URL}/return-forms", json=multi_item_data)
        
        if response.status_code == 200:
            data = response.json()
            form_id = data.get("id")
            print(f"✅ Multi-item form created: {form_id}")
            return form_id
        else:
            print(f"❌ Multi-item form creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_pdf_generation(self, form_id, form_type):
        """Test PDF generation for a form"""
        print(f"\n🔍 Testing PDF generation for {form_type} form: {form_id}")
        
        response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
        
        if response.status_code == 200:
            pdf_content = response.content
            pdf_size = len(pdf_content)
            
            # Check for content indicators
            has_apple_juice = b'Apple Juice' in pdf_content
            has_orange_juice = b'Orange Juice' in pdf_content
            has_foc_indicator = b'FOC' in pdf_content or b'Promotional' in pdf_content
            has_quantity_50 = b'50' in pdf_content
            has_quantity_25 = b'25' in pdf_content
            has_total_75 = b'75' in pdf_content
            has_value_187 = b'187.5' in pdf_content or b'187.50' in pdf_content
            
            print(f"  📄 PDF Size: {pdf_size} bytes")
            print(f"  🍎 Apple Juice: {has_apple_juice}")
            print(f"  🍊 Orange Juice: {has_orange_juice}")
            print(f"  🆓 FOC Indicator: {has_foc_indicator}")
            print(f"  📊 Quantity 50: {has_quantity_50}")
            print(f"  📊 Quantity 25: {has_quantity_25}")
            print(f"  📊 Total 75: {has_total_75}")
            print(f"  💰 Value 187.5: {has_value_187}")
            
            return {
                "success": True,
                "size": pdf_size,
                "has_apple_juice": has_apple_juice,
                "has_orange_juice": has_orange_juice,
                "has_foc_indicator": has_foc_indicator,
                "has_quantity_50": has_quantity_50,
                "has_quantity_25": has_quantity_25,
                "has_total_75": has_total_75,
                "has_value_187": has_value_187
            }
        else:
            print(f"  ❌ PDF generation failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return {"success": False, "error": response.text}
    
    def compare_stored_data(self, single_id, multi_id):
        """Compare how single vs multi-item data is stored"""
        print(f"\n🔍 Comparing stored data structures")
        
        response = self.session.get(f"{BACKEND_URL}/returns")
        
        if response.status_code == 200:
            forms = response.json()
            
            single_form = None
            multi_form = None
            
            for form in forms:
                if form.get("id") == single_id:
                    single_form = form
                elif form.get("id") == multi_id:
                    multi_form = form
            
            print(f"\n📋 Single-item form structure:")
            if single_form:
                print(f"  - Has product_name: {'product_name' in single_form}")
                print(f"  - Has quantity: {'quantity' in single_form}")
                print(f"  - Has purchase_price: {'purchase_price' in single_form}")
                print(f"  - Has items array: {'items' in single_form}")
                if 'items' in single_form:
                    print(f"  - Items count: {len(single_form['items'])}")
            
            print(f"\n📋 Multi-item form structure:")
            if multi_form:
                print(f"  - Has product_name: {'product_name' in multi_form}")
                print(f"  - Has quantity: {'quantity' in multi_form}")
                print(f"  - Has purchase_price: {'purchase_price' in multi_form}")
                print(f"  - Has items array: {'items' in multi_form}")
                if 'items' in multi_form:
                    print(f"  - Items count: {len(multi_form['items'])}")
                    for i, item in enumerate(multi_form['items']):
                        print(f"    Item {i+1}: {item.get('product_name', 'N/A')} - Qty: {item.get('quantity', 0)} - FOC: {item.get('is_foc', False)}")
                print(f"  - Has item_summary: {'item_summary' in multi_form}")
                if 'item_summary' in multi_form:
                    summary = multi_form['item_summary']
                    print(f"    Total items: {summary.get('total_items', 0)}")
                    print(f"    Total quantity: {summary.get('total_quantity', 0)}")
                    print(f"    Total value: {summary.get('total_value', 0)}")
        else:
            print(f"❌ Failed to retrieve forms: {response.status_code}")
    
    def run_investigation(self):
        """Run comprehensive investigation"""
        print("🔍 MULTI-ITEM RETURN FORM INVESTIGATION")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        # Create both types of forms
        single_id = self.create_single_item_form()
        multi_id = self.create_multi_item_form()
        
        if not single_id or not multi_id:
            print("❌ Failed to create test forms")
            return
        
        # Test PDF generation for both
        single_pdf_result = self.test_pdf_generation(single_id, "single-item")
        multi_pdf_result = self.test_pdf_generation(multi_id, "multi-item")
        
        # Compare stored data structures
        self.compare_stored_data(single_id, multi_id)
        
        # Analysis
        print(f"\n📊 ANALYSIS:")
        print(f"=" * 50)
        
        if single_pdf_result.get("success") and multi_pdf_result.get("success"):
            print("✅ Both PDF generations successful")
            
            # Check if multi-item PDF shows multiple products
            if multi_pdf_result.get("has_orange_juice"):
                print("✅ Multi-item PDF correctly shows multiple products")
            else:
                print("❌ Multi-item PDF does NOT show multiple products")
                print("   This indicates the PDF generation is using single-item logic")
            
            # Check FOC handling
            if multi_pdf_result.get("has_foc_indicator"):
                print("✅ Multi-item PDF shows FOC indicators")
            else:
                print("❌ Multi-item PDF does NOT show FOC indicators")
            
            # Check quantity totals
            if multi_pdf_result.get("has_total_75"):
                print("✅ Multi-item PDF shows correct total quantities")
            else:
                print("❌ Multi-item PDF does NOT show correct total quantities")
        
        print(f"\n🎯 CONCLUSION:")
        print(f"=" * 50)
        if not multi_pdf_result.get("has_orange_juice"):
            print("❌ CRITICAL ISSUE: Backend PDF generation does NOT support multi-item structure")
            print("   The PDF generation function needs to be updated to handle 'items' array")
            print("   Currently it only processes single-item fields like 'product_name', 'quantity'")
        else:
            print("✅ Multi-item PDF generation is working correctly")

if __name__ == "__main__":
    investigator = MultiItemInvestigator()
    investigator.run_investigation()