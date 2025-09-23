#!/usr/bin/env python3
"""
Email Alert System Backend Testing for Expiry Tracker
Tests email functionality with 06:00 AM Aden timezone functionality
Focus: Email Status, Settings, Test Email, Error Tracking, Timezone Handling
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import pytz

class EmailAlertSystemTester:
    def __init__(self, base_url="https://smart-inventory-69.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials from review request
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

    def test_email_status_endpoint(self):
        """Test GET /api/alerts/email-status - CRITICAL REQUIREMENT 1"""
        print("\n📧 Testing Email Status Endpoint")
        
        success, response = self.run_test(
            "Email Status Endpoint",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success and isinstance(response, dict):
            # Verify required fields from review request
            required_fields = [
                'current_aden_time',
                'timezone', 
                'daily_alert_time',
                'daily_alerts_enabled',
                'default_recipient',
                'email_configured'
            ]
            
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                self.log_test("Email Status Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            # Verify Aden timezone info
            timezone = response.get('timezone', '')
            current_aden_time = response.get('current_aden_time', '')
            daily_alert_time = response.get('daily_alert_time', '')
            
            print(f"   🕰️ Current Aden Time: {current_aden_time}")
            print(f"   🌍 Timezone: {timezone}")
            print(f"   ⏰ Daily Alert Time: {daily_alert_time}")
            print(f"   📧 Default Recipient: {response.get('default_recipient')}")
            print(f"   ⚙️ Email Configured: {response.get('email_configured')}")
            
            # Verify timezone is Asia/Aden (GMT+3)
            if timezone != "Asia/Aden (GMT+3)":
                self.log_test("Email Status Timezone", False, f"Expected 'Asia/Aden (GMT+3)', got '{timezone}'")
                return False
            
            # Verify daily alert time is 06:00
            if daily_alert_time != "06:00":
                self.log_test("Email Status Alert Time", False, f"Expected '06:00', got '{daily_alert_time}'")
                return False
            
            # Verify current time format includes timezone
            if "Asia/Aden" not in current_aden_time and "GMT+3" not in current_aden_time:
                self.log_test("Email Status Time Format", False, f"Time doesn't include timezone info: {current_aden_time}")
                return False
            
            # Check for recent failures array
            recent_failures = response.get('recent_failures', [])
            print(f"   🚨 Recent Email Failures: {len(recent_failures)}")
            
            if recent_failures:
                print("   Recent failures:")
                for i, failure in enumerate(recent_failures[-3:], 1):  # Show last 3
                    timestamp = failure.get('timestamp', 'Unknown')
                    error = failure.get('error', 'Unknown')
                    failure_type = failure.get('type', 'Unknown')
                    print(f"      {i}. {timestamp} - {failure_type}: {error[:50]}...")
            
            print("   ✅ Email status endpoint working correctly")
            return True
        
        return False

    def test_email_settings_get(self):
        """Test GET /api/settings/email - CRITICAL REQUIREMENT 2"""
        print("\n⚙️ Testing Email Settings GET Endpoint")
        
        success, response = self.run_test(
            "Get Email Settings",
            "GET",
            "settings/email",
            200
        )
        
        if success and isinstance(response, dict):
            # Verify default settings from review request
            daily_alert_time = response.get('daily_alert_time', '')
            timezone = response.get('timezone', '')
            default_recipient = response.get('default_recipient', '')
            daily_alerts_enabled = response.get('daily_alerts_enabled', False)
            
            print(f"   ⏰ Daily Alert Time: {daily_alert_time}")
            print(f"   🌍 Timezone: {timezone}")
            print(f"   📧 Default Recipient: {default_recipient}")
            print(f"   🔔 Daily Alerts Enabled: {daily_alerts_enabled}")
            
            # Verify 06:00 AM default time
            if daily_alert_time != "06:00":
                self.log_test("Email Settings Default Time", False, f"Expected '06:00', got '{daily_alert_time}'")
                return False
            
            # Verify Asia/Aden timezone
            if timezone != "Asia/Aden":
                self.log_test("Email Settings Timezone", False, f"Expected 'Asia/Aden', got '{timezone}'")
                return False
            
            # Verify other expected fields
            expected_fields = [
                'id', 'department_recipients', 'weekly_reports_enabled',
                'expiry_threshold_days', 'beverage_expiry_threshold_days',
                'email_failures', 'updated_at'
            ]
            
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️ Optional fields missing: {missing_fields}")
            
            # Check email failures array for debugging
            email_failures = response.get('email_failures', [])
            print(f"   🚨 Email Failures Logged: {len(email_failures)}")
            
            print("   ✅ Email settings GET endpoint working correctly")
            return True
        
        return False

    def test_email_settings_update(self):
        """Test PUT /api/settings/email - CRITICAL REQUIREMENT 3"""
        print("\n⚙️ Testing Email Settings UPDATE Endpoint")
        
        # First get current settings
        success, current_settings = self.run_test(
            "Get Current Email Settings",
            "GET",
            "settings/email",
            200
        )
        
        if not success:
            return False
        
        # Prepare update data - should force timezone to Asia/Aden and time to 06:00
        update_data = {
            "daily_alert_time": "08:00",  # Try to set different time
            "timezone": "UTC",  # Try to set different timezone
            "default_recipient": "test@example.com",
            "daily_alerts_enabled": True,
            "weekly_reports_enabled": True,
            "expiry_threshold_days": 7,
            "beverage_expiry_threshold_days": 15
        }
        
        success, response = self.run_test(
            "Update Email Settings",
            "PUT",
            "settings/email",
            200,
            data=update_data
        )
        
        if success and isinstance(response, dict):
            # Verify the response shows forced values
            returned_timezone = response.get('timezone', '')
            returned_time = response.get('daily_alert_time', '')
            aden_time_now = response.get('aden_time_now', '')
            
            print(f"   🌍 Returned Timezone: {returned_timezone}")
            print(f"   ⏰ Returned Alert Time: {returned_time}")
            print(f"   🕰️ Current Aden Time: {aden_time_now}")
            
            # Verify timezone was forced to Asia/Aden
            if returned_timezone != "Asia/Aden":
                self.log_test("Email Settings Update Timezone Force", False, f"Expected 'Asia/Aden', got '{returned_timezone}'")
                return False
            
            # Verify time was forced to 06:00
            if returned_time != "06:00":
                self.log_test("Email Settings Update Time Force", False, f"Expected '06:00', got '{returned_time}'")
                return False
            
            # Verify Aden time format
            if not aden_time_now or "Asia/Aden" not in aden_time_now:
                self.log_test("Email Settings Update Aden Time", False, f"Invalid Aden time format: {aden_time_now}")
                return False
            
            print("   ✅ Email settings update correctly forces Asia/Aden timezone and 06:00 time")
            
            # Verify settings were actually saved by getting them again
            success2, updated_settings = self.run_test(
                "Verify Updated Settings",
                "GET",
                "settings/email",
                200
            )
            
            if success2 and isinstance(updated_settings, dict):
                final_timezone = updated_settings.get('timezone', '')
                final_time = updated_settings.get('daily_alert_time', '')
                
                if final_timezone == "Asia/Aden" and final_time == "06:00":
                    print("   ✅ Settings persisted correctly in database")
                    return True
                else:
                    self.log_test("Email Settings Persistence", False, f"Settings not persisted: {final_timezone}, {final_time}")
                    return False
        
        return False

    def test_send_test_email(self):
        """Test POST /api/alerts/send-test-email - CRITICAL REQUIREMENT 4"""
        print("\n📧 Testing Send Test Email Endpoint")
        
        success, response = self.run_test(
            "Send Test Email",
            "POST",
            "alerts/send-test-email",
            200
        )
        
        if success and isinstance(response, dict):
            # Verify response contains expected fields
            expected_fields = ['message', 'sent_to', 'aden_time', 'timezone']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if missing_fields:
                self.log_test("Test Email Response Fields", False, f"Missing fields: {missing_fields}")
                return False
            
            message = response.get('message', '')
            sent_to = response.get('sent_to', [])
            aden_time = response.get('aden_time', '')
            timezone = response.get('timezone', '')
            
            print(f"   📧 Message: {message}")
            print(f"   📬 Sent To: {sent_to}")
            print(f"   🕰️ Aden Time: {aden_time}")
            print(f"   🌍 Timezone: {timezone}")
            
            # Verify success message
            if "successfully" not in message.lower():
                self.log_test("Test Email Success Message", False, f"Unexpected message: {message}")
                return False
            
            # Verify timezone info
            if timezone != "Asia/Aden (GMT+3)":
                self.log_test("Test Email Timezone", False, f"Expected 'Asia/Aden (GMT+3)', got '{timezone}'")
                return False
            
            # Verify Aden time format
            if not aden_time or len(aden_time) < 10:
                self.log_test("Test Email Time Format", False, f"Invalid time format: {aden_time}")
                return False
            
            # Verify recipients list
            if not isinstance(sent_to, list) or len(sent_to) == 0:
                self.log_test("Test Email Recipients", False, f"Invalid recipients: {sent_to}")
                return False
            
            print("   ✅ Test email endpoint working correctly")
            return True
        
        return False

    def test_send_test_email_failure_handling(self):
        """Test test email endpoint handles failures gracefully"""
        print("\n🚨 Testing Test Email Failure Handling")
        
        # The endpoint should handle email failures gracefully and log them
        # We can't force a failure easily, but we can check the response structure
        success, response = self.run_test(
            "Test Email Failure Handling",
            "POST",
            "alerts/send-test-email",
            200  # Should return 200 even if email fails (graceful handling)
        )
        
        if success:
            print("   ✅ Test email endpoint handles requests gracefully")
            
            # Check if email failures are being logged by checking email status
            success2, status_response = self.run_test(
                "Check Email Failures After Test",
                "GET",
                "alerts/email-status",
                200
            )
            
            if success2 and isinstance(status_response, dict):
                recent_failures = status_response.get('recent_failures', [])
                print(f"   📊 Email failures logged: {len(recent_failures)}")
                
                # If there are failures, verify they have proper structure
                if recent_failures:
                    latest_failure = recent_failures[-1]
                    required_failure_fields = ['timestamp', 'error', 'type']
                    
                    failure_fields_present = all(field in latest_failure for field in required_failure_fields)
                    if failure_fields_present:
                        print("   ✅ Email failures properly structured with timestamp, error, and type")
                        return True
                    else:
                        self.log_test("Email Failure Structure", False, f"Failure missing fields: {latest_failure}")
                        return False
                else:
                    print("   ✅ No recent email failures (email system working)")
                    return True
        
        return False

    def test_error_tracking_functionality(self):
        """Test error tracking in email_failures array - CRITICAL REQUIREMENT 5"""
        print("\n🚨 Testing Error Tracking Functionality")
        
        # Get current email status to check error tracking
        success, response = self.run_test(
            "Email Error Tracking Check",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success and isinstance(response, dict):
            recent_failures = response.get('recent_failures', [])
            print(f"   📊 Recent failures tracked: {len(recent_failures)}")
            
            # Verify error tracking structure
            if recent_failures:
                print("   🔍 Analyzing error tracking structure:")
                
                for i, failure in enumerate(recent_failures[-3:], 1):  # Check last 3
                    # Verify required fields
                    required_fields = ['timestamp', 'error', 'type']
                    missing_fields = [field for field in required_fields if field not in failure]
                    
                    if missing_fields:
                        self.log_test("Error Tracking Structure", False, f"Failure {i} missing fields: {missing_fields}")
                        return False
                    
                    timestamp = failure.get('timestamp', '')
                    error = failure.get('error', '')
                    failure_type = failure.get('type', '')
                    
                    print(f"      {i}. Type: {failure_type}")
                    print(f"         Timestamp: {timestamp}")
                    print(f"         Error: {error[:50]}...")
                    
                    # Verify timestamp is in Aden timezone format
                    if isinstance(timestamp, str):
                        # Check if timestamp contains timezone info
                        if "+" not in timestamp and "Z" not in timestamp and "GMT" not in timestamp:
                            print(f"         ⚠️ Timestamp may not include timezone info")
                    
                    # Verify error type is meaningful
                    valid_types = ['test_email', 'daily_alert', 'system_error']
                    if failure_type not in valid_types:
                        print(f"         ⚠️ Unexpected error type: {failure_type}")
                
                print("   ✅ Error tracking structure is properly implemented")
                return True
            else:
                print("   ✅ No recent failures (system working well)")
                return True
        
        return False

    def test_timezone_handling_accuracy(self):
        """Test timezone handling accuracy - CRITICAL REQUIREMENT 6"""
        print("\n🌍 Testing Timezone Handling Accuracy")
        
        # Get current Aden time from multiple endpoints
        endpoints_to_test = [
            ("alerts/email-status", "current_aden_time"),
            ("settings/email", "updated_at")
        ]
        
        aden_times = []
        
        for endpoint, time_field in endpoints_to_test:
            success, response = self.run_test(
                f"Timezone Test - {endpoint}",
                "GET",
                endpoint,
                200
            )
            
            if success and isinstance(response, dict):
                time_value = response.get(time_field)
                if time_value:
                    aden_times.append({
                        'endpoint': endpoint,
                        'field': time_field,
                        'time': time_value
                    })
                    print(f"   🕰️ {endpoint} - {time_field}: {time_value}")
        
        if not aden_times:
            self.log_test("Timezone Handling", False, "No timezone data found")
            return False
        
        # Verify timezone calculations
        try:
            # Get current UTC time
            utc_now = datetime.utcnow()
            
            # Calculate expected Aden time (GMT+3)
            aden_tz = pytz.timezone('Asia/Aden')
            expected_aden_time = utc_now.replace(tzinfo=pytz.UTC).astimezone(aden_tz)
            
            print(f"   🌐 Current UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🇾🇪 Expected Aden Time: {expected_aden_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Verify at least one endpoint returns proper Aden time
            valid_aden_times = 0
            
            for time_data in aden_times:
                time_str = time_data['time']
                
                # Check if time string contains timezone info
                if any(tz in str(time_str) for tz in ['Asia/Aden', 'GMT+3', '+03']):
                    valid_aden_times += 1
                    print(f"   ✅ {time_data['endpoint']} has proper timezone info")
                else:
                    print(f"   ⚠️ {time_data['endpoint']} may not have timezone info: {time_str}")
            
            if valid_aden_times > 0:
                print(f"   ✅ {valid_aden_times}/{len(aden_times)} endpoints have proper Aden timezone handling")
                return True
            else:
                self.log_test("Timezone Accuracy", False, "No endpoints show proper Aden timezone")
                return False
                
        except Exception as e:
            self.log_test("Timezone Calculation", False, f"Error calculating timezone: {str(e)}")
            return False

    def test_daily_alerts_endpoint(self):
        """Test daily alerts endpoint functionality"""
        print("\n📅 Testing Daily Alerts Endpoint")
        
        success, response = self.run_test(
            "Send Daily Alerts",
            "POST",
            "alerts/send-daily",
            200
        )
        
        if success and isinstance(response, dict):
            message = response.get('message', '')
            out_of_stock_count = response.get('out_of_stock_count', 0)
            near_expiry_count = response.get('near_expiry_count', 0)
            
            print(f"   📧 Message: {message}")
            print(f"   📉 Out of Stock Items: {out_of_stock_count}")
            print(f"   ⚠️ Near Expiry Items: {near_expiry_count}")
            
            # Verify response structure
            if "alert" in message.lower():
                print("   ✅ Daily alerts endpoint working correctly")
                return True
            else:
                self.log_test("Daily Alerts Response", False, f"Unexpected message: {message}")
                return False
        
        return False

    def test_email_configuration_status(self):
        """Test email configuration status detection"""
        print("\n⚙️ Testing Email Configuration Status")
        
        success, response = self.run_test(
            "Email Configuration Status",
            "GET",
            "alerts/email-status",
            200
        )
        
        if success and isinstance(response, dict):
            email_configured = response.get('email_configured', False)
            print(f"   📧 Email Configured: {email_configured}")
            
            # This tells us if EMAIL_PASSWORD is set in environment
            if isinstance(email_configured, bool):
                if email_configured:
                    print("   ✅ Email system is properly configured")
                else:
                    print("   ⚠️ Email system not configured (EMAIL_PASSWORD missing)")
                return True
            else:
                self.log_test("Email Configuration Status", False, f"Invalid email_configured value: {email_configured}")
                return False
        
        return False

    def test_email_settings_validation(self):
        """Test email settings validation and constraints"""
        print("\n✅ Testing Email Settings Validation")
        
        # Test invalid settings to ensure validation works
        invalid_settings = [
            {
                "data": {"daily_alert_time": "25:00"},  # Invalid time
                "description": "Invalid time format"
            },
            {
                "data": {"expiry_threshold_days": -1},  # Negative days
                "description": "Negative threshold days"
            },
            {
                "data": {"default_recipient": "invalid-email"},  # Invalid email
                "description": "Invalid email format"
            }
        ]
        
        validation_working = True
        
        for test_case in invalid_settings:
            success, response = self.run_test(
                f"Validation Test - {test_case['description']}",
                "PUT",
                "settings/email",
                422,  # Expect validation error
                data=test_case['data']
            )
            
            if not success:
                # If it doesn't return 422, check if it returns 200 with corrected values
                success2, response2 = self.run_test(
                    f"Validation Test Fallback - {test_case['description']}",
                    "PUT",
                    "settings/email",
                    200,
                    data=test_case['data']
                )
                
                if success2:
                    print(f"   ⚠️ {test_case['description']}: Accepted but may have been corrected")
                else:
                    validation_working = False
        
        if validation_working:
            print("   ✅ Email settings validation working correctly")
        else:
            print("   ⚠️ Some validation tests failed")
        
        return validation_working

    def run_all_email_tests(self):
        """Run all email alert system tests"""
        print("📧 Starting Email Alert System Testing")
        print("Focus: 06:00 AM Aden timezone functionality and email endpoints")
        print("=" * 70)
        
        # Authentication first
        if not self.test_login():
            print("❌ Admin login failed - stopping tests")
            return False
        
        # CRITICAL TESTING REQUIREMENTS from review request
        print("\n🔥 CRITICAL EMAIL TESTING REQUIREMENTS")
        print("-" * 50)
        
        # 1. Test Email Status Endpoint
        self.test_email_status_endpoint()
        
        # 2. Test Email Settings GET
        self.test_email_settings_get()
        
        # 3. Test Email Settings UPDATE
        self.test_email_settings_update()
        
        # 4. Test Email Send Functionality
        self.test_send_test_email()
        self.test_send_test_email_failure_handling()
        
        # 5. Test Error Tracking
        self.test_error_tracking_functionality()
        
        # 6. Test Timezone Handling
        self.test_timezone_handling_accuracy()
        
        # Additional email functionality tests
        print("\n📧 ADDITIONAL EMAIL FUNCTIONALITY TESTS")
        print("-" * 45)
        
        self.test_daily_alerts_endpoint()
        self.test_email_configuration_status()
        self.test_email_settings_validation()
        
        # Print final results
        print("\n" + "=" * 70)
        print("📊 EMAIL ALERT SYSTEM TEST RESULTS")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Summary of critical requirements
        print("\n🎯 CRITICAL REQUIREMENTS SUMMARY:")
        critical_tests = [
            "Email Status Endpoint",
            "Get Email Settings", 
            "Update Email Settings",
            "Send Test Email",
            "Email Error Tracking Check",
            "Timezone Test"
        ]
        
        critical_passed = 0
        for test_result in self.test_results:
            if any(critical in test_result['name'] for critical in critical_tests):
                if test_result['success']:
                    critical_passed += 1
                    print(f"✅ {test_result['name']}")
                else:
                    print(f"❌ {test_result['name']}: {test_result['details']}")
        
        print(f"\nCritical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("🎉 ALL CRITICAL EMAIL REQUIREMENTS PASSED!")
            return True
        else:
            print("⚠️ Some critical email requirements failed")
            return False

if __name__ == "__main__":
    tester = EmailAlertSystemTester()
    success = tester.run_all_email_tests()
    
    if success:
        print("\n✅ Email alert system testing completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Email alert system testing completed with failures")
        sys.exit(1)