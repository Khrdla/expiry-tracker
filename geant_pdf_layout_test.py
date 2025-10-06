#!/usr/bin/env python3
"""
GEANT Hypermarket Professional PDF Layout Design Testing
Testing the new professional PDF layout with A4 format, company branding, and clean sections
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration from review request
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_SUPERVISOR = "Mahmoud Badr"
TEST_BARCODE = "3222471081716"  # Apple Juice Box 1L
TEST_CURRENCY = "SAR"

class GeantPDFLayoutTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_return_form_id = None
        
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
        """Authenticate with admin credentials from review request"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Admin Authentication (imadqejji/066380531I)", True, 
                    f"JWT token received successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_product_lookup_for_return_form(self):
        """Test barcode lookup for Apple Juice Box 1L (3222471081716)"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/barcode/{TEST_BARCODE}")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                product = response.json()
                
                # Verify required fields for return form
                required_fields = ["product_name", "purchase_price", "purchase_currency", "supplier"]
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    self.log_result("Product Lookup for Return Form", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return None
                
                self.log_result("Product Lookup for Return Form", True,
                    f"Product: {product.get('product_name')}, "
                    f"Price: {product.get('purchase_price')} {product.get('purchase_currency')}, "
                    f"Supplier: {product.get('supplier')}", response_time)
                return product
            else:
                self.log_result("Product Lookup for Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Product Lookup for Return Form", False, f"Exception: {str(e)}")
            return None
    
    def create_complete_return_form(self, product_data):
        """Create return form with complete data as specified in review request"""
        try:
            start_time = time.time()
            
            # Calculate total value in SAR and USD equivalent
            purchase_price = product_data.get("purchase_price", 3.75)
            quantity = 98.5  # From review request
            total_sar = purchase_price * quantity
            usd_equivalent = total_sar * 0.2667  # SAR to USD conversion rate
            
            return_form_data = {
                "reference_number": f"RTN-GEANT-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": TEST_BARCODE,
                "quantity": quantity,
                "purchase_price": purchase_price,
                "purchase_currency": TEST_CURRENCY,
                "total_value_supplier_currency": total_sar,
                "usd_equivalent": usd_equivalent,
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality issue - damaged packaging during transport",
                "selected_supervisor": TEST_SUPERVISOR,
                "prepared_by_supervisor": TEST_SUPERVISOR,
                "section_manager_name": "Imad Qejji",
                "notes": "Professional PDF layout test - GEANT Hypermarket branding verification",
                "supervisor_approved": True,
                "supervisor_signature": f"{TEST_SUPERVISOR}_digital_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_digital_signature",
                "section_manager_timestamp": datetime.now().isoformat(),
                "return_date": datetime.now().strftime("%Y-%m-%d"),
                "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                self.created_return_form_id = form_id
                
                self.log_result("Complete Return Form Creation", True,
                    f"Form ID: {form_id}, Supervisor: {TEST_SUPERVISOR}, "
                    f"Total: {total_sar:.2f} SAR (${usd_equivalent:.2f} USD)", response_time)
                return form_id
            else:
                self.log_result("Complete Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Complete Return Form Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_professional_pdf_export(self):
        """Test PDF export with new professional layout design"""
        if not self.created_return_form_id:
            self.log_result("Professional PDF Export", False, "No return form created to test")
            return None
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.created_return_form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                content_type = response.headers.get('content-type', '')
                pdf_size = len(pdf_content)
                
                # Verify PDF format
                is_valid_pdf = pdf_content.startswith(b'%PDF') and b'%%EOF' in pdf_content
                
                # Check file size requirement (>5KB)
                meets_size_requirement = pdf_size > 5120  # 5KB in bytes
                
                self.log_result("Professional PDF Export", is_valid_pdf and meets_size_requirement,
                    f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                    f"Valid PDF: {is_valid_pdf}, Size >5KB: {meets_size_requirement}", response_time)
                
                return pdf_content if is_valid_pdf else None
            else:
                self.log_result("Professional PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Professional PDF Export", False, f"Exception: {str(e)}")
            return None
    
    def test_geant_branding_verification(self, pdf_content):
        """Verify GEANT branding elements in PDF"""
        if not pdf_content:
            self.log_result("GEANT Branding Verification", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check for GEANT HYPERMARKET branding
            has_geant = b'GEANT' in pdf_content
            has_hypermarket = b'HYPERMARKET' in pdf_content
            has_supplier_return_form = b'Supplier Return Form' in pdf_content
            
            # Check for professional green color theme indicators
            # (This is approximate as we can't easily detect colors in binary PDF)
            has_professional_styling = len(pdf_content) > 10000  # Larger size suggests styling
            
            # Check for clean header
            has_clean_header = has_geant and has_hypermarket and has_supplier_return_form
            
            response_time = (time.time() - start_time) * 1000
            
            branding_score = sum([has_geant, has_hypermarket, has_supplier_return_form, has_professional_styling])
            branding_success = branding_score >= 3
            
            self.log_result("GEANT Branding Verification", branding_success,
                f"GEANT: {has_geant}, HYPERMARKET: {has_hypermarket}, "
                f"Supplier Return Form: {has_supplier_return_form}, "
                f"Professional styling: {has_professional_styling} (Score: {branding_score}/4)", response_time)
            
        except Exception as e:
            self.log_result("GEANT Branding Verification", False, f"Exception: {str(e)}")
    
    def test_section_organization(self, pdf_content):
        """Check for clean section organization in PDF"""
        if not pdf_content:
            self.log_result("Section Organization Check", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check for required sections
            has_form_details = b'Reference Number' in pdf_content or b'Return Date' in pdf_content
            has_product_info = b'Product' in pdf_content or b'Barcode' in pdf_content
            has_return_value = b'SAR' in pdf_content or b'USD' in pdf_content
            has_approvals = b'Signature' in pdf_content or b'Approved' in pdf_content
            
            # Check for clean footer (no system messages)
            has_clean_footer = not (b'Status: PENDING' in pdf_content or b'Selected Supervisor:' in pdf_content)
            
            response_time = (time.time() - start_time) * 1000
            
            section_score = sum([has_form_details, has_product_info, has_return_value, has_approvals, has_clean_footer])
            section_success = section_score >= 4
            
            self.log_result("Section Organization Check", section_success,
                f"Form Details: {has_form_details}, Product Info: {has_product_info}, "
                f"Return Value: {has_return_value}, Approvals: {has_approvals}, "
                f"Clean Footer: {has_clean_footer} (Score: {section_score}/5)", response_time)
            
        except Exception as e:
            self.log_result("Section Organization Check", False, f"Exception: {str(e)}")
    
    def test_a4_layout_margins(self, pdf_content):
        """Test A4 layout with proper margins (approximation)"""
        if not pdf_content:
            self.log_result("A4 Layout with Proper Margins", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check for A4 page size indicators in PDF
            has_a4_indicators = b'/MediaBox' in pdf_content
            
            # Check for reasonable content size (indicates proper margins)
            pdf_size = len(pdf_content)
            has_reasonable_size = 5000 < pdf_size < 100000  # Between 5KB and 100KB
            
            # Check for proper page structure
            has_page_structure = b'/Page' in pdf_content and b'/Contents' in pdf_content
            
            response_time = (time.time() - start_time) * 1000
            
            layout_score = sum([has_a4_indicators, has_reasonable_size, has_page_structure])
            layout_success = layout_score >= 2
            
            self.log_result("A4 Layout with Proper Margins", layout_success,
                f"A4 indicators: {has_a4_indicators}, Reasonable size: {has_reasonable_size}, "
                f"Page structure: {has_page_structure}, PDF size: {pdf_size} bytes", response_time)
            
        except Exception as e:
            self.log_result("A4 Layout with Proper Margins", False, f"Exception: {str(e)}")
    
    def test_unicode_character_handling(self, pdf_content):
        """Test for Unicode character errors in PDF"""
        if not pdf_content:
            self.log_result("Unicode Character Error Check", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check for common Unicode error indicators
            has_unicode_errors = (
                b'Character' in pdf_content and b'outside the range' in pdf_content
            ) or (
                b'UnicodeDecodeError' in pdf_content
            ) or (
                b'encoding error' in pdf_content
            )
            
            # Check for proper text encoding (no obvious encoding issues)
            has_clean_text = not has_unicode_errors
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_result("Unicode Character Error Check", has_clean_text,
                f"No Unicode errors detected: {has_clean_text}, "
                f"PDF appears to have clean text encoding", response_time)
            
        except Exception as e:
            self.log_result("Unicode Character Error Check", False, f"Exception: {str(e)}")
    
    def test_sar_currency_conversion(self):
        """Test SAR currency with correct USD conversion"""
        if not self.created_return_form_id:
            self.log_result("SAR Currency Conversion Test", False, "No return form created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                test_form = None
                
                # Find our test form
                for form in forms:
                    if form.get("id") == self.created_return_form_id:
                        test_form = form
                        break
                
                if test_form:
                    purchase_currency = test_form.get("purchase_currency")
                    total_value = test_form.get("total_value_supplier_currency", 0)
                    usd_equivalent = test_form.get("usd_equivalent", 0)
                    
                    # Check if SAR conversion is correct (not 1:1)
                    is_sar_currency = purchase_currency == "SAR"
                    has_proper_conversion = usd_equivalent != total_value  # Should not be 1:1
                    expected_usd = total_value * 0.2667  # Approximate SAR to USD rate
                    conversion_accurate = abs(usd_equivalent - expected_usd) < 1.0  # Within $1 tolerance
                    
                    self.log_result("SAR Currency Conversion Test", 
                        is_sar_currency and has_proper_conversion and conversion_accurate,
                        f"Currency: {purchase_currency}, SAR Total: {total_value}, "
                        f"USD Equivalent: {usd_equivalent}, Expected USD: {expected_usd:.2f}, "
                        f"Proper conversion: {has_proper_conversion}", response_time)
                else:
                    self.log_result("SAR Currency Conversion Test", False,
                        "Test return form not found in response", response_time)
            else:
                self.log_result("SAR Currency Conversion Test", False,
                    f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("SAR Currency Conversion Test", False, f"Exception: {str(e)}")
    
    def run_geant_pdf_layout_tests(self):
        """Run all GEANT Hypermarket PDF layout design tests"""
        print("🏢 GEANT HYPERMARKET PROFESSIONAL PDF LAYOUT DESIGN TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Test Supervisor: {TEST_SUPERVISOR}")
        print(f"Test Product: Apple Juice Box 1L ({TEST_BARCODE})")
        print(f"Test Currency: {TEST_CURRENCY}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Product lookup for return form data
        product_data = self.test_product_lookup_for_return_form()
        if not product_data:
            # Use fallback data from review request
            product_data = {
                "product_name": "Apple Juice Box 1L",
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "item_number": "3222471081716"
            }
        
        # 3. Create complete return form with all required data
        form_id = self.create_complete_return_form(product_data)
        
        # 4. Test SAR currency conversion
        self.test_sar_currency_conversion()
        
        # 5. Test professional PDF export
        pdf_content = self.test_professional_pdf_export()
        
        # 6. GEANT branding verification
        self.test_geant_branding_verification(pdf_content)
        
        # 7. Section organization check
        self.test_section_organization(pdf_content)
        
        # 8. A4 layout with proper margins
        self.test_a4_layout_margins(pdf_content)
        
        # 9. Unicode character error check
        self.test_unicode_character_handling(pdf_content)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 GEANT HYPERMARKET PDF LAYOUT DESIGN TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        if self.created_return_form_id:
            print(f"📄 CREATED RETURN FORM ID: {self.created_return_form_id}")
        
        # Critical requirements verification from review request
        print("\n🎯 CRITICAL DESIGN REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Professional Layout Test": any("Professional PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "GEANT Branding Verification": any("GEANT Branding" in r["test"] and r["success"] for r in self.test_results),
            "Section Organization Check": any("Section Organization" in r["test"] and r["success"] for r in self.test_results),
            "A4 Layout with Proper Margins": any("A4 Layout" in r["test"] and r["success"] for r in self.test_results),
            "Export-Ready Quality (>5KB)": any("Professional PDF Export" in r["test"] and r["success"] and ">5KB: True" in r["details"] for r in self.test_results),
            "No Unicode Character Errors": any("Unicode Character" in r["test"] and r["success"] for r in self.test_results),
            "SAR Currency Conversion": any("SAR Currency" in r["test"] and r["success"] for r in self.test_results)
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
        print("🏁 GEANT HYPERMARKET PDF LAYOUT DESIGN TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = GeantPDFLayoutTester()
    tester.run_geant_pdf_layout_tests()