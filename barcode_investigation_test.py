#!/usr/bin/env python3
"""
URGENT BARCODE SEARCH INVESTIGATION
===================================
User reported that barcode "3222474131326" shows "No products found" in the waste form search.
This test investigates the specific barcode issue and verifies search functionality.

CRITICAL INVESTIGATION REQUIRED:
1. Test Specific Barcode: Check if barcode "3222474131326" exists in the database
2. Verify Search API Endpoints: Test both search methods used by WasteReports
3. Authentication Check: Ensure admin credentials still working
4. Database Verification: Check if barcode exists in products collection
5. Search Functionality Debug: Test search with product names vs barcodes
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"
PROBLEM_BARCODE = "3222474131326"  # The barcode user reported as not found

# Known working barcodes from previous tests for comparison
KNOWN_WORKING_BARCODES = [
    "3222471081716",  # Apple Juice Box 1L
    "3222471052747",  # Lemonade 150Cl
    "3222471075722",  # Mountain Water 6X50Cl
    "3222471081273"   # Orange Peach Apricot Nectar Box 1L
]

class BarcodeSearchInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.critical_issues = []
        
    def log_test(self, test_name, success, details, is_critical=False):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if not success and is_critical:
            self.critical_issues.append(f"❌ CRITICAL: {test_name} - {details}")
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Admin Authentication", True, f"Successfully authenticated as {ADMIN_USERNAME}")
                return True
            else:
                self.log_test("Admin Authentication", False, 
                    f"Failed with status {response.status_code}: {response.text}", is_critical=True)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}", is_critical=True)
            return False
    
    def test_specific_barcode_lookup(self, barcode, expected_found=None):
        """Test direct barcode lookup API"""
        try:
            response = self.session.get(f"{BACKEND_URL}/barcode/{barcode}")
            
            if response.status_code == 200:
                data = response.json()
                product_name = data.get("product_name", "Unknown")
                department = data.get("department", "Unknown")
                price = data.get("purchase_price", 0)
                currency = data.get("purchase_currency", "Unknown")
                
                self.log_test(f"Barcode Lookup: {barcode}", True, 
                    f"FOUND: {product_name} (Dept: {department}, Price: {price} {currency})")
                return True, data
                
            elif response.status_code == 404:
                self.log_test(f"Barcode Lookup: {barcode}", expected_found is False, 
                    f"NOT FOUND: Product with barcode {barcode} does not exist in database")
                return False, None
                
            else:
                self.log_test(f"Barcode Lookup: {barcode}", False, 
                    f"Unexpected status {response.status_code}: {response.text}", is_critical=True)
                return False, None
                
        except Exception as e:
            self.log_test(f"Barcode Lookup: {barcode}", False, f"Exception: {str(e)}", is_critical=True)
            return False, None
    
    def test_product_search(self, query, expected_results=None):
        """Test product search API"""
        try:
            response = self.session.get(f"{BACKEND_URL}/search", params={"q": query, "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data) if isinstance(data, list) else 0
                
                if results_count > 0:
                    # Show first result details
                    first_result = data[0]
                    product_name = first_result.get("product_name", "Unknown")
                    barcode = first_result.get("barcode", "No barcode")
                    
                    self.log_test(f"Product Search: '{query}'", True, 
                        f"Found {results_count} results. First: {product_name} (Barcode: {barcode})")
                else:
                    self.log_test(f"Product Search: '{query}'", expected_results == 0, 
                        f"No products found for query '{query}'")
                
                return results_count > 0, data
                
            else:
                self.log_test(f"Product Search: '{query}'", False, 
                    f"Search failed with status {response.status_code}: {response.text}", is_critical=True)
                return False, None
                
        except Exception as e:
            self.log_test(f"Product Search: '{query}'", False, f"Exception: {str(e)}", is_critical=True)
            return False, None
    
    def verify_database_integrity(self):
        """Check database for barcode patterns and integrity"""
        try:
            # Get all products to analyze barcode patterns
            response = self.session.get(f"{BACKEND_URL}/products", params={"limit": 1000})
            
            if response.status_code == 200:
                products = response.json()
                total_products = len(products)
                
                # Analyze barcode patterns
                barcodes_with_data = []
                barcode_patterns = {}
                
                for product in products:
                    barcode = product.get("barcode")
                    if barcode and barcode.strip():
                        barcodes_with_data.append({
                            "barcode": barcode,
                            "product_name": product.get("product_name", "Unknown"),
                            "department": product.get("department", "Unknown")
                        })
                        
                        # Analyze barcode patterns (first 6 digits)
                        pattern = barcode[:6] if len(barcode) >= 6 else barcode
                        barcode_patterns[pattern] = barcode_patterns.get(pattern, 0) + 1
                
                self.log_test("Database Integrity Check", True, 
                    f"Found {total_products} total products, {len(barcodes_with_data)} have barcodes")
                
                # Check if problem barcode pattern exists
                problem_pattern = PROBLEM_BARCODE[:6]
                pattern_count = barcode_patterns.get(problem_pattern, 0)
                
                self.log_test(f"Barcode Pattern Analysis", True, 
                    f"Pattern '{problem_pattern}' found in {pattern_count} products")
                
                # Show some example barcodes for comparison
                print(f"\n📊 BARCODE ANALYSIS:")
                print(f"   Total products: {total_products}")
                print(f"   Products with barcodes: {len(barcodes_with_data)}")
                print(f"   Problem barcode: {PROBLEM_BARCODE}")
                print(f"   Problem pattern ({problem_pattern}): {pattern_count} matches")
                
                # Show first 5 barcodes for pattern comparison
                print(f"\n🔍 SAMPLE BARCODES IN DATABASE:")
                for i, item in enumerate(barcodes_with_data[:5]):
                    print(f"   {i+1}. {item['barcode']} - {item['product_name']}")
                
                return True, {"total_products": total_products, "barcodes_count": len(barcodes_with_data)}
                
            else:
                self.log_test("Database Integrity Check", False, 
                    f"Failed to fetch products: {response.status_code}", is_critical=True)
                return False, None
                
        except Exception as e:
            self.log_test("Database Integrity Check", False, f"Exception: {str(e)}", is_critical=True)
            return False, None
    
    def test_waste_reports_search_endpoints(self):
        """Test the specific endpoints used by WasteReports form"""
        print(f"\n🗑️ TESTING WASTE REPORTS SEARCH ENDPOINTS:")
        
        # Test 1: Direct barcode lookup (primary method)
        found, data = self.test_specific_barcode_lookup(PROBLEM_BARCODE)
        
        # Test 2: Product search (fallback method)
        search_found, search_data = self.test_product_search(PROBLEM_BARCODE)
        
        # Test 3: Test with known working barcodes for comparison
        print(f"\n🔍 TESTING KNOWN WORKING BARCODES FOR COMPARISON:")
        working_count = 0
        for barcode in KNOWN_WORKING_BARCODES:
            found_working, _ = self.test_specific_barcode_lookup(barcode, expected_found=True)
            if found_working:
                working_count += 1
        
        self.log_test("Known Working Barcodes", working_count == len(KNOWN_WORKING_BARCODES), 
            f"{working_count}/{len(KNOWN_WORKING_BARCODES)} known barcodes working correctly")
        
        return found or search_found
    
    def run_investigation(self):
        """Run complete barcode search investigation"""
        print("🚨 URGENT BARCODE SEARCH INVESTIGATION")
        print("=" * 50)
        print(f"Investigating barcode: {PROBLEM_BARCODE}")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ CRITICAL: Cannot proceed without authentication")
            return False
        
        # Step 2: Database integrity check
        print(f"\n📊 DATABASE INTEGRITY VERIFICATION:")
        self.verify_database_integrity()
        
        # Step 3: Test specific barcode and search endpoints
        problem_found = self.test_waste_reports_search_endpoints()
        
        # Step 4: Additional search method tests
        print(f"\n🔍 ADDITIONAL SEARCH METHOD TESTS:")
        
        # Test partial barcode search
        partial_barcode = PROBLEM_BARCODE[:10]  # First 10 digits
        self.test_product_search(partial_barcode)
        
        # Test if barcode exists in product name or description
        self.test_product_search(PROBLEM_BARCODE[-6:])  # Last 6 digits
        
        # Step 5: Generate summary
        self.generate_investigation_summary(problem_found)
        
        return len(self.critical_issues) == 0
    
    def generate_investigation_summary(self, problem_barcode_found):
        """Generate investigation summary"""
        print(f"\n" + "=" * 60)
        print("🔍 BARCODE SEARCH INVESTIGATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        print(f"🎯 Problem Barcode ({PROBLEM_BARCODE}): {'FOUND' if problem_barcode_found else 'NOT FOUND'}")
        
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for issue in self.critical_issues:
                print(f"   {issue}")
        
        print(f"\n📋 INVESTIGATION FINDINGS:")
        
        if problem_barcode_found:
            print(f"   ✅ Barcode {PROBLEM_BARCODE} EXISTS in database")
            print(f"   ✅ Search APIs are working correctly")
            print(f"   🔍 Issue may be in frontend WasteReports form logic")
        else:
            print(f"   ❌ Barcode {PROBLEM_BARCODE} NOT FOUND in database")
            print(f"   🔍 This barcode was never imported or was deleted")
            print(f"   💡 User may have mistyped the barcode")
        
        print(f"\n🎯 RECOMMENDED ACTIONS:")
        if problem_barcode_found:
            print(f"   1. Check WasteReports frontend form implementation")
            print(f"   2. Verify barcode scanner is reading correctly")
            print(f"   3. Check for any frontend filtering logic")
        else:
            print(f"   1. Verify the barcode number with the user")
            print(f"   2. Check if product needs to be imported")
            print(f"   3. Search for similar barcode patterns in database")
            print(f"   4. Consider manual product entry if barcode is correct")
        
        print(f"\n⏰ Investigation completed at: {datetime.now().isoformat()}")

def main():
    """Main investigation function"""
    investigator = BarcodeSearchInvestigator()
    success = investigator.run_investigation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()