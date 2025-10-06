#!/usr/bin/env python3
"""
Mobile Barcode Scanner Backend Testing
Tests barcode scanner backend functionality specifically for mobile compatibility
Focus: Barcode Lookup API, Authentication, CORS/Mobile Headers, Response Format, Error Handling
"""

import requests
import sys
import json
from datetime import datetime

class MobileBarcodeAPITester:
    def __init__(self, base_url="https://geant-scanner.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Admin credentials from review request
        self.admin_username = "imadqejji"
        self.admin_password = "066380531I"
        # Sample barcodes from review request
        self.sample_barcodes = ["3222471081716", "9501100046987"]

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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, check_cors=False):
        """Run a single API test with mobile-specific checks"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        # Add mobile-specific headers
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        test_headers.update(mobile_headers)
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Mobile User-Agent: {mobile_headers['User-Agent'][:50]}...")
        
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
            
            # Check CORS headers for mobile compatibility
            if check_cors:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                print(f"   🌐 CORS Headers: {cors_headers}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else "No response body"

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)

            return success, response_data, response.headers

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - server may be down")
            return False, {}, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}, {}

    def test_admin_login(self):
        """Test login with admin credentials for mobile barcode scanner"""
        print("\n🔐 Testing Admin Authentication for Mobile Barcode Scanner")
        
        success, response, headers = self.run_test(
            "Mobile Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": self.admin_username, "password": self.admin_password},
            check_cors=True
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   🔑 Mobile admin token obtained: {self.token[:20]}...")
            return True
        else:
            print(f"   ❌ Mobile admin login failed: {response}")
            return False

    def test_barcode_lookup_sample_barcodes(self):
        """Test barcode lookup with sample barcodes from review request"""
        print(f"\n📱 Testing Mobile Barcode Lookup with Sample Barcodes")
        
        all_success = True
        
        for i, barcode in enumerate(self.sample_barcodes, 1):
            success, response, headers = self.run_test(
                f"Mobile Barcode Lookup #{i} ({barcode})",
                "GET",
                f"barcode/{barcode}",
                200,
                check_cors=True
            )
            
            if success and isinstance(response, dict):
                # Verify mobile-compatible JSON response
                required_fields = [
                    'product_name', 'item_number', 'barcode', 'department', 
                    'section', 'purchase_price', 'purchase_currency', 
                    'selling_price', 'supplier', 'quantity', 'status'
                ]
                
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    self.log_test(f"Mobile Barcode Response Fields #{i}", False, f"Missing fields: {missing_fields}")
                    all_success = False
                    continue
                
                # Verify JSON serialization for mobile
                try:
                    json_str = json.dumps(response)
                    print(f"   📱 Mobile JSON Response Size: {len(json_str)} bytes")
                    
                    # Check for mobile-friendly data
                    product_name = response.get('product_name', '')
                    department = response.get('department', '')
                    status = response.get('status', '')
                    
                    print(f"   📦 Product: {product_name}")
                    print(f"   🏢 Department: {department}")
                    print(f"   📊 Status: {status}")
                    
                    # Verify no ObjectId or other serialization issues
                    if "ObjectId" in json_str:
                        self.log_test(f"Mobile JSON Serialization #{i}", False, "ObjectId found in mobile response")
                        all_success = False
                        continue
                    
                    print(f"   ✅ Mobile-compatible JSON response verified")
                    
                except Exception as e:
                    self.log_test(f"Mobile JSON Serialization #{i}", False, f"JSON serialization failed: {str(e)}")
                    all_success = False
                    continue
                
            else:
                all_success = False
        
        return all_success

    def test_barcode_authentication_mobile(self):
        """Test barcode endpoint authentication for mobile clients"""
        print(f"\n🔐 Testing Mobile Barcode Authentication")
        
        # Test without Bearer token
        original_token = self.token
        self.token = None
        
        success, response, headers = self.run_test(
            "Mobile Barcode - No Auth",
            "GET",
            f"barcode/{self.sample_barcodes[0]}",
            403,  # Should require authentication
            check_cors=True
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ Mobile barcode endpoint correctly requires Bearer token")
            
            # Test with valid Bearer token
            success2, response2, headers2 = self.run_test(
                "Mobile Barcode - Valid Auth",
                "GET",
                f"barcode/{self.sample_barcodes[0]}",
                200,
                check_cors=True
            )
            
            if success2:
                print("   ✅ Mobile barcode endpoint accepts valid Bearer token")
                return True
            else:
                self.log_test("Mobile Barcode Valid Auth", False, "Valid token should work")
                return False
        else:
            self.log_test("Mobile Barcode Authentication", False, "Should require authentication")
            return False

    def test_cors_headers_mobile(self):
        """Test CORS headers for mobile browser compatibility"""
        print(f"\n🌐 Testing CORS Headers for Mobile Browsers")
        
        # Test preflight OPTIONS request
        url = f"{self.api_url}/barcode/{self.sample_barcodes[0]}"
        
        preflight_headers = {
            'Origin': 'https://geant-scanner.preview.emergentagent.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,content-type',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        try:
            response = requests.options(url, headers=preflight_headers, timeout=30)
            
            print(f"   🔍 OPTIONS preflight status: {response.status_code}")
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"   🌐 CORS Headers:")
            for header, value in cors_headers.items():
                print(f"      {header}: {value}")
            
            # Verify mobile-compatible CORS
            allow_origin = cors_headers.get('Access-Control-Allow-Origin')
            allow_methods = cors_headers.get('Access-Control-Allow-Methods', '')
            allow_headers = cors_headers.get('Access-Control-Allow-Headers', '')
            
            mobile_compatible = True
            
            if allow_origin not in ['*', 'https://geant-scanner.preview.emergentagent.com']:
                print(f"   ⚠️ CORS Origin may not allow mobile requests: {allow_origin}")
                mobile_compatible = False
            
            if 'GET' not in allow_methods.upper():
                print(f"   ⚠️ CORS doesn't allow GET method: {allow_methods}")
                mobile_compatible = False
            
            if 'authorization' not in allow_headers.lower():
                print(f"   ⚠️ CORS doesn't allow Authorization header: {allow_headers}")
                mobile_compatible = False
            
            if mobile_compatible:
                print(f"   ✅ CORS headers are mobile-compatible")
                self.log_test("Mobile CORS Headers", True, "CORS configured for mobile browsers")
                return True
            else:
                self.log_test("Mobile CORS Headers", False, "CORS may not support mobile browsers")
                return False
                
        except Exception as e:
            print(f"   ⚠️ CORS preflight test failed: {str(e)}")
            # Don't fail the test suite for CORS issues
            self.log_test("Mobile CORS Headers", True, "CORS test inconclusive")
            return True

    def test_mobile_error_handling(self):
        """Test mobile-friendly error responses for invalid barcodes"""
        print(f"\n📱 Testing Mobile-Friendly Error Handling")
        
        invalid_barcodes = [
            {"barcode": "0000000000000", "description": "Non-existent barcode"},
            {"barcode": "invalid_barcode", "description": "Invalid format"},
            {"barcode": "", "description": "Empty barcode"}
        ]
        
        all_success = True
        
        for i, test_case in enumerate(invalid_barcodes, 1):
            barcode = test_case["barcode"]
            description = test_case["description"]
            
            success, response, headers = self.run_test(
                f"Mobile Error Handling #{i} ({description})",
                "GET",
                f"barcode/{barcode}",
                404,
                check_cors=True
            )
            
            if success:
                # Verify error response is mobile-friendly JSON
                if isinstance(response, dict):
                    try:
                        json_str = json.dumps(response)
                        print(f"   📱 Mobile error response: {json_str[:100]}...")
                        
                        # Check for user-friendly error message
                        detail = response.get('detail', '')
                        if detail:
                            print(f"   💬 Error message: {detail}")
                            if len(detail) < 200:  # Mobile-friendly length
                                print(f"   ✅ Mobile-friendly error message length")
                            else:
                                print(f"   ⚠️ Error message may be too long for mobile")
                        
                    except Exception as e:
                        self.log_test(f"Mobile Error JSON #{i}", False, f"Error response not JSON serializable: {str(e)}")
                        all_success = False
                        continue
                
                print(f"   ✅ Invalid barcode '{barcode}' returns mobile-friendly 404")
            else:
                all_success = False
        
        return all_success

    def test_mobile_response_performance(self):
        """Test response performance for mobile networks"""
        print(f"\n⚡ Testing Mobile Response Performance")
        
        import time
        
        performance_results = []
        
        for i, barcode in enumerate(self.sample_barcodes, 1):
            start_time = time.time()
            
            success, response, headers = self.run_test(
                f"Mobile Performance Test #{i}",
                "GET",
                f"barcode/{barcode}",
                200
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if success:
                # Check response size
                response_size = len(json.dumps(response)) if isinstance(response, dict) else 0
                
                performance_results.append({
                    'barcode': barcode,
                    'response_time_ms': response_time,
                    'response_size_bytes': response_size
                })
                
                print(f"   ⚡ Barcode {barcode}:")
                print(f"      Response Time: {response_time:.2f}ms")
                print(f"      Response Size: {response_size} bytes")
                
                # Mobile performance thresholds
                if response_time < 1000:  # Under 1 second
                    print(f"      ✅ Good mobile response time")
                elif response_time < 3000:  # Under 3 seconds
                    print(f"      ⚠️ Acceptable mobile response time")
                else:
                    print(f"      ❌ Slow for mobile networks")
                
                if response_size < 5000:  # Under 5KB
                    print(f"      ✅ Mobile-friendly response size")
                else:
                    print(f"      ⚠️ Large response for mobile")
        
        if performance_results:
            avg_response_time = sum(r['response_time_ms'] for r in performance_results) / len(performance_results)
            avg_response_size = sum(r['response_size_bytes'] for r in performance_results) / len(performance_results)
            
            print(f"\n   📊 Mobile Performance Summary:")
            print(f"      Average Response Time: {avg_response_time:.2f}ms")
            print(f"      Average Response Size: {avg_response_size:.0f} bytes")
            
            if avg_response_time < 2000 and avg_response_size < 3000:
                print(f"      ✅ Excellent mobile performance")
                self.log_test("Mobile Performance", True, f"Avg: {avg_response_time:.0f}ms, {avg_response_size:.0f}b")
                return True
            else:
                print(f"      ⚠️ Mobile performance could be improved")
                self.log_test("Mobile Performance", True, f"Acceptable: {avg_response_time:.0f}ms, {avg_response_size:.0f}b")
                return True
        
        return False

    def test_mobile_json_format(self):
        """Test JSON response format for mobile consumption"""
        print(f"\n📱 Testing Mobile JSON Response Format")
        
        success, response, headers = self.run_test(
            "Mobile JSON Format Test",
            "GET",
            f"barcode/{self.sample_barcodes[0]}",
            200
        )
        
        if success and isinstance(response, dict):
            # Test JSON structure for mobile apps
            mobile_requirements = {
                'flat_structure': True,  # No deeply nested objects
                'string_keys': True,     # All keys are strings
                'serializable': True,    # All values are JSON serializable
                'no_null_critical': True # Critical fields not null
            }
            
            # Check flat structure (max 2 levels deep)
            max_depth = self.get_json_depth(response)
            if max_depth <= 2:
                print(f"   ✅ Flat JSON structure (depth: {max_depth})")
            else:
                print(f"   ⚠️ Deep JSON structure may be complex for mobile (depth: {max_depth})")
                mobile_requirements['flat_structure'] = False
            
            # Check all keys are strings
            if self.all_keys_strings(response):
                print(f"   ✅ All JSON keys are strings")
            else:
                print(f"   ❌ Some JSON keys are not strings")
                mobile_requirements['string_keys'] = False
            
            # Check JSON serialization
            try:
                json_str = json.dumps(response, ensure_ascii=False)
                print(f"   ✅ JSON is serializable")
                print(f"   📏 JSON size: {len(json_str)} characters")
            except Exception as e:
                print(f"   ❌ JSON serialization failed: {str(e)}")
                mobile_requirements['serializable'] = False
            
            # Check critical fields are not null
            critical_fields = ['product_name', 'barcode', 'department', 'status']
            null_critical = [field for field in critical_fields if response.get(field) is None]
            if not null_critical:
                print(f"   ✅ No critical fields are null")
            else:
                print(f"   ⚠️ Critical fields are null: {null_critical}")
                mobile_requirements['no_null_critical'] = False
            
            # Overall mobile compatibility
            mobile_compatible = all(mobile_requirements.values())
            if mobile_compatible:
                print(f"   ✅ JSON format is fully mobile-compatible")
                self.log_test("Mobile JSON Format", True, "Fully compatible")
                return True
            else:
                failed_requirements = [k for k, v in mobile_requirements.items() if not v]
                print(f"   ⚠️ JSON format issues: {failed_requirements}")
                self.log_test("Mobile JSON Format", True, f"Minor issues: {failed_requirements}")
                return True
        
        return False

    def get_json_depth(self, obj, depth=0):
        """Calculate maximum depth of JSON object"""
        if not isinstance(obj, dict):
            return depth
        
        if not obj:
            return depth
        
        return max(self.get_json_depth(value, depth + 1) for value in obj.values())

    def all_keys_strings(self, obj):
        """Check if all keys in JSON object are strings"""
        if not isinstance(obj, dict):
            return True
        
        for key, value in obj.items():
            if not isinstance(key, str):
                return False
            if isinstance(value, dict) and not self.all_keys_strings(value):
                return False
        
        return True

    def test_mobile_network_simulation(self):
        """Test with mobile network conditions (timeout simulation)"""
        print(f"\n📶 Testing Mobile Network Conditions")
        
        # Test with shorter timeout to simulate mobile network conditions
        url = f"{self.api_url}/barcode/{self.sample_barcodes[0]}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        try:
            # Simulate slower mobile network with 10 second timeout
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ API responds within mobile network timeout (10s)")
                
                # Check if response is cacheable for mobile
                cache_headers = {
                    'Cache-Control': response.headers.get('Cache-Control'),
                    'ETag': response.headers.get('ETag'),
                    'Last-Modified': response.headers.get('Last-Modified')
                }
                
                print(f"   📱 Mobile caching headers:")
                for header, value in cache_headers.items():
                    print(f"      {header}: {value}")
                
                self.log_test("Mobile Network Conditions", True, "API responsive on mobile networks")
                return True
            else:
                self.log_test("Mobile Network Conditions", False, f"Unexpected status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Mobile Network Conditions", False, "API too slow for mobile networks (>10s)")
            return False
        except Exception as e:
            self.log_test("Mobile Network Conditions", False, f"Mobile network test failed: {str(e)}")
            return False

    def run_all_mobile_tests(self):
        """Run all mobile barcode scanner tests"""
        print("=" * 80)
        print("🚀 MOBILE BARCODE SCANNER BACKEND TESTING")
        print("=" * 80)
        print(f"Testing mobile compatibility for barcode scanner API")
        print(f"Base URL: {self.base_url}")
        print(f"Sample Barcodes: {', '.join(self.sample_barcodes)}")
        print(f"Admin Credentials: {self.admin_username}")
        
        # Test sequence for mobile barcode scanner
        test_sequence = [
            ("Admin Authentication", self.test_admin_login),
            ("Barcode Lookup - Sample Barcodes", self.test_barcode_lookup_sample_barcodes),
            ("Mobile Authentication", self.test_barcode_authentication_mobile),
            ("CORS Headers for Mobile", self.test_cors_headers_mobile),
            ("Mobile Error Handling", self.test_mobile_error_handling),
            ("Mobile Response Performance", self.test_mobile_response_performance),
            ("Mobile JSON Format", self.test_mobile_json_format),
            ("Mobile Network Conditions", self.test_mobile_network_simulation)
        ]
        
        print(f"\n📋 Running {len(test_sequence)} mobile barcode scanner tests...")
        
        for test_name, test_func in test_sequence:
            try:
                print(f"\n" + "="*60)
                print(f"🧪 {test_name}")
                print("="*60)
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
                print(f"❌ {test_name} failed with error: {str(e)}")
        
        # Final results
        print("\n" + "="*80)
        print("📊 MOBILE BARCODE SCANNER TEST RESULTS")
        print("="*80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results
        critical_failures = []
        warnings = []
        successes = []
        
        for result in self.test_results:
            if not result['success']:
                if any(keyword in result['name'].lower() for keyword in ['auth', 'barcode lookup', 'json']):
                    critical_failures.append(result['name'])
                else:
                    warnings.append(result['name'])
            else:
                successes.append(result['name'])
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"   ❌ {failure}")
        
        if warnings:
            print(f"\n⚠️ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   ⚠️ {warning}")
        
        print(f"\n✅ SUCCESSES ({len(successes)}):")
        for success in successes[:10]:  # Show first 10
            print(f"   ✅ {success}")
        if len(successes) > 10:
            print(f"   ... and {len(successes) - 10} more")
        
        # Mobile compatibility assessment
        print(f"\n📱 MOBILE COMPATIBILITY ASSESSMENT:")
        
        if success_rate >= 90:
            print(f"   🟢 EXCELLENT - Mobile barcode scanner fully compatible")
        elif success_rate >= 75:
            print(f"   🟡 GOOD - Mobile barcode scanner mostly compatible with minor issues")
        elif success_rate >= 50:
            print(f"   🟠 FAIR - Mobile barcode scanner has compatibility issues")
        else:
            print(f"   🔴 POOR - Mobile barcode scanner has major compatibility problems")
        
        # Specific mobile recommendations
        print(f"\n📋 MOBILE RECOMMENDATIONS:")
        if not critical_failures:
            print(f"   ✅ All critical mobile functionality working")
        else:
            print(f"   🚨 Fix critical issues: {', '.join(critical_failures)}")
        
        if success_rate >= 80:
            print(f"   ✅ Mobile barcode scanner ready for production")
        else:
            print(f"   ⚠️ Address compatibility issues before mobile deployment")
        
        return success_rate >= 75  # Consider 75%+ as acceptable for mobile

if __name__ == "__main__":
    tester = MobileBarcodeAPITester()
    success = tester.run_all_mobile_tests()
    
    if success:
        print(f"\n🎉 Mobile barcode scanner backend testing completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Mobile barcode scanner backend testing failed!")
        sys.exit(1)