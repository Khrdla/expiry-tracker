#!/usr/bin/env python3
"""
URGENT: Dashboard API Debug Test for Expired Items Count Discrepancy
User reports dashboard shows 6 expired items but only added 1 item.
Troubleshoot agent found database is completely empty.
Need to identify source of the 6 expired items.
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class DashboardDebugTester:
    def __init__(self, base_url="https://stock-genius-24.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
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
        
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")

    def login(self):
        """Login with admin credentials"""
        print(f"\n🔑 Logging in as admin: {self.admin_username}")
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": self.admin_username, "password": self.admin_password},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    print(f"✅ Login successful, token obtained: {self.token[:20]}...")
                    return True
                else:
                    print(f"❌ Login failed: No access token in response")
                    return False
            else:
                print(f"❌ Login failed: Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def test_dashboard_api_direct(self):
        """Test GET /api/dashboard endpoint directly"""
        print(f"\n🔍 DIRECT DASHBOARD API TEST")
        print("=" * 60)
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/dashboard",
                headers=headers,
                timeout=30
            )
            
            print(f"📡 Request URL: {self.api_url}/dashboard")
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n📋 DASHBOARD API RESPONSE:")
                    print("=" * 40)
                    print(json.dumps(data, indent=2, default=str))
                    
                    # Extract KPI data
                    kpis = data.get('kpis', [])
                    print(f"\n📊 KPI ANALYSIS:")
                    print("=" * 30)
                    
                    total_expired = 0
                    total_items = 0
                    
                    for i, kpi in enumerate(kpis):
                        dept = kpi.get('department', 'Unknown')
                        expired = kpi.get('expired_items', 0)
                        total = kpi.get('total_items', 0)
                        near_expiry = kpi.get('near_expiry_items', 0)
                        out_of_stock = kpi.get('out_of_stock_items', 0)
                        low_stock = kpi.get('low_stock_items', 0)
                        stock_value = kpi.get('total_stock_value', 0)
                        
                        print(f"Department {i+1}: {dept}")
                        print(f"  Total Items: {total}")
                        print(f"  Expired Items: {expired}")
                        print(f"  Near Expiry: {near_expiry}")
                        print(f"  Out of Stock: {out_of_stock}")
                        print(f"  Low Stock: {low_stock}")
                        print(f"  Stock Value: {stock_value}")
                        print()
                        
                        total_expired += expired
                        total_items += total
                    
                    print(f"🚨 CRITICAL FINDINGS:")
                    print(f"   Total Expired Items Across All Departments: {total_expired}")
                    print(f"   Total Items in Database: {total_items}")
                    
                    # Check expiry_status summary
                    expiry_status = data.get('expiry_status', {})
                    if expiry_status:
                        print(f"\n📈 EXPIRY STATUS SUMMARY:")
                        for status, count in expiry_status.items():
                            print(f"   {status}: {count}")
                    
                    # This is the key finding for the bug report
                    if total_expired == 6:
                        print(f"\n🎯 ISSUE CONFIRMED: Dashboard shows {total_expired} expired items")
                        self.log_test("Dashboard Expired Items Count", False, 
                                    f"Shows {total_expired} expired items when database should be empty")
                    elif total_expired == 0:
                        print(f"\n✅ NO ISSUE: Dashboard correctly shows {total_expired} expired items")
                        self.log_test("Dashboard Expired Items Count", True, 
                                    f"Correctly shows {total_expired} expired items")
                    else:
                        print(f"\n⚠️ UNEXPECTED: Dashboard shows {total_expired} expired items (expected 0 or 6)")
                        self.log_test("Dashboard Expired Items Count", False, 
                                    f"Shows {total_expired} expired items (unexpected count)")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {str(e)}")
                    print(f"Raw response: {response.text[:500]}")
                    return False
            else:
                print(f"❌ Dashboard API failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard API test error: {str(e)}")
            return False

    def test_database_verification(self):
        """Verify database is truly empty by checking products count"""
        print(f"\n🗄️ DATABASE VERIFICATION TEST")
        print("=" * 50)
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            # Test products endpoint to count actual products
            response = requests.get(
                f"{self.api_url}/products?limit=1000",  # Get up to 1000 products
                headers=headers,
                timeout=30
            )
            
            print(f"📡 Request URL: {self.api_url}/products?limit=1000")
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    products = response.json()
                    if isinstance(products, list):
                        total_products = len(products)
                        print(f"\n📦 PRODUCTS IN DATABASE: {total_products}")
                        
                        if total_products == 0:
                            print("✅ Database is confirmed EMPTY - no products found")
                            self.log_test("Database Empty Verification", True, "Database contains 0 products")
                        else:
                            print(f"⚠️ Database is NOT empty - found {total_products} products")
                            
                            # Check expiry dates of products
                            expired_count = 0
                            near_expiry_count = 0
                            products_with_expiry = 0
                            
                            for product in products[:10]:  # Check first 10 products
                                expiry_date = product.get('expiry_date')
                                if expiry_date:
                                    products_with_expiry += 1
                                    try:
                                        if isinstance(expiry_date, str):
                                            expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                                        else:
                                            expiry_dt = expiry_date
                                        
                                        now = datetime.utcnow()
                                        if expiry_dt < now:
                                            expired_count += 1
                                        elif expiry_dt < now + timedelta(days=7):
                                            near_expiry_count += 1
                                    except:
                                        pass
                            
                            print(f"   Products with expiry dates (first 10): {products_with_expiry}")
                            print(f"   Expired products (first 10): {expired_count}")
                            print(f"   Near expiry products (first 10): {near_expiry_count}")
                            
                            # Show sample products
                            print(f"\n📋 SAMPLE PRODUCTS:")
                            for i, product in enumerate(products[:5], 1):
                                name = product.get('product_name', 'Unknown')
                                dept = product.get('department', 'Unknown')
                                quantity = product.get('quantity', 0)
                                expiry = product.get('expiry_date', 'None')
                                print(f"   {i}. {name} ({dept}) - Qty: {quantity}, Expiry: {expiry}")
                            
                            self.log_test("Database Empty Verification", False, 
                                        f"Database contains {total_products} products, not empty")
                        
                        return total_products == 0
                    else:
                        print(f"❌ Unexpected response format: {type(products)}")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse products response: {str(e)}")
                    return False
            else:
                print(f"❌ Products API failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Database verification error: {str(e)}")
            return False

    def test_kpi_calculation_with_empty_db(self):
        """Test KPI calculation behavior with empty database"""
        print(f"\n🧮 KPI CALCULATION TEST")
        print("=" * 40)
        
        # First verify if database is empty
        is_empty = self.test_database_verification()
        
        if is_empty:
            print(f"\n✅ Database confirmed empty, testing KPI calculation...")
            
            # Now test dashboard again to see KPI calculation
            dashboard_success = self.test_dashboard_api_direct()
            
            if dashboard_success:
                print(f"\n🔍 ANALYSIS: Empty database but dashboard may show non-zero values")
                print("This suggests:")
                print("1. KPI calculation has hardcoded/cached values")
                print("2. Database connection issues")
                print("3. Different database being queried")
                print("4. Calculation logic errors")
                
                return True
        else:
            print(f"\n⚠️ Database is not empty, so expired items count may be legitimate")
            return True

    def test_calculate_product_status_function(self):
        """Test the calculate_product_status function behavior"""
        print(f"\n⚙️ PRODUCT STATUS CALCULATION TEST")
        print("=" * 50)
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Get a few products to test status calculation
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/products?limit=10",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                products = response.json()
                if isinstance(products, list) and len(products) > 0:
                    print(f"📦 Testing status calculation on {len(products)} products:")
                    
                    for i, product in enumerate(products, 1):
                        name = product.get('product_name', 'Unknown')
                        quantity = product.get('quantity', 0)
                        expiry_date = product.get('expiry_date')
                        status = product.get('status', 'unknown')
                        
                        print(f"   {i}. {name[:30]}...")
                        print(f"      Quantity: {quantity}")
                        print(f"      Expiry Date: {expiry_date}")
                        print(f"      Calculated Status: {status}")
                        
                        # Manual status calculation
                        manual_status = "unknown"
                        if quantity <= 0:
                            manual_status = "out_of_stock"
                        elif expiry_date:
                            try:
                                if isinstance(expiry_date, str):
                                    expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                                    now = datetime.utcnow()
                                    if expiry_dt < now:
                                        manual_status = "expired"
                                    elif expiry_dt < now + timedelta(days=7):
                                        manual_status = "near_expiry"
                                    else:
                                        manual_status = "in_stock"
                            except:
                                manual_status = "in_stock"
                        else:
                            manual_status = "in_stock"
                        
                        print(f"      Manual Calculation: {manual_status}")
                        
                        if status != manual_status:
                            print(f"      ⚠️ STATUS MISMATCH!")
                        else:
                            print(f"      ✅ Status calculation correct")
                        print()
                    
                    return True
                else:
                    print("📦 No products found for status calculation test")
                    return True
            else:
                print(f"❌ Failed to get products for status test: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Status calculation test error: {str(e)}")
            return False

    def run_comprehensive_debug(self):
        """Run comprehensive debug test for expired items discrepancy"""
        print("🚨 URGENT: DASHBOARD EXPIRED ITEMS DEBUG TEST")
        print("=" * 60)
        print("Issue: User reports 6 expired items but only added 1 item")
        print("Troubleshoot agent found database completely empty")
        print("Need to identify source of 6 expired items count")
        print("=" * 60)
        
        # Step 1: Login
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Direct dashboard API test
        print(f"\n" + "="*60)
        print("STEP 1: DIRECT DASHBOARD API TEST")
        print("="*60)
        dashboard_success = self.test_dashboard_api_direct()
        
        # Step 3: Database verification
        print(f"\n" + "="*60)
        print("STEP 2: DATABASE VERIFICATION")
        print("="*60)
        db_empty = self.test_database_verification()
        
        # Step 4: KPI calculation test
        print(f"\n" + "="*60)
        print("STEP 3: KPI CALCULATION ANALYSIS")
        print("="*60)
        kpi_success = self.test_kpi_calculation_with_empty_db()
        
        # Step 5: Product status calculation test
        print(f"\n" + "="*60)
        print("STEP 4: PRODUCT STATUS CALCULATION TEST")
        print("="*60)
        status_success = self.test_calculate_product_status_function()
        
        # Final analysis
        print(f"\n" + "="*60)
        print("FINAL ANALYSIS & RECOMMENDATIONS")
        print("="*60)
        
        print(f"Tests completed: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🔍 KEY FINDINGS:")
        if db_empty:
            print("✅ Database is confirmed empty (0 products)")
            print("🚨 If dashboard still shows 6 expired items, this indicates:")
            print("   - Hardcoded/cached values in KPI calculation")
            print("   - Database connection issues")
            print("   - Different database being queried")
            print("   - Bug in calculate_product_status function")
        else:
            print("⚠️ Database is NOT empty - contains products")
            print("📊 Expired items count may be legitimate")
            print("🔍 Need to verify actual expiry dates vs calculation")
        
        print(f"\n💡 NEXT STEPS:")
        print("1. Check backend logs for database connection issues")
        print("2. Verify MONGO_URL environment variable")
        print("3. Check if multiple databases exist")
        print("4. Review calculate_product_status function logic")
        print("5. Clear any cached KPI values")
        
        return True

if __name__ == "__main__":
    tester = DashboardDebugTester()
    tester.run_comprehensive_debug()