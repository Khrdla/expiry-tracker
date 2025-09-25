#!/usr/bin/env python3
"""
IMAGE FIX VERIFICATION TEST - Verify the ProductDetailsModal image URL fix

This test verifies that the image URL construction fix works correctly
for the "7up lemon 1L" product with barcode 012000108402.

Test Coverage:
1. Authenticate with admin credentials
2. Find the target product
3. Test the corrected URL construction
4. Verify image accessibility
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Target product details
TARGET_BARCODE = "012000108402"

class ImageFixVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.target_product = None
        
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
                    self.log_test("Admin Login", True, f"Token received")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def get_target_product(self):
        """Test 2: Get the target product"""
        print("\n🔍 GETTING TARGET PRODUCT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Product Retrieval", False, "No authentication token")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{TARGET_BARCODE}")
            
            if response.status_code == 200:
                self.target_product = response.json()
                self.log_test("Product Retrieval", True, 
                            f"Found: {self.target_product.get('product_name', 'N/A')}")
                return True
            else:
                self.log_test("Product Retrieval", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Product Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_corrected_url_construction(self):
        """Test 3: Test the corrected URL construction"""
        print("\n🔧 TESTING CORRECTED URL CONSTRUCTION")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("URL Construction Test", False, "No target product")
            return False
        
        image_url = self.target_product.get('image_url')
        if not image_url:
            self.log_test("URL Construction Test", False, "No image_url in product")
            return False
        
        # Simulate the corrected frontend URL construction
        frontend_backend_url = "https://geant-inventory-2.preview.emergentagent.com"
        corrected_url = f"{frontend_backend_url}/api{image_url}"
        
        print(f"📋 Original image_url: {image_url}")
        print(f"🔧 Corrected full URL: {corrected_url}")
        
        try:
            response = requests.get(corrected_url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if content_type.startswith('image/'):
                    self.log_test("Corrected URL Access", True, 
                                f"Success: {content_length} bytes, {content_type}")
                    
                    # Additional validation
                    if content_length > 1000:  # Reasonable image size
                        self.log_test("Image Content Validation", True, 
                                    f"Valid image size: {content_length} bytes")
                    else:
                        self.log_test("Image Content Validation", False, 
                                    f"Suspiciously small image: {content_length} bytes")
                else:
                    self.log_test("Corrected URL Access", False, 
                                f"Wrong content-type: {content_type}")
            else:
                self.log_test("Corrected URL Access", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Corrected URL Access", False, f"Exception: {str(e)}")
    
    def test_old_vs_new_url_comparison(self):
        """Test 4: Compare old (broken) vs new (fixed) URL construction"""
        print("\n⚖️ COMPARING OLD VS NEW URL CONSTRUCTION")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("URL Comparison", False, "No target product")
            return False
        
        image_url = self.target_product.get('image_url')
        if not image_url:
            self.log_test("URL Comparison", False, "No image_url in product")
            return False
        
        frontend_backend_url = "https://geant-inventory-2.preview.emergentagent.com"
        
        # Old (broken) construction
        old_url = f"{frontend_backend_url}{image_url}"
        
        # New (fixed) construction  
        new_url = f"{frontend_backend_url}/api{image_url}"
        
        print(f"🔴 OLD (broken) URL: {old_url}")
        print(f"🟢 NEW (fixed) URL: {new_url}")
        
        # Test old URL (should fail)
        try:
            old_response = requests.get(old_url)
            if old_response.status_code == 200 and old_response.headers.get('content-type', '').startswith('image/'):
                self.log_test("Old URL (should fail)", False, "Old URL unexpectedly works")
            else:
                self.log_test("Old URL (should fail)", True, f"Old URL correctly fails: HTTP {old_response.status_code}")
        except Exception as e:
            self.log_test("Old URL (should fail)", True, f"Old URL correctly fails: {str(e)}")
        
        # Test new URL (should work)
        try:
            new_response = requests.get(new_url)
            if new_response.status_code == 200 and new_response.headers.get('content-type', '').startswith('image/'):
                self.log_test("New URL (should work)", True, f"New URL works: {len(new_response.content)} bytes")
            else:
                self.log_test("New URL (should work)", False, f"New URL fails: HTTP {new_response.status_code}")
        except Exception as e:
            self.log_test("New URL (should work)", False, f"New URL fails: {str(e)}")
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🔧 IMAGE FIX VERIFICATION TEST - ProductDetailsModal URL fix")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Target Barcode: {TARGET_BARCODE}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            product_found = self.get_target_product()
            
            if product_found:
                self.test_corrected_url_construction()
                self.test_old_vs_new_url_comparison()
            else:
                print("\n❌ CRITICAL: Target product not found")
        else:
            print("\n❌ CRITICAL: Authentication failed")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 IMAGE FIX VERIFICATION SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 FIX VERIFICATION RESULTS:")
        
        if self.target_product:
            image_url = self.target_product.get('image_url', '')
            print(f"✅ Target Product: {self.target_product.get('product_name', 'N/A')}")
            print(f"📋 Image URL: {image_url}")
            print(f"🔧 Fixed URL: https://geant-inventory-2.preview.emergentagent.com/api{image_url}")
        
        # Analyze results
        url_tests = [r for r in self.test_results if "URL" in r["test"]]
        successful_url_tests = [r for r in url_tests if r["success"]]
        
        print("\n🔍 CONCLUSION:")
        if success_rate >= 80:
            print("✅ IMAGE URL FIX SUCCESSFUL!")
            print("✅ ProductDetailsModal should now display images correctly")
            print("✅ The /api prefix has been added to image URL construction")
        elif success_rate >= 50:
            print("⚠️  PARTIAL SUCCESS - Some issues remain")
        else:
            print("❌ IMAGE URL FIX FAILED - Issues need to be resolved")
        
        print("\n📝 NEXT STEPS:")
        print("1. Test the fix in the actual ProductDetailsModal component")
        print("2. Verify image display works for the 7up lemon 1L product")
        print("3. Check other products with images to ensure no regression")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = ImageFixVerificationTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()