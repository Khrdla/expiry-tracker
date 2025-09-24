#!/usr/bin/env python3
"""
IMAGE URL DEBUG TEST - Specific investigation for 7up lemon 1L product image issue

This test focuses specifically on debugging the image URL issue for the "7up lemon 1L" 
product with barcode 012000108402 as reported by the user.

Test Coverage:
1. Find the specific product by barcode or name
2. Check image_url field in database
3. Test image serving through /api/uploads/{filename} endpoint
4. Verify URL format and file existence
5. Test direct image access

User Report: Successfully uploaded an image but it's not displaying in ProductDetailsModal.
The constructed URL appears to be very long, suggesting storage/serving issue.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Target product details from review request
TARGET_BARCODE = "012000108402"
TARGET_PRODUCT_NAME = "7up lemon"

class ImageDebugTester:
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
    
    def find_target_product(self):
        """Test 2: Find the specific 7up lemon 1L product"""
        print("\n🔍 FINDING TARGET PRODUCT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Product Search Setup", False, "No authentication token available")
            return False
        
        # Method 1: Try direct barcode lookup
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{TARGET_BARCODE}")
            
            if response.status_code == 200:
                self.target_product = response.json()
                self.log_test("Direct Barcode Lookup", True, 
                            f"Found: {self.target_product.get('product_name', 'N/A')}")
                return True
            elif response.status_code == 404:
                self.log_test("Direct Barcode Lookup", False, "Product not found with barcode")
            else:
                self.log_test("Direct Barcode Lookup", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Direct Barcode Lookup", False, f"Exception: {str(e)}")
        
        # Method 2: Search by product name
        try:
            response = self.session.get(f"{BACKEND_URL}/search", params={"q": TARGET_PRODUCT_NAME})
            
            if response.status_code == 200:
                products = response.json()
                
                if products:
                    # Look for products containing "7up" and "lemon"
                    matching_products = []
                    for product in products:
                        name = product.get('product_name', '').lower()
                        if '7up' in name and 'lemon' in name:
                            matching_products.append(product)
                    
                    if matching_products:
                        self.target_product = matching_products[0]  # Take first match
                        self.log_test("Product Name Search", True, 
                                    f"Found: {self.target_product.get('product_name', 'N/A')}")
                        return True
                    else:
                        self.log_test("Product Name Search", False, 
                                    f"No matching products found in {len(products)} results")
                else:
                    self.log_test("Product Name Search", False, "No products returned from search")
            else:
                self.log_test("Product Name Search", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Product Name Search", False, f"Exception: {str(e)}")
        
        # Method 3: Get all products and search manually
        try:
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 1000})
            
            if response.status_code == 200:
                products = response.json()
                
                # Search for products with barcode or name match
                for product in products:
                    barcode = product.get('barcode', '')
                    name = product.get('product_name', '').lower()
                    
                    if (barcode == TARGET_BARCODE or 
                        ('7up' in name and 'lemon' in name)):
                        self.target_product = product
                        self.log_test("Manual Product Search", True, 
                                    f"Found: {product.get('product_name', 'N/A')} (Barcode: {barcode})")
                        return True
                
                self.log_test("Manual Product Search", False, 
                            f"No matching products found in {len(products)} total products")
            else:
                self.log_test("Manual Product Search", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Manual Product Search", False, f"Exception: {str(e)}")
        
        return False
    
    def analyze_image_url_field(self):
        """Test 3: Analyze the image_url field in the target product"""
        print("\n🖼️ ANALYZING IMAGE URL FIELD")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("Image URL Analysis", False, "No target product found")
            return False
        
        image_url = self.target_product.get('image_url')
        
        if not image_url:
            self.log_test("Image URL Field", False, "No image_url field found in product data")
            return False
        
        # Log the exact image_url value
        print(f"📋 EXACT IMAGE_URL VALUE: '{image_url}'")
        
        # Analyze the URL format
        if image_url.startswith('/uploads/'):
            self.log_test("Image URL Format", True, f"Correct format: {image_url}")
            filename = image_url.replace('/uploads/', '')
            
            # Check filename format
            if '.' in filename and len(filename) > 10:
                self.log_test("Filename Format", True, f"Valid filename: {filename}")
            else:
                self.log_test("Filename Format", False, f"Suspicious filename: {filename}")
                
        elif image_url.startswith('uploads/'):
            self.log_test("Image URL Format", False, f"Missing leading slash: {image_url}")
        elif len(image_url) > 200:
            self.log_test("Image URL Format", False, f"URL too long ({len(image_url)} chars): {image_url[:100]}...")
        else:
            self.log_test("Image URL Format", False, f"Unexpected format: {image_url}")
        
        return True
    
    def test_image_serving_endpoint(self):
        """Test 4: Test the /api/uploads/{filename} endpoint"""
        print("\n🌐 TESTING IMAGE SERVING ENDPOINT")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("Image Serving Setup", False, "No target product found")
            return False
        
        image_url = self.target_product.get('image_url')
        if not image_url:
            self.log_test("Image Serving Setup", False, "No image_url in product")
            return False
        
        # Extract filename from URL
        if image_url.startswith('/uploads/'):
            filename = image_url.replace('/uploads/', '')
        elif image_url.startswith('uploads/'):
            filename = image_url.replace('uploads/', '')
        else:
            self.log_test("Filename Extraction", False, f"Cannot extract filename from: {image_url}")
            return False
        
        # Test direct API endpoint access
        try:
            api_url = f"{BACKEND_URL}/uploads/{filename}"
            response = requests.get(api_url)  # No auth needed for public images
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if content_type.startswith('image/'):
                    self.log_test("Image API Endpoint", True, 
                                f"Success: {content_length} bytes, {content_type}")
                else:
                    self.log_test("Image API Endpoint", False, 
                                f"Wrong content-type: {content_type}")
            elif response.status_code == 404:
                self.log_test("Image API Endpoint", False, "Image file not found (404)")
            else:
                self.log_test("Image API Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Image API Endpoint", False, f"Exception: {str(e)}")
        
        # Test alternative URL constructions
        alternative_urls = [
            f"https://stockmate-14.preview.emergentagent.com/uploads/{filename}",  # Direct static
            f"{BACKEND_URL.replace('/api', '')}/uploads/{filename}",  # Without /api
        ]
        
        for alt_url in alternative_urls:
            try:
                response = requests.get(alt_url)
                test_name = f"Alternative URL ({alt_url.split('/')[-2]}/...)"
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if content_type.startswith('image/'):
                        self.log_test(test_name, True, f"Working: {content_type}")
                    else:
                        self.log_test(test_name, False, f"Wrong content-type: {content_type}")
                else:
                    self.log_test(test_name, False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Alternative URL Test", False, f"Exception: {str(e)}")
    
    def test_file_system_existence(self):
        """Test 5: Check if image file exists in /app/uploads directory"""
        print("\n📁 TESTING FILE SYSTEM EXISTENCE")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("File System Check", False, "No target product found")
            return False
        
        image_url = self.target_product.get('image_url')
        if not image_url:
            self.log_test("File System Check", False, "No image_url in product")
            return False
        
        # Extract filename
        if image_url.startswith('/uploads/'):
            filename = image_url.replace('/uploads/', '')
        elif image_url.startswith('uploads/'):
            filename = image_url.replace('uploads/', '')
        else:
            filename = image_url  # Use as-is if no prefix
        
        # Check if file exists
        file_path = f"/app/uploads/{filename}"
        
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                self.log_test("File Existence", True, f"File exists: {file_size} bytes at {file_path}")
                
                # Check file permissions
                if os.access(file_path, os.R_OK):
                    self.log_test("File Permissions", True, "File is readable")
                else:
                    self.log_test("File Permissions", False, "File is not readable")
            else:
                self.log_test("File Existence", False, f"File not found at {file_path}")
                
                # List files in uploads directory for debugging
                try:
                    uploads_files = os.listdir("/app/uploads")
                    if uploads_files:
                        print(f"📂 Files in /app/uploads: {uploads_files[:10]}")  # Show first 10
                        
                        # Look for similar filenames
                        similar_files = [f for f in uploads_files if filename[:10] in f or f[:10] in filename]
                        if similar_files:
                            self.log_test("Similar Files Found", True, f"Similar: {similar_files}")
                        else:
                            self.log_test("Similar Files Found", False, "No similar filenames found")
                    else:
                        self.log_test("Uploads Directory", False, "Uploads directory is empty")
                        
                except Exception as e:
                    self.log_test("Directory Listing", False, f"Cannot list uploads: {str(e)}")
                    
        except Exception as e:
            self.log_test("File System Check", False, f"Exception: {str(e)}")
    
    def test_product_details_modal_url_construction(self):
        """Test 6: Simulate how ProductDetailsModal constructs image URLs"""
        print("\n🔧 TESTING URL CONSTRUCTION LOGIC")
        print("=" * 50)
        
        if not self.target_product:
            self.log_test("URL Construction", False, "No target product found")
            return False
        
        image_url = self.target_product.get('image_url')
        if not image_url:
            self.log_test("URL Construction", False, "No image_url in product")
            return False
        
        # Simulate different URL construction methods that frontend might use
        backend_url = "https://stockmate-14.preview.emergentagent.com"
        
        construction_methods = [
            ("Direct image_url", image_url),
            ("Backend + image_url", f"{backend_url}{image_url}"),
            ("Backend/api + image_url", f"{backend_url}/api{image_url}"),
            ("Remove /api prefix", image_url.replace('/api', '')),
        ]
        
        for method_name, constructed_url in construction_methods:
            try:
                response = requests.get(constructed_url)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if content_type.startswith('image/'):
                        self.log_test(f"URL Construction - {method_name}", True, 
                                    f"Working: {constructed_url}")
                    else:
                        self.log_test(f"URL Construction - {method_name}", False, 
                                    f"Wrong content-type: {content_type}")
                else:
                    self.log_test(f"URL Construction - {method_name}", False, 
                                f"HTTP {response.status_code}: {constructed_url}")
                    
            except Exception as e:
                self.log_test(f"URL Construction - {method_name}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all image debug tests"""
        print("🖼️ IMAGE URL DEBUG TEST - 7up lemon 1L product investigation")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Target Barcode: {TARGET_BARCODE}")
        print(f"Target Product: {TARGET_PRODUCT_NAME}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            product_found = self.find_target_product()
            
            if product_found:
                self.analyze_image_url_field()
                self.test_image_serving_endpoint()
                self.test_file_system_existence()
                self.test_product_details_modal_url_construction()
            else:
                print("\n❌ CRITICAL: Target product not found - cannot proceed with image tests")
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary with specific findings"""
        print("\n" + "=" * 80)
        print("📊 IMAGE DEBUG TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 SPECIFIC FINDINGS FOR 7UP LEMON 1L:")
        
        if self.target_product:
            print(f"✅ Product Found: {self.target_product.get('product_name', 'N/A')}")
            print(f"📋 Product ID: {self.target_product.get('id', 'N/A')}")
            print(f"📊 Barcode: {self.target_product.get('barcode', 'N/A')}")
            
            image_url = self.target_product.get('image_url')
            if image_url:
                print(f"🖼️ Image URL: '{image_url}'")
                print(f"📏 URL Length: {len(image_url)} characters")
                
                if len(image_url) > 200:
                    print("⚠️  WARNING: Image URL is very long - this may be the issue!")
                
                # Provide recommended fix
                if image_url.startswith('/uploads/'):
                    print("✅ URL Format: Correct (/uploads/filename)")
                else:
                    print("❌ URL Format: Incorrect - should start with /uploads/")
            else:
                print("❌ Image URL: Not found in product data")
        else:
            print("❌ Product: Not found in database")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        
        # Analyze test results to provide specific recommendations
        image_tests = [r for r in self.test_results if "Image" in r["test"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        if any("Image URL Format" in t["test"] and not t["success"] for t in failed_tests):
            print("1. Fix image_url format in database - ensure it starts with '/uploads/'")
        
        if any("File Existence" in t["test"] and not t["success"] for t in failed_tests):
            print("2. Check if image file was actually saved to /app/uploads directory")
        
        if any("Image API Endpoint" in t["test"] and not t["success"] for t in failed_tests):
            print("3. Verify /api/uploads/{filename} endpoint is working correctly")
        
        if any("URL Construction" in t["test"] and not t["success"] for t in failed_tests):
            print("4. Fix frontend ProductDetailsModal URL construction logic")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        if success_rate >= 80:
            print("✅ Image infrastructure appears to be working correctly")
            print("✅ Issue may be in frontend ProductDetailsModal component")
        elif success_rate >= 50:
            print("⚠️  Mixed results - some components working, others need fixes")
        else:
            print("❌ Critical issues found in image storage/serving infrastructure")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = ImageDebugTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()