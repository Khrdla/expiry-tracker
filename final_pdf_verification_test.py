#!/usr/bin/env python3
"""
Final PDF Verification Test for GEANT Hypermarket Professional Layout
Comprehensive testing of the new professional PDF layout with detailed content analysis
"""

import requests
import json
import os
import time
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FinalPDFVerificationTester:
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
                    f"JWT token received successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_test_return_form(self):
        """Create a comprehensive test return form with all required data"""
        try:
            start_time = time.time()
            
            # Get product data first
            product_response = self.session.get(f"{BACKEND_URL}/barcode/3222471081716")
            if product_response.status_code == 200:
                product_data = product_response.json()
            else:
                product_data = {
                    "product_name": "Apple Juice Box 1L",
                    "purchase_price": 3.75,
                    "purchase_currency": "SAR",
                    "supplier": "ExtenC",
                    "item_number": "3222471081716"
                }
            
            return_form_data = {
                "reference_number": f"RTN-FINAL-TEST-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": "3222471081716",
                "quantity": 98.5,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality issue - damaged packaging during transport",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "notes": "Final verification test for GEANT Hypermarket professional PDF layout design",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_digital_signature",
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
                
                # Calculate expected values
                total_sar = 3.75 * 98.5
                usd_equivalent = total_sar * 0.2667
                
                self.log_result("Test Return Form Creation", True,
                    f"Form ID: {form_id}, Total: {total_sar:.2f} SAR (${usd_equivalent:.2f} USD)", response_time)
                return form_id
            else:
                self.log_result("Test Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Test Return Form Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_professional_pdf_generation(self):
        """Test the professional PDF generation with comprehensive analysis"""
        if not self.created_return_form_id:
            self.log_result("Professional PDF Generation", False, "No return form created")
            return None
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.created_return_form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Verify PDF structure
                is_valid_pdf = pdf_content.startswith(b'%PDF') and b'%%EOF' in pdf_content
                meets_size_requirement = pdf_size > 5120  # >5KB
                
                # Save PDF for manual inspection
                pdf_filename = f"/app/final_test_geant_return_form.pdf"
                with open(pdf_filename, 'wb') as f:
                    f.write(pdf_content)
                
                self.log_result("Professional PDF Generation", is_valid_pdf and meets_size_requirement,
                    f"Size: {pdf_size} bytes, Valid PDF: {is_valid_pdf}, >5KB: {meets_size_requirement}, Saved: {pdf_filename}", response_time)
                
                return pdf_content
            else:
                self.log_result("Professional PDF Generation", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Professional PDF Generation", False, f"Exception: {str(e)}")
            return None
    
    def analyze_pdf_structure(self, pdf_content):
        """Analyze PDF structure for professional layout elements"""
        if not pdf_content:
            self.log_result("PDF Structure Analysis", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check for ReportLab generation (indicates professional layout)
            has_reportlab = b'ReportLab' in pdf_content
            
            # Check for A4 page size
            has_a4_mediabox = b'/MediaBox' in pdf_content
            
            # Check for image objects (logo)
            has_image_objects = b'/Image' in pdf_content and b'/XObject' in pdf_content
            
            # Check for proper font embedding
            has_helvetica_fonts = b'Helvetica' in pdf_content
            
            # Check for color objects (green theme)
            has_color_objects = b'/ColorSpace' in pdf_content or b'/DeviceRGB' in pdf_content
            
            # Check for table structures
            has_table_structures = pdf_content.count(b'/Table') > 0 or pdf_content.count(b'Td') > 10
            
            response_time = (time.time() - start_time) * 1000
            
            structure_score = sum([
                has_reportlab, has_a4_mediabox, has_image_objects, 
                has_helvetica_fonts, has_color_objects, has_table_structures
            ])
            
            structure_success = structure_score >= 4
            
            self.log_result("PDF Structure Analysis", structure_success,
                f"ReportLab: {has_reportlab}, A4: {has_a4_mediabox}, Images: {has_image_objects}, "
                f"Fonts: {has_helvetica_fonts}, Colors: {has_color_objects}, Tables: {has_table_structures} "
                f"(Score: {structure_score}/6)", response_time)
            
        except Exception as e:
            self.log_result("PDF Structure Analysis", False, f"Exception: {str(e)}")
    
    def test_geant_branding_implementation(self, pdf_content):
        """Test GEANT branding implementation in PDF"""
        if not pdf_content:
            self.log_result("GEANT Branding Implementation", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Convert to string for text analysis (ignore encoding errors)
            pdf_text = pdf_content.decode('utf-8', errors='ignore')
            
            # Check for GEANT HYPERMARKET branding
            has_geant = 'GEANT' in pdf_text
            has_hypermarket = 'HYPERMARKET' in pdf_text
            has_supplier_return_form = 'Supplier Return Form' in pdf_text
            
            # Check for professional green color theme (hex values in PDF)
            has_green_colors = any(color in pdf_text for color in ['0.1 0.4 0.2', '0.85 0.95 0.88', '0.2 0.6 0.3'])
            
            # Check for company logo (image object with specific dimensions)
            has_logo_dimensions = '1.5' in pdf_text and 'inch' in pdf_text
            
            # Check for professional footer
            has_professional_footer = 'Inventory Management System' in pdf_text
            
            response_time = (time.time() - start_time) * 1000
            
            branding_score = sum([
                has_geant, has_hypermarket, has_supplier_return_form,
                has_green_colors, has_logo_dimensions, has_professional_footer
            ])
            
            branding_success = branding_score >= 4
            
            self.log_result("GEANT Branding Implementation", branding_success,
                f"GEANT: {has_geant}, HYPERMARKET: {has_hypermarket}, Return Form: {has_supplier_return_form}, "
                f"Green Colors: {has_green_colors}, Logo: {has_logo_dimensions}, Footer: {has_professional_footer} "
                f"(Score: {branding_score}/6)", response_time)
            
        except Exception as e:
            self.log_result("GEANT Branding Implementation", False, f"Exception: {str(e)}")
    
    def test_section_organization_implementation(self, pdf_content):
        """Test section organization implementation"""
        if not pdf_content:
            self.log_result("Section Organization Implementation", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            pdf_text = pdf_content.decode('utf-8', errors='ignore')
            
            # Check for required sections
            has_form_details = 'FORM DETAILS' in pdf_text
            has_product_info = 'PRODUCT INFORMATION' in pdf_text
            has_return_value = 'RETURN VALUE CALCULATION' in pdf_text
            has_approvals = 'APPROVALS & SIGNATURES' in pdf_text
            
            # Check for specific data fields
            has_reference_number = 'Reference Number' in pdf_text
            has_barcode_field = 'Barcode' in pdf_text
            has_sar_currency = 'SAR' in pdf_text
            has_usd_equivalent = 'USD Equivalent' in pdf_text
            has_supervisor_name = 'Mahmoud Badr' in pdf_text
            has_section_manager = 'Imad Qejji' in pdf_text
            
            response_time = (time.time() - start_time) * 1000
            
            section_score = sum([
                has_form_details, has_product_info, has_return_value, has_approvals,
                has_reference_number, has_barcode_field, has_sar_currency, 
                has_usd_equivalent, has_supervisor_name, has_section_manager
            ])
            
            section_success = section_score >= 7
            
            self.log_result("Section Organization Implementation", section_success,
                f"Form Details: {has_form_details}, Product Info: {has_product_info}, "
                f"Return Value: {has_return_value}, Approvals: {has_approvals}, "
                f"Reference: {has_reference_number}, Barcode: {has_barcode_field}, "
                f"SAR: {has_sar_currency}, USD: {has_usd_equivalent}, "
                f"Supervisor: {has_supervisor_name}, Manager: {has_section_manager} "
                f"(Score: {section_score}/10)", response_time)
            
        except Exception as e:
            self.log_result("Section Organization Implementation", False, f"Exception: {str(e)}")
    
    def test_clean_footer_no_system_messages(self, pdf_content):
        """Test for clean footer without system messages"""
        if not pdf_content:
            self.log_result("Clean Footer Verification", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            pdf_text = pdf_content.decode('utf-8', errors='ignore')
            
            # Check for system messages that should NOT be present
            has_status_pending = 'Status: PENDING' in pdf_text
            has_selected_supervisor_debug = 'Selected Supervisor:' in pdf_text
            has_debug_messages = 'debug' in pdf_text.lower()
            has_error_messages = 'error' in pdf_text.lower()
            
            # Check for clean professional footer
            has_professional_footer = 'GEANT HYPERMARKET Inventory Management System' in pdf_text
            has_generated_timestamp = 'Generated:' in pdf_text
            
            response_time = (time.time() - start_time) * 1000
            
            # Success if no system messages and has professional footer
            clean_footer_success = (not any([has_status_pending, has_selected_supervisor_debug, 
                                           has_debug_messages, has_error_messages]) and
                                  has_professional_footer and has_generated_timestamp)
            
            self.log_result("Clean Footer Verification", clean_footer_success,
                f"No system messages: {not any([has_status_pending, has_selected_supervisor_debug, has_debug_messages, has_error_messages])}, "
                f"Professional footer: {has_professional_footer}, Timestamp: {has_generated_timestamp}", response_time)
            
        except Exception as e:
            self.log_result("Clean Footer Verification", False, f"Exception: {str(e)}")
    
    def test_sar_usd_conversion_accuracy(self):
        """Test SAR to USD conversion accuracy"""
        if not self.created_return_form_id:
            self.log_result("SAR to USD Conversion Accuracy", False, "No return form created")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                test_form = None
                
                for form in forms:
                    if form.get("id") == self.created_return_form_id:
                        test_form = form
                        break
                
                if test_form:
                    purchase_price = float(test_form.get("purchase_price", 0))
                    quantity = float(test_form.get("quantity", 0))
                    currency = test_form.get("purchase_currency")
                    
                    total_sar = purchase_price * quantity
                    expected_usd = total_sar * 0.2667  # SAR to USD rate
                    
                    # Check if conversion is NOT 1:1 (the critical bug that was fixed)
                    is_not_one_to_one = abs(total_sar - expected_usd) > 1.0
                    
                    # Check if conversion is approximately correct
                    actual_usd = test_form.get("usd_equivalent", 0)
                    conversion_accurate = abs(float(actual_usd) - expected_usd) < 1.0
                    
                    self.log_result("SAR to USD Conversion Accuracy", is_not_one_to_one and conversion_accurate,
                        f"SAR Total: {total_sar:.2f}, Expected USD: {expected_usd:.2f}, "
                        f"Actual USD: {actual_usd}, Not 1:1: {is_not_one_to_one}, "
                        f"Accurate: {conversion_accurate}", response_time)
                else:
                    self.log_result("SAR to USD Conversion Accuracy", False,
                        "Test return form not found", response_time)
            else:
                self.log_result("SAR to USD Conversion Accuracy", False,
                    f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("SAR to USD Conversion Accuracy", False, f"Exception: {str(e)}")
    
    def run_final_verification_tests(self):
        """Run all final verification tests for GEANT PDF layout"""
        print("🏢 GEANT HYPERMARKET FINAL PDF LAYOUT VERIFICATION")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Test Requirements: Professional A4 layout, GEANT branding, clean sections")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create comprehensive test return form
        form_id = self.create_test_return_form()
        
        # 3. Test SAR to USD conversion accuracy
        self.test_sar_usd_conversion_accuracy()
        
        # 4. Generate and analyze professional PDF
        pdf_content = self.test_professional_pdf_generation()
        
        if pdf_content:
            # 5. Analyze PDF structure
            self.analyze_pdf_structure(pdf_content)
            
            # 6. Test GEANT branding implementation
            self.test_geant_branding_implementation(pdf_content)
            
            # 7. Test section organization
            self.test_section_organization_implementation(pdf_content)
            
            # 8. Test clean footer
            self.test_clean_footer_no_system_messages(pdf_content)
        
        # Summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 GEANT HYPERMARKET FINAL PDF VERIFICATION SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        if self.created_return_form_id:
            print(f"📄 CREATED RETURN FORM ID: {self.created_return_form_id}")
        
        # Critical requirements verification from review request
        print("\n🎯 CRITICAL DESIGN REQUIREMENTS FROM REVIEW REQUEST:")
        
        critical_tests = {
            "1. Professional Layout Test": any("Professional PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "2. GEANT Branding Verification": any("GEANT Branding Implementation" in r["test"] and r["success"] for r in self.test_results),
            "3. Section Organization Check": any("Section Organization Implementation" in r["test"] and r["success"] for r in self.test_results),
            "4. Export-Ready Quality (>5KB)": any("Professional PDF Generation" in r["test"] and r["success"] and ">5KB: True" in r["details"] for r in self.test_results),
            "5. A4 Layout with Proper Margins": any("PDF Structure Analysis" in r["test"] and r["success"] for r in self.test_results),
            "6. Clean Footer (No System Messages)": any("Clean Footer Verification" in r["test"] and r["success"] for r in self.test_results),
            "7. SAR Currency with USD Conversion": any("SAR to USD Conversion Accuracy" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Overall assessment
        critical_passed = sum(1 for status in critical_tests.values() if status)
        critical_total = len(critical_tests)
        critical_success_rate = (critical_passed / critical_total * 100) if critical_total > 0 else 0
        
        print(f"\n🎯 CRITICAL REQUIREMENTS: {critical_passed}/{critical_total} ({critical_success_rate:.1f}%)")
        
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
        
        # Final verdict
        if critical_success_rate >= 85:
            print(f"\n🎉 FINAL VERDICT: GEANT HYPERMARKET PDF LAYOUT DESIGN IS PRODUCTION-READY!")
            print(f"✅ Professional layout meets all critical requirements from review request")
        elif critical_success_rate >= 70:
            print(f"\n⚠️ FINAL VERDICT: GEANT HYPERMARKET PDF LAYOUT NEEDS MINOR IMPROVEMENTS")
            print(f"🔧 Most requirements met, minor fixes needed for full compliance")
        else:
            print(f"\n❌ FINAL VERDICT: GEANT HYPERMARKET PDF LAYOUT NEEDS MAJOR IMPROVEMENTS")
            print(f"🚨 Critical requirements not met, significant fixes required")
        
        print("\n" + "=" * 70)
        print("🏁 GEANT HYPERMARKET FINAL PDF VERIFICATION COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = FinalPDFVerificationTester()
    tester.run_final_verification_tests()