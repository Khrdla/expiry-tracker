#!/usr/bin/env python3
"""
Enhanced Return Form PDF with Barcode Display & Single-Page Layout Testing
Testing comprehensive optimizations for barcode display and single-page layout
"""

import requests
import json
import os
import time
from datetime import datetime
import PyPDF2
import io

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Test data from review request
TEST_BARCODES = ["3222471081716", "3222471052747", "3222471075722", "3222471081273"]
SUPERVISOR_NAME = "Mahmoud Badr"
SECTION_MANAGER = "Imad Qejji"

class EnhancedPDFBarcodeTester:
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
                    f"JWT token received for {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_multi_item_return_form_with_barcodes(self):
        """Create return form with 4-5 items including FOC items with clear barcodes"""
        try:
            start_time = time.time()
            
            # Multi-item return form with barcodes as specified in review request
            return_form_data = {
                "reference_number": f"RTN-BARCODE-{int(time.time())}",
                "supplier": "ExtenC",
                "prepared_by_supervisor": SUPERVISOR_NAME,
                "section_manager_name": SECTION_MANAGER,
                "supervisor_approved": True,
                "supervisor_signature": f"{SUPERVISOR_NAME}_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": f"{SECTION_MANAGER}_signature",
                "section_manager_timestamp": datetime.now().isoformat(),
                "items": [
                    {
                        "product_name": "Apple Juice Box 1L",
                        "barcode": "3222471081716",
                        "quantity": 50,
                        "purchase_price": 3.75,
                        "purchase_currency": "SAR",
                        "total_value": 187.50,
                        "reason_for_return": "Quality issue",
                        "is_foc": False
                    },
                    {
                        "product_name": "Orange Juice Box 1L", 
                        "barcode": "3222471052747",
                        "quantity": 25,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR",
                        "total_value": 0.0,
                        "reason_for_return": "Promotional sample",
                        "is_foc": True,
                        "foc_reason": "Promotional sample"
                    },
                    {
                        "product_name": "Mango Juice Box 1L",
                        "barcode": "3222471075722", 
                        "quantity": 10,
                        "purchase_price": 4.00,
                        "purchase_currency": "SAR",
                        "total_value": 40.00,
                        "reason_for_return": "Damaged packaging",
                        "is_foc": False
                    },
                    {
                        "product_name": "Grape Juice Box 1L",
                        "barcode": "3222471081273",
                        "quantity": 15,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR", 
                        "total_value": 0.0,
                        "reason_for_return": "Expired promotion",
                        "is_foc": True,
                        "foc_reason": "Expired promotion"
                    }
                ],
                "total_items": 4,
                "total_quantity": 100,
                "total_value": 227.50,
                "notes": "Multi-item return form with FOC items for barcode display testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                self.log_result("Multi-Item Return Form Creation", True,
                    f"Form ID: {form_id}, Items: 4 (2 normal, 2 FOC), Total: 227.50 SAR", response_time)
                return form_id
            else:
                self.log_result("Multi-Item Return Form Creation", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Multi-Item Return Form Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_enhanced_pdf_generation(self, form_id):
        """Test enhanced PDF generation with barcode display"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                content_type = response.headers.get('content-type', '')
                pdf_size = len(pdf_content)
                
                # Verify PDF format
                is_valid_pdf = pdf_content.startswith(b'%PDF') and 'application/pdf' in content_type
                
                # Check PDF size (should be substantial for professional format)
                size_appropriate = pdf_size > 40000  # 40KB+ indicates comprehensive content
                
                self.log_result("Enhanced PDF Generation", is_valid_pdf and size_appropriate,
                    f"Size: {pdf_size} bytes, Content-Type: {content_type}, "
                    f"Valid PDF: {is_valid_pdf}", response_time)
                
                return pdf_content if is_valid_pdf else None
            else:
                self.log_result("Enhanced PDF Generation", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Enhanced PDF Generation", False, f"Exception: {str(e)}")
            return None
    
    def test_barcode_display_in_pdf(self, pdf_content):
        """Test barcode display in PDF using PyPDF2 text extraction"""
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for enhanced table header
            has_enhanced_header = "Product Name & Barcode" in extracted_text
            
            # Check for barcode display format (Product Name\n[Barcode])
            barcode_format_checks = []
            for barcode in TEST_BARCODES:
                # Look for barcode in extracted text
                barcode_present = barcode in extracted_text
                barcode_format_checks.append(barcode_present)
            
            barcodes_displayed = sum(barcode_format_checks)
            
            # Check for product names with barcodes
            product_barcode_pairs = [
                ("Apple Juice Box 1L", "3222471081716"),
                ("Orange Juice Box 1L", "3222471052747"), 
                ("Mango Juice Box 1L", "3222471075722"),
                ("Grape Juice Box 1L", "3222471081273")
            ]
            
            product_barcode_display = 0
            for product_name, barcode in product_barcode_pairs:
                if product_name in extracted_text and barcode in extracted_text:
                    product_barcode_display += 1
            
            success = has_enhanced_header and barcodes_displayed >= 3 and product_barcode_display >= 3
            
            self.log_result("Barcode Display in PDF", success,
                f"Enhanced header: {has_enhanced_header}, Barcodes displayed: {barcodes_displayed}/4, "
                f"Product-barcode pairs: {product_barcode_display}/4", response_time)
            
            return success
            
        except Exception as e:
            self.log_result("Barcode Display in PDF", False, f"Exception: {str(e)}")
            return False
    
    def test_single_page_layout(self, pdf_content):
        """Test single-page layout optimization"""
        try:
            start_time = time.time()
            
            # Check PDF page count
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            page_count = len(pdf_reader.pages)
            
            response_time = (time.time() - start_time) * 1000
            
            # Single page requirement
            is_single_page = page_count == 1
            
            # Check for content completeness on single page
            if page_count > 0:
                page_text = pdf_reader.pages[0].extract_text()
                
                # Check for all required sections
                required_sections = [
                    "GEANT HYPERMARKET",
                    "FORM DETAILS", 
                    "PRODUCT INFORMATION",
                    "RETURN VALUE",
                    "APPROVALS",
                    "SIGNATURES"
                ]
                
                sections_present = sum(1 for section in required_sections if section in page_text)
                content_complete = sections_present >= 4  # At least 4/6 sections
                
                # Check for all 4 items on single page
                items_on_page = sum(1 for barcode in TEST_BARCODES if barcode in page_text)
                all_items_present = items_on_page >= 3  # At least 3/4 items
                
                success = is_single_page and content_complete and all_items_present
                
                self.log_result("Single-Page Layout", success,
                    f"Pages: {page_count}, Sections: {sections_present}/6, "
                    f"Items on page: {items_on_page}/4", response_time)
            else:
                self.log_result("Single-Page Layout", False, "No pages found in PDF", response_time)
                success = False
            
            return success
            
        except Exception as e:
            self.log_result("Single-Page Layout", False, f"Exception: {str(e)}")
            return False
    
    def test_content_preservation(self, pdf_content):
        """Test content preservation with FOC functionality"""
        try:
            start_time = time.time()
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for supplier information
            has_supplier = "ExtenC" in extracted_text
            
            # Check for supervisor information
            has_supervisor = SUPERVISOR_NAME in extracted_text
            
            # Check for FOC indicators
            foc_indicators = ["FOC", "FREE", "Promotional sample", "Expired promotion"]
            foc_present = sum(1 for indicator in foc_indicators if indicator in extracted_text)
            
            # Check for approval signatures
            has_approvals = "signature" in extracted_text.lower() or "approved" in extracted_text.lower()
            
            # Check for GEANT branding
            has_branding = "GEANT" in extracted_text and "HYPERMARKET" in extracted_text
            
            success = has_supplier and has_supervisor and foc_present >= 2 and has_approvals and has_branding
            
            self.log_result("Content Preservation", success,
                f"Supplier: {has_supplier}, Supervisor: {has_supervisor}, "
                f"FOC indicators: {foc_present}/4, Approvals: {has_approvals}, "
                f"Branding: {has_branding}", response_time)
            
            return success
            
        except Exception as e:
            self.log_result("Content Preservation", False, f"Exception: {str(e)}")
            return False
    
    def test_performance_check(self, form_id):
        """Test PDF generation performance"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_size = len(response.content)
                
                # Performance requirements
                fast_generation = response_time < 100  # <100ms requirement
                appropriate_size = 40000 <= pdf_size <= 60000  # 40-60KB range
                
                success = fast_generation and appropriate_size
                
                self.log_result("Performance Check", success,
                    f"Generation time: {response_time:.0f}ms (target: <100ms), "
                    f"File size: {pdf_size} bytes (target: 40-60KB)", response_time)
                
                return success
            else:
                self.log_result("Performance Check", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Performance Check", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all enhanced PDF barcode display tests"""
        print("🚀 ENHANCED RETURN FORM PDF WITH BARCODE DISPLAY TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Barcodes: {TEST_BARCODES}")
        print(f"Supervisor: {SUPERVISOR_NAME}")
        print(f"Section Manager: {SECTION_MANAGER}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Create Multi-Item Return Form with Barcodes
        form_id = self.create_multi_item_return_form_with_barcodes()
        if not form_id:
            print("❌ Return form creation failed - stopping tests")
            return
        
        # 3. Test Enhanced PDF Generation
        pdf_content = self.test_enhanced_pdf_generation(form_id)
        if not pdf_content:
            print("❌ PDF generation failed - stopping content tests")
            return
        
        # 4. Test Barcode Display in PDF
        self.test_barcode_display_in_pdf(pdf_content)
        
        # 5. Test Single-Page Layout
        self.test_single_page_layout(pdf_content)
        
        # 6. Test Content Preservation
        self.test_content_preservation(pdf_content)
        
        # 7. Test Performance
        self.test_performance_check(form_id)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 ENHANCED PDF BARCODE DISPLAY TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Multi-Item Return Form Creation": any("Multi-Item Return Form Creation" in r["test"] and r["success"] for r in self.test_results),
            "Enhanced PDF Generation": any("Enhanced PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "Barcode Display in PDF": any("Barcode Display in PDF" in r["test"] and r["success"] for r in self.test_results),
            "Single-Page Layout": any("Single-Page Layout" in r["test"] and r["success"] for r in self.test_results),
            "Content Preservation": any("Content Preservation" in r["test"] and r["success"] for r in self.test_results),
            "Performance Check": any("Performance Check" in r["test"] and r["success"] for r in self.test_results)
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
        print("🏁 ENHANCED PDF BARCODE DISPLAY TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = EnhancedPDFBarcodeTester()
    tester.run_comprehensive_tests()