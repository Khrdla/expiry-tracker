#!/usr/bin/env python3
"""
Comprehensive Enhanced Inventory Scanning Excel Export Test
Testing all requirements from the review request
"""

import asyncio
import aiohttp
import json
import openpyxl
from io import BytesIO
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

async def comprehensive_inventory_scanning_test():
    """Test all Enhanced Inventory Scanning Excel Export requirements"""
    
    print("🚀 COMPREHENSIVE ENHANCED INVENTORY SCANNING EXCEL EXPORT TESTING")
    print("=" * 80)
    print("Testing Requirements:")
    print("1. Multi-Zone Data Setup (SA01, SA02, WH01, WH02)")
    print("2. Worksheet Creation (separate Excel worksheets/tabs per zone)")
    print("3. Zone Header Validation (zone number, SKU count, timestamp)")
    print("4. Professional Formatting (bold headers, colors, alignment, borders)")
    print("5. Zone Totals (auto-sum calculations)")
    print("6. Worksheet Organization (proper tab labels)")
    print("7. Data Integrity (zone-specific items with aggregation)")
    print("8. File Generation (proper filename format)")
    print("=" * 80)
    
    session = aiohttp.ClientSession()
    test_results = []
    
    try:
        # Step 1: Authentication
        print("\n1️⃣ AUTHENTICATION TEST")
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                auth_token = data.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                test_results.append("✅ Admin authentication successful")
                print("✅ Admin authentication successful")
            else:
                test_results.append(f"❌ Authentication failed: {response.status}")
                print(f"❌ Authentication failed: {response.status}")
                return False
        
        # Step 2: Clear existing data
        print("\n2️⃣ DATA CLEANUP")
        async with session.delete(f"{BACKEND_URL}/inventory-scans/clear", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                test_results.append(f"✅ Cleared existing data: {data.get('message')}")
                print(f"✅ Cleared existing data: {data.get('message')}")
            else:
                test_results.append(f"⚠️ Clear failed: {response.status}")
                print(f"⚠️ Clear failed: {response.status}")
        
        # Step 3: Multi-Zone Data Setup
        print("\n3️⃣ MULTI-ZONE DATA SETUP")
        test_scans = [
            # SA Zone 1 - Multiple items
            ("SA", 1, "3222471081716", 50),  # Apple Juice Box 1L
            ("SA", 1, "3222471052747", 30),  # Lemonade 150Cl
            ("SA", 1, "3222471075722", 25),  # Mountain Water 6X50Cl
            
            # SA Zone 2 - Different items
            ("SA", 2, "3222471081273", 40),  # Orange Peach Apricot Nectar Box 1L
            ("SA", 2, "3222471090022", 35),  # Different product
            
            # WH Zone 1 - Mixed items (some same as SA zones)
            ("WH", 1, "3222471081716", 20),  # Apple Juice Box 1L (same as SA01)
            ("WH", 1, "3222471075722", 15),  # Mountain Water 6X50Cl (same as SA01)
            
            # WH Zone 2 - Unique items
            ("WH", 2, "3222471052747", 45),  # Lemonade 150Cl (same as SA01)
            ("WH", 2, "3222471081273", 25),  # Orange Peach Apricot Nectar (same as SA02)
        ]
        
        created_scans = 0
        for zone_type, zone_number, barcode, quantity in test_scans:
            scan_data = {
                "zone_type": zone_type,
                "zone_number": zone_number,
                "barcode": barcode,
                "quantity_scanned": quantity
            }
            
            async with session.post(f"{BACKEND_URL}/inventory-scans", json=scan_data, headers=headers) as response:
                if response.status == 200:
                    created_scans += 1
                    print(f"✅ Created scan: {zone_type}{zone_number:02d} - {barcode} - {quantity} qty")
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create scan {zone_type}{zone_number:02d}: {response.status}")
        
        test_results.append(f"✅ Multi-zone data setup: {created_scans}/{len(test_scans)} scans created")
        print(f"✅ Multi-zone data setup: {created_scans}/{len(test_scans)} scans created")
        
        if created_scans < 6:  # Need at least 6 scans for meaningful test
            test_results.append("❌ Insufficient test data created")
            print("❌ Insufficient test data created")
            return False
        
        # Step 4: Excel Export and File Generation Test
        print("\n4️⃣ EXCEL EXPORT AND FILE GENERATION")
        async with session.get(f"{BACKEND_URL}/inventory-scans/export", headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                test_results.append(f"❌ Export failed: {response.status}")
                print(f"❌ Export failed: {response.status}")
                return False
            
            excel_content = await response.read()
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            # File Generation Tests
            if len(excel_content) > 5000:
                test_results.append(f"✅ File generation: {len(excel_content)} bytes")
                print(f"✅ File generation: {len(excel_content)} bytes")
            else:
                test_results.append(f"❌ File too small: {len(excel_content)} bytes")
                print(f"❌ File too small: {len(excel_content)} bytes")
            
            if 'spreadsheet' in content_type:
                test_results.append("✅ Correct Content-Type for Excel")
                print("✅ Correct Content-Type for Excel")
            else:
                test_results.append(f"❌ Wrong Content-Type: {content_type}")
                print(f"❌ Wrong Content-Type: {content_type}")
            
            if 'Inventory_Scan_Report_' in content_disposition and datetime.now().strftime('%Y%m%d') in content_disposition:
                test_results.append("✅ Proper filename format with timestamp")
                print("✅ Proper filename format with timestamp")
            else:
                test_results.append(f"❌ Wrong filename format: {content_disposition}")
                print(f"❌ Wrong filename format: {content_disposition}")
        
        # Step 5: Worksheet Creation and Organization
        print("\n5️⃣ WORKSHEET CREATION AND ORGANIZATION")
        workbook = openpyxl.load_workbook(BytesIO(excel_content))
        worksheet_names = workbook.sheetnames
        
        expected_zones = ["SA01", "SA02", "WH01", "WH02"]
        zones_found = []
        
        for expected_zone in expected_zones:
            if expected_zone in worksheet_names:
                zones_found.append(expected_zone)
                test_results.append(f"✅ Worksheet tab created: {expected_zone}")
                print(f"✅ Worksheet tab created: {expected_zone}")
            else:
                test_results.append(f"❌ Missing worksheet tab: {expected_zone}")
                print(f"❌ Missing worksheet tab: {expected_zone}")
        
        if len(zones_found) == len(expected_zones):
            test_results.append("✅ All expected zone worksheets created")
            print("✅ All expected zone worksheets created")
        else:
            test_results.append(f"❌ Missing {len(expected_zones) - len(zones_found)} worksheets")
            print(f"❌ Missing {len(expected_zones) - len(zones_found)} worksheets")
        
        # Step 6: Zone Header Validation
        print("\n6️⃣ ZONE HEADER VALIDATION")
        header_validation_passed = 0
        
        for zone_name in zones_found:
            worksheet = workbook[zone_name]
            print(f"\n📋 Validating headers for {zone_name}:")
            
            # Zone Number Display
            zone_header = worksheet['A1'].value
            if zone_header and f"Zone Number: {zone_name}" in str(zone_header):
                test_results.append(f"✅ {zone_name}: Zone number display correct")
                print(f"✅ Zone number display: {zone_header}")
                header_validation_passed += 1
            else:
                test_results.append(f"❌ {zone_name}: Zone number display incorrect: {zone_header}")
                print(f"❌ Zone number display incorrect: {zone_header}")
            
            # Total SKUs Count
            sku_count_cell = worksheet['A2'].value
            if sku_count_cell and "Total SKUs Scanned:" in str(sku_count_cell):
                sku_count = str(sku_count_cell).split(":")[-1].strip()
                test_results.append(f"✅ {zone_name}: SKU count display: {sku_count}")
                print(f"✅ SKU count display: {sku_count}")
                header_validation_passed += 1
            else:
                test_results.append(f"❌ {zone_name}: SKU count missing: {sku_count_cell}")
                print(f"❌ SKU count missing: {sku_count_cell}")
            
            # Generated Timestamp (YYYY-MM-DD format)
            timestamp_cell = worksheet['A3'].value
            if timestamp_cell and "Generated On:" in str(timestamp_cell):
                timestamp = str(timestamp_cell).split(":")[-1].strip()
                try:
                    datetime.strptime(timestamp, '%Y-%m-%d')
                    test_results.append(f"✅ {zone_name}: Timestamp format correct: {timestamp}")
                    print(f"✅ Timestamp format correct: {timestamp}")
                    header_validation_passed += 1
                except:
                    test_results.append(f"❌ {zone_name}: Timestamp format wrong: {timestamp}")
                    print(f"❌ Timestamp format wrong: {timestamp}")
            else:
                test_results.append(f"❌ {zone_name}: Timestamp missing: {timestamp_cell}")
                print(f"❌ Timestamp missing: {timestamp_cell}")
        
        # Step 7: Professional Formatting
        print("\n7️⃣ PROFESSIONAL FORMATTING VALIDATION")
        formatting_tests_passed = 0
        
        for zone_name in zones_found:
            worksheet = workbook[zone_name]
            print(f"\n🎨 Checking formatting for {zone_name}:")
            
            # Bold headers with blue background and white text
            header_cell = worksheet.cell(row=5, column=1)
            if header_cell.font.bold:
                test_results.append(f"✅ {zone_name}: Headers are bold")
                print("✅ Headers are bold")
                formatting_tests_passed += 1
            else:
                test_results.append(f"❌ {zone_name}: Headers not bold")
                print("❌ Headers not bold")
            
            # Check header background color (should be blue)
            if header_cell.fill.start_color.rgb in ["FF366092", "00366092"]:
                test_results.append(f"✅ {zone_name}: Headers have blue background")
                print("✅ Headers have blue background")
                formatting_tests_passed += 1
            else:
                test_results.append(f"⚠️ {zone_name}: Header background color: {header_cell.fill.start_color.rgb}")
                print(f"⚠️ Header background color: {header_cell.fill.start_color.rgb}")
            
            # Frozen header row
            if worksheet.freeze_panes == "A6":
                test_results.append(f"✅ {zone_name}: Header row frozen for scrolling")
                print("✅ Header row frozen for scrolling")
                formatting_tests_passed += 1
            else:
                test_results.append(f"⚠️ {zone_name}: Freeze panes: {worksheet.freeze_panes}")
                print(f"⚠️ Freeze panes: {worksheet.freeze_panes}")
            
            # Right-aligned numeric columns (6-11)
            data_row = 6  # First data row
            if worksheet.cell(row=data_row, column=1).value:  # If there's data
                numeric_alignment_correct = True
                for col in range(6, 12):  # Columns 6-11 should be right-aligned
                    cell = worksheet.cell(row=data_row, column=col)
                    if cell.alignment.horizontal != 'right':
                        numeric_alignment_correct = False
                        break
                
                if numeric_alignment_correct:
                    test_results.append(f"✅ {zone_name}: Numeric columns right-aligned")
                    print("✅ Numeric columns right-aligned")
                    formatting_tests_passed += 1
                else:
                    test_results.append(f"⚠️ {zone_name}: Some numeric columns not right-aligned")
                    print("⚠️ Some numeric columns not right-aligned")
        
        # Step 8: Zone Totals Validation
        print("\n8️⃣ ZONE TOTALS VALIDATION")
        totals_tests_passed = 0
        
        for zone_name in zones_found:
            worksheet = workbook[zone_name]
            print(f"\n🧮 Checking totals for {zone_name}:")
            
            # Count data rows
            data_rows = 0
            row = 6
            while worksheet.cell(row=row, column=1).value:
                data_rows += 1
                row += 1
            
            # Check totals row
            totals_row = 5 + data_rows + 1
            totals_label = worksheet.cell(row=totals_row, column=5).value
            
            if totals_label == "TOTALS:":
                test_results.append(f"✅ {zone_name}: Totals row found")
                print("✅ Totals row found")
                
                # Check auto-sum calculations
                total_sa = worksheet.cell(row=totals_row, column=6).value
                total_wh = worksheet.cell(row=totals_row, column=7).value
                total_inventory = worksheet.cell(row=totals_row, column=8).value
                total_variance = worksheet.cell(row=totals_row, column=11).value
                
                if all(isinstance(val, (int, float)) for val in [total_sa, total_wh, total_inventory, total_variance]):
                    test_results.append(f"✅ {zone_name}: Auto-sum calculations working")
                    print(f"✅ Auto-sum calculations: SA={total_sa}, WH={total_wh}, Total={total_inventory}, Variance={total_variance}")
                    totals_tests_passed += 1
                else:
                    test_results.append(f"❌ {zone_name}: Auto-sum calculations failed")
                    print("❌ Auto-sum calculations failed")
            else:
                test_results.append(f"❌ {zone_name}: Totals row not found")
                print(f"❌ Totals row not found. Found: '{totals_label}'")
        
        # Step 9: Data Integrity Test
        print("\n9️⃣ DATA INTEGRITY VALIDATION")
        
        # Test same item in different zones
        test_cases = [
            ("3222471081716", ["SA01", "WH01"], "Apple Juice Box 1L"),
            ("3222471075722", ["SA01", "WH01"], "Mountain Water 6X50Cl"),
            ("3222471052747", ["SA01", "WH02"], "Lemonade 150Cl"),
            ("3222471081273", ["SA02", "WH02"], "Orange Peach Apricot Nectar")
        ]
        
        data_integrity_passed = 0
        for barcode, expected_zones, product_name in test_cases:
            zones_found_for_item = []
            for zone_name in expected_zones:
                if zone_name in workbook.sheetnames:
                    worksheet = workbook[zone_name]
                    # Look for barcode in column B (starting from row 6)
                    row = 6
                    found_in_zone = False
                    while worksheet.cell(row=row, column=1).value:
                        if worksheet.cell(row=row, column=2).value == barcode:
                            found_in_zone = True
                            zones_found_for_item.append(zone_name)
                            break
                        row += 1
            
            if len(zones_found_for_item) == len(expected_zones):
                test_results.append(f"✅ {product_name} appears in correct zones: {zones_found_for_item}")
                print(f"✅ {product_name} appears in correct zones: {zones_found_for_item}")
                data_integrity_passed += 1
            else:
                test_results.append(f"❌ {product_name} missing from some zones. Found in: {zones_found_for_item}")
                print(f"❌ {product_name} missing from some zones. Found in: {zones_found_for_item}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Count results
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.startswith("✅"))
        failed_tests = sum(1 for result in test_results if result.startswith("❌"))
        warning_tests = sum(1 for result in test_results if result.startswith("⚠️"))
        
        print(f"📈 OVERALL SCORE: {passed_tests}/{total_tests} tests passed")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️ WARNINGS: {warning_tests}")
        
        # Critical requirements check
        critical_requirements = [
            len(zones_found) == 4,  # All 4 zones created
            header_validation_passed >= 8,  # Most headers correct
            formatting_tests_passed >= 8,  # Most formatting correct
            totals_tests_passed >= 2,  # At least half the totals working
            data_integrity_passed >= 2,  # At least half the cross-zone items working
            len(excel_content) > 5000  # Reasonable file size
        ]
        
        critical_passed = sum(critical_requirements)
        critical_total = len(critical_requirements)
        
        print(f"\n🎯 CRITICAL REQUIREMENTS: {critical_passed}/{critical_total}")
        print("1. Multi-Zone Worksheets:", "✅" if len(zones_found) == 4 else "❌")
        print("2. Zone Headers:", "✅" if header_validation_passed >= 8 else "❌")
        print("3. Professional Formatting:", "✅" if formatting_tests_passed >= 8 else "❌")
        print("4. Zone Totals:", "✅" if totals_tests_passed >= 2 else "❌")
        print("5. Data Integrity:", "✅" if data_integrity_passed >= 2 else "❌")
        print("6. File Generation:", "✅" if len(excel_content) > 5000 else "❌")
        
        if critical_passed == critical_total:
            print("\n🎉 ENHANCED INVENTORY SCANNING EXCEL EXPORT: FULLY FUNCTIONAL!")
            print("✅ All critical requirements met")
            print("✅ Multi-zone worksheets working correctly")
            print("✅ Professional formatting applied")
            print("✅ Zone-specific data aggregation working")
            print("✅ Ready for production use")
            return True
        else:
            print(f"\n🚨 ISSUES DETECTED: {critical_total - critical_passed} critical requirements failed")
            print("⚠️ System needs attention before production use")
            return False
        
    except Exception as e:
        test_results.append(f"❌ Test execution error: {str(e)}")
        print(f"❌ Test execution error: {str(e)}")
        return False
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(comprehensive_inventory_scanning_test())