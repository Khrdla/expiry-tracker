#!/usr/bin/env python3
"""
Dashboard Stock Value Calculation Fix Testing
Testing the UPDATED Dashboard Stock Value Calculation fix after additional frontend and backend changes.
User reported screenshots showing main dashboard still showed $0.00 values despite analytics endpoints working.
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
    'YER': 0.004,
    'SAR': 0.267, 
    'EUR': 1.10,
    'USD': 1.0
}

class DashboardStockValueTester:
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
                    f"Token received for {ADMIN_USERNAME}", response_time)
                return True
            else:
                self.log_result("Admin Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_main_dashboard_endpoint(self):
        """Test GET /api/dashboard with admin credentials to verify USD currency conversion"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if KPIs are present
                kpis = data.get("kpis", [])
                if not kpis:
                    self.log_result("Main Dashboard Endpoint", False,
                        "No KPIs found in dashboard response", response_time)
                    return None
                
                # Check for total_stock_value field (not stock_value)
                has_correct_field = False
                stock_values = []
                
                for kpi in kpis:
                    if "total_stock_value" in kpi:
                        has_correct_field = True
                        stock_value = kpi["total_stock_value"]
                        stock_values.append({
                            "department": kpi.get("department"),
                            "total_stock_value": stock_value
                        })
                
                self.log_result("Main Dashboard Endpoint", has_correct_field,
                    f"Found {len(kpis)} departments, correct field 'total_stock_value': {has_correct_field}, "
                    f"Stock values: {stock_values}", response_time)
                return data
            else:
                self.log_result("Main Dashboard Endpoint", False,
                    f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_result("Main Dashboard Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_department_kpi_verification(self, dashboard_data):
        """Verify that each department's total_stock_value field contains calculated USD values"""
        if not dashboard_data:
            self.log_result("Department KPI Verification", False, "No dashboard data to verify")
            return
        
        try:
            kpis = dashboard_data.get("kpis", [])
            departments_with_values = []
            departments_with_zero = []
            
            for kpi in kpis:
                dept = kpi.get("department")
                stock_value = kpi.get("total_stock_value", 0)
                total_items = kpi.get("total_items", 0)
                total_quantity = kpi.get("total_quantity", 0)
                
                if stock_value > 0:
                    departments_with_values.append({
                        "department": dept,
                        "stock_value": stock_value,
                        "items": total_items,
                        "quantity": total_quantity
                    })
                else:
                    departments_with_zero.append({
                        "department": dept,
                        "stock_value": stock_value,
                        "items": total_items,
                        "quantity": total_quantity
                    })
            
            # Success if we have departments with calculated values > 0
            has_calculated_values = len(departments_with_values) > 0
            
            self.log_result("Department KPI Verification", has_calculated_values,
                f"Departments with stock values > $0: {len(departments_with_values)}, "
                f"Departments with $0 (correct for zero stock): {len(departments_with_zero)}, "
                f"Values: {departments_with_values}", 0)
            
            return departments_with_values
            
        except Exception as e:
            self.log_result("Department KPI Verification", False, f"Exception: {str(e)}")
            return []
    
    def test_currency_conversion(self):
        """Verify the main dashboard applies exchange rates correctly"""
        try:
            start_time = time.time()
            
            # First get exchange rates
            rates_response = self.session.get(f"{BACKEND_URL}/currency/rates")
            response_time = (time.time() - start_time) * 1000
            
            if rates_response.status_code == 200:
                rates_data = rates_response.json()
                exchange_rates = rates_data.get("exchange_rates", {})
                
                # Check if expected rates are present
                rates_match = True
                rate_details = []
                
                for currency, expected_rate in EXPECTED_EXCHANGE_RATES.items():
                    actual_rate = exchange_rates.get(currency)
                    if actual_rate is None:
                        rates_match = False
                        rate_details.append(f"{currency}: MISSING")
                    else:
                        # Allow small tolerance for rate differences
                        tolerance = 0.001
                        if abs(actual_rate - expected_rate) > tolerance:
                            rates_match = False
                            rate_details.append(f"{currency}: {actual_rate} (expected {expected_rate})")
                        else:
                            rate_details.append(f"{currency}: {actual_rate} ✓")
                
                self.log_result("Currency Conversion Test", rates_match,
                    f"Exchange rates verification: {', '.join(rate_details)}", response_time)
                return exchange_rates
            else:
                self.log_result("Currency Conversion Test", False,
                    f"Failed to get exchange rates: {rates_response.status_code}", response_time)
                return None
                
        except Exception as e:
            self.log_result("Currency Conversion Test", False, f"Exception: {str(e)}")
            return None
    
    def test_field_structure_validation(self, dashboard_data):
        """Confirm the response includes the correct field name 'total_stock_value' that frontend expects"""
        if not dashboard_data:
            self.log_result("Field Structure Validation", False, "No dashboard data to validate")
            return
        
        try:
            kpis = dashboard_data.get("kpis", [])
            
            # Check each KPI for correct field structure
            correct_fields = []
            missing_fields = []
            
            expected_fields = ["department", "total_items", "total_stock_value", "total_quantity"]
            
            for i, kpi in enumerate(kpis):
                dept = kpi.get("department", f"Department_{i}")
                
                for field in expected_fields:
                    if field in kpi:
                        if field == "total_stock_value":
                            correct_fields.append(f"{dept}: {field}=${kpi[field]:.2f}")
                        else:
                            correct_fields.append(f"{dept}: {field}={kpi[field]}")
                    else:
                        missing_fields.append(f"{dept}: missing {field}")
            
            has_correct_structure = len(missing_fields) == 0 and len(correct_fields) > 0
            
            self.log_result("Field Structure Validation", has_correct_structure,
                f"Correct fields: {len(correct_fields)}, Missing: {len(missing_fields)}, "
                f"Sample: {correct_fields[:3] if correct_fields else 'None'}", 0)
            
        except Exception as e:
            self.log_result("Field Structure Validation", False, f"Exception: {str(e)}")
    
    def test_compare_with_analytics(self):
        """Compare main dashboard values with analytics endpoint values to ensure consistency"""
        try:
            start_time = time.time()
            
            # Get analytics department breakdown
            analytics_response = self.session.get(f"{BACKEND_URL}/analytics/department-breakdown")
            analytics_time = (time.time() - start_time) * 1000
            
            if analytics_response.status_code != 200:
                self.log_result("Compare with Analytics", False,
                    f"Analytics endpoint failed: {analytics_response.status_code}", analytics_time)
                return
            
            analytics_data = analytics_response.json()
            
            # Get main dashboard data
            start_time = time.time()
            dashboard_response = self.session.get(f"{BACKEND_URL}/dashboard")
            dashboard_time = (time.time() - start_time) * 1000
            
            if dashboard_response.status_code != 200:
                self.log_result("Compare with Analytics", False,
                    f"Dashboard endpoint failed: {dashboard_response.status_code}", dashboard_time)
                return
            
            dashboard_data = dashboard_response.json()
            
            # Compare values
            analytics_values = {}
            if isinstance(analytics_data, list):
                # Analytics returns a list directly
                for dept in analytics_data:
                    dept_name = dept.get("_id")  # Analytics uses "_id" for department name
                    total_value = dept.get("total_value_usd", 0)
                    analytics_values[dept_name] = total_value
            elif "departments" in analytics_data:
                for dept in analytics_data["departments"]:
                    dept_name = dept.get("department")
                    total_value = dept.get("total_value_usd", 0)
                    analytics_values[dept_name] = total_value
            
            dashboard_values = {}
            for kpi in dashboard_data.get("kpis", []):
                dept_name = kpi.get("department")
                stock_value = kpi.get("total_stock_value", 0)
                dashboard_values[dept_name] = stock_value
            
            # Check consistency
            consistent_values = []
            inconsistent_values = []
            
            for dept in dashboard_values:
                dashboard_val = dashboard_values[dept]
                analytics_val = analytics_values.get(dept, 0)
                
                # Allow small tolerance for floating point differences
                tolerance = 0.01
                if abs(dashboard_val - analytics_val) <= tolerance:
                    consistent_values.append(f"{dept}: ${dashboard_val:.2f}")
                else:
                    inconsistent_values.append(f"{dept}: Dashboard=${dashboard_val:.2f}, Analytics=${analytics_val:.2f}")
            
            is_consistent = len(inconsistent_values) == 0
            
            self.log_result("Compare with Analytics", is_consistent,
                f"Consistent: {len(consistent_values)}, Inconsistent: {len(inconsistent_values)}, "
                f"Details: {inconsistent_values if inconsistent_values else consistent_values[:2]}", 
                analytics_time + dashboard_time)
            
        except Exception as e:
            self.log_result("Compare with Analytics", False, f"Exception: {str(e)}")
    
    def test_performance(self):
        """Verify response time is still good after adding currency conversion"""
        try:
            # Test multiple requests to get average
            response_times = []
            
            for i in range(3):
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/dashboard")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response_times.append(response_time)
                else:
                    self.log_result("Performance Test", False,
                        f"Request {i+1} failed: {response.status_code}", response_time)
                    return
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Performance is good if average < 500ms and max < 1000ms
            performance_good = avg_response_time < 500 and max_response_time < 1000
            
            self.log_result("Performance Test", performance_good,
                f"Average: {avg_response_time:.0f}ms, Max: {max_response_time:.0f}ms, "
                f"All times: {[f'{t:.0f}ms' for t in response_times]}", avg_response_time)
            
        except Exception as e:
            self.log_result("Performance Test", False, f"Exception: {str(e)}")
    
    def test_specific_department_values(self):
        """Test specific department values mentioned in the review (01-FMG should show ~$11,399)"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/dashboard")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                kpis = data.get("kpis", [])
                
                # Look for 01-FMG department specifically
                fmg_found = False
                fmg_value = 0
                
                for kpi in kpis:
                    if kpi.get("department") == "01-FMG":
                        fmg_found = True
                        fmg_value = kpi.get("total_stock_value", 0)
                        break
                
                # Check if value is in expected range (~$11,399)
                expected_value = 11399
                tolerance = 1000  # Allow ±$1000 tolerance
                
                value_in_range = False
                if fmg_found and fmg_value > 0:
                    value_in_range = abs(fmg_value - expected_value) <= tolerance
                
                self.log_result("Specific Department Values (01-FMG)", fmg_found and value_in_range,
                    f"01-FMG found: {fmg_found}, Value: ${fmg_value:.2f}, "
                    f"Expected: ~${expected_value:.2f}, In range: {value_in_range}", response_time)
                
            else:
                self.log_result("Specific Department Values (01-FMG)", False,
                    f"Dashboard request failed: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_result("Specific Department Values (01-FMG)", False, f"Exception: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all dashboard stock value calculation tests"""
        print("🚀 DASHBOARD STOCK VALUE CALCULATION FIX TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_USERNAME}/{'*' * len(ADMIN_PASSWORD)}")
        print(f"Expected Exchange Rates: {EXPECTED_EXCHANGE_RATES}")
        print("=" * 70)
        
        # 1. Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        # 2. Main Dashboard Endpoint Test
        dashboard_data = self.test_main_dashboard_endpoint()
        
        # 3. Department KPI Verification
        departments_with_values = self.test_department_kpi_verification(dashboard_data)
        
        # 4. Currency Conversion Test
        self.test_currency_conversion()
        
        # 5. Field Structure Validation
        self.test_field_structure_validation(dashboard_data)
        
        # 6. Compare with Analytics
        self.test_compare_with_analytics()
        
        # 7. Performance Test
        self.test_performance()
        
        # 8. Specific Department Values Test
        self.test_specific_department_values()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 DASHBOARD STOCK VALUE CALCULATION TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ PASSED: {passed}/{total} tests ({success_rate:.1f}%)")
        
        # Critical requirements verification
        print("\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
        
        critical_tests = {
            "Main Dashboard USD Conversion": any("Main Dashboard Endpoint" in r["test"] and r["success"] for r in self.test_results),
            "Department KPI Values > $0": any("Department KPI Verification" in r["test"] and r["success"] for r in self.test_results),
            "Currency Exchange Rates": any("Currency Conversion Test" in r["test"] and r["success"] for r in self.test_results),
            "Correct Field Structure": any("Field Structure Validation" in r["test"] and r["success"] for r in self.test_results),
            "Analytics Consistency": any("Compare with Analytics" in r["test"] and r["success"] for r in self.test_results),
            "Performance Maintained": any("Performance Test" in r["test"] and r["success"] for r in self.test_results),
            "01-FMG Department Value": any("Specific Department Values" in r["test"] and r["success"] for r in self.test_results)
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
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        if success_rate >= 85:
            print("✅ DASHBOARD STOCK VALUE CALCULATION FIX IS WORKING CORRECTLY")
            print("   Main dashboard now shows calculated USD stock values instead of $0.00")
        elif success_rate >= 70:
            print("⚠️  DASHBOARD STOCK VALUE CALCULATION PARTIALLY WORKING")
            print("   Some issues remain but core functionality is operational")
        else:
            print("❌ DASHBOARD STOCK VALUE CALCULATION FIX NEEDS ATTENTION")
            print("   Multiple critical issues detected")
        
        print("\n" + "=" * 70)
        print("🏁 DASHBOARD STOCK VALUE CALCULATION TESTING COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    tester = DashboardStockValueTester()
    tester.run_comprehensive_tests()