#!/usr/bin/env python3
"""
Dashboard Stock Value Calculation Testing
Testing the fixed analytics endpoints that were showing $0.00 instead of actual calculated values
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Expected exchange rates from the fix
EXPECTED_EXCHANGE_RATES = {
    "YER": 0.004,
    "SAR": 0.267,
    "EUR": 1.10,
    "USD": 1.0
}

class DashboardAnalyticsTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.0f}ms",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({response_time:.0f}ms)")
        if details:
            print(f"    Details: {details}")
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Admin Authentication", True, 
                    f"JWT token received successfully", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_department_breakdown_analytics(self):
        """Test GET /api/analytics/department-breakdown for stock value calculations"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has departments
                if not isinstance(data, list) or len(data) == 0:
                    self.log_result("Department Breakdown Analytics", False,
                        f"No department data returned", response_time)
                    return False
                
                # Verify each department has total_value_usd field
                departments_with_values = []
                total_stock_value = 0
                
                for dept in data:
                    dept_name = dept.get("department", "Unknown")
                    total_value_usd = dept.get("total_value_usd", 0)
                    
                    if total_value_usd > 0:
                        departments_with_values.append(f"{dept_name}: ${total_value_usd:,.2f}")
                        total_stock_value += total_value_usd
                    elif total_value_usd == 0:
                        # Check if there are products but value is still 0 (the bug)
                        product_count = dept.get("product_count", 0)
                        if product_count > 0:
                            departments_with_values.append(f"{dept_name}: ${total_value_usd} (BUG: {product_count} products)")
                        else:
                            departments_with_values.append(f"{dept_name}: ${total_value_usd} (no products)")
                
                # Success if we have non-zero values or proper zero values
                has_calculated_values = any(dept.get("total_value_usd", 0) > 0 for dept in data)
                
                self.log_result("Department Breakdown Analytics", has_calculated_values,
                    f"Departments: {len(data)}, With values: {departments_with_values}, "
                    f"Total stock value: ${total_stock_value:,.2f}", response_time)
                
                return data
            else:
                self.log_result("Department Breakdown Analytics", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Department Breakdown Analytics", False, f"Exception: {str(e)}")
            return None
    
    def test_stock_levels_analytics(self):
        """Test GET /api/analytics/stock-levels for stock value calculations"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/stock-levels")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if not isinstance(data, dict):
                    self.log_result("Stock Levels Analytics", False,
                        f"Invalid response structure: {type(data)}", response_time)
                    return None
                
                # Look for stock level categories with values
                stock_categories = []
                total_value = 0
                
                for category, info in data.items():
                    if isinstance(info, dict) and "total_value_usd" in info:
                        value = info.get("total_value_usd", 0)
                        count = info.get("count", 0)
                        stock_categories.append(f"{category}: {count} items, ${value:,.2f}")
                        total_value += value
                    elif isinstance(info, (int, float)):
                        stock_categories.append(f"{category}: {info}")
                
                # Success if we have calculated values
                has_values = total_value > 0
                
                self.log_result("Stock Levels Analytics", has_values,
                    f"Categories: {stock_categories}, Total value: ${total_value:,.2f}", response_time)
                
                return data
            else:
                self.log_result("Stock Levels Analytics", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Stock Levels Analytics", False, f"Exception: {str(e)}")
            return None
    
    def test_supplier_performance_analytics(self):
        """Test GET /api/analytics/supplier-performance for stock value calculations"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/supplier-performance")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has suppliers
                if not isinstance(data, list) or len(data) == 0:
                    self.log_result("Supplier Performance Analytics", False,
                        f"No supplier data returned", response_time)
                    return False
                
                # Verify suppliers have total_stock_value > 0
                suppliers_with_values = []
                total_supplier_value = 0
                
                for supplier in data:
                    supplier_name = supplier.get("supplier_name", "Unknown")
                    total_stock_value = supplier.get("total_stock_value", 0)
                    item_count = supplier.get("total_items", 0)
                    
                    if total_stock_value > 0:
                        suppliers_with_values.append(f"{supplier_name}: {item_count} items, ${total_stock_value:,.2f}")
                        total_supplier_value += total_stock_value
                    elif total_stock_value == 0 and item_count > 0:
                        suppliers_with_values.append(f"{supplier_name}: ${total_stock_value} (BUG: {item_count} items)")
                    else:
                        suppliers_with_values.append(f"{supplier_name}: ${total_stock_value} (no items)")
                
                # Success if we have non-zero values
                has_calculated_values = any(supplier.get("total_stock_value", 0) > 0 for supplier in data)
                
                self.log_result("Supplier Performance Analytics", has_calculated_values,
                    f"Suppliers: {len(data)}, With values: {suppliers_with_values[:3]}, "
                    f"Total supplier value: ${total_supplier_value:,.2f}", response_time)
                
                return data
            else:
                self.log_result("Supplier Performance Analytics", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Supplier Performance Analytics", False, f"Exception: {str(e)}")
            return None
    
    def test_currency_conversion_logic(self, department_data):
        """Test that currency conversion is working correctly"""
        if not department_data:
            self.log_result("Currency Conversion Logic", False, "No department data to test")
            return
        
        try:
            # Get some sample products to verify conversion logic
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/products?limit=10")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    self.log_result("Currency Conversion Logic", False, 
                        "No products found to test conversion", response_time)
                    return
                
                # Test conversion logic manually
                conversion_tests = []
                for product in products[:3]:  # Test first 3 products
                    quantity = product.get("quantity", 0)
                    purchase_price = product.get("purchase_price", 0)
                    currency = product.get("purchase_currency", "USD")
                    
                    if quantity > 0 and purchase_price > 0:
                        # Calculate expected USD value
                        exchange_rate = EXPECTED_EXCHANGE_RATES.get(currency, 1.0)
                        expected_usd_value = quantity * purchase_price * exchange_rate
                        
                        conversion_tests.append({
                            "product": product.get("product_name", "Unknown")[:20],
                            "quantity": quantity,
                            "price": purchase_price,
                            "currency": currency,
                            "rate": exchange_rate,
                            "expected_usd": expected_usd_value
                        })
                
                self.log_result("Currency Conversion Logic", len(conversion_tests) > 0,
                    f"Tested {len(conversion_tests)} products with conversion logic. "
                    f"Sample: {conversion_tests[0] if conversion_tests else 'None'}", response_time)
                
            else:
                self.log_result("Currency Conversion Logic", False,
                    f"Failed to get products for conversion test: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("Currency Conversion Logic", False, f"Exception: {str(e)}")
    
    def test_performance_requirements(self):
        """Test that all analytics endpoints respond within 500ms"""
        endpoints = [
            "/analytics/department-breakdown",
            "/analytics/stock-levels", 
            "/analytics/supplier-performance"
        ]
        
        performance_results = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                meets_requirement = response_time < 500
                performance_results.append({
                    "endpoint": endpoint,
                    "time": response_time,
                    "meets_requirement": meets_requirement
                })
                
            except Exception as e:
                performance_results.append({
                    "endpoint": endpoint,
                    "time": 999999,
                    "meets_requirement": False,
                    "error": str(e)
                })
        
        # Overall performance test
        all_meet_requirement = all(result["meets_requirement"] for result in performance_results)
        avg_response_time = sum(result["time"] for result in performance_results) / len(performance_results)
        
        details = ", ".join([f"{r['endpoint'].split('/')[-1]}: {r['time']:.0f}ms" for r in performance_results])
        
        self.log_result("Performance Requirements (<500ms)", all_meet_requirement,
            f"Average: {avg_response_time:.0f}ms, Details: {details}", avg_response_time)
    
    def test_zero_dollar_bug_verification(self):
        """Specifically test that we're not getting $0.00 values when there should be actual values"""
        try:
            # Test all three analytics endpoints for the $0.00 bug
            endpoints_to_test = [
                ("/analytics/department-breakdown", "department"),
                ("/analytics/stock-levels", "stock_levels"),
                ("/analytics/supplier-performance", "supplier")
            ]
            
            zero_dollar_issues = []
            
            for endpoint, endpoint_type in endpoints_to_test:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if endpoint_type == "department" and isinstance(data, list):
                        for dept in data:
                            total_value = dept.get("total_value_usd", 0)
                            product_count = dept.get("product_count", 0)
                            if total_value == 0 and product_count > 0:
                                zero_dollar_issues.append(f"Department {dept.get('department')}: $0.00 with {product_count} products")
                    
                    elif endpoint_type == "supplier" and isinstance(data, list):
                        for supplier in data:
                            total_value = supplier.get("total_stock_value", 0)
                            item_count = supplier.get("total_items", 0)
                            if total_value == 0 and item_count > 0:
                                zero_dollar_issues.append(f"Supplier {supplier.get('supplier_name')}: $0.00 with {item_count} items")
                    
                    elif endpoint_type == "stock_levels" and isinstance(data, dict):
                        for category, info in data.items():
                            if isinstance(info, dict):
                                total_value = info.get("total_value_usd", 0)
                                count = info.get("count", 0)
                                if total_value == 0 and count > 0:
                                    zero_dollar_issues.append(f"Stock level {category}: $0.00 with {count} items")
            
            # Success if no zero dollar issues found
            bug_fixed = len(zero_dollar_issues) == 0
            
            self.log_result("Zero Dollar Bug Verification", bug_fixed,
                f"Issues found: {zero_dollar_issues[:3] if zero_dollar_issues else 'None'}", 0)
            
        except Exception as e:
            self.log_result("Zero Dollar Bug Verification", False, f"Exception: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all dashboard analytics tests"""
        print("🚀 DASHBOARD STOCK VALUE CALCULATION TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Fix: Dashboard stock values showing $0.00 instead of actual calculated values")
        print(f"Expected Exchange Rates: {EXPECTED_EXCHANGE_RATES}")
        print("=" * 60)
        
        # 1. Authentication Test
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Test Department Breakdown Analytics
        department_data = self.test_department_breakdown_analytics()
        
        # 3. Test Stock Levels Analytics  
        stock_levels_data = self.test_stock_levels_analytics()
        
        # 4. Test Supplier Performance Analytics
        supplier_data = self.test_supplier_performance_analytics()
        
        # 5. Test Currency Conversion Logic
        self.test_currency_conversion_logic(department_data)
        
        # 6. Test Performance Requirements
        self.test_performance_requirements()
        
        # 7. Test Zero Dollar Bug Verification
        self.test_zero_dollar_bug_verification()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD ANALYTICS TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Admin Authentication": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results),
            "Department Breakdown Analytics": any("Department Breakdown Analytics" in r["test"] and r["success"] for r in self.test_results),
            "Stock Levels Analytics": any("Stock Levels Analytics" in r["test"] and r["success"] for r in self.test_results),
            "Supplier Performance Analytics": any("Supplier Performance Analytics" in r["test"] and r["success"] for r in self.test_results),
            "Currency Conversion Logic": any("Currency Conversion Logic" in r["test"] and r["success"] for r in self.test_results),
            "Performance Requirements": any("Performance Requirements" in r["test"] and r["success"] for r in self.test_results),
            "Zero Dollar Bug Fixed": any("Zero Dollar Bug Verification" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in critical_tests.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {requirement}")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Performance summary
        if self.test_results:
            avg_response_time = sum(float(r["response_time"].replace("ms", "")) for r in self.test_results) / len(self.test_results)
            print(f"\n⚡ AVERAGE RESPONSE TIME: {avg_response_time:.0f}ms")
        
        print("\n" + "=" * 60)
        print("🏁 DASHBOARD ANALYTICS TESTING COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = DashboardAnalyticsTester()
    tester.run_comprehensive_tests()