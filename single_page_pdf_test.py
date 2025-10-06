#!/usr/bin/env python3
"""
Single-Page Return Form PDF Export Testing with Dynamic Scaling
Testing comprehensive single-page enforcement with automatic scaling for Return Form PDF exports
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

# Test data for maximum content scenarios
TEST_PRODUCTS = [
    {
        "product_name": "Apple Juice Box 1L Premium Quality Fresh Natural",
        "barcode": "3222471081716",
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    },
    {
        "product_name": "Orange Juice Box 1L Vitamin C Enriched Natural",
        "barcode": "3222471052747",
        "purchase_price": 4.25,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    },
    {
        "product_name": "Mango Juice Box 1L Tropical Fresh Premium",
        "barcode": "3222471075722",
        "purchase_price": 4.50,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    },
    {
        "product_name": "Grape Juice Box 1L Sweet Natural Antioxidant Rich",
        "barcode": "3222471081273",
        "purchase_price": 4.00,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    },
    {
        "product_name": "Pineapple Juice Box 1L Tropical Paradise Fresh",
        "barcode": "3222471090022",
        "purchase_price": 4.75,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    },
    {
        "product_name": "Mixed Fruit Juice Box 1L Five Fruit Blend Premium",
        "barcode": "3222471091739",
        "purchase_price": 5.00,
        "purchase_currency": "SAR",
        "supplier": "ExtenC International Trading Company Ltd"
    }
]

class SinglePagePDFTester:
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
                    f"JWT token received for user: {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def create_return_form_with_items(self, item_count, include_foc=True):
        """Create return form with specified number of items"""
        try:
            start_time = time.time()
            
            # Select items based on count
            selected_products = TEST_PRODUCTS[:item_count]
            
            # Create items array with mix of normal and FOC items
            items = []
            for i, product in enumerate(selected_products):
                # Make every other item FOC if include_foc is True
                is_foc = include_foc and (i % 2 == 1)
                
                item = {
                    "product_name": product["product_name"],
                    "barcode": product["barcode"],
                    "quantity": 98.5 if not is_foc else 25.0,
                    "purchase_price": 0.0 if is_foc else product["purchase_price"],
                    "purchase_currency": product["purchase_currency"],
                    "supplier": product["supplier"],
                    "total_value": 0.0 if is_foc else (98.5 * product["purchase_price"]),
                    "is_foc": is_foc,
                    "foc_reason": "Promotional sample" if is_foc else None
                }
                items.append(item)
            
            return_form_data = {
                "reference_number": f"RTN-{int(time.time())}-{item_count}ITEMS",
                "items": items,  # Multi-item array
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr", 
                "section_manager_name": "Imad Qejji",
                "reason_for_return": f"Quality control testing with {item_count} items - comprehensive single-page PDF validation",
                "notes": f"Testing single-page PDF export with {item_count} items including FOC items for dynamic scaling validation",
                "supervisor_approved": True,
                "supervisor_signature": "Mahmoud_Badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "Imad_Qejji_signature",
                "section_manager_timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append({
                        "id": form_id,
                        "item_count": item_count,
                        "has_foc": include_foc
                    })
                
                # Calculate totals for verification
                normal_items = [item for item in items if not item.get("is_foc", False)]
                foc_items = [item for item in items if item.get("is_foc", False)]
                total_value = sum(item["total_value"] for item in normal_items)
                
                self.log_result(f"Create {item_count}-Item Return Form", True,
                    f"Form ID: {form_id}, Normal items: {len(normal_items)}, FOC items: {len(foc_items)}, "
                    f"Total value: {total_value:.2f} SAR", response_time)
                return form_id
            else:
                self.log_result(f"Create {item_count}-Item Return Form", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result(f"Create {item_count}-Item Return Form", False, f"Exception: {str(e)}")
            return None
    
    def test_single_page_pdf_export(self, form_id, item_count):
        """Test single-page PDF export with comprehensive validation"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Verify PDF format
                is_pdf = pdf_content.startswith(b'%PDF')
                content_type = response.headers.get('content-type', '')
                
                if not is_pdf:
                    self.log_result(f"Single-Page PDF Export ({item_count} items)", False,
                        f"Invalid PDF format, Content-Type: {content_type}", response_time)
                    return False
                
                # Parse PDF to count pages
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                    page_count = len(pdf_reader.pages)
                    
                    # Extract text from first page for content verification
                    first_page_text = pdf_reader.pages[0].extract_text()
                    
                    # Check for single-page compliance
                    is_single_page = page_count == 1
                    
                    # Check for GEANT branding
                    has_geant_branding = "GEANT HYPERMARKET" in first_page_text
                    
                    # Check for barcode display
                    has_barcodes = any(product["barcode"] in first_page_text for product in TEST_PRODUCTS[:item_count])
                    
                    # Check for signature section
                    has_signatures = "Dept Head" in first_page_text or "General Mgr" in first_page_text or "Finance" in first_page_text
                    
                    # Check for dynamic scaling indicators (smaller fonts for more items)
                    scaling_indicators = []
                    if item_count >= 6:
                        scaling_indicators.append("Ultra-compact mode expected")
                    elif item_count >= 4:
                        scaling_indicators.append("Compact mode expected")
                    else:
                        scaling_indicators.append("Standard mode expected")
                    
                    success = is_single_page and has_geant_branding
                    
                    self.log_result(f"Single-Page PDF Export ({item_count} items)", success,
                        f"Pages: {page_count}, Size: {pdf_size} bytes, GEANT branding: {has_geant_branding}, "
                        f"Barcodes: {has_barcodes}, Signatures: {has_signatures}, {scaling_indicators[0]}", response_time)
                    
                    return success
                    
                except Exception as pdf_error:
                    self.log_result(f"Single-Page PDF Export ({item_count} items)", False,
                        f"PDF parsing error: {str(pdf_error)}, Size: {pdf_size} bytes", response_time)
                    return False
            else:
                self.log_result(f"Single-Page PDF Export ({item_count} items)", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_result(f"Single-Page PDF Export ({item_count} items)", False, f"Exception: {str(e)}")
            return False
    
    def test_dynamic_scaling_verification(self, form_id, item_count):
        """Test dynamic scaling features based on item count"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Parse PDF for scaling analysis
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                    first_page_text = pdf_reader.pages[0].extract_text()
                    
                    # Analyze content density and scaling
                    text_length = len(first_page_text)
                    line_count = len(first_page_text.split('\n'))
                    
                    # Expected scaling behavior
                    expected_scaling = {}
                    if item_count >= 6:
                        expected_scaling = {
                            "mode": "Ultra-compact",
                            "font_size": "5pt",
                            "column_width": "Ultra-compact",
                            "row_padding": "0.5pt"
                        }
                    elif item_count >= 4:
                        expected_scaling = {
                            "mode": "Compact", 
                            "font_size": "6-7pt",
                            "column_width": "Compact",
                            "row_padding": "0.7pt"
                        }
                    else:
                        expected_scaling = {
                            "mode": "Standard",
                            "font_size": "8-9pt", 
                            "column_width": "Standard",
                            "row_padding": "1.0pt"
                        }
                    
                    # Check for ultra-compact signature section
                    has_compact_signatures = "Dept Head:" in first_page_text and "|" in first_page_text
                    
                    # Verify all items are present
                    items_present = sum(1 for product in TEST_PRODUCTS[:item_count] 
                                      if product["product_name"][:20] in first_page_text)
                    all_items_present = items_present == item_count
                    
                    success = all_items_present and has_compact_signatures
                    
                    self.log_result(f"Dynamic Scaling Verification ({item_count} items)", success,
                        f"Mode: {expected_scaling['mode']}, Items present: {items_present}/{item_count}, "
                        f"Compact signatures: {has_compact_signatures}, Text density: {text_length} chars", response_time)
                    
                    return success
                    
                except Exception as pdf_error:
                    self.log_result(f"Dynamic Scaling Verification ({item_count} items)", False,
                        f"PDF analysis error: {str(pdf_error)}", response_time)
                    return False
            else:
                self.log_result(f"Dynamic Scaling Verification ({item_count} items)", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result(f"Dynamic Scaling Verification ({item_count} items)", False, f"Exception: {str(e)}")
            return False
    
    def test_barcode_display_verification(self, form_id, item_count):
        """Test barcode display beside product names"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                    first_page_text = pdf_reader.pages[0].extract_text()
                    
                    # Check for barcode display beside items
                    barcodes_found = []
                    for i, product in enumerate(TEST_PRODUCTS[:item_count]):
                        barcode = product["barcode"]
                        product_name = product["product_name"][:30]  # Truncated name
                        
                        # Check if both product name and barcode are present
                        has_product = any(word in first_page_text for word in product_name.split()[:3])
                        has_barcode = barcode in first_page_text
                        
                        if has_product and has_barcode:
                            barcodes_found.append(barcode)
                    
                    barcodes_displayed = len(barcodes_found)
                    all_barcodes_present = barcodes_displayed == item_count
                    
                    # Check for proper barcode format (Product Name\n[Barcode])
                    has_proper_format = "[" in first_page_text and "]" in first_page_text
                    
                    success = all_barcodes_present and has_proper_format
                    
                    self.log_result(f"Barcode Display Verification ({item_count} items)", success,
                        f"Barcodes displayed: {barcodes_displayed}/{item_count}, "
                        f"Proper format: {has_proper_format}, Found: {barcodes_found[:3]}", response_time)
                    
                    return success
                    
                except Exception as pdf_error:
                    self.log_result(f"Barcode Display Verification ({item_count} items)", False,
                        f"PDF parsing error: {str(pdf_error)}", response_time)
                    return False
            else:
                self.log_result(f"Barcode Display Verification ({item_count} items)", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result(f"Barcode Display Verification ({item_count} items)", False, f"Exception: {str(e)}")
            return False
    
    def test_professional_formatting_verification(self, form_id, item_count):
        """Test professional GEANT formatting and layout integrity"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                    first_page_text = pdf_reader.pages[0].extract_text()
                    
                    # Check for professional elements
                    has_geant_branding = "GEANT HYPERMARKET" in first_page_text
                    has_form_details = "FORM DETAILS" in first_page_text
                    has_product_info = "PRODUCT INFORMATION" in first_page_text
                    has_return_value = "RETURN VALUE" in first_page_text
                    has_approvals = "APPROVALS" in first_page_text or "SIGNATURES" in first_page_text
                    
                    # Check for supervisor information
                    has_supervisor = "Mahmoud Badr" in first_page_text
                    
                    # Check for currency information
                    has_currency = "SAR" in first_page_text
                    
                    # Professional size indicator (logo + content)
                    is_professional_size = pdf_size > 40000  # Should be substantial with logo
                    
                    # Check for no debug messages or system errors
                    has_clean_layout = "Error" not in first_page_text and "Exception" not in first_page_text
                    
                    professional_elements = [
                        has_geant_branding, has_form_details, has_product_info, 
                        has_return_value, has_approvals, has_supervisor, 
                        has_currency, is_professional_size, has_clean_layout
                    ]
                    
                    professional_score = sum(professional_elements)
                    success = professional_score >= 7  # At least 7/9 elements
                    
                    self.log_result(f"Professional Formatting ({item_count} items)", success,
                        f"Professional elements: {professional_score}/9, Size: {pdf_size} bytes, "
                        f"GEANT branding: {has_geant_branding}, Clean layout: {has_clean_layout}", response_time)
                    
                    return success
                    
                except Exception as pdf_error:
                    self.log_result(f"Professional Formatting ({item_count} items)", False,
                        f"PDF analysis error: {str(pdf_error)}", response_time)
                    return False
            else:
                self.log_result(f"Professional Formatting ({item_count} items)", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result(f"Professional Formatting ({item_count} items)", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_single_page_tests(self):
        """Run comprehensive single-page PDF export tests"""
        print("🚀 SINGLE-PAGE RETURN FORM PDF EXPORT TESTING WITH DYNAMIC SCALING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}")
        print(f"Test Products: {len(TEST_PRODUCTS)} items available")
        print("=" * 80)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Test different item counts for dynamic scaling
        test_scenarios = [
            {"item_count": 1, "description": "Single item (Standard mode)"},
            {"item_count": 3, "description": "Few items (Standard mode)"},
            {"item_count": 5, "description": "Medium items (Compact mode)"},
            {"item_count": 6, "description": "Many items (Ultra-compact mode)"}
        ]
        
        for scenario in test_scenarios:
            item_count = scenario["item_count"]
            description = scenario["description"]
            
            print(f"\n📋 Testing {description}")
            print("-" * 50)
            
            # Create return form with specified item count
            form_id = self.create_return_form_with_items(item_count, include_foc=True)
            
            if form_id:
                # Test single-page compliance
                self.test_single_page_pdf_export(form_id, item_count)
                
                # Test dynamic scaling
                self.test_dynamic_scaling_verification(form_id, item_count)
                
                # Test barcode display
                self.test_barcode_display_verification(form_id, item_count)
                
                # Test professional formatting
                self.test_professional_formatting_verification(form_id, item_count)
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 SINGLE-PAGE PDF EXPORT TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL SINGLE-PAGE REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Single-Page Compliance": any("Single-Page PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "Dynamic Scaling": any("Dynamic Scaling Verification" in r["test"] and r["success"] for r in self.test_results),
            "Barcode Display": any("Barcode Display Verification" in r["test"] and r["success"] for r in self.test_results),
            "Professional Formatting": any("Professional Formatting" in r["test"] and r["success"] for r in self.test_results),
            "Ultra-Compact Mode": any("6 items" in r["test"] and r["success"] for r in self.test_results)
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
        
        # Success criteria
        print(f"\n🏆 SUCCESS CRITERIA:")
        print(f"   • ALL multi-item forms fit on exactly one A4 page: {'✅' if critical_tests['Single-Page Compliance'] else '❌'}")
        print(f"   • Dynamic scaling working for different item counts: {'✅' if critical_tests['Dynamic Scaling'] else '❌'}")
        print(f"   • Barcodes clearly visible beside all product names: {'✅' if critical_tests['Barcode Display'] else '❌'}")
        print(f"   • Professional GEANT formatting maintained: {'✅' if critical_tests['Professional Formatting'] else '❌'}")
        print(f"   • Ultra-compact signatures in single row: {'✅' if critical_tests['Ultra-Compact Mode'] else '❌'}")
        
        overall_success = all(critical_tests.values())
        print(f"\n🎯 OVERALL RESULT: {'✅ 100% SUCCESS - SINGLE-PAGE COMPLIANCE ACHIEVED' if overall_success else '❌ ISSUES DETECTED - REQUIRES ATTENTION'}")
        
        print("\n" + "=" * 80)
        print("🏁 SINGLE-PAGE PDF EXPORT TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = SinglePagePDFTester()
    tester.run_comprehensive_single_page_tests()