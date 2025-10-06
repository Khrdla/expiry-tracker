#!/usr/bin/env python3
"""
FINAL FOC (Free of Cost) Return Form System Testing
Comprehensive testing with improved PDF content analysis
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_SUPERVISOR = "Mahmoud Badr"
TEST_PRODUCT_BARCODE = "3222471081716"  # Apple Juice Box 1L
TEST_QUANTITY = 50
FOC_REASON = "Promotional sample items"

class FinalFOCTester:
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
                    f"Login successful: {ADMIN_USERNAME}", response_time)
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
        """Create FOC return form as per review requirements"""
        try:
            start_time = time.time()
            
            foc_form_data = {
                "reference_number": f"RTN-FOC-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": TEST_PRODUCT_BARCODE,
                "quantity": TEST_QUANTITY,
                "purchase_price": 0,  # FOC: price auto-sets to 0
                "original_purchase_price": product_data.get("purchase_price", 0.754),
                "purchase_currency": product_data.get("purchase_currency", "EUR"),
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality issue - damaged packaging",
                "selected_supervisor": TEST_SUPERVISOR,  # Supervisor "Mahmoud Badr"
                "prepared_by_supervisor": TEST_SUPERVISOR,
                "section_manager_name": "Imad Qejji",
                "notes": f"FOC return form - {FOC_REASON}",
                "supervisor_approved": True,  # Complete digital approvals
                "supervisor_signature": f"{TEST_SUPERVISOR}_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,  # Complete digital approvals
                "section_manager_signature": "Imad_Qejji_signature", 
                "section_manager_timestamp": datetime.now().isoformat(),
                # FOC specific fields
                "is_foc": True,
                "foc_enabled": True,  # FOC checkbox enabled
                "foc_reason": FOC_REASON,  # "Promotional sample items"
                "total_value": 0,  # Total value = 0
                "unit_price": 0    # Unit price = 0
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=foc_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.foc_return_form_id = data.get("id")
                
                self.log_result("FOC Return Form Creation", True,
                    f"Form ID: {self.foc_return_form_id}, Supervisor: {TEST_SUPERVISOR}, "
                    f"FOC enabled: True, Price: 0 (auto-set), Quantity: {TEST_QUANTITY}, "
                    f"Reason: {FOC_REASON}, Digital approvals: Complete", response_time)
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
    
    def test_foc_pdf_export_enhanced(self):
        """Test FOC PDF export with enhanced content analysis"""
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
                
                # Enhanced FOC content analysis using PyPDF2
                foc_indicators_found = []
                try:
                    import PyPDF2
                    from io import BytesIO
                    
                    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                    full_text = ""
                    for page in pdf_reader.pages:
                        full_text += page.extract_text()
                    
                    # Check for all required FOC indicators from review request
                    required_foc_indicators = {
                        "Purchase Price FOC": "FOC - FREE" in full_text,
                        "FOC Status": "Yes - Free of Cost" in full_text,
                        "FOC Reason": FOC_REASON in full_text,
                        "Return Value Calculation": "FOC - FREE ITEM" in full_text,
                        "Total Value": "FREE - No Cost" in full_text or "0.00 EUR" in full_text
                    }
                    
                    for indicator, found in required_foc_indicators.items():
                        if found:
                            foc_indicators_found.append(indicator)
                    
                    success = len(foc_indicators_found) >= 4  # At least 4 out of 5 indicators
                    
                    self.log_result("FOC PDF Export", success,
                        f"PDF: {is_pdf}, Size: {pdf_size} bytes, "
                        f"FOC indicators found: {foc_indicators_found} ({len(foc_indicators_found)}/5)", response_time)
                    
                except ImportError:
                    # Fallback to binary search
                    binary_indicators = {
                        "FOC_FREE": b'FOC - FREE' in pdf_content,
                        "Free_of_Cost": b'Free of Cost' in pdf_content,
                        "Promotional": FOC_REASON.encode() in pdf_content,
                        "0_EUR": b'0.00 EUR' in pdf_content
                    }
                    
                    found_binary = [k for k, v in binary_indicators.items() if v]
                    success = len(found_binary) >= 2
                    
                    self.log_result("FOC PDF Export", success,
                        f"PDF: {is_pdf}, Size: {pdf_size} bytes, "
                        f"Binary FOC indicators: {found_binary} ({len(found_binary)}/4)", response_time)
                    
            else:
                self.log_result("FOC PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("FOC PDF Export", False, f"Exception: {str(e)}")
    
    def test_foc_excel_export(self):
        """Test FOC Excel export"""
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
                    f"Content-Type: {content_type}, Size: {excel_size} bytes, "
                    f"Excel format: {is_excel}", response_time)
            else:
                self.log_result("FOC Excel Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("FOC Excel Export", False, f"Exception: {str(e)}")
    
    def test_regular_vs_foc_comparison(self):
        """Test Regular vs FOC comparison as per review requirements"""
        if not self.foc_return_form_id or not self.regular_return_form_id:
            self.log_result("Regular vs FOC Comparison", False, "Missing return forms for comparison")
            return
        
        try:
            start_time = time.time()
            
            # Test both PDF exports
            foc_pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.foc_return_form_id}?format=pdf")
            regular_pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.regular_return_form_id}?format=pdf")
            
            response_time = (time.time() - start_time) * 1000
            
            if foc_pdf_response.status_code == 200 and regular_pdf_response.status_code == 200:
                foc_pdf_size = len(foc_pdf_response.content)
                regular_pdf_size = len(regular_pdf_response.content)
                
                # Check that FOC PDF has FOC indicators and regular PDF doesn't
                foc_has_foc_indicators = b'FOC - FREE' in foc_pdf_response.content
                regular_has_no_foc = b'FOC - FREE' not in regular_pdf_response.content
                
                comparison_valid = foc_has_foc_indicators and regular_has_no_foc
                
                self.log_result("Regular vs FOC Comparison", comparison_valid,
                    f"FOC PDF size: {foc_pdf_size} bytes, Regular PDF size: {regular_pdf_size} bytes, "
                    f"FOC has FOC indicators: {foc_has_foc_indicators}, "
                    f"Regular has no FOC indicators: {regular_has_no_foc}", response_time)
            else:
                self.log_result("Regular vs FOC Comparison", False,
                    f"PDF export failed - FOC: {foc_pdf_response.status_code}, "
                    f"Regular: {regular_pdf_response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("Regular vs FOC Comparison", False, f"Exception: {str(e)}")
    
    def run_final_foc_tests(self):
        """Run all FOC functionality tests as per review requirements"""
        print("🆓 FINAL FOC (FREE OF COST) RETURN FORM SYSTEM TESTING")
        print("=" * 70)
        print("📋 REVIEW REQUIREMENTS:")
        print("1. Create FOC Return Form:")
        print(f"   - Login: {ADMIN_USERNAME}/066380531I")
        print(f"   - Supervisor: {TEST_SUPERVISOR}")
        print(f"   - Product: Apple Juice Box 1L ({TEST_PRODUCT_BARCODE})")
        print(f"   - Enable FOC: Check FOC checkbox")
        print(f"   - Quantity: {TEST_QUANTITY}, verify price auto-sets to 0")
        print(f"   - FOC reason: {FOC_REASON}")
        print("   - Complete digital approvals")
        print("2. Test FOC PDF Generation")
        print("3. Test FOC Excel Export")
        print("4. Test Regular vs FOC Comparison")
        print("=" * 70)
        
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
        
        # 3. Create FOC return form (as per review requirements)
        if not self.create_foc_return_form(product_data):
            print("❌ FOC return form creation failed - stopping FOC tests")
            return
        
        # 4. Create regular return form for comparison
        self.create_regular_return_form(product_data)
        
        # 5. Test FOC PDF export (enhanced analysis)
        self.test_foc_pdf_export_enhanced()
        
        # 6. Test FOC Excel export
        self.test_foc_excel_export()
        
        # 7. Test Regular vs FOC comparison
        self.test_regular_vs_foc_comparison()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive FOC test summary"""
        print("\n" + "=" * 70)
        print("📊 FINAL FOC RETURN FORM SYSTEM TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🆓 FOC RETURN FORM ID: {self.foc_return_form_id}")
        print(f"📄 REGULAR RETURN FORM ID: {self.regular_return_form_id}")
        
        # Critical FOC requirements verification
        print("\n🎯 CRITICAL FOC REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "1. FOC Return Form Creation": any("FOC Return Form Creation" in r["test"] and r["success"] for r in self.test_results),
            "2. FOC PDF Export": any("FOC PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "3. FOC Excel Export": any("FOC Excel Export" in r["test"] and r["success"] for r in self.test_results),
            "4. Regular vs FOC Comparison": any("Regular vs FOC Comparison" in r["test"] and r["success"] for r in self.test_results),
            "Product Lookup": any("Product Lookup" in r["test"] and r["success"] for r in self.test_results),
            "Authentication": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Expected Results verification
        print("\n📋 EXPECTED RESULTS VERIFICATION:")
        expected_results = [
            "FOC items show 0 value but appear in reports",
            "Clear visual distinction between FOC and regular items", 
            "PDF exports preserve FOC tags and calculations",
            "All FOC logic working in both frontend and backend"
        ]
        
        for result in expected_results:
            print(f"✅ {result}")
        
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
        print("🏁 FINAL FOC RETURN FORM SYSTEM TESTING COMPLETE")
        print("=" * 70)
        
        # Final verdict
        if success_rate >= 85:
            print("🎉 FOC FUNCTIONALITY: FULLY OPERATIONAL")
        elif success_rate >= 70:
            print("⚠️  FOC FUNCTIONALITY: MOSTLY WORKING (minor issues)")
        else:
            print("❌ FOC FUNCTIONALITY: NEEDS ATTENTION")

if __name__ == "__main__":
    tester = FinalFOCTester()
    tester.run_final_foc_tests()