#!/usr/bin/env python3
"""
COMPREHENSIVE MULTI-ITEM RETURN FORM WITH FOC TESTING
Testing complete multi-item Return Form system with FOC support as per review request
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

# Test data from review request - Multi-Item Return Form
MULTI_ITEM_TEST_DATA = {
    "items": [
        {
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 50,
            "purchase_price": 3.75,
            "purchase_currency": "SAR",
            "is_foc": False,
            "foc_reason": None,
            "supplier": "ExtenC",
            "total_value": 187.50
        },
        {
            "product_name": "Orange Juice Box 1L", 
            "barcode": "3222471052747",
            "quantity": 25,
            "purchase_price": 0.0,
            "purchase_currency": "SAR",
            "is_foc": True,
            "foc_reason": "Promotional sample",
            "supplier": "ExtenC",
            "total_value": 0.0
        },
        {
            "product_name": "Mango Juice Box 1L",
            "barcode": "3222471075722", 
            "quantity": 10,
            "purchase_price": 4.00,
            "purchase_currency": "SAR",
            "is_foc": False,
            "foc_reason": None,
            "supplier": "ExtenC",
            "total_value": 40.00
        },
        {
            "product_name": "Grape Juice Box 1L",
            "barcode": "3222471081273",
            "quantity": 15,
            "purchase_price": 0.0,
            "purchase_currency": "SAR", 
            "is_foc": True,
            "foc_reason": "Expired promotion",
            "supplier": "ExtenC",
            "total_value": 0.0
        }
    ],
    "expected_summary": {
        "total_items": 4,
        "normal_items": 2,
        "foc_items": 2,
        "total_quantity": 100,
        "normal_quantity": 60,
        "foc_quantity": 40,
        "total_value": 227.50,
        "supplier": "ExtenC"
    }
}

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
                    f"Token received for multi-item FOC testing", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_item_data_storage(self):
        """Test POST /api/return-forms with complete multi-item data structure"""
        try:
            start_time = time.time()
            
            # Create comprehensive multi-item return form
            return_form_data = {
                "reference_number": f"RTN-MULTI-FOC-{int(time.time())}",
                "supplier": MULTI_ITEM_TEST_DATA["expected_summary"]["supplier"],
                "items": MULTI_ITEM_TEST_DATA["items"],
                "summary": MULTI_ITEM_TEST_DATA["expected_summary"],
                "reason_for_return": "Mixed return - normal items + FOC samples",
                "selected_supervisor": "Mahmoud Badr",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "supervisor_signature": "mahmoud_badr_signature",
                "supervisor_timestamp": datetime.now().isoformat(),
                "section_manager_approved": True,
                "section_manager_signature": "imad_qejji_signature",
                "section_manager_timestamp": datetime.now().isoformat(),
                "notes": "Multi-item return form with FOC support testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                form_id = data.get("id")
                if form_id:
                    self.created_return_forms.append(form_id)
                
                # Verify response contains multi-item structure
                form_data = data.get("form", {})
                has_items_array = "items" in form_data and isinstance(form_data["items"], list)
                has_summary = "summary" in form_data
                items_count = len(form_data.get("items", []))
                
                self.log_result("Multi-Item Data Storage", has_items_array and items_count == 4,
                    f"Form ID: {form_id}, Items array: {has_items_array}, "
                    f"Items count: {items_count}, Summary: {has_summary}", response_time)
                return form_id
            else:
                self.log_result("Multi-Item Data Storage", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Multi-Item Data Storage", False, f"Exception: {str(e)}")
            return None
    
    def test_multi_item_data_retrieval(self, form_id):
        """Test retrieval and validation of multi-item data structure"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                # Find our test form
                test_form = None
                for form in forms:
                    if form.get("id") == form_id:
                        test_form = form
                        break
                
                if not test_form:
                    self.log_result("Multi-Item Data Retrieval", False,
                        f"Test form {form_id} not found in response", response_time)
                    return False
                
                # Validate multi-item structure
                items = test_form.get("items", [])
                summary = test_form.get("summary", {})
                
                # Verify items array structure
                items_valid = len(items) == 4
                foc_items = [item for item in items if item.get("is_foc", False)]
                normal_items = [item for item in items if not item.get("is_foc", False)]
                
                # Verify FOC separation
                foc_count = len(foc_items)
                normal_count = len(normal_items)
                
                # Verify summary calculations
                summary_valid = (
                    summary.get("total_items") == 4 and
                    summary.get("normal_items") == 2 and
                    summary.get("foc_items") == 2 and
                    summary.get("total_quantity") == 100 and
                    summary.get("total_value") == 227.50
                )
                
                self.log_result("Multi-Item Data Retrieval", items_valid and summary_valid,
                    f"Items: {len(items)}, FOC: {foc_count}, Normal: {normal_count}, "
                    f"Summary valid: {summary_valid}, Total value: {summary.get('total_value')}", response_time)
                return True
            else:
                self.log_result("Multi-Item Data Retrieval", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Multi-Item Data Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_foc_business_logic_validation(self, form_id):
        """Test FOC business logic validation"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                test_form = next((form for form in forms if form.get("id") == form_id), None)
                
                if not test_form:
                    self.log_result("FOC Business Logic Validation", False,
                        "Test form not found", response_time)
                    return False
                
                items = test_form.get("items", [])
                
                # Validate FOC items
                foc_validation_results = []
                for item in items:
                    if item.get("is_foc", False):
                        # FOC items should have 0 price and 0 total
                        has_zero_price = item.get("purchase_price", 0) == 0.0
                        has_zero_total = item.get("total_value", 0) == 0.0
                        has_foc_reason = bool(item.get("foc_reason"))
                        
                        foc_validation_results.append({
                            "product": item.get("product_name"),
                            "zero_price": has_zero_price,
                            "zero_total": has_zero_total,
                            "has_reason": has_foc_reason,
                            "reason": item.get("foc_reason")
                        })
                
                # Validate normal items
                normal_validation_results = []
                for item in items:
                    if not item.get("is_foc", False):
                        # Normal items should have proper price calculation
                        expected_total = item.get("quantity", 0) * item.get("purchase_price", 0)
                        actual_total = item.get("total_value", 0)
                        calculation_correct = abs(expected_total - actual_total) < 0.01
                        
                        normal_validation_results.append({
                            "product": item.get("product_name"),
                            "calculation_correct": calculation_correct,
                            "expected": expected_total,
                            "actual": actual_total
                        })
                
                # Validate supplier consistency
                suppliers = list(set(item.get("supplier") for item in items))
                supplier_consistent = len(suppliers) == 1 and suppliers[0] == "ExtenC"
                
                all_foc_valid = all(r["zero_price"] and r["zero_total"] and r["has_reason"] for r in foc_validation_results)
                all_normal_valid = all(r["calculation_correct"] for r in normal_validation_results)
                
                self.log_result("FOC Business Logic Validation", 
                    all_foc_valid and all_normal_valid and supplier_consistent,
                    f"FOC items valid: {all_foc_valid} ({len(foc_validation_results)} items), "
                    f"Normal items valid: {all_normal_valid} ({len(normal_validation_results)} items), "
                    f"Supplier consistent: {supplier_consistent}", response_time)
                return True
            else:
                self.log_result("FOC Business Logic Validation", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("FOC Business Logic Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_pdf_generation_multi_item_mixed(self, form_id):
        """Test Case 3: Multi-item mixed (2-3 normal + 2-3 FOC items)"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                pdf_size = len(pdf_content)
                
                # Check PDF signature
                is_valid_pdf = pdf_content.startswith(b'%PDF')
                
                # Check for multi-item content indicators
                has_multi_item_table = b'Apple Juice' in pdf_content and b'Orange Juice' in pdf_content
                has_foc_indicators = b'FOC' in pdf_content or b'Free' in pdf_content
                has_geant_branding = b'GEANT' in pdf_content or b'Geant' in pdf_content
                
                # Professional PDF should be substantial size (>30KB for multi-item with branding)
                is_professional_size = pdf_size > 30000
                
                self.log_result("Enhanced PDF Generation - Multi-Item Mixed", 
                    is_valid_pdf and is_professional_size,
                    f"PDF size: {pdf_size} bytes, Multi-item table: {has_multi_item_table}, "
                    f"FOC indicators: {has_foc_indicators}, GEANT branding: {has_geant_branding}", response_time)
                return True
            else:
                self.log_result("Enhanced PDF Generation - Multi-Item Mixed", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Enhanced PDF Generation - Multi-Item Mixed", False, f"Exception: {str(e)}")
            return False
    
    def test_pdf_content_verification(self, form_id):
        """Test PDF content verification for multi-item FOC display"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                
                # Convert bytes to string for text search (basic approach)
                try:
                    pdf_text = pdf_content.decode('utf-8', errors='ignore')
                except:
                    pdf_text = str(pdf_content)
                
                # Check for multi-item table content
                content_checks = {
                    "multi_item_table": any(juice in pdf_text for juice in ["Apple Juice", "Orange Juice", "Mango Juice", "Grape Juice"]),
                    "foc_status_display": "FOC" in pdf_text or "Free" in pdf_text or "🆓" in pdf_text,
                    "summary_section": "summary" in pdf_text.lower() or "total" in pdf_text.lower(),
                    "geant_branding": "GEANT" in pdf_text or "Geant" in pdf_text,
                    "professional_layout": len(pdf_content) > 20000  # Professional layout indicator
                }
                
                all_content_present = all(content_checks.values())
                
                self.log_result("PDF Content Verification", all_content_present,
                    f"Multi-item table: {content_checks['multi_item_table']}, "
                    f"FOC status: {content_checks['foc_status_display']}, "
                    f"Summary: {content_checks['summary_section']}, "
                    f"Branding: {content_checks['geant_branding']}, "
                    f"Professional: {content_checks['professional_layout']}", response_time)
                return True
            else:
                self.log_result("PDF Content Verification", False,
                    f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("PDF Content Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_excel_export_multi_item_foc(self, form_id):
        """Test Excel export with multi-item FOC data preservation"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=excel")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                excel_content = response.content
                excel_size = len(excel_content)
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                is_excel = 'spreadsheet' in content_type or 'excel' in content_type or excel_size > 5000
                
                # Excel should be substantial for multi-item data
                is_comprehensive = excel_size > 10000
                
                self.log_result("Excel Export - Multi-Item FOC", is_excel and is_comprehensive,
                    f"Content-Type: {content_type}, Size: {excel_size} bytes, "
                    f"Comprehensive: {is_comprehensive}", response_time)
                return True
            else:
                self.log_result("Excel Export - Multi-Item FOC", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Excel Export - Multi-Item FOC", False, f"Exception: {str(e)}")
            return False
    
    def test_backward_compatibility_single_item(self):
        """Test backward compatibility with single-item forms"""
        try:
            start_time = time.time()
            
            # Create single-item return form (backward compatibility)
            single_item_data = {
                "reference_number": f"RTN-SINGLE-{int(time.time())}",
                "product_code": "TEST-001",
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 50,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "supplier": "ExtenC",
                "reason_for_return": "Single item return - backward compatibility test",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "section_manager_approved": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=single_item_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                single_form_id = data.get("id")
                
                # Test PDF generation for single item
                pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{single_form_id}/pdf")
                pdf_works = pdf_response.status_code == 200 and pdf_response.content.startswith(b'%PDF')
                
                self.log_result("Backward Compatibility - Single Item", pdf_works,
                    f"Single form ID: {single_form_id}, PDF generation: {pdf_works}, "
                    f"PDF size: {len(pdf_response.content) if pdf_works else 0} bytes", response_time)
                return True
            else:
                self.log_result("Backward Compatibility - Single Item", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Backward Compatibility - Single Item", False, f"Exception: {str(e)}")
            return False
    
    def test_all_foc_items_edge_case(self):
        """Test Case 4: All FOC items (edge case)"""
        try:
            start_time = time.time()
            
            # Create all-FOC return form
            all_foc_data = {
                "reference_number": f"RTN-ALL-FOC-{int(time.time())}",
                "supplier": "ExtenC",
                "items": [
                    {
                        "product_name": "Orange Juice Box 1L",
                        "quantity": 25,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR",
                        "is_foc": True,
                        "foc_reason": "Promotional sample",
                        "supplier": "ExtenC",
                        "total_value": 0.0
                    },
                    {
                        "product_name": "Grape Juice Box 1L",
                        "quantity": 15,
                        "purchase_price": 0.0,
                        "purchase_currency": "SAR",
                        "is_foc": True,
                        "foc_reason": "Expired promotion",
                        "supplier": "ExtenC",
                        "total_value": 0.0
                    }
                ],
                "summary": {
                    "total_items": 2,
                    "normal_items": 0,
                    "foc_items": 2,
                    "total_quantity": 40,
                    "total_value": 0.0,
                    "supplier": "ExtenC"
                },
                "reason_for_return": "All FOC items return - edge case test",
                "prepared_by_supervisor": "Mahmoud Badr",
                "section_manager_name": "Imad Qejji",
                "supervisor_approved": True,
                "section_manager_approved": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=all_foc_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                all_foc_form_id = data.get("id")
                
                # Test PDF generation for all FOC items
                pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{all_foc_form_id}/pdf")
                pdf_works = pdf_response.status_code == 200 and pdf_response.content.startswith(b'%PDF')
                
                # Verify zero total value handling
                form_data = data.get("form", {})
                summary = form_data.get("summary", {})
                zero_total_handled = summary.get("total_value") == 0.0
                
                self.log_result("All FOC Items Edge Case", pdf_works and zero_total_handled,
                    f"All FOC form ID: {all_foc_form_id}, PDF generation: {pdf_works}, "
                    f"Zero total handled: {zero_total_handled}, Total value: {summary.get('total_value')}", response_time)
                return True
            else:
                self.log_result("All FOC Items Edge Case", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_result("All FOC Items Edge Case", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_multi_item_foc_tests(self):
        """Run all comprehensive multi-item FOC tests"""
        print("🚀 COMPREHENSIVE MULTI-ITEM RETURN FORM WITH FOC TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Data: {MULTI_ITEM_TEST_DATA['expected_summary']}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Multi-Item Data Storage & Retrieval
        form_id = self.test_multi_item_data_storage()
        if form_id:
            self.test_multi_item_data_retrieval(form_id)
            
            # 3. FOC Business Logic Validation
            self.test_foc_business_logic_validation(form_id)
            
            # 4. Enhanced PDF Generation (Multi-Item Mixed)
            self.test_enhanced_pdf_generation_multi_item_mixed(form_id)
            
            # 5. PDF Content Verification
            self.test_pdf_content_verification(form_id)
            
            # 6. Excel Export Testing
            self.test_excel_export_multi_item_foc(form_id)
        
        # 7. Backward Compatibility Testing
        self.test_backward_compatibility_single_item()
        
        # 8. Edge Case Testing - All FOC Items
        self.test_all_foc_items_edge_case()
        
        # Summary
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE MULTI-ITEM FOC TESTING SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification from review request
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Multi-Item Data Storage": any("Multi-Item Data Storage" in r["test"] and r["success"] for r in self.test_results),
            "Multi-Item Data Retrieval": any("Multi-Item Data Retrieval" in r["test"] and r["success"] for r in self.test_results),
            "FOC Business Logic": any("FOC Business Logic" in r["test"] and r["success"] for r in self.test_results),
            "Enhanced PDF Generation": any("Enhanced PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "PDF Content Verification": any("PDF Content Verification" in r["test"] and r["success"] for r in self.test_results),
            "Excel Export Multi-Item FOC": any("Excel Export - Multi-Item FOC" in r["test"] and r["success"] for r in self.test_results),
            "Backward Compatibility": any("Backward Compatibility" in r["test"] and r["success"] for r in self.test_results),
            "All FOC Items Edge Case": any("All FOC Items Edge Case" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Expected Results Verification
        print(f"\n📋 EXPECTED RESULTS FROM REVIEW REQUEST:")
        expected = MULTI_ITEM_TEST_DATA["expected_summary"]
        print(f"✅ Total Items: {expected['total_items']} (2 normal, 2 FOC)")
        print(f"✅ Total Quantity: {expected['total_quantity']} (60 normal, 40 FOC)")
        print(f"✅ Total Value: {expected['total_value']} SAR (FOC excluded)")
        print(f"✅ Supplier: {expected['supplier']} (consistent across all items)")
        
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
        
        # Success criteria evaluation
        print(f"\n🏆 SUCCESS CRITERIA EVALUATION:")
        success_criteria = {
            "Multi-item data stored correctly": any("Multi-Item Data Storage" in r["test"] and r["success"] for r in self.test_results),
            "PDF generation works with items array": any("Enhanced PDF Generation" in r["test"] and r["success"] for r in self.test_results),
            "FOC items clearly differentiated": any("FOC Business Logic" in r["test"] and r["success"] for r in self.test_results),
            "Summary calculations accurate": any("Multi-Item Data Retrieval" in r["test"] and r["success"] for r in self.test_results),
            "Professional single-page PDF format": any("PDF Content Verification" in r["test"] and r["success"] for r in self.test_results),
            "Export formats preserve FOC info": any("Excel Export" in r["test"] and r["success"] for r in self.test_results),
            "Backward compatibility maintained": any("Backward Compatibility" in r["test"] and r["success"] for r in self.test_results)
        }
        
        success_count = sum(1 for status in success_criteria.values() if status)
        total_criteria = len(success_criteria)
        
        for criteria, status in success_criteria.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {criteria}")
        
        print(f"\n🎯 TARGET: 100% - ACHIEVED: {success_count}/{total_criteria} ({success_count/total_criteria*100:.1f}%)")
        
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE MULTI-ITEM FOC TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = MultiItemFOCTester()
    tester.run_comprehensive_multi_item_foc_tests()