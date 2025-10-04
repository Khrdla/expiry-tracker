#!/usr/bin/env python3
"""
COMPREHENSIVE IMAGE LOADING DEBUG TEST
Debug the image loading issue - check if the image URLs and serving are working properly

This test covers:
1. Check Product with Image: Find products that have image_url and verify values
2. Test Image Serving: Test if the /api/uploads/{filename} endpoint works
3. Verify Image Files: Check if actual image files exist in /app/uploads directory
4. Test Full URL: Test complete image URL that frontend tries to access
5. Check CORS/Headers: Verify CORS or header issues preventing image loading
"""

import requests
import json
import os
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"
UPLOADS_DIR = "/app/uploads"

class ComprehensiveImageDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, success, details):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}")
                return True
            else:
                self.log_result("Authentication", False, f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def check_uploads_directory(self):
        """Check if uploads directory exists and list files"""
        try:
            if os.path.exists(UPLOADS_DIR):
                files = os.listdir(UPLOADS_DIR)
                file_count = len(files)
                
                if file_count > 0:
                    # Show first 10 files as examples
                    sample_files = files[:10]
                    self.log_result("Uploads Directory Check", True, 
                                  f"Directory exists with {file_count} files. Sample: {sample_files}")
                    return files
                else:
                    self.log_result("Uploads Directory Check", False, "Directory exists but is empty")
                    return []
            else:
                self.log_result("Uploads Directory Check", False, "Directory does not exist")
                return []
                
        except Exception as e:
            self.log_result("Uploads Directory Check", False, f"Exception: {str(e)}")
            return []
    
    def find_products_with_images(self):
        """Find products that have image_url set"""
        try:
            response = self.session.get(f"{BACKEND_URL}/products?limit=1000")
            
            if response.status_code == 200:
                products = response.json()
                products_with_images = []
                
                for product in products:
                    if product.get('image_url'):
                        products_with_images.append({
                            'id': product.get('id'),
                            'product_name': product.get('product_name'),
                            'image_url': product.get('image_url'),
                            'barcode': product.get('barcode', 'N/A')
                        })
                
                if products_with_images:
                    self.log_result("Products with Images", True, 
                                  f"Found {len(products_with_images)} products with images out of {len(products)} total")
                    
                    # Show details of first 5 products
                    print("\n📋 PRODUCTS WITH IMAGES:")
                    for i, product in enumerate(products_with_images[:5]):
                        print(f"   {i+1}. {product['product_name']}")
                        print(f"      Image URL: {product['image_url']}")
                        print(f"      Product ID: {product['id']}")
                        print(f"      Barcode: {product['barcode']}")
                        print()
                    
                    return products_with_images
                else:
                    self.log_result("Products with Images", False, f"No products found with image_url set out of {len(products)} total products")
                    return []
            else:
                self.log_result("Products with Images", False, 
                              f"Failed to fetch products: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_result("Products with Images", False, f"Exception: {str(e)}")
            return []
    
    def test_image_serving_endpoint(self, filename):
        """Test the /api/uploads/{filename} endpoint"""
        try:
            # Test the API endpoint
            api_url = f"{BACKEND_URL}/uploads/{filename}"
            response = self.session.get(api_url)
            
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('Content-Type', 'unknown')
                content_length = len(response.content)
                cache_control = response.headers.get('Cache-Control', 'none')
                
                self.log_result(f"Image Serving API - {filename}", True, 
                              f"Status: {response.status_code}, Content-Type: {content_type}, "
                              f"Size: {content_length} bytes, Cache-Control: {cache_control}")
                return True
            else:
                self.log_result(f"Image Serving API - {filename}", False, 
                              f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_result(f"Image Serving API - {filename}", False, f"Exception: {str(e)}")
            return False
    
    def test_full_frontend_url(self, image_url):
        """Test the complete URL that frontend would use"""
        try:
            # Construct the full URL as frontend would
            if image_url.startswith('/uploads/'):
                filename = image_url.replace('/uploads/', '')
                full_url = f"https://inventory-master-78.preview.emergentagent.com/api/uploads/{filename}"
            else:
                full_url = f"https://inventory-master-78.preview.emergentagent.com{image_url}"
            
            # Test without authentication (as frontend would)
            response = requests.get(full_url)
            
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('Content-Type', 'unknown')
                content_length = len(response.content)
                
                self.log_result(f"Frontend URL Test", True, 
                              f"URL: {full_url}, Status: {response.status_code}, "
                              f"Content-Type: {content_type}, Size: {content_length} bytes")
                return True
            else:
                self.log_result(f"Frontend URL Test", False, 
                              f"URL: {full_url}, Status: {response.status_code}, "
                              f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_result(f"Frontend URL Test", False, f"Exception: {str(e)}")
            return False
    
    def check_cors_headers(self, filename):
        """Check CORS headers for image serving"""
        try:
            api_url = f"{BACKEND_URL}/uploads/{filename}"
            
            # Test OPTIONS request (preflight)
            options_response = requests.options(api_url)
            
            # Test GET request
            get_response = requests.get(api_url)
            
            cors_headers = {}
            for header_name in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 
                              'Access-Control-Allow-Headers', 'Access-Control-Allow-Credentials']:
                cors_headers[header_name] = get_response.headers.get(header_name, 'Not set')
            
            self.log_result("CORS Headers Check", True, 
                          f"CORS headers: {json.dumps(cors_headers, indent=2)}")
            
            return cors_headers
            
        except Exception as e:
            self.log_result("CORS Headers Check", False, f"Exception: {str(e)}")
            return {}
    
    def verify_file_exists(self, image_url):
        """Verify if the actual file exists on disk"""
        try:
            if image_url.startswith('/uploads/'):
                filename = image_url.replace('/uploads/', '')
                file_path = os.path.join(UPLOADS_DIR, filename)
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    self.log_result(f"File Exists Check - {filename}", True, 
                                  f"File exists at {file_path}, Size: {file_size} bytes")
                    return True
                else:
                    self.log_result(f"File Exists Check - {filename}", False, 
                                  f"File does not exist at {file_path}")
                    return False
            else:
                self.log_result(f"File Exists Check", False, 
                              f"Invalid image_url format: {image_url}")
                return False
                
        except Exception as e:
            self.log_result(f"File Exists Check", False, f"Exception: {str(e)}")
            return False
    
    def test_image_upload_functionality(self):
        """Test image upload functionality by uploading a test image"""
        try:
            # First, find a product without an image to test upload
            response = self.session.get(f"{BACKEND_URL}/products?limit=10")
            
            if response.status_code != 200:
                self.log_result("Image Upload Test Setup", False, "Cannot fetch products for upload test")
                return False
            
            products = response.json()
            test_product = None
            
            for product in products:
                if not product.get('image_url'):
                    test_product = product
                    break
            
            if not test_product:
                self.log_result("Image Upload Test Setup", False, "No products without images found for testing")
                return False
            
            # Create a small test image (1x1 pixel PNG)
            import base64
            from io import BytesIO
            
            # Minimal PNG data (1x1 transparent pixel)
            png_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=='
            )
            
            # Upload the test image
            files = {'image': ('test.png', BytesIO(png_data), 'image/png')}
            upload_url = f"{BACKEND_URL}/products/{test_product['id']}/image"
            
            upload_response = self.session.post(upload_url, files=files)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                image_url = upload_data.get('image_url')
                
                if image_url:
                    self.log_result("Image Upload Test", True, 
                                  f"Successfully uploaded test image: {image_url}")
                    
                    # Test if the uploaded image can be served
                    if image_url.startswith('/uploads/'):
                        filename = image_url.replace('/uploads/', '')
                        return self.test_image_serving_endpoint(filename)
                    
                    return True
                else:
                    self.log_result("Image Upload Test", False, "Upload succeeded but no image_url returned")
                    return False
            else:
                self.log_result("Image Upload Test", False, 
                              f"Upload failed: {upload_response.status_code} - {upload_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Image Upload Test", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_debug(self):
        """Run comprehensive image loading debug"""
        print("🔍 COMPREHENSIVE IMAGE LOADING DEBUG TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print(f"Uploads Directory: {UPLOADS_DIR}")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
        
        # Step 2: Check uploads directory
        print("\n📁 CHECKING UPLOADS DIRECTORY")
        print("-" * 40)
        uploaded_files = self.check_uploads_directory()
        
        # Step 3: Find products with images
        print("\n🖼️ FINDING PRODUCTS WITH IMAGES")
        print("-" * 40)
        products_with_images = self.find_products_with_images()
        
        # Step 4: Test specific products and their images
        if products_with_images:
            print("\n🧪 TESTING IMAGE SERVING FOR SPECIFIC PRODUCTS")
            print("-" * 50)
            
            for i, product in enumerate(products_with_images[:3]):  # Test first 3 products
                print(f"\n--- Testing Product {i+1}: {product['product_name']} ---")
                image_url = product['image_url']
                
                # Extract filename from image_url
                if image_url.startswith('/uploads/'):
                    filename = image_url.replace('/uploads/', '')
                    
                    # Test 1: Verify file exists on disk
                    self.verify_file_exists(image_url)
                    
                    # Test 2: Test API endpoint
                    self.test_image_serving_endpoint(filename)
                    
                    # Test 3: Test full frontend URL
                    self.test_full_frontend_url(image_url)
                    
                    # Test 4: Check CORS headers
                    self.check_cors_headers(filename)
                    
                    print()
        
        # Step 5: Test with files that exist in uploads directory
        elif uploaded_files:
            print("\n🔧 TESTING WITH ACTUAL FILES IN UPLOADS DIRECTORY")
            print("-" * 50)
            
            for filename in uploaded_files[:3]:  # Test first 3 files
                print(f"\n--- Testing file: {filename} ---")
                
                # Test API endpoint
                self.test_image_serving_endpoint(filename)
                
                # Test full URL
                image_url = f"/uploads/{filename}"
                self.test_full_frontend_url(image_url)
                
                # Check CORS
                self.check_cors_headers(filename)
                
                print()
        
        # Step 6: Test image upload functionality
        print("\n📤 TESTING IMAGE UPLOAD FUNCTIONALITY")
        print("-" * 40)
        self.test_image_upload_functionality()
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 40)
        
        success_rate = (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.total_tests - self.passed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n🎯 SPECIFIC FINDINGS:")
        
        if not uploaded_files:
            print("   ⚠️  No files found in /app/uploads directory")
        else:
            print(f"   ✅ Found {len(uploaded_files)} files in uploads directory")
        
        if not products_with_images:
            print("   ⚠️  No products have image_url set in database")
        else:
            print(f"   ✅ Found {len(products_with_images)} products with image_url set")
        
        print("\n🔧 RECOMMENDATIONS:")
        
        if not uploaded_files and not products_with_images:
            print("   1. No images have been uploaded yet - test image upload functionality")
            print("   2. Upload test images to verify the complete image pipeline")
        elif uploaded_files and not products_with_images:
            print("   1. Files exist in uploads directory but no products reference them")
            print("   2. Check image upload process - image_url may not be saved to database")
        elif products_with_images and not uploaded_files:
            print("   1. Products have image_url but files don't exist on disk")
            print("   2. Files may have been deleted or moved")
        
        if success_rate < 50:
            print("   3. Check backend logs for detailed error information")
            print("   4. Verify file permissions on /app/uploads directory")
            print("   5. Ensure image serving endpoint is properly configured")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        if success_rate >= 80:
            print("   ✅ Image infrastructure appears to be working correctly")
        elif success_rate >= 50:
            print("   ⚠️  Mixed results - some components working, others need fixes")
        else:
            print("   ❌ Critical issues found in image storage/serving infrastructure")

def main():
    """Main function"""
    tester = ComprehensiveImageDebugTester()
    tester.run_comprehensive_debug()
    
    # Return appropriate exit code
    success_rate = (tester.passed_tests/tester.total_tests*100) if tester.total_tests > 0 else 0
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())