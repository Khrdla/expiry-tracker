#!/usr/bin/env python3
"""
KPI ENDPOINT DEBUG TEST - Department Data Investigation

This test specifically debugs why department data shows as numeric indices (0, 1, 2) 
instead of actual department names (01-FMG, 01-CGD, 01-OPSS) as reported by the user.

User's screenshot shows:
- Department "0": 716 items
- Department "1": 43 items  
- Department "2": 1,091 items

But these should show as:
- "01-FMG": X items
- "01-CGD": Y items
- "01-OPSS": Z items

Test Coverage:
1. Test KPI endpoint (/api/kpis or /api/dashboard) and examine exact response structure
2. Check department mapping to see what keys are being used in KPI data
3. Verify product data to see their actual department field values
4. Understand how backend aggregates products by department for KPI calculation
"""

import requests
import json
import sys
from datetime import datetime
from collections import Counter

# Configuration
BACKEND_URL = "https://stockmate-14.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class KPIDebugTester:
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
                    self.log_test("Admin Login", True, f"Token received successfully")
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
    
    def test_kpi_endpoint(self):
        """Test 2: Call KPI endpoint and examine response structure"""
        print("\n📊 TESTING KPI ENDPOINT")
        print("=" * 50)
        
        if not self.token:
            self.log_test("KPI Endpoint Setup", False, "No authentication token available")
            return None
            
        # Try different possible KPI endpoints
        endpoints_to_try = [
            "/kpis",
            "/dashboard", 
            "/dashboard/kpis"
        ]
        
        kpi_data = None
        
        for endpoint in endpoints_to_try:
            try:
                print(f"🔍 Trying endpoint: {endpoint}")
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(f"KPI Endpoint {endpoint}", True, f"Response received ({len(json.dumps(data))} bytes)")
                        
                        # Print the raw response structure for analysis
                        print(f"\n📋 RAW KPI RESPONSE STRUCTURE from {endpoint}:")
                        print("=" * 60)
                        print(json.dumps(data, indent=2)[:2000] + "..." if len(json.dumps(data)) > 2000 else json.dumps(data, indent=2))
                        print("=" * 60)
                        
                        kpi_data = data
                        break
                        
                    except json.JSONDecodeError:
                        self.log_test(f"KPI Endpoint {endpoint}", False, "Invalid JSON response")
                        
                elif response.status_code == 404:
                    self.log_test(f"KPI Endpoint {endpoint}", False, "Endpoint not found (404)")
                else:
                    self.log_test(f"KPI Endpoint {endpoint}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"KPI Endpoint {endpoint}", False, f"Exception: {str(e)}")
        
        return kpi_data
    
    def analyze_department_mapping(self, kpi_data):
        """Test 3: Analyze department mapping in KPI data"""
        print("\n🗂️ ANALYZING DEPARTMENT MAPPING")
        print("=" * 50)
        
        if not kpi_data:
            self.log_test("Department Mapping Analysis", False, "No KPI data available")
            return
        
        # Look for department-related data in different parts of the response
        department_analysis = {}
        
        # Check KPIs section
        if 'kpis' in kpi_data:
            print("📊 Found KPIs section:")
            for i, kpi in enumerate(kpi_data['kpis']):
                dept_key = kpi.get('department', f'Unknown_{i}')
                dept_items = kpi.get('total_items', 0)
                department_analysis[dept_key] = dept_items
                print(f"  KPI {i}: Department='{dept_key}', Items={dept_items}")
        
        # Check stock_distribution section
        if 'stock_distribution' in kpi_data:
            print("\n📈 Found stock_distribution section:")
            for key, value in kpi_data['stock_distribution'].items():
                print(f"  Stock Distribution: '{key}' = {value} items")
                department_analysis[f"stock_{key}"] = value
        
        # Check any other department-related fields
        for key, value in kpi_data.items():
            if 'department' in key.lower() or 'dept' in key.lower():
                print(f"\n🔍 Found department-related field: {key} = {value}")
        
        # Analyze the mapping
        if department_analysis:
            print(f"\n🎯 DEPARTMENT MAPPING ANALYSIS:")
            print("=" * 40)
            
            numeric_keys = [k for k in department_analysis.keys() if k.isdigit()]
            proper_dept_keys = [k for k in department_analysis.keys() if k in ['01-FMG', '01-CGD', '01-OPSS']]
            
            if numeric_keys:
                self.log_test("Numeric Department Keys Found", False, f"Found numeric keys: {numeric_keys}")
                print(f"❌ ISSUE IDENTIFIED: Numeric department keys found: {numeric_keys}")
                
                # Map the values to see if they match user's report
                user_reported = {"0": 716, "1": 43, "2": 1091}
                for key in numeric_keys:
                    actual_value = department_analysis.get(key, 0)
                    expected_value = user_reported.get(key, "N/A")
                    print(f"   Department '{key}': Actual={actual_value}, User Reported={expected_value}")
            
            if proper_dept_keys:
                self.log_test("Proper Department Keys Found", True, f"Found proper keys: {proper_dept_keys}")
                print(f"✅ GOOD: Proper department keys found: {proper_dept_keys}")
            
            if not numeric_keys and not proper_dept_keys:
                self.log_test("Department Key Analysis", False, "No recognizable department keys found")
        else:
            self.log_test("Department Mapping Analysis", False, "No department data found in KPI response")
    
    def test_product_department_values(self):
        """Test 4: Check actual product data to see department field values"""
        print("\n🏷️ TESTING PRODUCT DEPARTMENT VALUES")
        print("=" * 50)
        
        if not self.token:
            self.log_test("Product Department Test Setup", False, "No authentication token available")
            return
        
        try:
            # Get a sample of products to check their department values
            response = self.session.get(f"{BACKEND_URL}/products?limit=50")
            
            if response.status_code == 200:
                products = response.json()
                
                if products:
                    # Analyze department values in products
                    department_values = [p.get('department', 'N/A') for p in products]
                    dept_counter = Counter(department_values)
                    
                    print(f"📊 PRODUCT DEPARTMENT VALUES (from {len(products)} products):")
                    print("=" * 40)
                    
                    for dept, count in dept_counter.most_common():
                        print(f"  Department '{dept}': {count} products")
                    
                    # Check if we have numeric vs proper department values
                    numeric_depts = [d for d in dept_counter.keys() if str(d).isdigit()]
                    proper_depts = [d for d in dept_counter.keys() if d in ['01-FMG', '01-CGD', '01-OPSS']]
                    
                    if numeric_depts:
                        self.log_test("Product Numeric Departments", False, f"Products have numeric departments: {numeric_depts}")
                    
                    if proper_depts:
                        self.log_test("Product Proper Departments", True, f"Products have proper departments: {proper_depts}")
                    
                    # Show sample products with their department values
                    print(f"\n📋 SAMPLE PRODUCT DEPARTMENT VALUES:")
                    for i, product in enumerate(products[:5]):
                        dept = product.get('department', 'N/A')
                        name = product.get('product_name', 'N/A')[:30]
                        print(f"  Product {i+1}: '{name}' -> Department: '{dept}'")
                    
                    self.log_test("Product Department Analysis", True, f"Analyzed {len(products)} products")
                    
                else:
                    self.log_test("Product Department Analysis", False, "No products returned")
            else:
                self.log_test("Product Department Analysis", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Product Department Analysis", False, f"Exception: {str(e)}")
    
    def test_kpi_aggregation_logic(self):
        """Test 5: Understand how backend aggregates products by department"""
        print("\n🔄 TESTING KPI AGGREGATION LOGIC")
        print("=" * 50)
        
        if not self.token:
            self.log_test("KPI Aggregation Test Setup", False, "No authentication token available")
            return
        
        try:
            # Get products for each known department to understand aggregation
            departments_to_test = ['01-FMG', '01-CGD', '01-OPSS', '0', '1', '2']
            
            aggregation_results = {}
            
            for dept in departments_to_test:
                try:
                    response = self.session.get(f"{BACKEND_URL}/products?department={dept}&limit=1000")
                    
                    if response.status_code == 200:
                        products = response.json()
                        count = len(products)
                        aggregation_results[dept] = count
                        
                        if count > 0:
                            print(f"  Department '{dept}': {count} products")
                            # Show sample product from this department
                            sample = products[0]
                            sample_name = sample.get('product_name', 'N/A')[:30]
                            sample_dept = sample.get('department', 'N/A')
                            print(f"    Sample: '{sample_name}' (stored as dept: '{sample_dept}')")
                        else:
                            print(f"  Department '{dept}': 0 products")
                    else:
                        print(f"  Department '{dept}': Error {response.status_code}")
                        
                except Exception as e:
                    print(f"  Department '{dept}': Exception {str(e)}")
            
            # Compare with user's reported values
            user_reported = {"0": 716, "1": 43, "2": 1091}
            proper_expected = {"01-FMG": "?", "01-CGD": "?", "01-OPSS": "?"}
            
            print(f"\n🎯 AGGREGATION COMPARISON:")
            print("=" * 40)
            print("User Reported vs Actual:")
            
            matches_user_report = True
            for key, expected in user_reported.items():
                actual = aggregation_results.get(key, 0)
                match_status = "✅" if abs(actual - expected) < 50 else "❌"  # Allow some variance
                print(f"  Department '{key}': Expected={expected}, Actual={actual} {match_status}")
                if abs(actual - expected) >= 50:
                    matches_user_report = False
            
            if matches_user_report:
                self.log_test("User Report Validation", True, "Aggregation matches user's reported values")
                print("✅ CONFIRMED: Backend is returning numeric department indices as reported by user")
            else:
                self.log_test("User Report Validation", False, "Aggregation doesn't match user's reported values")
            
            # Check proper department aggregation
            print(f"\nProper Department Aggregation:")
            for dept in ['01-FMG', '01-CGD', '01-OPSS']:
                actual = aggregation_results.get(dept, 0)
                print(f"  Department '{dept}': {actual} products")
            
            self.log_test("KPI Aggregation Analysis", True, f"Tested {len(departments_to_test)} department filters")
            
        except Exception as e:
            self.log_test("KPI Aggregation Analysis", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all KPI debug tests"""
        print("🔍 KPI ENDPOINT DEBUG TEST - Department Data Investigation")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin User: {ADMIN_USERNAME}")
        print("\n🎯 INVESTIGATING: Why departments show as 0, 1, 2 instead of 01-FMG, 01-CGD, 01-OPSS")
        print("=" * 80)
        
        # Run tests in sequence
        auth_success = self.test_authentication()
        
        if auth_success:
            kpi_data = self.test_kpi_endpoint()
            self.analyze_department_mapping(kpi_data)
            self.test_product_department_values()
            self.test_kpi_aggregation_logic()
        else:
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with KPI debug tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary and diagnosis"""
        print("\n" + "=" * 80)
        print("📊 KPI DEBUG TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("=" * 40)
        
        # Analyze test results to provide diagnosis
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        numeric_dept_issues = [r for r in failed_tests if "Numeric Department" in r["test"]]
        if numeric_dept_issues:
            print("❌ ISSUE CONFIRMED: Backend is using numeric department indices (0, 1, 2)")
            print("   This explains why user sees numbers instead of department names")
        
        user_validation = [r for r in self.test_results if "User Report Validation" in r["test"]]
        if user_validation and user_validation[0]["success"]:
            print("✅ USER REPORT VALIDATED: Numbers match user's screenshot")
        
        print("\n💡 RECOMMENDED FIXES:")
        print("=" * 40)
        
        if numeric_dept_issues:
            print("1. 🔧 Backend KPI Processing: Fix department aggregation to use proper names")
            print("2. 🔧 Frontend Display: Ensure department mapping shows names not indices")
            print("3. 🔧 Data Consistency: Verify all products have proper department values")
        
        print("\n🎯 NEXT STEPS:")
        print("=" * 40)
        print("1. Check backend KPI calculation logic in server.py")
        print("2. Verify department enum/mapping in models.py")
        print("3. Test frontend department display logic")
        print("4. Ensure consistent department field values in database")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = KPIDebugTester()
    tester.run_all_tests()
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()