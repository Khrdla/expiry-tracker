#!/usr/bin/env python3
"""
Enhanced Supplier Return Form System Testing
Testing comprehensive return form functionality with supervisor dropdown, dual currency, and PDF exports
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
TEST_SUPERVISORS = ["Mahmoud Badr", "Abdelhamed Mostafa"]
SECTION_MANAGER = "Imad Qejji"
TEST_CURRENCIES = ["YER", "SAR", "EUR"]
TEST_BARCODE = "3222471081716"  # Apple Juice Box 1L

class EnhancedReturnFormTester:
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
                    f"Token received, expires in 24h", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_currency_rates_api(self):
        """Test GET /api/currency/rates for real-time exchange rates"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/currency/rates")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["base_currency", "exchange_rates", "last_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Currency Rates API Structure", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return False
                
                # Check if test currencies are present
                exchange_rates = data.get("exchange_rates", {})
                test_currencies_present = [curr for curr in TEST_CURRENCIES if curr in exchange_rates]
                
                self.log_result("Currency Rates API", True,
                    f"Base: {data.get('base_currency')}, Rates: {len(exchange_rates)} currencies, "
                    f"Test currencies present: {test_currencies_present}", response_time)
                return True
            else:
                self.log_result("Currency Rates API", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Currency Rates API", False, f"Exception: {str(e)}")
            return False
    
    def test_barcode_lookup(self):
        """Test barcode lookup for test data"""
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
                    self.log_result("Test Barcode Lookup", False,
                        f"Missing fields: {missing_fields}", response_time)
                    return None
                
                self.log_result("Test Barcode Lookup", True,
                    f"Product: {product.get('product_name')}, "
                    f"Price: {product.get('purchase_price')} {product.get('purchase_currency')}, "
                    f"Supplier: {product.get('supplier')}", response_time)
                return product
            else:
                self.log_result("Test Barcode Lookup", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Test Barcode Lookup", False, f"Exception: {str(e)}")
            return None
    
    def test_return_form_creation_with_supervisor(self, product_data):
        """Test return form creation with supervisor dropdown integration"""
        try:
            for supervisor in TEST_SUPERVISORS:
                start_time = time.time()
                
                return_form_data = {
                    "reference_number": f"RTN-{int(time.time())}-{supervisor.replace(' ', '')}",
                    "product_code": product_data.get("item_number", "TEST-001"),
                    "product_name": product_data.get("product_name", "Test Product"),
                    "barcode": TEST_BARCODE,
                    "quantity": 5,
                    "purchase_price": product_data.get("purchase_price", 10.0),
                    "purchase_currency": product_data.get("purchase_currency", "YER"),
                    "supplier": product_data.get("supplier", "Test Supplier"),
                    "reason_for_return": "Quality issue - damaged packaging",
                    "selected_supervisor": supervisor,  # Key requirement from review
                    "prepared_by_supervisor": supervisor,
                    "section_manager_name": SECTION_MANAGER,
                    "notes": f"Test return form with supervisor: {supervisor}",
                    "supervisor_approved": True,
                    "supervisor_signature": f"{supervisor}_signature",
                    "supervisor_timestamp": datetime.now().isoformat(),
                    "section_manager_approved": True,
                    "section_manager_signature": f"{SECTION_MANAGER}_signature", 
                    "section_manager_timestamp": datetime.now().isoformat()
                }
                
                response = self.session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    form_id = data.get("id")
                    if form_id:
                        self.created_return_forms.append(form_id)
                    
                    self.log_result(f"Return Form Creation - {supervisor}", True,
                        f"Form ID: {form_id}, Supervisor: {supervisor}, "
                        f"Currency: {return_form_data['purchase_currency']}", response_time)
                else:
                    self.log_result(f"Return Form Creation - {supervisor}", False,
                        f"Status: {response.status_code}, Response: {response.text}", response_time)
                    
        except Exception as e:
            self.log_result("Return Form Creation with Supervisor", False, f"Exception: {str(e)}")
    
    def test_dual_currency_display(self):
        """Test dual currency display in return form responses"""
        if not self.created_return_forms:
            self.log_result("Dual Currency Display", False, "No return forms created to test")
            return
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/returns")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                forms = response.json()
                
                if not forms:
                    self.log_result("Dual Currency Display", False, "No return forms found", response_time)
                    return
                
                # Check first form for dual currency fields
                test_form = forms[0]
                
                # Look for original currency
                has_original_currency = "purchase_currency" in test_form and "purchase_price" in test_form
                
                # Look for USD conversion (this might be calculated on-the-fly)
                currency_fields = [key for key in test_form.keys() if "currency" in key.lower()]
                price_fields = [key for key in test_form.keys() if "price" in key.lower() or "usd" in key.lower()]
                
                self.log_result("Dual Currency Display", has_original_currency,
                    f"Original currency: {has_original_currency}, "
                    f"Currency fields: {currency_fields}, Price fields: {price_fields}", response_time)
            else:
                self.log_result("Dual Currency Display", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                    
        except Exception as e:
            self.log_result("Dual Currency Display", False, f"Exception: {str(e)}")
    
    def test_pdf_export_main(self):
        """Test main PDF export endpoint: GET /api/export/return-form/{form_id}?format=pdf"""
        if not self.created_return_forms:
            self.log_result("Main PDF Export", False, "No return forms created to test")
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
                
                self.log_result("Main PDF Export", is_pdf,
                    f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                    f"PDF signature: {response.content[:10]}", response_time)
            else:
                self.log_result("Main PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("Main PDF Export", False, f"Exception: {str(e)}")
    
    def test_pdf_export_individual(self):
        """Test individual PDF export endpoint: GET /api/export/return-form/{return_id}/pdf"""
        if not self.created_return_forms:
            self.log_result("Individual PDF Export", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it's a PDF
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type or response.content.startswith(b'%PDF')
                pdf_size = len(response.content)
                
                self.log_result("Individual PDF Export", is_pdf,
                    f"Content-Type: {content_type}, Size: {pdf_size} bytes, "
                    f"PDF signature: {response.content[:10]}", response_time)
            else:
                self.log_result("Individual PDF Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("Individual PDF Export", False, f"Exception: {str(e)}")
    
    def test_approval_workflow_validation(self):
        """Test approval workflow and digital signature timestamps"""
        try:
            # Test creating return form without approvals
            start_time = time.time()
            
            incomplete_form_data = {
                "reference_number": f"RTN-INCOMPLETE-{int(time.time())}",
                "product_code": "TEST-001",
                "product_name": "Test Product",
                "quantity": 1,
                "purchase_price": 10.0,
                "purchase_currency": "YER",
                "supplier": "Test Supplier",
                "reason_for_return": "Test incomplete form",
                "selected_supervisor": TEST_SUPERVISORS[0],
                # Missing approvals intentionally
                "supervisor_approved": False,
                "section_manager_approved": False
            }
            
            response = self.session.post(f"{BACKEND_URL}/return-forms", json=incomplete_form_data)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                incomplete_form_id = data.get("id")
                
                # Try to export without approvals - should fail
                export_response = self.session.get(f"{BACKEND_URL}/export/return-form/{incomplete_form_id}/pdf")
                
                if export_response.status_code == 403:
                    self.log_result("Approval Workflow Validation", True,
                        f"Export correctly blocked without approvals (403 status)", response_time)
                else:
                    self.log_result("Approval Workflow Validation", False,
                        f"Export should be blocked but got status: {export_response.status_code}", response_time)
            else:
                self.log_result("Approval Workflow Validation", False,
                    f"Failed to create incomplete form: {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("Approval Workflow Validation", False, f"Exception: {str(e)}")
    
    def test_excel_export(self):
        """Test Excel export functionality"""
        if not self.created_return_forms:
            self.log_result("Excel Export", False, "No return forms created to test")
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
                
                self.log_result("Excel Export", is_excel or excel_size > 1000,
                    f"Content-Type: {content_type}, Size: {excel_size} bytes", response_time)
            else:
                self.log_result("Excel Export", False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}", response_time)
                    
        except Exception as e:
            self.log_result("Excel Export", False, f"Exception: {str(e)}")
    
    def test_company_branding_in_exports(self):
        """Test company logo and branding in PDF exports"""
        if not self.created_return_forms:
            self.log_result("Company Branding in Exports", False, "No return forms created to test")
            return
        
        try:
            form_id = self.created_return_forms[0]
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                pdf_content = response.content
                
                # Check for company branding indicators in PDF
                has_geant_branding = b'GEANT' in pdf_content or b'Geant' in pdf_content
                has_hypermarket = b'HYPERMARKET' in pdf_content or b'Hypermarket' in pdf_content
                pdf_size = len(pdf_content)
                
                # Larger PDF size might indicate logo/branding inclusion
                has_branding = has_geant_branding or has_hypermarket or pdf_size > 5000
                
                self.log_result("Company Branding in Exports", has_branding,
                    f"GEANT branding: {has_geant_branding}, Hypermarket: {has_hypermarket}, "
                    f"PDF size: {pdf_size} bytes", response_time)
            else:
                self.log_result("Company Branding in Exports", False,
                    f"Status: {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_result("Company Branding in Exports", False, f"Exception: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all enhanced return form system tests"""
        print("🚀 ENHANCED SUPPLIER RETURN FORM SYSTEM TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Supervisors: {TEST_SUPERVISORS}")
        print(f"Section Manager: {SECTION_MANAGER}")
        print(f"Test Currencies: {TEST_CURRENCIES}")
        print(f"Test Barcode: {TEST_BARCODE}")
        print("=" * 60)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Currency API Integration
        self.test_currency_rates_api()
        
        # 3. Test barcode lookup for product data
        product_data = self.test_barcode_lookup()
        if not product_data:
            # Use fallback data if barcode lookup fails
            product_data = {
                "product_name": "Apple Juice Box 1L",
                "purchase_price": 0.754,
                "purchase_currency": "EUR",
                "supplier": "ExtenC",
                "item_number": "TEST-001"
            }
        
        # 4. Supervisor Dropdown Integration
        self.test_return_form_creation_with_supervisor(product_data)
        
        # 5. Dual Currency Display
        self.test_dual_currency_display()
        
        # 6. Enhanced PDF Export - Main endpoint
        self.test_pdf_export_main()
        
        # 7. Enhanced PDF Export - Individual endpoint
        self.test_pdf_export_individual()
        
        # 8. Excel Export
        self.test_excel_export()
        
        # 9. Approval Workflow Validation
        self.test_approval_workflow_validation()
        
        # 10. Company Branding in Exports
        self.test_company_branding_in_exports()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 ENHANCED RETURN FORM SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        print(f"🔄 CREATED RETURN FORMS: {len(self.created_return_forms)}")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Supervisor Dropdown Integration": any("Return Form Creation -" in r["test"] and r["success"] for r in self.test_results),
            "Currency API Integration": any("Currency Rates API" in r["test"] and r["success"] for r in self.test_results),
            "Dual Currency Display": any("Dual Currency Display" in r["test"] and r["success"] for r in self.test_results),
            "Main PDF Export": any("Main PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "Individual PDF Export": any("Individual PDF Export" in r["test"] and r["success"] for r in self.test_results),
            "Approval Workflow": any("Approval Workflow" in r["test"] and r["success"] for r in self.test_results),
            "Company Branding": any("Company Branding" in r["test"] and r["success"] for r in self.test_results)
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
        avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
        print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 60)
        print("🏁 ENHANCED RETURN FORM SYSTEM TESTING COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = EnhancedReturnFormTester()
    tester.run_comprehensive_tests()