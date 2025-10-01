#!/usr/bin/env python3
"""
FOC (Free of Cost) Return Form System Testing
Testing comprehensive FOC functionality with PDF/Excel exports and visual indicators
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_SUPERVISOR = "Mahmoud Badr"
TEST_PRODUCT_BARCODE = "3222471081716"  # Apple Juice Box 1L
TEST_QUANTITY = 50
FOC_REASON = "Promotional sample items"

class FOCReturnFormTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.foc_return_form_id = None
        self.regular_return_form_id = None
        
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
    
    def test_product_lookup(self):
        """Test product lookup for Apple Juice Box 1L"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/barcode/{TEST_PRODUCT_BARCODE}")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                product = response.json()
                
                # Verify required fields for return form
                required_fields = ["product_name", "purchase_price", "purchase_currency", "supplier"]
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    self.log_result("Product Lookup", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return None
                
                self.log_result("Product Lookup", True,
                    f"Product: {product.get('product_name')}, "
                    f"Price: {product.get('purchase_price')} {product.get('purchase_currency')}, "
                    f"Supplier: {product.get('supplier')}", response_time)
                return product
            else:
                self.log_result("Product Lookup", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Product Lookup", False, f"Exception: {str(e)}")
            return None
    
    def create_foc_return_form(self, product_data):
        """Create FOC return form with all required FOC fields"""
        try:
            start_time = time.time()
            
            foc_form_data = {
                "reference_number": f"RTN-FOC-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": TEST_PRODUCT_BARCODE,
                "quantity": TEST_QUANTITY,
                "purchase_price": 0,  # FOC price should be 0
                "original_purchase_price": product_data.get("purchase_price", 0.754),  # Store original price
                "purchase_currency": product_data.get("purchase_currency", "EUR"),
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality issue - damaged packaging",
                "selected_supervisor": TEST_SUPERVISOR,
                "prepared_by_supervisor": TEST_SUPERVISOR,
                "section_manager_name": "Imad Qejji",
                "notes": f"FOC return form - {FOC_REASON}",
                "supervisor_approved": True,
                "supervisor_signature": f"{TEST_SUPERVISOR}_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat(),
                # FOC specific fields
                "is_foc": True,
                "foc_enabled": True,
                "foc_reason": FOC_REASON,
                "total_value": 0,  # FOC total should be 0
                "unit_price": 0    # FOC unit price should be 0
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=foc_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.foc_return_form_id = data.get("id")
                
                self.log_result("FOC Return Form Creation", True,
                    f"Form ID: {self.foc_return_form_id}, FOC enabled: True, "
                    f"Price: 0 (FOC), Quantity: {TEST_QUANTITY}, Reason: {FOC_REASON}", response_time)
                return True
            else:
                self.log_result("FOC Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("FOC Return Form Creation", False, f"Exception: {str(e)}")
            return False
    
    def create_regular_return_form(self, product_data):
        """Create regular (non-FOC) return form for comparison"""
        try:
            start_time = time.time()
            
            regular_form_data = {
                "reference_number": f"RTN-REG-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": TEST_PRODUCT_BARCODE,
                "quantity": TEST_QUANTITY,
                "purchase_price": product_data.get("purchase_price", 0.754),  # Regular price
                "purchase_currency": product_data.get("purchase_currency", "EUR"),
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality issue - damaged packaging",
                "selected_supervisor": TEST_SUPERVISOR,
                "prepared_by_supervisor": TEST_SUPERVISOR,
                "section_manager_name": "Imad Qejji",
                "notes": "Regular return form for comparison",
                "supervisor_approved": True,
                "supervisor_signature": f"{TEST_SUPERVISOR}_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat(),
                # Regular form fields
                "is_foc": False,
                "foc_enabled": False,
                "total_value": TEST_QUANTITY * product_data.get("purchase_price", 0.754),
                "unit_price": product_data.get("purchase_price", 0.754)
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=regular_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.regular_return_form_id = data.get("id")
                
                self.log_result("Regular Return Form Creation", True,
                    f"Form ID: {self.regular_return_form_id}, FOC enabled: False, "
                    f"Price: {product_data.get('purchase_price', 0.754)}, Quantity: {TEST_QUANTITY}", response_time)
                return True
            else:
                self.log_result("Regular Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Regular Return Form Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_foc_pdf_export(self):
        """Test FOC PDF export with all FOC indicators"""
        if not self.foc_return_form_id:
            self.log_result("FOC PDF Export", False, "No FOC return form created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.foc_return_form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or pdf_content.startswith(b'%PDF')
                pdf_size = len(pdf_content)
                
                # Check for FOC indicators in PDF content
                foc_indicators = {
                    "FOC_FREE": b'FOC - FREE' in pdf_content,
                    "FREE_OF_COST": b'Free of Cost' in pdf_content,
                    "FOC_STATUS": b'FOC Status' in pdf_content,
                    "FOC_REASON": FOC_REASON.encode() in pdf_content,
                    "ZERO_SAR": b'0 SAR' in pdf_content or b'0.00 SAR' in pdf_content,
                    "FREE_ITEM": b'FREE ITEM' in pdf_content,
                    "NO_COST": b'No Cost' in pdf_content
                }
                
                found_indicators = [key for key, found in foc_indicators.items() if found]
                
                self.log_result("FOC PDF Export", is_pdf and len(found_indicators) >= 2,
                    f"PDF: {is_pdf}, Size: {pdf_size} bytes, "
                    f"FOC indicators found: {found_indicators}", response_time)
            else:
                self.log_result("FOC PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("FOC PDF Export", False, f"Exception: {str(e)}")
    
    def test_foc_excel_export(self):
        """Test FOC Excel export with FOC information"""
        if not self.foc_return_form_id:
            self.log_result("FOC Excel Export", False, "No FOC return form created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.foc_return_form_id}?format=excel")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                excel_size = len(response.content)
                
                self.log_result("FOC Excel Export", is_excel or excel_size > 1000,
                    f"Content-Type: {content_type}, Size: {excel_size} bytes", response_time)
            else:
                self.log_result("FOC Excel Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("FOC Excel Export", False, f"Exception: {str(e)}")
    
    def test_regular_pdf_export(self):
        """Test regular PDF export for comparison"""
        if not self.regular_return_form_id:
            self.log_result("Regular PDF Export", False, "No regular return form created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.regular_return_form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or pdf_content.startswith(b'%PDF')
                pdf_size = len(pdf_content)
                
                # Check that regular form does NOT have FOC indicators
                no_foc_indicators = {
                    "NO_FOC_FREE": b'FOC - FREE' not in pdf_content,
                    "NO_FREE_OF_COST": b'Free of Cost' not in pdf_content,
                    "NO_FREE_ITEM": b'FREE ITEM' not in pdf_content
                }
                
                regular_indicators = sum(no_foc_indicators.values())
                
                self.log_result("Regular PDF Export", is_pdf and regular_indicators >= 2,
                    f"PDF: {is_pdf}, Size: {pdf_size} bytes, "
                    f"No FOC indicators (correct): {regular_indicators}/3", response_time)
            else:
                self.log_result("Regular PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("Regular PDF Export", False, f"Exception: {str(e)}")
    
    def test_foc_vs_regular_comparison(self):
        """Compare FOC vs Regular return forms"""
        if not self.foc_return_form_id or not self.regular_return_form_id:
            self.log_result("FOC vs Regular Comparison", False, "Missing return forms for comparison")
            return
        
        try:
            start_time = time.time()
            
            # Get both forms
            foc_response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if foc_response.status_code == 200:
                forms = foc_response.json()
                
                foc_form = None
                regular_form = None
                
                for form in forms:
                    if form.get("id") == self.foc_return_form_id:
                        foc_form = form
                    elif form.get("id") == self.regular_return_form_id:
                        regular_form = form
                
                if foc_form and regular_form:
                    # Compare key differences
                    foc_price = foc_form.get("purchase_price", 0)
                    regular_price = regular_form.get("purchase_price", 0)
                    
                    foc_total = foc_form.get("total_value", 0)
                    regular_total = regular_form.get("total_value", 0)
                    
                    foc_enabled = foc_form.get("is_foc", False) or foc_form.get("foc_enabled", False)
                    regular_enabled = regular_form.get("is_foc", False) or regular_form.get("foc_enabled", False)
                    
                    comparison_valid = (
                        foc_price == 0 and regular_price > 0 and
                        foc_total == 0 and regular_total > 0 and
                        foc_enabled and not regular_enabled
                    )
                    
                    self.log_result("FOC vs Regular Comparison", comparison_valid,
                        f"FOC price: {foc_price}, Regular price: {regular_price}, "
                        f"FOC total: {foc_total}, Regular total: {regular_total}, "
                        f"FOC enabled: {foc_enabled}, Regular enabled: {regular_enabled}", response_time)
                else:
                    self.log_result("FOC vs Regular Comparison", False,
                        f"Forms not found - FOC: {foc_form is not None}, Regular: {regular_form is not None}", response_time)
            else:
                self.log_result("FOC vs Regular Comparison", False,
                    f"Status: {foc_response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("FOC vs Regular Comparison", False, f"Exception: {str(e)}")
    
    def test_foc_calculation_logic(self):
        """Test FOC calculation logic (quantity × 0 = 0)"""
        if not self.foc_return_form_id:
            self.log_result("FOC Calculation Logic", False, "No FOC return form created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                foc_form = None
                for form in forms:
                    if form.get("id") == self.foc_return_form_id:
                        foc_form = form
                        break
                
                if foc_form:
                    quantity = foc_form.get("quantity", 0)
                    unit_price = foc_form.get("purchase_price", 0)
                    total_value = foc_form.get("total_value", 0)
                    
                    # FOC logic: quantity × 0 = 0
                    calculation_correct = (
                        unit_price == 0 and
                        total_value == 0 and
                        quantity == TEST_QUANTITY
                    )
                    
                    self.log_result("FOC Calculation Logic", calculation_correct,
                        f"Quantity: {quantity}, Unit Price: {unit_price}, "
                        f"Total Value: {total_value} (should be 0)", response_time)
                else:
                    self.log_result("FOC Calculation Logic", False,
                        "FOC form not found in response", response_time)
            else:
                self.log_result("FOC Calculation Logic", False,
                    f"Status: {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("FOC Calculation Logic", False, f"Exception: {str(e)}")
    
    def run_comprehensive_foc_tests(self):
        """Run all FOC functionality tests"""
        print("🆓 FOC (FREE OF COST) RETURN FORM SYSTEM TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Supervisor: {TEST_SUPERVISOR}")
        print(f"Test Product: Apple Juice Box 1L ({TEST_PRODUCT_BARCODE})")
        print(f"Test Quantity: {TEST_QUANTITY}")
        print(f"FOC Reason: {FOC_REASON}")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Product lookup
        product_data = self.test_product_lookup()
        if not product_data:
            # Use fallback data if lookup fails
            product_data = {
                "product_name": "Apple Juice Box 1L",
                "purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "item_number": "3222471081716"
            }
        
        # 3. Create FOC return form
        if not self.create_foc_return_form(product_data):
            print("❌ FOC return form creation failed - stopping FOC tests")
            return
        
        # 4. Create regular return form for comparison
        self.create_regular_return_form(product_data)
        
        # 5. Test FOC calculation logic
        self.test_foc_calculation_logic()
        
        # 6. Test FOC PDF export
        self.test_foc_pdf_export()
        
        # 7. Test FOC Excel export
        self.test_foc_excel_export()
        
        # 8. Test regular PDF export (for comparison)
        self.test_regular_pdf_export()
        
        # 9. Compare FOC vs Regular forms
        self.test_foc_vs_regular_comparison()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive FOC test summary"""
        print("\n" + "=" * 60)
        print("📊 FOC RETURN FORM SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🆓 FOC RETURN FORM ID: {self.foc_return_form_id}")
        print(f"📄 REGULAR RETURN FORM ID: {self.regular_return_form_id}")
        
        # Critical FOC requirements verification
        print("\n🎯 CRITICAL FOC REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "FOC Return Form Creation": any("FOC Return Form Creation" in r["test"] and r["success"] for r in self.test_results),
            "FOC Calculation Logic": any("FOC Calculation Logic" in r["test"] and r["success"] for r in self.test_results),
            "FOC PDF Export": any("FOC PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "FOC Excel Export": any("FOC Excel Export" in r["test"] and r["success"] for r in self.test_results),
            "Regular vs FOC Comparison": any("FOC vs Regular Comparison" in r["test"] and r["success"] for r in self.test_results),
            "Product Lookup": any("Product Lookup" in r["test"] and r["success"] for r in self.test_results)
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
        
        print("\n" + "=" * 60)
        print("🏁 FOC RETURN FORM SYSTEM TESTING COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = FOCReturnFormTester()
    tester.run_comprehensive_foc_tests()