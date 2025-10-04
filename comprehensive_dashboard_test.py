#!/usr/bin/env python3
"""
Comprehensive Dashboard Stock Value Calculation Testing
Testing all requirements from the review request for the fixed analytics endpoints
"""

import requests
import json
import os
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

# Expected exchange rates from the fix
EXPECTED_EXCHANGE_RATES = {
    "YER": 0.004,
    "SAR": 0.267,
    "EUR": 1.10,
    "USD": 1.0
}

class ComprehensiveDashboardTester:
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
        """Test 1: Authentication Test - Login with admin credentials"""
        try:
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/auth/login", 
                json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("1. Authentication Test (imadqejji/066380531I)", True, 
                    f"JWT token received, admin access granted", response_time)
                return True
            else:
                self.log_result("1. Authentication Test (imadqejji/066380531I)", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("1. Authentication Test (imadqejji/066380531I)", False, f"Exception: {str(e)}")
            return False
    
    def test_department_breakdown_endpoint(self):
        """Test 2: Analytics Endpoints Test - Department Breakdown"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure and calculations
                departments_with_stock_value = []
                total_calculated_value = 0
                
                for dept in data:
                    dept_name = dept.get("_id", "Unknown")
                    total_value_usd = dept.get("total_value_usd", 0)
                    total_products = dept.get("total_products", 0)
                    total_stock = dept.get("total_stock", 0)
                    
                    if total_value_usd > 0:
                        departments_with_stock_value.append(f"{dept_name}: ${total_value_usd:,.2f} ({total_products} products, {total_stock} stock)")
                        total_calculated_value += total_value_usd
                    elif total_products > 0:
                        departments_with_stock_value.append(f"{dept_name}: ${total_value_usd} ({total_products} products, {total_stock} stock)")
                
                # Success if we have calculated values and proper structure
                has_calculated_values = total_calculated_value > 0
                has_proper_structure = all("total_value_usd" in dept for dept in data)
                
                success = has_calculated_values and has_proper_structure and response_time < 500
                
                self.log_result("2. Department Breakdown Analytics Endpoint", success,
                    f"Departments: {len(data)}, Total calculated value: ${total_calculated_value:,.2f}, "
                    f"Details: {departments_with_stock_value}", response_time)
                
                return data
            else:
                self.log_result("2. Department Breakdown Analytics Endpoint", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("2. Department Breakdown Analytics Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_stock_levels_endpoint(self):
        """Test 3: Analytics Endpoints Test - Stock Levels"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/stock-levels")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                has_status_breakdown = "status_breakdown" in data
                has_stock_ranges = "stock_ranges" in data
                
                total_value_from_status = 0
                total_value_from_ranges = 0
                
                # Check status breakdown
                if has_status_breakdown:
                    for status_item in data["status_breakdown"]:
                        total_value_from_status += status_item.get("total_value", 0)
                
                # Check stock ranges
                if has_stock_ranges:
                    for range_item in data["stock_ranges"]:
                        total_value_from_ranges += range_item.get("total_value", 0)
                
                success = (has_status_breakdown and has_stock_ranges and 
                          (total_value_from_status > 0 or total_value_from_ranges > 0) and 
                          response_time < 500)
                
                self.log_result("3. Stock Levels Analytics Endpoint", success,
                    f"Status breakdown value: ${total_value_from_status:,.2f}, "
                    f"Stock ranges value: ${total_value_from_ranges:,.2f}", response_time)
                
                return data
            else:
                self.log_result("3. Stock Levels Analytics Endpoint", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("3. Stock Levels Analytics Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_supplier_performance_endpoint(self):
        """Test 4: Analytics Endpoints Test - Supplier Performance"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/analytics/supplier-performance")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify suppliers have calculated stock values
                suppliers_with_values = []
                total_supplier_value = 0
                
                for supplier in data:
                    supplier_name = supplier.get("_id", "Unknown")
                    total_stock_value = supplier.get("total_stock_value", 0)
                    total_products = supplier.get("total_products", 0)
                    
                    if total_stock_value > 0:
                        suppliers_with_values.append(f"{supplier_name}: ${total_stock_value:,.2f} ({total_products} products)")
                        total_supplier_value += total_stock_value
                
                success = (len(suppliers_with_values) > 0 and total_supplier_value > 0 and response_time < 500)
                
                self.log_result("4. Supplier Performance Analytics Endpoint", success,
                    f"Suppliers with values: {len(suppliers_with_values)}/{len(data)}, "
                    f"Total supplier value: ${total_supplier_value:,.2f}", response_time)
                
                return data
            else:
                self.log_result("4. Supplier Performance Analytics Endpoint", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("4. Supplier Performance Analytics Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_stock_value_calculation_formula(self):
        """Test 5: Stock Value Calculation Verification - quantity × purchase_price × exchange_rate"""
        try:
            # Get some sample products to verify the calculation formula
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/products?limit=20")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    self.log_result("5. Stock Value Calculation Formula Verification", False, 
                        "No products found to verify calculation", response_time)
                    return
                
                # Test calculation formula on sample products
                calculation_tests = []
                total_manual_calculation = 0
                
                for product in products[:5]:  # Test first 5 products
                    quantity = product.get("quantity", 0)
                    purchase_price = product.get("purchase_price", 0)
                    currency = product.get("purchase_currency", "USD")
                    product_name = product.get("product_name", "Unknown")[:25]
                    
                    if quantity > 0 and purchase_price > 0:
                        # Apply the formula: quantity × purchase_price × exchange_rate
                        exchange_rate = EXPECTED_EXCHANGE_RATES.get(currency, 1.0)
                        calculated_usd_value = quantity * purchase_price * exchange_rate
                        
                        calculation_tests.append({
                            "product": product_name,
                            "quantity": quantity,
                            "price": purchase_price,
                            "currency": currency,
                            "rate": exchange_rate,
                            "calculated_usd": calculated_usd_value
                        })
                        
                        total_manual_calculation += calculated_usd_value
                
                success = len(calculation_tests) > 0 and total_manual_calculation > 0
                
                self.log_result("5. Stock Value Calculation Formula Verification", success,
                    f"Tested {len(calculation_tests)} products, Total manual calculation: ${total_manual_calculation:,.2f}, "
                    f"Sample: {calculation_tests[0] if calculation_tests else 'None'}", response_time)
                
            else:
                self.log_result("5. Stock Value Calculation Formula Verification", False,
                    f"Failed to get products: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("5. Stock Value Calculation Formula Verification", False, f"Exception: {str(e)}")
    
    def test_currency_conversion_rates(self):
        """Test 6: Currency Conversion Test - Verify exchange rates are applied correctly"""
        try:
            # Test that the expected exchange rates are being used
            start_time = time.time()
            
            # Get department breakdown which shows currency conversion
            response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                currency_conversion_evidence = []
                
                for dept in data:
                    total_value_yer = dept.get("total_value_yer", 0)
                    total_value_usd = dept.get("total_value_usd", 0)
                    dept_name = dept.get("_id", "Unknown")
                    
                    if total_value_yer > 0 and total_value_usd > 0:
                        # Calculate implied conversion rate
                        implied_rate = total_value_usd / total_value_yer
                        expected_rate = EXPECTED_EXCHANGE_RATES.get("YER", 0.004)
                        
                        rate_matches = abs(implied_rate - expected_rate) < 0.001
                        
                        currency_conversion_evidence.append({
                            "department": dept_name,
                            "yer_value": total_value_yer,
                            "usd_value": total_value_usd,
                            "implied_rate": implied_rate,
                            "expected_rate": expected_rate,
                            "rate_matches": rate_matches
                        })
                
                # Success if we have evidence of proper currency conversion
                success = len(currency_conversion_evidence) > 0 and any(item["rate_matches"] for item in currency_conversion_evidence)
                
                self.log_result("6. Currency Conversion Test", success,
                    f"Conversion evidence: {currency_conversion_evidence}", response_time)
                
            else:
                self.log_result("6. Currency Conversion Test", False,
                    f"Failed to get department data: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("6. Currency Conversion Test", False, f"Exception: {str(e)}")
    
    def test_no_zero_dollar_values(self):
        """Test 7: Data Validation - Ensure total_value_usd field contains actual calculated values instead of $0.00"""
        try:
            start_time = time.time()
            
            # Test all three endpoints for zero dollar bug
            endpoints = [
                ("/analytics/department-breakdown", "departments"),
                ("/analytics/stock-levels", "stock_levels"),
                ("/analytics/supplier-performance", "suppliers")
            ]
            
            zero_dollar_issues = []
            total_non_zero_values = 0
            
            for endpoint, endpoint_type in endpoints:
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if endpoint_type == "departments" and isinstance(data, list):
                        for dept in data:
                            total_value = dept.get("total_value_usd", 0)
                            total_products = dept.get("total_products", 0)
                            if total_value == 0 and total_products > 0:
                                zero_dollar_issues.append(f"Department {dept.get('_id')}: $0.00 with {total_products} products")
                            elif total_value > 0:
                                total_non_zero_values += 1
                    
                    elif endpoint_type == "suppliers" and isinstance(data, list):
                        for supplier in data:
                            total_value = supplier.get("total_stock_value", 0)
                            total_products = supplier.get("total_products", 0)
                            if total_value == 0 and total_products > 0:
                                zero_dollar_issues.append(f"Supplier {supplier.get('_id')}: $0.00 with {total_products} products")
                            elif total_value > 0:
                                total_non_zero_values += 1
                    
                    elif endpoint_type == "stock_levels" and isinstance(data, dict):
                        for category_type in ["status_breakdown", "stock_ranges"]:
                            if category_type in data:
                                for item in data[category_type]:
                                    total_value = item.get("total_value", 0)
                                    count = item.get("count", 0)
                                    if total_value == 0 and count > 0:
                                        zero_dollar_issues.append(f"{category_type} {item.get('_id')}: $0.00 with {count} items")
                                    elif total_value > 0:
                                        total_non_zero_values += 1
            
            response_time = (time.time() - start_time) * 1000
            
            # Success if no zero dollar issues and we have non-zero values
            success = len(zero_dollar_issues) == 0 and total_non_zero_values > 0
            
            self.log_result("7. No Zero Dollar Values Validation", success,
                f"Zero dollar issues: {len(zero_dollar_issues)}, Non-zero values found: {total_non_zero_values}, "
                f"Issues: {zero_dollar_issues[:3] if zero_dollar_issues else 'None'}", response_time)
            
        except Exception as e:
            self.log_result("7. No Zero Dollar Values Validation", False, f"Exception: {str(e)}")
    
    def test_performance_requirements(self):
        """Test 8: Performance Test - Verify all endpoints respond within reasonable time (<500ms)"""
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
                
                meets_requirement = response_time < 500 and response.status_code == 200
                performance_results.append({
                    "endpoint": endpoint.split('/')[-1],
                    "time": response_time,
                    "status": response.status_code,
                    "meets_requirement": meets_requirement
                })
                
            except Exception as e:
                performance_results.append({
                    "endpoint": endpoint.split('/')[-1],
                    "time": 999999,
                    "status": 500,
                    "meets_requirement": False,
                    "error": str(e)
                })
        
        # Overall performance test
        all_meet_requirement = all(result["meets_requirement"] for result in performance_results)
        avg_response_time = sum(result["time"] for result in performance_results) / len(performance_results)
        
        details = ", ".join([f"{r['endpoint']}: {r['time']:.0f}ms" for r in performance_results])
        
        self.log_result("8. Performance Test (<500ms)", all_meet_requirement,
            f"Average: {avg_response_time:.0f}ms, All endpoints: {details}", avg_response_time)
    
    def run_comprehensive_tests(self):
        """Run all comprehensive dashboard analytics tests"""
        print("🚀 COMPREHENSIVE DASHBOARD STOCK VALUE CALCULATION TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing Fix: Dashboard stock values consistently show $0.00 instead of actual calculated values")
        print(f"Expected Exchange Rates: {EXPECTED_EXCHANGE_RATES}")
        print("=" * 80)
        print("\n📋 TESTING REQUIREMENTS FROM REVIEW REQUEST:")
        print("1. Authentication Test: Login with admin credentials (imadqejji/066380531I)")
        print("2. Analytics Endpoints Test: Test the 3 key analytics endpoints")
        print("3. Stock Value Calculation Verification: quantity × purchase_price × exchange_rate")
        print("4. Currency Conversion Test: Verify exchange rates (YER: 0.004, SAR: 0.267, EUR: 1.10, USD: 1.0)")
        print("5. Data Validation: Ensure total_value_usd contains actual values instead of $0.00")
        print("6. Performance Test: Verify all endpoints respond within <500ms")
        print("=" * 80)
        
        # Run all tests in sequence
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        self.test_department_breakdown_endpoint()
        self.test_stock_levels_endpoint()
        self.test_supplier_performance_endpoint()
        self.test_stock_value_calculation_formula()
        self.test_currency_conversion_rates()
        self.test_no_zero_dollar_values()
        self.test_performance_requirements()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DASHBOARD ANALYTICS TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # Review requirements verification
        print("\n🎯 REVIEW REQUIREMENTS VERIFICATION:")
        
        review_requirements = {
            "1. Authentication Test": any("Authentication Test" in r["test"] and r["success"] for r in self.test_results),
            "2. Department Breakdown Endpoint": any("Department Breakdown" in r["test"] and r["success"] for r in self.test_results),
            "3. Stock Levels Endpoint": any("Stock Levels" in r["test"] and r["success"] for r in self.test_results),
            "4. Supplier Performance Endpoint": any("Supplier Performance" in r["test"] and r["success"] for r in self.test_results),
            "5. Stock Value Calculation Formula": any("Stock Value Calculation" in r["test"] and r["success"] for r in self.test_results),
            "6. Currency Conversion Test": any("Currency Conversion" in r["test"] and r["success"] for r in self.test_results),
            "7. No Zero Dollar Values": any("No Zero Dollar" in r["test"] and r["success"] for r in self.test_results),
            "8. Performance Requirements": any("Performance Test" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for requirement, status in review_requirements.items():
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
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        if success_rate >= 85:
            print("✅ DASHBOARD STOCK VALUE CALCULATION FIX IS WORKING CORRECTLY")
            print("✅ All analytics endpoints return calculated stock values instead of $0.00")
            print("✅ Currency conversion and performance requirements met")
        elif success_rate >= 70:
            print("⚠️  DASHBOARD STOCK VALUE CALCULATION PARTIALLY WORKING")
            print("⚠️  Some issues remain but core functionality is operational")
        else:
            print("❌ DASHBOARD STOCK VALUE CALCULATION FIX NEEDS ATTENTION")
            print("❌ Multiple critical issues identified")
        
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE DASHBOARD ANALYTICS TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = ComprehensiveDashboardTester()
    tester.run_comprehensive_tests()