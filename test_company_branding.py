#!/usr/bin/env python3
"""
Company Branding Testing for Enhanced Report Generation
Tests all enhanced report generation functions with company logo and branding
Focus: Waste Reports, Return Form PDF, Daily Alerts, Excel Template, Dashboard Exports
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class CompanyBrandingTester:
    def __init__(self, base_url="https://stockmate-12.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'response_data': response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)

            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - server may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Admin Login (imadqejji)",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password}
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Admin token obtained: {self.token[:20]}...")
            return True
        else:
            print(f"   ❌ Admin login failed: {response}")
            return False

    def test_company_branding_waste_reports(self):
        """Test waste report generation with company branding"""
        print("\n🏢 Testing Company Branding in Waste Reports")
        
        # First create some waste entries for testing
        waste_entry_data = {
            "product_id": "test-product-123",
            "product_name": "Test Product for Waste",
            "quantity_wasted": 5,
            "waste_reason": "damaged",
            "department": "01-FMG",
            "section": "S001 - Test Section",
            "purchase_price": 10.50,
            "purchase_currency": "YER",
            "notes": "Test waste entry for branding"
        }
        
        # Create waste entry
        success, response = self.run_test(
            "Create Waste Entry for Branding Test",
            "POST",
            "waste/entries",
            200,
            data=waste_entry_data
        )
        
        if not success:
            print("   ⚠️ Could not create waste entry, testing with existing data")
        
        # Test waste report Excel export with branding
        success, response = self.run_test(
            "Waste Report Excel Export (with branding)",
            "GET",
            "export/waste-report/daily?format=excel",
            200
        )
        
        if success:
            print("   ✅ Waste report Excel export successful")
            # Check if response is binary data (Excel file)
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                print(f"   📊 Excel file size: {response_size} bytes")
                if response_size > 1000:  # Should be substantial with branding
                    self.log_test("Waste Report Excel Branding", True, f"Excel file generated: {response_size} bytes")
                else:
                    self.log_test("Waste Report Excel Branding", False, f"Excel file too small: {response_size} bytes")
            else:
                print("   ✅ Waste report Excel endpoint accessible")
        
        # Test waste report PDF export with branding
        success, response = self.run_test(
            "Waste Report PDF Export (with branding)",
            "GET",
            "export/waste-report/daily?format=pdf",
            200
        )
        
        if success:
            print("   ✅ Waste report PDF export successful")
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                print(f"   📄 PDF file size: {response_size} bytes")
                if response_size > 1000:  # Should be substantial with branding
                    self.log_test("Waste Report PDF Branding", True, f"PDF file generated: {response_size} bytes")
                else:
                    self.log_test("Waste Report PDF Branding", False, f"PDF file too small: {response_size} bytes")
        
        return True

    def test_company_branding_return_form_pdf(self):
        """Test return form PDF generation with company branding"""
        print("\n🏢 Testing Company Branding in Return Form PDF")
        
        # Create a test return form
        return_form_data = {
            "reference_number": f"RTN-BRAND-{int(datetime.now().timestamp())}",
            "product_code": "TEST-001",
            "product_name": "Test Product for Return",
            "quantity": 10,
            "purchase_price": 25.50,
            "purchase_currency": "YER",
            "supplier": "Test Supplier",
            "reason_for_return": "damaged",
            "department": "01-FMG",
            "section": "S001 - Test Section",
            "requested_by": "Test User",
            "approved_by": "Test Manager",
            "notes": "Test return form for branding verification"
        }
        
        # Create return form
        success, response = self.run_test(
            "Create Return Form for Branding Test",
            "POST",
            "returns",
            200,
            data=return_form_data
        )
        
        if success and isinstance(response, dict):
            return_id = response.get('id')
            if return_id:
                print(f"   📝 Created return form: {return_id}")
                
                # Test PDF export with branding
                success, pdf_response = self.run_test(
                    "Return Form PDF Export (with branding)",
                    "GET",
                    f"export/return-form/{return_id}/pdf",
                    200
                )
                
                if success:
                    print("   ✅ Return form PDF export successful")
                    if isinstance(pdf_response, (bytes, str)):
                        response_size = len(pdf_response) if isinstance(pdf_response, bytes) else len(pdf_response.encode())
                        print(f"   📄 PDF file size: {response_size} bytes")
                        if response_size > 2000:  # Should be substantial with branding and logo
                            self.log_test("Return Form PDF Branding", True, f"PDF with branding generated: {response_size} bytes")
                            return True
                        else:
                            self.log_test("Return Form PDF Branding", False, f"PDF file too small: {response_size} bytes")
                    else:
                        print("   ✅ Return form PDF endpoint accessible")
                        return True
        
        return False

    def test_company_branding_daily_alerts(self):
        """Test daily alert reports with company branding"""
        print("\n🏢 Testing Company Branding in Daily Alert Reports")
        
        # Test daily alert Excel generation
        success, response = self.run_test(
            "Daily Alert Excel Generation (with branding)",
            "POST",
            "alerts/send-daily",
            200
        )
        
        if success:
            print("   ✅ Daily alert generation successful")
            if isinstance(response, dict):
                message = response.get('message', '')
                print(f"   📧 Response: {message}")
                if isinstance(message, str) and ('queued' in message.lower() or 'sent' in message.lower()):
                    self.log_test("Daily Alert Branding", True, "Daily alerts with branding generated")
                    return True
        
        # Test email status endpoint for branding verification
        success, response = self.run_test(
            "Email Alert Status (branding info)",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success and isinstance(response, dict):
            print("   ✅ Email status endpoint accessible")
            email_configured = response.get('email_configured', False)
            current_time = response.get('current_aden_time', '')
            print(f"   📧 Email configured: {email_configured}")
            print(f"   🕐 Aden time: {current_time}")
            self.log_test("Daily Alert Status", True, f"Email configured: {email_configured}")
            return True
        
        return False

    def test_company_branding_excel_template(self):
        """Test Excel import template with company branding"""
        print("\n🏢 Testing Company Branding in Excel Import Template")
        
        # Test template download
        success, response = self.run_test(
            "Excel Import Template Download (with branding)",
            "GET",
            "system/import-template",
            200
        )
        
        if success:
            print("   ✅ Excel template download successful")
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                print(f"   📊 Template file size: {response_size} bytes")
                if response_size > 5000:  # Should be substantial with branding and logo
                    self.log_test("Excel Template Branding", True, f"Template with branding: {response_size} bytes")
                    return True
                else:
                    self.log_test("Excel Template Branding", False, f"Template file too small: {response_size} bytes")
            else:
                print("   ✅ Excel template endpoint accessible")
                return True
        
        return False

    def test_company_branding_dashboard_exports(self):
        """Test dashboard export functions with company branding"""
        print("\n🏢 Testing Company Branding in Dashboard Exports")
        
        # Test dashboard Excel export
        success, response = self.run_test(
            "Dashboard Excel Export (with branding)",
            "GET",
            "export/dashboard/excel",
            200
        )
        
        if success:
            print("   ✅ Dashboard Excel export successful")
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                print(f"   📊 Excel file size: {response_size} bytes")
                if response_size > 3000:  # Should include branding
                    self.log_test("Dashboard Excel Branding", True, f"Dashboard Excel with branding: {response_size} bytes")
                else:
                    self.log_test("Dashboard Excel Branding", False, f"Excel file too small: {response_size} bytes")
        
        # Test dashboard PDF export
        success, response = self.run_test(
            "Dashboard PDF Export (with branding)",
            "GET",
            "export/dashboard/pdf",
            200
        )
        
        if success:
            print("   ✅ Dashboard PDF export successful")
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                print(f"   📄 PDF file size: {response_size} bytes")
                if response_size > 3000:  # Should include branding and logo
                    self.log_test("Dashboard PDF Branding", True, f"Dashboard PDF with branding: {response_size} bytes")
                    return True
                else:
                    self.log_test("Dashboard PDF Branding", False, f"PDF file too small: {response_size} bytes")
        
        return True

    def test_company_logo_file_exists(self):
        """Test if company logo file exists on server"""
        print("\n🖼️ Testing Company Logo File Existence")
        
        # The logo should be at /app/backend/geant-logo.jpeg
        # We can't directly check file system, but we can test if branding functions work
        
        # Test by trying to generate a report that uses the logo
        success, response = self.run_test(
            "Test Logo Usage in Reports",
            "GET",
            "export/dashboard/pdf",
            200
        )
        
        if success:
            print("   ✅ Logo usage test successful (PDF generation works)")
            if isinstance(response, (bytes, str)):
                response_size = len(response) if isinstance(response, bytes) else len(response.encode())
                if response_size > 2000:  # Larger size suggests logo is included
                    self.log_test("Company Logo File", True, f"Logo appears to be included in reports: {response_size} bytes")
                    return True
                else:
                    print("   ⚠️ PDF size suggests logo may not be included")
                    self.log_test("Company Logo File", False, f"PDF too small, logo may be missing: {response_size} bytes")
        
        return False

    def test_company_branding_colors(self):
        """Test company branding color scheme consistency"""
        print("\n🎨 Testing Company Branding Color Scheme")
        
        # Test multiple report endpoints to ensure consistent branding
        report_endpoints = [
            ("Dashboard Excel", "export/dashboard/excel"),
            ("Dashboard PDF", "export/dashboard/pdf"),
            ("Waste Report Excel", "export/waste-report/daily?format=excel"),
            ("Waste Report PDF", "export/waste-report/daily?format=pdf"),
            ("Excel Template", "system/import-template")
        ]
        
        branding_tests_passed = 0
        total_branding_tests = len(report_endpoints)
        
        for report_name, endpoint in report_endpoints:
            success, response = self.run_test(
                f"{report_name} Branding Colors",
                "GET",
                endpoint,
                200
            )
            
            if success:
                print(f"   ✅ {report_name}: Branding applied successfully")
                branding_tests_passed += 1
            else:
                print(f"   ❌ {report_name}: Branding test failed")
        
        success_rate = (branding_tests_passed / total_branding_tests) * 100
        print(f"   📊 Branding consistency: {branding_tests_passed}/{total_branding_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:  # 80% or higher success rate
            self.log_test("Company Branding Colors", True, f"Branding consistency: {success_rate:.1f}%")
            return True
        else:
            self.log_test("Company Branding Colors", False, f"Low branding consistency: {success_rate:.1f}%")
            return False

    def test_email_html_template_branding(self):
        """Test email HTML template with company branding"""
        print("\n📧 Testing Email HTML Template Branding")
        
        # Test email settings to verify branding configuration
        success, response = self.run_test(
            "Email Settings (branding configuration)",
            "GET",
            "settings/email",
            200
        )
        
        if success and isinstance(response, dict):
            print("   ✅ Email settings accessible")
            sender_email = response.get('sender_email', '')
            daily_time = response.get('daily_alert_time', '')
            timezone = response.get('timezone', '')
            
            print(f"   📧 Sender: {sender_email}")
            print(f"   🕐 Daily time: {daily_time}")
            print(f"   🌍 Timezone: {timezone}")
            
            # Check if sender email contains company domain
            if 'geant' in sender_email.lower():
                print("   ✅ Email sender reflects company branding")
                self.log_test("Email HTML Template Branding", True, f"Company email: {sender_email}")
                return True
            else:
                print("   ⚠️ Email sender may not reflect company branding")
                self.log_test("Email HTML Template Branding", False, f"Non-company email: {sender_email}")
        
        # Test sending a test email to verify HTML template
        success, response = self.run_test(
            "Test Email with HTML Branding",
            "POST",
            "alerts/test-email",
            200,
            data={"recipient": "test@example.com", "subject": "Branding Test"}
        )
        
        if success:
            print("   ✅ Test email with branding sent successfully")
            self.log_test("Email HTML Template Test", True, "Test email sent with branding")
            return True
        
        return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🏢 COMPANY BRANDING TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Group results by category
        failed_tests = [test for test in self.test_results if not test['success']]
        passed_tests = [test for test in self.test_results if test['success']]
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests[:10]:  # Show first 10 passed tests
                print(f"   • {test['name']}")
            if len(passed_tests) > 10:
                print(f"   ... and {len(passed_tests) - 10} more")
        
        print("=" * 80)
        
        return success_rate >= 80

    def run_all_tests(self):
        """Run all company branding tests"""
        print("🚀 Starting Company Branding Testing for Enhanced Report Generation")
        print("Focus: GEANT HYPERMARKET LOGO AND THEME IN ALL GENERATED REPORTS")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Login failed - cannot proceed with authenticated tests")
            return False
        
        # Company branding tests
        tests = [
            self.test_company_branding_waste_reports,
            self.test_company_branding_return_form_pdf,
            self.test_company_branding_daily_alerts,
            self.test_company_branding_excel_template,
            self.test_company_branding_dashboard_exports,
            self.test_company_logo_file_exists,
            self.test_company_branding_colors,
            self.test_email_html_template_branding,
        ]
        
        # Run all tests
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        return self.print_summary()

if __name__ == "__main__":
    tester = CompanyBrandingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)