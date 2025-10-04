#!/usr/bin/env python3
"""
Multi-Item Return Form with FOC Support - Backend Testing
Testing comprehensive multi-item FOC functionality for Return Form backend implementation
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_ITEMS = [
    {
        "product_name": "Apple Juice Box 1L",
        "barcode": "3222471081716",
        "quantity": 50,
        "price": 3.75,
        "currency": "SAR",
        "is_foc": False,
        "foc_reason": ""
    },
    {
        "product_name": "Orange Juice Box 1L", 
        "barcode": "3222471081717",
        "quantity": 25,
        "price": 0,
        "currency": "SAR",
        "is_foc": True,
        "foc_reason": "Promotional sample"
    }
]

class MultiItemFOCTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_forms = []
        
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
    
    def authenticate(self):
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
                    f"Token received for user: {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_item_data_structure(self):
        """Test backend accepts new multi-item data structure"""
        try:
            start_time = time.time()
            
            # Create multi-item return form data structure
            multi_item_form_data = {
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
                },
                
                # Totals
                "totals": {
                    "normal_items_value": 187.50,
                    "foc_items_value": 0,
                    "total_value": 187.50,
                    "currency": "SAR"
                }
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=multi_item_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                self.log_result("Multi-Item Data Structure", True,
                    f"Form ID: {form_id}, Items: {len(multi_item_form_data['items'])}, "
                    f"Total Value: {multi_item_form_data['totals']['total_value']} SAR", response_time)
                return True
            else:
                self.log_result("Multi-Item Data Structure", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Multi-Item Data Structure", False, f"Exception: {str(e)}")
            return False
    
    def test_foc_normal_item_separation(self):
        """Test FOC/normal item separation works"""
        if not self.created_return_forms:
            self.log_result("FOC/Normal Item Separation", False, "No return forms created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                if not forms:
                    self.log_result("FOC/Normal Item Separation", False, "No return forms found", response_time)
                    return
                
                # Find our multi-item form
                multi_item_form = None
                for form in forms:
                    if "items" in form and len(form.get("items", [])) > 1:
                        multi_item_form = form
                        break
                
                if not multi_item_form:
                    self.log_result("FOC/Normal Item Separation", False, "Multi-item form not found", response_time)
                    return
                
                # Check FOC/normal separation
                items = multi_item_form.get("items", [])
                foc_items = [item for item in items if item.get("is_foc", False)]
                normal_items = [item for item in items if not item.get("is_foc", False)]
                
                has_foc_separation = len(foc_items) > 0 and len(normal_items) > 0
                foc_has_reason = all(item.get("foc_reason") for item in foc_items)
                
                self.log_result("FOC/Normal Item Separation", has_foc_separation and foc_has_reason,
                    f"FOC items: {len(foc_items)}, Normal items: {len(normal_items)}, "
                    f"FOC reasons present: {foc_has_reason}", response_time)
                return True
            else:
                self.log_result("FOC/Normal Item Separation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("FOC/Normal Item Separation", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_item_pdf_generation(self):
        """Test PDF generation handles multiple items"""
        if not self.created_return_forms:
            self.log_result("Multi-Item PDF Generation", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                # Check for multi-item indicators in PDF content
                pdf_content = response.content
                has_apple_juice = b'Apple Juice' in pdf_content
                has_orange_juice = b'Orange Juice' in pdf_content
                has_foc_indicator = b'FOC' in pdf_content or b'Promotional' in pdf_content
                
                multi_item_success = is_pdf and has_apple_juice and has_orange_juice
                
                self.log_result("Multi-Item PDF Generation", multi_item_success,
                    f"PDF: {is_pdf}, Size: {pdf_size} bytes, Apple Juice: {has_apple_juice}, "
                    f"Orange Juice: {has_orange_juice}, FOC indicator: {has_foc_indicator}", response_time)
                return multi_item_success
            else:
                self.log_result("Multi-Item PDF Generation", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Multi-Item PDF Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_foc_items_in_pdf(self):
        """Test FOC items show properly in PDF"""
        if not self.created_return_forms:
            self.log_result("FOC Items in PDF", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                
                # Check for FOC-specific content
                has_foc_reason = b'Promotional sample' in pdf_content
                has_zero_price = b'0.00' in pdf_content or b'0 SAR' in pdf_content
                has_foc_label = b'FOC' in pdf_content
                has_quantity_25 = b'25' in pdf_content
                
                foc_display_success = has_foc_reason or has_zero_price or has_foc_label
                
                self.log_result("FOC Items in PDF", foc_display_success,
                    f"FOC reason: {has_foc_reason}, Zero price: {has_zero_price}, "
                    f"FOC label: {has_foc_label}, Quantity 25: {has_quantity_25}", response_time)
                return foc_display_success
            else:
                self.log_result("FOC Items in PDF", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("FOC Items in PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_total_quantities_in_pdf(self):
        """Test total quantities (75 total, 50 normal, 25 FOC) in PDF"""
        if not self.created_return_forms:
            self.log_result("Total Quantities in PDF", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                
                # Check for quantity totals
                has_total_75 = b'75' in pdf_content
                has_quantity_50 = b'50' in pdf_content
                has_quantity_25 = b'25' in pdf_content
                has_total_value = b'187.50' in pdf_content or b'187.5' in pdf_content
                
                quantities_success = has_total_75 and has_quantity_50 and has_quantity_25
                
                self.log_result("Total Quantities in PDF", quantities_success,
                    f"Total 75: {has_total_75}, Qty 50: {has_quantity_50}, "
                    f"Qty 25: {has_quantity_25}, Value 187.50: {has_total_value}", response_time)
                return quantities_success
            else:
                self.log_result("Total Quantities in PDF", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Total Quantities in PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_total_value_calculation(self):
        """Test total value (187.50 SAR from normal items only)"""
        if not self.created_return_forms:
            self.log_result("Total Value Calculation", False, "No return forms created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                # Find our multi-item form
                multi_item_form = None
                for form in forms:
                    if "items" in form and len(form.get("items", [])) > 1:
                        multi_item_form = form
                        break
                
                if not multi_item_form:
                    self.log_result("Total Value Calculation", False, "Multi-item form not found", response_time)
                    return
                
                # Check value calculations
                totals = multi_item_form.get("totals", {})
                item_summary = multi_item_form.get("item_summary", {})
                
                expected_total_value = 187.50
                actual_total_value = totals.get("total_value", 0)
                normal_items_value = totals.get("normal_items_value", 0)
                foc_items_value = totals.get("foc_items_value", 0)
                
                value_calculation_correct = (
                    abs(actual_total_value - expected_total_value) < 0.01 and
                    foc_items_value == 0 and
                    normal_items_value == expected_total_value
                )
                
                self.log_result("Total Value Calculation", value_calculation_correct,
                    f"Expected: {expected_total_value}, Actual: {actual_total_value}, "
                    f"Normal: {normal_items_value}, FOC: {foc_items_value}", response_time)
                return value_calculation_correct
            else:
                self.log_result("Total Value Calculation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Total Value Calculation", False, f"Exception: {str(e)}")
            return False
    
    def test_excel_export_multi_item(self):
        """Test Excel export with multi-item data structure"""
        if not self.created_return_forms:
            self.log_result("Excel Export Multi-Item", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=excel")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's an Excel file
                content_type = response.headers.get('content-type', '')
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                excel_size = len(response.content)
                
                # Excel files should be reasonably sized for multi-item data
                size_appropriate = excel_size > 5000  # Multi-item should be larger
                
                self.log_result("Excel Export Multi-Item", is_excel and size_appropriate,
                    f"Content-Type: {content_type}, Size: {excel_size} bytes, "
                    f"Size appropriate: {size_appropriate}", response_time)
                return is_excel and size_appropriate
            else:
                self.log_result("Excel Export Multi-Item", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Excel Export Multi-Item", False, f"Exception: {str(e)}")
            return False
    
    def test_single_page_pdf_format(self):
        """Test single-page PDF format maintained even with multiple items"""
        if not self.created_return_forms:
            self.log_result("Single-Page PDF Format", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check for single page indicators
                # Multiple pages would typically have page break indicators
                page_break_count = pdf_content.count(b'/Page')
                single_page_likely = page_break_count <= 2  # Usually 1-2 for single page
                
                # Size check - single page PDFs are typically under 100KB
                size_reasonable = pdf_size < 100000
                
                single_page_success = single_page_likely and size_reasonable
                
                self.log_result("Single-Page PDF Format", single_page_success,
                    f"PDF size: {pdf_size} bytes, Page breaks: {page_break_count}, "
                    f"Single page likely: {single_page_likely}", response_time)
                return single_page_success
            else:
                self.log_result("Single-Page PDF Format", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                    
        except Exception as e:
            self.log_result("Single-Page PDF Format", False, f"Exception: {str(e)}")
            return False
    
    def test_supplier_validation(self):
        """Test supplier validation in multi-item forms"""
        try:
            start_time = time.time()
            
            # Test with invalid supplier
            invalid_supplier_form = {
                "reference_number": f"RTN-INVALID-{int(time.time())}",
                "supplier": "",  # Empty supplier
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "reason_for_return": "Test invalid supplier",
                "items": [
                    {
                        "product_name": "Test Product",
                        "quantity": 1,
                        "price": 10.0,
                        "currency": "SAR",
                        "is_foc": False
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=invalid_supplier_form)
            response_time = (time.time() - start_time) * 1000
            
            # Should either reject (400/422) or accept with validation
            validation_working = response.status_code in [400, 422] or (
                response.status_code == 200 and 
                response.json().get("message", "").lower().find("validation") != -1
            )
            
            self.log_result("Supplier Validation", validation_working,
                f"Status: {response.status_code}, Validation response appropriate", response_time)
            return validation_working
                
        except Exception as e:
            self.log_result("Supplier Validation", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all multi-item FOC tests"""
        print("🚀 MULTI-ITEM RETURN FORM WITH FOC SUPPORT - BACKEND TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Items: {len(TEST_ITEMS)} items (1 normal, 1 FOC)")
        print(f"Expected Total: 75 items (50 normal + 25 FOC)")
        print(f"Expected Value: 187.50 SAR (FOC excluded)")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Multi-Item Data Handling
        self.test_multi_item_data_structure()
        
        # 3. FOC/Normal Item Separation
        self.test_foc_normal_item_separation()
        
        # 4. PDF Generation Test
        self.test_multi_item_pdf_generation()
        
        # 5. FOC Items in PDF
        self.test_foc_items_in_pdf()
        
        # 6. Total Quantities in PDF
        self.test_total_quantities_in_pdf()
        
        # 7. Total Value Calculation
        self.test_total_value_calculation()
        
        # 8. Excel Export Multi-Item
        self.test_excel_export_multi_item()
        
        # 9. Single-Page PDF Format
        self.test_single_page_pdf_format()
        
        # 10. Supplier Validation
        self.test_supplier_validation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 MULTI-ITEM FOC RETURN FORM TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Multi-Item Data Handling": any("Multi-Item Data Structure" in r["test"] and r["success"] for r in self.test_results),
            "FOC/Normal Separation": any("FOC/Normal Item Separation" in r["test"] and r["success"] for r in self.test_results),
            "PDF Generation": any("Multi-Item PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "FOC Items in PDF": any("FOC Items in PDF" in r["test"] and r["success"] for r in self.test_results),
            "Total Quantities": any("Total Quantities in PDF" in r["test"] and r["success"] for r in self.test_results),
            "Value Calculation": any("Total Value Calculation" in r["test"] and r["success"] for r in self.test_results),
            "Excel Export": any("Excel Export Multi-Item" in r["test"] and r["success"] for r in self.test_results),
            "Single-Page Format": any("Single-Page PDF Format" in r["test"] and r["success"] for r in self.test_results)
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
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 70)
        print("🏁 MULTI-ITEM FOC RETURN FORM TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = MultiItemFOCTester()
    tester.run_comprehensive_tests()