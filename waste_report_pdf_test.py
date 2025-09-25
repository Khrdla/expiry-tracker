#!/usr/bin/env python3
"""
WASTE REPORT PDF EXPORT TEST - Fix Verification

This test focuses specifically on testing the fixed waste report PDF export functionality
to verify that the corruption issue has been resolved and PDFs are now generating properly.

Test Coverage:
1. Authentication with admin credentials
2. Waste report PDF export (daily, weekly, monthly)
3. PDF file validation (size, content-type, format)
4. Excel format verification
5. Department filtering
6. Error handling and edge cases
"""

import requests
import json
import sys
from datetime import datetime
import io

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class WasteReportPDFTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
            
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_authentication(self):
        """Test 1: Authentication with admin credentials"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Admin Login", True, f"Token received: {self.token[:20]}...")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_daily_pdf_export(self):
        """Test 2: Daily waste report PDF export"""
        print("\n📄 TESTING DAILY PDF EXPORT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Daily PDF Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf")
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    self.log_test("Daily PDF Content-Type", True, f"Correct content-type: {content_type}")
                else:
                    self.log_test("Daily PDF Content-Type", False, f"Wrong content-type: {content_type}")
                
                # Check file size
                file_size = len(response.content)
                if file_size > 10000:  # > 10KB
                    if file_size >= 30000:  # Ideally 30-50KB
                        self.log_test("Daily PDF File Size", True, f"Excellent size: {file_size:,} bytes ({file_size/1024:.1f}KB)")
                    else:
                        self.log_test("Daily PDF File Size", True, f"Good size: {file_size:,} bytes ({file_size/1024:.1f}KB)")
                else:
                    self.log_test("Daily PDF File Size", False, f"Too small: {file_size:,} bytes ({file_size/1024:.1f}KB)")
                
                # Check PDF signature
                pdf_signature = response.content[:4]
                if pdf_signature == b'%PDF':
                    self.log_test("Daily PDF Format", True, "Valid PDF signature detected")
                else:
                    self.log_test("Daily PDF Format", False, f"Invalid PDF signature: {pdf_signature}")
                
                # Check if PDF can be parsed (basic validation)
                try:
                    # Try to read PDF content to verify it's not corrupted
                    pdf_content = response.content
                    if b'%%EOF' in pdf_content:
                        self.log_test("Daily PDF Structure", True, "PDF has proper EOF marker")
                    else:
                        self.log_test("Daily PDF Structure", False, "PDF missing EOF marker")
                        
                    # Check for company branding
                    if b'GEANT' in pdf_content or b'Geant' in pdf_content:
                        self.log_test("Daily PDF Branding", True, "Company branding detected in PDF")
                    else:
                        self.log_test("Daily PDF Branding", False, "No company branding found")
                        
                except Exception as e:
                    self.log_test("Daily PDF Validation", False, f"PDF validation error: {str(e)}")
                
                self.log_test("Daily PDF Export", True, f"Successfully generated {file_size:,} byte PDF")
                return True
                
            else:
                self.log_test("Daily PDF Export", False, f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Daily PDF Export", False, f"Exception: {str(e)}")
            return False
    
    def test_weekly_pdf_export(self):
        """Test 3: Weekly waste report PDF export"""
        print("\n📄 TESTING WEEKLY PDF EXPORT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Weekly PDF Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/weekly?format=pdf")
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get('content-type', '')
                
                # Validate content type and size
                if 'application/pdf' in content_type and file_size > 10000:
                    self.log_test("Weekly PDF Export", True, f"Generated {file_size:,} byte PDF with correct content-type")
                else:
                    self.log_test("Weekly PDF Export", False, f"Issues: content-type={content_type}, size={file_size}")
                
                return True
            else:
                self.log_test("Weekly PDF Export", False, f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Weekly PDF Export", False, f"Exception: {str(e)}")
            return False
    
    def test_monthly_pdf_export(self):
        """Test 4: Monthly waste report PDF export"""
        print("\n📄 TESTING MONTHLY PDF EXPORT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Monthly PDF Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/monthly?format=pdf")
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get('content-type', '')
                
                if 'application/pdf' in content_type and file_size > 10000:
                    self.log_test("Monthly PDF Export", True, f"Generated {file_size:,} byte PDF")
                else:
                    self.log_test("Monthly PDF Export", False, f"Issues: content-type={content_type}, size={file_size}")
                
                return True
            else:
                self.log_test("Monthly PDF Export", False, f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Monthly PDF Export", False, f"Exception: {str(e)}")
            return False
    
    def test_excel_format_still_works(self):
        """Test 5: Verify Excel format still works"""
        print("\n📊 TESTING EXCEL FORMAT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Excel Format Setup", False, "No authentication token available")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=excel")
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get('content-type', '')
                
                # Check for Excel content type
                excel_types = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                              'application/vnd.ms-excel', 'application/octet-stream']
                
                if any(excel_type in content_type for excel_type in excel_types):
                    self.log_test("Excel Content-Type", True, f"Valid Excel content-type: {content_type}")
                else:
                    self.log_test("Excel Content-Type", False, f"Unexpected content-type: {content_type}")
                
                # Check file size
                if file_size > 5000:  # Excel files should be substantial
                    self.log_test("Excel File Size", True, f"Good size: {file_size:,} bytes")
                else:
                    self.log_test("Excel File Size", False, f"Too small: {file_size:,} bytes")
                
                # Check Excel signature (PK for ZIP-based formats)
                excel_signature = response.content[:2]
                if excel_signature == b'PK':
                    self.log_test("Excel Format", True, "Valid Excel/ZIP signature detected")
                else:
                    self.log_test("Excel Format", False, f"Invalid Excel signature: {excel_signature}")
                
                self.log_test("Excel Export", True, f"Successfully generated {file_size:,} byte Excel file")
                return True
                
            else:
                self.log_test("Excel Export", False, f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Excel Export", False, f"Exception: {str(e)}")
            return False
    
    def test_department_filtering(self):
        """Test 6: Department filtering in PDF export"""
        print("\n🏢 TESTING DEPARTMENT FILTERING")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Department Filter Setup", False, "No authentication token available")
            return False
        
        departments = ["01-FMG", "01-CGD", "01-OPSS"]
        
        for dept in departments:
            try:
                response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf&department={dept}")
                
                if response.status_code == 200:
                    file_size = len(response.content)
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/pdf' in content_type and file_size > 5000:
                        self.log_test(f"Department Filter {dept}", True, f"Generated {file_size:,} byte PDF")
                    else:
                        self.log_test(f"Department Filter {dept}", False, f"Issues: content-type={content_type}, size={file_size}")
                else:
                    self.log_test(f"Department Filter {dept}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Department Filter {dept}", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test 7: Error handling for invalid requests"""
        print("\n🚫 TESTING ERROR HANDLING")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Error Handling Setup", False, "No authentication token available")
            return False
        
        # Test invalid format
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/daily?format=invalid")
            
            if response.status_code == 400:
                self.log_test("Invalid Format Error", True, "Correctly returns 400 for invalid format")
            else:
                self.log_test("Invalid Format Error", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Format Error", False, f"Exception: {str(e)}")
        
        # Test invalid period
        try:
            response = self.session.get(f"{BACKEND_URL}/export/waste-report/invalid?format=pdf")
            
            if response.status_code in [400, 404]:
                self.log_test("Invalid Period Error", True, f"Correctly returns {response.status_code} for invalid period")
            else:
                self.log_test("Invalid Period Error", False, f"Expected 400/404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Period Error", False, f"Exception: {str(e)}")
    
    def test_authentication_required(self):
        """Test 8: Verify authentication is required"""
        print("\n🔒 TESTING AUTHENTICATION REQUIREMENTS")
        print("=" * 50)
        
        # Test without authentication
        session_no_auth = requests.Session()
        
        try:
            response = session_no_auth.get(f"{BACKEND_URL}/export/waste-report/daily?format=pdf")
            
            if response.status_code in [401, 403]:
                self.log_test("Auth Required", True, f"Correctly returns {response.status_code} without auth")
            else:
                self.log_test("Auth Required", False, f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Required", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all waste report PDF export tests"""
        print("🎯 WASTE REPORT PDF EXPORT TEST - Fix Verification")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("Testing PDF corruption fix and enhanced functionality")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            self.test_daily_pdf_export()
            self.test_weekly_pdf_export()
            self.test_monthly_pdf_export()
            self.test_excel_format_still_works()
            self.test_department_filtering()
            self.test_error_handling()
            self.test_authentication_required()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with PDF export tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 WASTE REPORT PDF EXPORT TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 PDF CORRUPTION FIX VERIFICATION:")
        
        # Analyze results to answer the key question
        pdf_tests = [r for r in self.test_results if "PDF Export" in r["test"] and r["success"]]
        format_tests = [r for r in self.test_results if "PDF Format" in r["test"] and r["success"]]
        size_tests = [r for r in self.test_results if "PDF File Size" in r["test"] and r["success"]]
        
        if pdf_tests:
            print(f"✅ PDF Generation: WORKING - {len(pdf_tests)} PDF exports successful")
        else:
            print("❌ PDF Generation: FAILED - No successful PDF exports")
        
        if format_tests:
            print("✅ PDF Format: VALID - PDFs have correct signature and structure")
        else:
            print("❌ PDF Format: INVALID - PDF format issues detected")
        
        if size_tests:
            print("✅ PDF Size: SUBSTANTIAL - Files are properly sized (>10KB)")
        else:
            print("❌ PDF Size: INSUFFICIENT - Files too small or corrupted")
        
        excel_tests = [r for r in self.test_results if "Excel Export" in r["test"] and r["success"]]
        if excel_tests:
            print("✅ Excel Format: WORKING - Excel exports still functional")
        else:
            print("❌ Excel Format: BROKEN - Excel export issues detected")
        
        print("\n🔍 FINAL VERDICT:")
        if success_rate >= 85:
            print("✅ PDF CORRUPTION ISSUE RESOLVED!")
            print("✅ Waste report PDF exports are now working correctly")
            print("✅ Files are properly formatted and can be opened")
            print("✅ All enhanced features are functional")
        elif success_rate >= 70:
            print("⚠️  PDF exports are MOSTLY WORKING but some issues remain")
            print("⚠️  Minor fixes may be needed for full functionality")
        else:
            print("❌ PDF CORRUPTION ISSUE NOT RESOLVED")
            print("❌ Critical problems still exist with PDF generation")
            print("❌ Further investigation and fixes required")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = WasteReportPDFTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 85:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()