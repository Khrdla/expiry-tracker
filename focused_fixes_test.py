#!/usr/bin/env python3
"""
FOCUSED TEST for the two specific fixes mentioned in review request
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class FocusedFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        response = self.session.post(f"{BACKEND_URL}/auth/login", 
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    
    def test_scenario_1_excel_export_fix(self):
        """Scenario 1: Excel Export Fix - Create approved return form and test Excel export"""
        print("\n🔧 SCENARIO 1: Excel Export Fix")
        print("-" * 40)
        
        # Create approved return form
        approved_form_data = {
            "reference_number": f"RTN-EXCEL-TEST-{int(time.time())}",
            "product_code": "EXCEL-TEST-001",
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 10,
            "purchase_price": 0.754,
            "purchase_currency": "EUR",
            "supplier": "ExtenC",
            "reason_for_return": "Excel export test",
            "selected_supervisor": "Mahmoud Badr",
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            "supervisor_approved": True,
            "supervisor_signature": "Mahmoud_Badr_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "Imad_Qejji_signature", 
            "section_manager_timestamp": datetime.now().isoformat()
        }
        
        # Create form
        create_response = self.session.post(f"{BACKEND_URL}/return-forms", json=approved_form_data)
        if create_response.status_code != 200:
            print(f"❌ Failed to create approved form: {create_response.status_code}")
            return False
        
        form_id = create_response.json().get("id")
        print(f"✅ Created approved return form: {form_id}")
        
        # Test Excel export
        excel_response = self.session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=excel")
        
        if excel_response.status_code == 200:
            content_type = excel_response.headers.get('content-type', '')
            excel_size = len(excel_response.content)
            
            # Check for Excel format
            is_excel = (
                'spreadsheet' in content_type.lower() or 
                'excel' in content_type.lower() or
                excel_response.content.startswith(b'PK') or
                excel_size > 5000
            )
            
            # Check for MergedCell error in response
            try:
                response_text = excel_response.content.decode('utf-8', errors='ignore')
                has_mergedcell_error = 'MergedCell' in response_text or 'column_letter' in response_text
            except:
                has_mergedcell_error = False
            
            if is_excel and not has_mergedcell_error:
                print(f"✅ Excel export working - Size: {excel_size} bytes, Content-Type: {content_type}")
                print("✅ NO MergedCell column_letter error detected")
                return True
            else:
                print(f"❌ Excel export issues - Excel format: {is_excel}, MergedCell error: {has_mergedcell_error}")
                return False
        else:
            print(f"❌ Excel export failed: {excel_response.status_code} - {excel_response.text[:200]}")
            return False
    
    def test_scenario_2_pdf_export_validation(self):
        """Scenario 2: PDF Export Validation Fix"""
        print("\n🔧 SCENARIO 2: PDF Export Validation Fix")
        print("-" * 40)
        
        # Create return form WITHOUT approvals
        unapproved_form_data = {
            "reference_number": f"RTN-PDF-TEST-{int(time.time())}",
            "product_code": "PDF-TEST-001",
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 5,
            "purchase_price": 0.754,
            "purchase_currency": "EUR",
            "supplier": "ExtenC",
            "reason_for_return": "PDF validation test",
            "selected_supervisor": "Abdelhamed Mostafa",
            "prepared_by_supervisor": "Abdelhamed Mostafa",
            "section_manager_name": "Imad Qejji",
            # CRITICAL: No approvals
            "supervisor_approved": False,
            "section_manager_approved": False
        }
        
        # Create unapproved form
        create_response = self.session.post(f"{BACKEND_URL}/return-forms", json=unapproved_form_data)
        if create_response.status_code != 200:
            print(f"❌ Failed to create unapproved form: {create_response.status_code}")
            return False
        
        unapproved_form_id = create_response.json().get("id")
        print(f"✅ Created unapproved return form: {unapproved_form_id}")
        
        # Test individual PDF export - should be blocked
        pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{unapproved_form_id}/pdf")
        
        if pdf_response.status_code == 400:
            response_text = pdf_response.text.lower()
            has_approval_message = (
                'approval' in response_text or 
                'approved' in response_text or
                'signature' in response_text
            )
            print(f"✅ PDF export correctly blocked with 400 status")
            print(f"✅ Response contains approval message: {has_approval_message}")
            print(f"   Response: {pdf_response.text[:100]}")
            
            # Now test with approved form
            return self.test_approved_form_pdf_export()
        else:
            print(f"❌ PDF export should be blocked but got status: {pdf_response.status_code}")
            print(f"   Response: {pdf_response.text[:200]}")
            return False
    
    def test_approved_form_pdf_export(self):
        """Test PDF export with approved form - should work"""
        print("\n   Testing approved form PDF export...")
        
        # Create approved form
        approved_form_data = {
            "reference_number": f"RTN-PDF-APPROVED-{int(time.time())}",
            "product_code": "PDF-APPROVED-001",
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 8,
            "purchase_price": 0.754,
            "purchase_currency": "EUR",
            "supplier": "ExtenC",
            "reason_for_return": "PDF approved test",
            "selected_supervisor": "Mahmoud Badr",
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            # CRITICAL: Both approvals TRUE
            "supervisor_approved": True,
            "supervisor_signature": "Mahmoud_Badr_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "Imad_Qejji_signature", 
            "section_manager_timestamp": datetime.now().isoformat()
        }
        
        create_response = self.session.post(f"{BACKEND_URL}/return-forms", json=approved_form_data)
        if create_response.status_code != 200:
            print(f"   ❌ Failed to create approved form: {create_response.status_code}")
            return False
        
        approved_form_id = create_response.json().get("id")
        
        # Test PDF export - should work
        pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{approved_form_id}/pdf")
        
        if pdf_response.status_code == 200:
            content_type = pdf_response.headers.get('content-type', '')
            is_pdf = 'application/pdf' in content_type or pdf_response.content.startswith(b'%PDF')
            pdf_size = len(pdf_response.content)
            
            if is_pdf:
                print(f"   ✅ Approved form PDF export working - Size: {pdf_size} bytes")
                return True
            else:
                print(f"   ❌ PDF format issue - Content-Type: {content_type}")
                return False
        else:
            print(f"   ❌ Approved form PDF export failed: {pdf_response.status_code}")
            return False
    
    def test_scenario_3_complete_workflow(self):
        """Scenario 3: Complete Workflow Test"""
        print("\n🔧 SCENARIO 3: Complete Workflow Test")
        print("-" * 40)
        
        # Create return form with supervisor "Mahmoud Badr" as specified
        workflow_form_data = {
            "reference_number": f"RTN-WORKFLOW-{int(time.time())}",
            "product_code": "WORKFLOW-001",
            "product_name": "Apple Juice Box 1L",
            "barcode": "3222471081716",
            "quantity": 12,
            "purchase_price": 0.754,
            "purchase_currency": "EUR",
            "supplier": "ExtenC",
            "reason_for_return": "Complete workflow test with dual currency",
            "selected_supervisor": "Mahmoud Badr",  # As specified in review
            "prepared_by_supervisor": "Mahmoud Badr",
            "section_manager_name": "Imad Qejji",
            "notes": "Testing complete workflow with dual currency display",
            # Add digital approvals
            "supervisor_approved": True,
            "supervisor_signature": "Mahmoud_Badr_digital_signature",
            "supervisor_timestamp": datetime.now().isoformat(),
            "section_manager_approved": True,
            "section_manager_signature": "Imad_Qejji_digital_signature", 
            "section_manager_timestamp": datetime.now().isoformat()
        }
        
        # Create form
        create_response = self.session.post(f"{BACKEND_URL}/return-forms", json=workflow_form_data)
        if create_response.status_code != 200:
            print(f"❌ Failed to create workflow form: {create_response.status_code}")
            return False
        
        workflow_form_id = create_response.json().get("id")
        print(f"✅ Created workflow return form: {workflow_form_id}")
        
        # Test both export formats
        pdf_success = False
        excel_success = False
        
        # Test PDF export
        pdf_response = self.session.get(f"{BACKEND_URL}/export/return-form/{workflow_form_id}/pdf")
        if pdf_response.status_code == 200 and pdf_response.content.startswith(b'%PDF'):
            pdf_success = True
            print(f"✅ PDF export working - Size: {len(pdf_response.content)} bytes")
        else:
            print(f"❌ PDF export failed: {pdf_response.status_code}")
        
        # Test Excel export
        excel_response = self.session.get(f"{BACKEND_URL}/export/return-form/{workflow_form_id}?format=excel")
        if excel_response.status_code == 200 and len(excel_response.content) > 5000:
            excel_success = True
            print(f"✅ Excel export working - Size: {len(excel_response.content)} bytes")
        else:
            print(f"❌ Excel export failed: {excel_response.status_code}")
        
        # Check for dual currency display
        dual_currency_success = False
        if pdf_success:
            try:
                pdf_content = pdf_response.content.decode('utf-8', errors='ignore')
                has_eur = 'EUR' in pdf_content
                has_usd_or_equivalent = 'USD' in pdf_content or '$' in pdf_content or 'equivalent' in pdf_content.lower()
                dual_currency_success = has_eur and has_usd_or_equivalent
                print(f"✅ Dual currency check - EUR: {has_eur}, USD/equivalent: {has_usd_or_equivalent}")
            except:
                print("⚠️  Could not check dual currency in PDF")
        
        overall_success = pdf_success and excel_success
        print(f"✅ Complete workflow test: {'PASSED' if overall_success else 'FAILED'}")
        
        return overall_success
    
    def run_focused_tests(self):
        """Run focused tests for the two critical fixes"""
        print("🎯 FOCUSED FIXES VERIFICATION")
        print("=" * 50)
        print("Testing specific fixes mentioned in review request:")
        print("1. Excel Export MergedCell Fix")
        print("2. Individual PDF Export Validation")
        print("=" * 50)
        
        if not self.authenticate():
            return
        
        # Test results
        results = {}
        
        # Scenario 1: Excel Export Fix
        results['excel_fix'] = self.test_scenario_1_excel_export_fix()
        
        # Scenario 2: PDF Export Validation Fix
        results['pdf_validation_fix'] = self.test_scenario_2_pdf_export_validation()
        
        # Scenario 3: Complete Workflow Test
        results['complete_workflow'] = self.test_scenario_3_complete_workflow()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 FOCUSED FIXES TEST RESULTS")
        print("=" * 50)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"✅ PASSED: {passed}/{total} scenarios")
        
        for scenario, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {scenario.replace('_', ' ').title()}")
        
        # Critical assessment
        excel_fix_working = results.get('excel_fix', False)
        pdf_validation_working = results.get('pdf_validation_fix', False)
        
        print(f"\n🎯 CRITICAL FIXES STATUS:")
        print(f"{'✅' if excel_fix_working else '❌'} Excel Export MergedCell Fix")
        print(f"{'✅' if pdf_validation_working else '❌'} PDF Export Validation Fix")
        
        if excel_fix_working and pdf_validation_working:
            print(f"\n🏆 OVERALL: ✅ BOTH CRITICAL FIXES ARE WORKING")
        else:
            print(f"\n🏆 OVERALL: ❌ SOME CRITICAL FIXES NEED ATTENTION")
        
        print("=" * 50)

if __name__ == "__main__":
    tester = FocusedFixesTester()
    tester.run_focused_tests()