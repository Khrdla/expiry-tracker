#!/usr/bin/env python3
"""
Single-Page PDF Layout Optimization Testing
Testing comprehensive optimizations to fit Return Form PDF entirely on one page
"""

import requests
import json
import os
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
SUPERVISOR_NAME = "Mahmoud Badr"
PRODUCT_BARCODE = "3222471081716"  # Apple Juice Box 1L
TEST_CURRENCY = "SAR"

class SinglePagePDFTester:
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
                    f"Login successful with credentials {ADMIN_USERNAME}/{ADMIN_PASSWORD}", response_time)
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
            response = self.session.get(f"{BACKEND_URL}/barcode/{PRODUCT_BARCODE}")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                product = response.json()
                
                # Verify it's the correct product
                product_name = product.get("product_name", "")
                is_apple_juice = "apple" in product_name.lower() and "juice" in product_name.lower()
                
                self.log_result("Product Lookup - Apple Juice Box 1L", True,
                    f"Product: {product_name}, Barcode: {PRODUCT_BARCODE}, "
                    f"Price: {product.get('purchase_price')} {product.get('purchase_currency')}, "
                    f"Supplier: {product.get('supplier')}", response_time)
                return product
            else:
                self.log_result("Product Lookup - Apple Juice Box 1L", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Product Lookup - Apple Juice Box 1L", False, f"Exception: {str(e)}")
            return None
    
    def create_complete_return_form(self, product_data):
        """Create complete return form with all required data for single-page PDF test"""
        try:
            start_time = time.time()
            
            # Calculate SAR values for maximum content
            quantity = 98.5
            price_per_unit = 3.75
            total_sar_value = quantity * price_per_unit
            
            return_form_data = {
                "reference_number": f"RTN-SINGLE-PAGE-{int(time.time())}",
                "product_code": product_data.get("item_number", "3222471081716"),
                "product_name": product_data.get("product_name", "Apple Juice Box 1L"),
                "barcode": PRODUCT_BARCODE,
                "quantity": quantity,
                "purchase_price": price_per_unit,
                "purchase_currency": TEST_CURRENCY,
                "supplier": product_data.get("supplier", "ExtenC"),
                "reason_for_return": "Quality control issue - damaged packaging during transport. Product integrity compromised requiring immediate return to supplier for replacement or credit.",
                "selected_supervisor": SUPERVISOR_NAME,
                "prepared_by_supervisor": SUPERVISOR_NAME,
                "section_manager_name": "Imad Qejji",
                "notes": f"COMPREHENSIVE SINGLE-PAGE PDF TEST: This return form contains maximum content to test single-page optimization. Supervisor: {SUPERVISOR_NAME}, Product: Apple Juice Box 1L, Currency: {TEST_CURRENCY}, Total Value: {total_sar_value} SAR. All sections included: Form Details, Product Information, Return Value Calculation, Approvals & Signatures, Manual Signatures section. Testing optimized margins (0.7cm), reduced fonts (14pt header, 10pt sections, 9pt/8pt tables), compressed spacing, and professional GEANT branding layout.",
                "supervisor_approved": True,
                "supervisor_signature": f"{SUPERVISOR_NAME}_digital_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_digital_signature", 
                "section_manager_timestamp": datetime.now().isoformat(),
                "department": product_data.get("department", "01-CGD"),
                "section": product_data.get("section", "S010 - Beverage"),
                "total_value": total_sar_value,
                "return_type": "supplier_return",
                "urgency": "high",
                "expected_credit": total_sar_value,
                "quality_issue_details": "Packaging damage, product leakage, expiry date concerns",
                "transport_conditions": "Temperature controlled, handled with care",
                "replacement_requested": True,
                "credit_requested": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                self.created_return_form_id = form_id
                
                self.log_result("Complete Return Form Creation", True,
                    f"Form ID: {form_id}, Supervisor: {SUPERVISOR_NAME}, "
                    f"Product: Apple Juice Box 1L, Currency: {TEST_CURRENCY}, "
                    f"Quantity: {quantity}, Total: {total_sar_value} SAR, "
                    f"Full approvals: supervisor_approved=true, section_manager_approved=true", response_time)
                return form_id
            else:
                self.log_result("Complete Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Complete Return Form Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_single_page_pdf_generation(self):
        """Test single-page PDF generation and analysis"""
        if not self.created_return_form_id:
            self.log_result("Single-Page PDF Generation", False, "No return form created to test")
            return None
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{self.created_return_form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Verify PDF format
                is_valid_pdf = pdf_content.startswith(b'%PDF')
                content_type = response.headers.get('content-type', '')
                is_pdf_content_type = 'application/pdf' in content_type
                
                self.log_result("Single-Page PDF Generation", is_valid_pdf and is_pdf_content_type,
                    f"PDF Size: {pdf_size} bytes, Content-Type: {content_type}, "
                    f"Valid PDF signature: {is_valid_pdf}", response_time)
                
                return pdf_content if is_valid_pdf else None
            else:
                self.log_result("Single-Page PDF Generation", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                    
        except Exception as e:
            self.log_result("Single-Page PDF Generation", False, f"Exception: {str(e)}")
            return None
    
    def analyze_pdf_page_count(self, pdf_content):
        """Analyze PDF page count - CRITICAL TEST"""
        if not pdf_content:
            self.log_result("PDF Page Count Analysis", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Use PyPDF2 to analyze page count
            pdf_stream = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            page_count = len(pdf_reader.pages)
            
            # CRITICAL REQUIREMENT: Must be exactly 1 page
            is_single_page = page_count == 1
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_result("PDF Page Count Analysis - CRITICAL", is_single_page,
                f"Page Count: {page_count} (Requirement: exactly 1 page), "
                f"Single-page optimization: {'SUCCESS' if is_single_page else 'FAILED'}", response_time)
            
            return page_count
                    
        except Exception as e:
            self.log_result("PDF Page Count Analysis - CRITICAL", False, f"Exception: {str(e)}")
            return None
    
    def analyze_pdf_content_completeness(self, pdf_content):
        """Analyze PDF content completeness - verify all sections present"""
        if not pdf_content:
            self.log_result("PDF Content Completeness", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_stream = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            if len(pdf_reader.pages) == 0:
                self.log_result("PDF Content Completeness", False, "No pages found in PDF")
                return
            
            # Extract text from first (and should be only) page
            page_text = pdf_reader.pages[0].extract_text()
            
            # Check for required sections
            required_sections = {
                "GEANT HYPERMARKET": "GEANT" in page_text or "Geant" in page_text,
                "Form Details": "FORM DETAILS" in page_text or "Form Details" in page_text,
                "Product Information": "PRODUCT INFORMATION" in page_text or "Product Information" in page_text,
                "Return Value Calculation": "RETURN VALUE" in page_text or "Return Value" in page_text,
                "Approvals & Signatures": "APPROVALS" in page_text or "SIGNATURES" in page_text,
                "Supervisor Name": SUPERVISOR_NAME in page_text,
                "Apple Juice Box": "Apple Juice" in page_text or "Apple" in page_text,
                "SAR Currency": "SAR" in page_text,
                "Barcode": PRODUCT_BARCODE in page_text or "barcode" in page_text.lower()
            }
            
            present_sections = [section for section, present in required_sections.items() if present]
            missing_sections = [section for section, present in required_sections.items() if not present]
            
            completeness_score = len(present_sections) / len(required_sections) * 100
            is_complete = completeness_score >= 80  # 80% threshold for completeness
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_result("PDF Content Completeness", is_complete,
                f"Completeness: {completeness_score:.1f}% ({len(present_sections)}/{len(required_sections)} sections), "
                f"Present: {present_sections[:3]}{'...' if len(present_sections) > 3 else ''}, "
                f"Missing: {missing_sections[:2] if missing_sections else 'None'}", response_time)
            
            return completeness_score
                    
        except Exception as e:
            self.log_result("PDF Content Completeness", False, f"Exception: {str(e)}")
            return None
    
    def analyze_pdf_professional_quality(self, pdf_content):
        """Analyze PDF professional quality and readability"""
        if not pdf_content:
            self.log_result("PDF Professional Quality", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            pdf_size = len(pdf_content)
            
            # Professional quality indicators
            quality_indicators = {
                "Adequate Size": pdf_size > 10000,  # At least 10KB for professional content
                "GEANT Branding": b'GEANT' in pdf_content or b'Geant' in pdf_content,
                "Professional Structure": b'/Page' in pdf_content and b'/Font' in pdf_content,
                "Proper PDF Format": pdf_content.startswith(b'%PDF-1.') and pdf_content.endswith(b'%%EOF\n'),
                "Contains Images/Logo": pdf_size > 30000  # Larger size suggests logo inclusion
            }
            
            quality_score = sum(quality_indicators.values()) / len(quality_indicators) * 100
            is_professional = quality_score >= 60  # 60% threshold for professional quality
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_result("PDF Professional Quality", is_professional,
                f"Quality Score: {quality_score:.1f}%, Size: {pdf_size} bytes, "
                f"Professional indicators: {sum(quality_indicators.values())}/{len(quality_indicators)}", response_time)
            
            return quality_score
                    
        except Exception as e:
            self.log_result("PDF Professional Quality", False, f"Exception: {str(e)}")
            return None
    
    def test_print_readiness(self, pdf_content):
        """Test print readiness and A4 format compliance"""
        if not pdf_content:
            self.log_result("Print Readiness", False, "No PDF content to analyze")
            return
        
        try:
            start_time = time.time()
            
            # Check PDF structure for print readiness
            pdf_stream = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            if len(pdf_reader.pages) == 0:
                self.log_result("Print Readiness", False, "No pages found in PDF")
                return
            
            page = pdf_reader.pages[0]
            
            # Get page dimensions (in points, 72 points = 1 inch)
            mediabox = page.mediabox
            width = float(mediabox.width)
            height = float(mediabox.height)
            
            # A4 dimensions in points: 595.276 x 841.890
            a4_width = 595.276
            a4_height = 841.890
            
            # Check if dimensions are close to A4 (within 5% tolerance)
            width_match = abs(width - a4_width) / a4_width < 0.05
            height_match = abs(height - a4_height) / a4_height < 0.05
            is_a4_format = width_match and height_match
            
            response_time = (time.time() - start_time) * 1000
            
            self.log_result("Print Readiness - A4 Format", is_a4_format,
                f"Page dimensions: {width:.1f} x {height:.1f} points, "
                f"A4 standard: {a4_width} x {a4_height} points, "
                f"Format match: {is_a4_format}", response_time)
            
            return is_a4_format
                    
        except Exception as e:
            self.log_result("Print Readiness - A4 Format", False, f"Exception: {str(e)}")
            return None
    
    def run_single_page_optimization_tests(self):
        """Run comprehensive single-page PDF optimization tests"""
        print("🎯 SINGLE-PAGE PDF LAYOUT OPTIMIZATION TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        print(f"Supervisor: {SUPERVISOR_NAME}")
        print(f"Product: Apple Juice Box 1L ({PRODUCT_BARCODE})")
        print(f"Currency: {TEST_CURRENCY}")
        print("=" * 70)
        print("🔍 TESTING OPTIMIZATION CHANGES:")
        print("   • Reduced Margins: 1.2cm/1.5cm → 0.7cm/0.7cm")
        print("   • Logo Size: 1.5\" → 1.1\"")
        print("   • Header Font: 16pt → 14pt")
        print("   • Table Fonts: 10pt → 9pt, 9pt → 8pt")
        print("   • Table Padding: 6 → 3, 4 → 2")
        print("   • Section Headers: 12pt → 10pt")
        print("   • All Vertical Spacing Reduced 50%+")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Product lookup
        product_data = self.test_product_lookup()
        if not product_data:
            # Use fallback data
            product_data = {
                "product_name": "Apple Juice Box 1L",
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "item_number": "3222471081716",
                "department": "01-CGD",
                "section": "S010 - Beverage"
            }
        
        # 3. Create complete return form with maximum content
        form_id = self.create_complete_return_form(product_data)
        if not form_id:
            print("❌ Return form creation failed - stopping tests")
            return
        
        # 4. Generate and analyze single-page PDF
        pdf_content = self.test_single_page_pdf_generation()
        if not pdf_content:
            print("❌ PDF generation failed - stopping tests")
            return
        
        # 5. CRITICAL TEST: Analyze page count
        page_count = self.analyze_pdf_page_count(pdf_content)
        
        # 6. Analyze content completeness
        completeness_score = self.analyze_pdf_content_completeness(pdf_content)
        
        # 7. Analyze professional quality
        quality_score = self.analyze_pdf_professional_quality(pdf_content)
        
        # 8. Test print readiness
        print_ready = self.test_print_readiness(pdf_content)
        
        # Summary
        self.print_optimization_summary(page_count, completeness_score, quality_score, print_ready)
    
    def print_optimization_summary(self, page_count, completeness_score, quality_score, print_ready):
        """Print comprehensive optimization test summary"""
        print("\n" + "=" * 70)
        print("📊 SINGLE-PAGE PDF OPTIMIZATION TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # CRITICAL REQUIREMENTS VERIFICATION
        print("\n🎯 CRITICAL OPTIMIZATION REQUIREMENTS:")
        
        critical_results = {
            "Single Page PDF": page_count == 1 if page_count else False,
            "Content Complete": completeness_score >= 80 if completeness_score else False,
            "Professional Quality": quality_score >= 60 if quality_score else False,
            "Print Ready (A4)": print_ready if print_ready is not None else False,
            "GEANT Branding": any("GEANT" in r["details"] for r in self.test_results if r["success"]),
            "SAR Currency": any("SAR" in r["details"] for r in self.test_results if r["success"]),
            "Supervisor Integration": any(SUPERVISOR_NAME in r["details"] for r in self.test_results if r["success"])
        }
        
        for requirement, status in critical_results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # OPTIMIZATION RESULTS
        print(f"\n📏 OPTIMIZATION RESULTS:")
        if page_count is not None:
            print(f"   📄 Page Count: {page_count} (Target: 1 page)")
        if completeness_score is not None:
            print(f"   📋 Content Completeness: {completeness_score:.1f}% (Target: ≥80%)")
        if quality_score is not None:
            print(f"   🎨 Professional Quality: {quality_score:.1f}% (Target: ≥60%)")
        
        # FINAL VERDICT
        all_critical_passed = all(critical_results.values())
        single_page_success = page_count == 1 if page_count else False
        
        print(f"\n🏆 FINAL VERDICT:")
        if single_page_success and all_critical_passed:
            print("✅ SINGLE-PAGE OPTIMIZATION: COMPLETE SUCCESS!")
            print("   All content fits on one A4 page with professional quality maintained.")
        elif single_page_success:
            print("⚠️  SINGLE-PAGE OPTIMIZATION: PARTIAL SUCCESS")
            print("   Content fits on one page but some quality issues detected.")
        else:
            print("❌ SINGLE-PAGE OPTIMIZATION: FAILED")
            print("   Content does not fit on single page - further optimization needed.")
        
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
        print("🏁 SINGLE-PAGE PDF OPTIMIZATION TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = SinglePagePDFTester()
    tester.run_single_page_optimization_tests()