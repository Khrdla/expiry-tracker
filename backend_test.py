#!/usr/bin/env python3
"""
Enhanced Inventory Scanning Excel Export Testing
Testing multi-zone Excel export with separate worksheets per zone
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import openpyxl
from io import BytesIO

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class InventoryScanningTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.test_results.append("✅ Authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Authentication error: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def clear_existing_scans(self):
        """Clear all existing inventory scans"""
        try:
            async with self.session.delete(
                f"{BACKEND_URL}/inventory-scans/clear",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(f"✅ Cleared existing scans: {data.get('message', 'Success')}")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Failed to clear scans: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Clear scans error: {str(e)}")
            return False
            
    async def create_inventory_scan(self, zone_type, zone_number, barcode, quantity):
        """Create an inventory scan entry"""
        try:
            scan_data = {
                "zone_type": zone_type,
                "zone_number": zone_number,
                "barcode": barcode,
                "quantity_scanned": quantity
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/inventory-scans",
                json=scan_data,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_results.append(f"✅ Created scan: {zone_type}{zone_number:02d} - {barcode} - {quantity} qty")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Failed to create scan {zone_type}{zone_number:02d}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results.append(f"❌ Create scan error: {str(e)}")
            return False
            
    async def setup_multi_zone_data(self):
        """Setup inventory scans in multiple zones with different items"""
        self.test_results.append("\n🔧 SETTING UP MULTI-ZONE TEST DATA:")
        
        # Test data for different zones
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
            ("WH", 1, "9501100046987", 60),  # Different product
            
            # WH Zone 2 - Unique items
            ("WH", 2, "3222471052747", 45),  # Lemonade 150Cl (same as SA01)
            ("WH", 2, "3222471081273", 25),  # Orange Peach Apricot Nectar (same as SA02)
        ]
        
        success_count = 0
        for zone_type, zone_number, barcode, quantity in test_scans:
            if await self.create_inventory_scan(zone_type, zone_number, barcode, quantity):
                success_count += 1
                
        self.test_results.append(f"✅ Created {success_count}/{len(test_scans)} inventory scans")
        return success_count == len(test_scans)
        
    async def export_and_analyze_excel(self):
        """Export inventory scans to Excel and analyze the multi-worksheet structure"""
        try:
            self.test_results.append("\n📊 TESTING EXCEL EXPORT WITH MULTIPLE WORKSHEETS:")
            
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans/export",
                headers=self.get_auth_headers()
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Export failed: {response.status} - {error_text}")
                    return False
                    
                # Get the Excel file content
                excel_content = await response.read()
                self.test_results.append(f"✅ Excel file downloaded: {len(excel_content)} bytes")
                
                # Verify Content-Type header
                content_type = response.headers.get('content-type', '')
                if 'spreadsheet' in content_type:
                    self.test_results.append("✅ Correct Content-Type header for Excel file")
                else:
                    self.test_results.append(f"⚠️ Unexpected Content-Type: {content_type}")
                
                # Verify filename
                content_disposition = response.headers.get('content-disposition', '')
                if 'Inventory_Scan_Report_' in content_disposition:
                    self.test_results.append("✅ Proper filename format with timestamp")
                else:
                    self.test_results.append(f"⚠️ Unexpected filename: {content_disposition}")
                
                # Analyze Excel structure
                return await self.analyze_excel_structure(excel_content)
                
        except Exception as e:
            self.test_results.append(f"❌ Export error: {str(e)}")
            return False
            
    async def analyze_excel_structure(self, excel_content):
        """Analyze the Excel file structure for multiple worksheets"""
        try:
            self.test_results.append("\n🔍 ANALYZING EXCEL STRUCTURE:")
            
            # Load Excel file
            workbook = openpyxl.load_workbook(BytesIO(excel_content))
            
            # Check worksheet names
            worksheet_names = workbook.sheetnames
            self.test_results.append(f"✅ Found {len(worksheet_names)} worksheets: {worksheet_names}")
            
            # Expected zones based on our test data
            expected_zones = ["SA01", "SA02", "WH01", "WH02"]
            
            # Verify each expected zone has a worksheet
            zones_found = []
            for expected_zone in expected_zones:
                if expected_zone in worksheet_names:
                    zones_found.append(expected_zone)
                    self.test_results.append(f"✅ Worksheet found for zone: {expected_zone}")
                else:
                    self.test_results.append(f"❌ Missing worksheet for zone: {expected_zone}")
            
            if len(zones_found) == len(expected_zones):
                self.test_results.append("✅ All expected zone worksheets created")
            else:
                self.test_results.append(f"❌ Missing {len(expected_zones) - len(zones_found)} zone worksheets")
            
            # Analyze each worksheet
            worksheet_analysis_success = True
            for zone_name in zones_found:
                if not await self.analyze_worksheet(workbook[zone_name], zone_name):
                    worksheet_analysis_success = False
            
            return worksheet_analysis_success and len(zones_found) == len(expected_zones)
            
        except Exception as e:
            self.test_results.append(f"❌ Excel analysis error: {str(e)}")
            return False
            
    async def analyze_worksheet(self, worksheet, zone_name):
        """Analyze individual worksheet structure and formatting"""
        try:
            self.test_results.append(f"\n📋 ANALYZING WORKSHEET: {zone_name}")
            
            # Check zone header information
            zone_header = worksheet['A1'].value
            if zone_header and f"Zone Number: {zone_name}" in str(zone_header):
                self.test_results.append(f"✅ Zone header correct: {zone_header}")
            else:
                self.test_results.append(f"❌ Zone header incorrect: {zone_header}")
                return False
            
            # Check SKU count header
            sku_count_cell = worksheet['A2'].value
            if sku_count_cell and "Total SKUs Scanned:" in str(sku_count_cell):
                sku_count = str(sku_count_cell).split(":")[-1].strip()
                self.test_results.append(f"✅ SKU count header found: {sku_count} SKUs")
            else:
                self.test_results.append(f"❌ SKU count header missing: {sku_count_cell}")
                return False
            
            # Check timestamp header
            timestamp_cell = worksheet['A3'].value
            if timestamp_cell and "Generated On:" in str(timestamp_cell):
                timestamp = str(timestamp_cell).split(":")[-1].strip()
                # Verify YYYY-MM-DD format
                try:
                    datetime.strptime(timestamp, '%Y-%m-%d')
                    self.test_results.append(f"✅ Timestamp header correct format: {timestamp}")
                except:
                    self.test_results.append(f"⚠️ Timestamp format unexpected: {timestamp}")
            else:
                self.test_results.append(f"❌ Timestamp header missing: {timestamp_cell}")
                return False
            
            # Check table headers (row 5)
            expected_headers = [
                "Item Number", "Barcode", "Description", "Supplier Code", "Supplier Name",
                "Qty Scanned in SA", "Qty Scanned in WH", "Total Inventory Scan",
                "System Stock", "Variance in Qty", "Variance in Value"
            ]
            
            headers_correct = True
            for col_num, expected_header in enumerate(expected_headers, 1):
                actual_header = worksheet.cell(row=5, column=col_num).value
                if actual_header == expected_header:
                    continue
                else:
                    self.test_results.append(f"❌ Header mismatch col {col_num}: expected '{expected_header}', got '{actual_header}'")
                    headers_correct = False
            
            if headers_correct:
                self.test_results.append("✅ All table headers correct")
            
            # Check header formatting
            header_cell = worksheet.cell(row=5, column=1)
            if header_cell.font.bold:
                self.test_results.append("✅ Headers are bold")
            else:
                self.test_results.append("❌ Headers are not bold")
                
            if header_cell.fill.start_color.rgb == "FF366092":  # Blue background
                self.test_results.append("✅ Headers have blue background")
            else:
                self.test_results.append(f"⚠️ Header background color: {header_cell.fill.start_color.rgb}")
                
            if header_cell.font.color.rgb == "FFFFFFFF":  # White text
                self.test_results.append("✅ Headers have white text")
            else:
                self.test_results.append(f"⚠️ Header text color: {header_cell.font.color.rgb}")
            
            # Check frozen panes
            if worksheet.freeze_panes == "A6":
                self.test_results.append("✅ Header row is frozen")
            else:
                self.test_results.append(f"⚠️ Freeze panes setting: {worksheet.freeze_panes}")
            
            # Check data rows and formatting
            data_rows_found = 0
            row = 6  # First data row
            while worksheet.cell(row=row, column=1).value:
                data_rows_found += 1
                
                # Check numeric column alignment (columns 6-11)
                for col in range(6, 12):
                    cell = worksheet.cell(row=row, column=col)
                    if cell.alignment.horizontal == 'right':
                        continue
                    else:
                        self.test_results.append(f"⚠️ Row {row} Col {col} not right-aligned")
                        break
                
                # Check alternating row colors
                if row % 2 == 0:  # Even rows should have background
                    cell = worksheet.cell(row=row, column=1)
                    if cell.fill.start_color.rgb == "FFF2F2F2":
                        continue
                    else:
                        self.test_results.append(f"⚠️ Row {row} missing alternating background")
                        break
                
                row += 1
            
            self.test_results.append(f"✅ Found {data_rows_found} data rows in {zone_name}")
            
            # Check totals row
            totals_row = 5 + data_rows_found + 1
            totals_label = worksheet.cell(row=totals_row, column=5).value
            if totals_label == "TOTALS:":
                self.test_results.append("✅ Totals row found with correct label")
                
                # Check if totals are calculated
                total_sa = worksheet.cell(row=totals_row, column=6).value
                total_wh = worksheet.cell(row=totals_row, column=7).value
                total_inventory = worksheet.cell(row=totals_row, column=8).value
                total_variance = worksheet.cell(row=totals_row, column=11).value
                
                if all(isinstance(val, (int, float)) for val in [total_sa, total_wh, total_inventory, total_variance]):
                    self.test_results.append(f"✅ Zone totals calculated: SA={total_sa}, WH={total_wh}, Total={total_inventory}, Variance={total_variance}")
                else:
                    self.test_results.append("❌ Zone totals not properly calculated")
                    return False
            else:
                self.test_results.append(f"❌ Totals row not found or incorrect: {totals_label}")
                return False
            
            # Check borders on all cells
            borders_correct = True
            for row_num in range(5, totals_row + 1):
                for col_num in range(1, len(expected_headers) + 1):
                    cell = worksheet.cell(row=row_num, column=col_num)
                    if not (cell.border.left.style and cell.border.right.style and 
                           cell.border.top.style and cell.border.bottom.style):
                        borders_correct = False
                        break
                if not borders_correct:
                    break
            
            if borders_correct:
                self.test_results.append("✅ All cells have proper borders")
            else:
                self.test_results.append("⚠️ Some cells missing borders")
            
            return True
            
        except Exception as e:
            self.test_results.append(f"❌ Worksheet analysis error for {zone_name}: {str(e)}")
            return False
            
    async def verify_data_integrity(self):
        """Verify that each zone shows only its scanned items with proper aggregation"""
        try:
            self.test_results.append("\n🔍 VERIFYING DATA INTEGRITY:")
            
            # Get all scans from API
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans",
                headers=self.get_auth_headers()
            ) as response:
                if response.status != 200:
                    self.test_results.append("❌ Could not retrieve scans for verification")
                    return False
                    
                scans_data = await response.json()
                self.test_results.append(f"✅ Retrieved {len(scans_data)} scan records")
                
                # Group by zone for verification
                zones_data = {}
                for scan in scans_data:
                    zone_key = f"{scan['zone_type']}{scan['zone_number']:02d}"
                    if zone_key not in zones_data:
                        zones_data[zone_key] = []
                    zones_data[zone_key].append(scan)
                
                # Verify each zone has correct data
                for zone_key, zone_scans in zones_data.items():
                    unique_barcodes = set(scan['barcode'] for scan in zone_scans)
                    self.test_results.append(f"✅ Zone {zone_key}: {len(zone_scans)} scans, {len(unique_barcodes)} unique items")
                    
                    # Verify aggregation for items scanned multiple times
                    barcode_totals = {}
                    for scan in zone_scans:
                        barcode = scan['barcode']
                        if barcode not in barcode_totals:
                            barcode_totals[barcode] = 0
                        barcode_totals[barcode] += scan.get('qty_scanned_sa', 0) + scan.get('qty_scanned_wh', 0)
                    
                    for barcode, total_qty in barcode_totals.items():
                        if total_qty > 0:
                            self.test_results.append(f"✅ {zone_key} - {barcode}: {total_qty} total qty")
                
                return True
                
        except Exception as e:
            self.test_results.append(f"❌ Data integrity verification error: {str(e)}")
            return False
            
    async def test_same_item_different_zones(self):
        """Test that same item scanned in different zones appears in respective worksheets"""
        try:
            self.test_results.append("\n🔄 TESTING SAME ITEM IN DIFFERENT ZONES:")
            
            # Apple Juice Box 1L (3222471081716) should appear in SA01 and WH01
            # Mountain Water (3222471075722) should appear in SA01 and WH01
            # Lemonade (3222471052747) should appear in SA01 and WH02
            
            test_cases = [
                ("3222471081716", ["SA01", "WH01"], "Apple Juice Box 1L"),
                ("3222471075722", ["SA01", "WH01"], "Mountain Water 6X50Cl"),
                ("3222471052747", ["SA01", "WH02"], "Lemonade 150Cl")
            ]
            
            # Export Excel again to verify
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans/export",
                headers=self.get_auth_headers()
            ) as response:
                if response.status != 200:
                    self.test_results.append("❌ Could not export Excel for cross-zone verification")
                    return False
                    
                excel_content = await response.read()
                workbook = openpyxl.load_workbook(BytesIO(excel_content))
                
                for barcode, expected_zones, product_name in test_cases:
                    zones_found = []
                    for zone_name in expected_zones:
                        if zone_name in workbook.sheetnames:
                            worksheet = workbook[zone_name]
                            # Look for barcode in column B (starting from row 6)
                            row = 6
                            found_in_zone = False
                            while worksheet.cell(row=row, column=1).value:  # While there's data
                                if worksheet.cell(row=row, column=2).value == barcode:
                                    found_in_zone = True
                                    zones_found.append(zone_name)
                                    break
                                row += 1
                            
                            if found_in_zone:
                                self.test_results.append(f"✅ {product_name} ({barcode}) found in {zone_name}")
                            else:
                                self.test_results.append(f"❌ {product_name} ({barcode}) NOT found in {zone_name}")
                    
                    if len(zones_found) == len(expected_zones):
                        self.test_results.append(f"✅ {product_name} correctly appears in all expected zones")
                    else:
                        self.test_results.append(f"❌ {product_name} missing from some zones")
                        return False
                
                return True
                
        except Exception as e:
            self.test_results.append(f"❌ Cross-zone verification error: {str(e)}")
            return False
            
    async def run_comprehensive_test(self):
        """Run comprehensive test of Enhanced Inventory Scanning Excel Export"""
        print("🚀 STARTING ENHANCED INVENTORY SCANNING EXCEL EXPORT TESTING")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Step 1: Authentication
            if not await self.authenticate():
                return False
                
            # Step 2: Clear existing data
            if not await self.clear_existing_scans():
                return False
                
            # Step 3: Setup multi-zone test data
            if not await self.setup_multi_zone_data():
                return False
                
            # Step 4: Export and analyze Excel structure
            if not await self.export_and_analyze_excel():
                return False
                
            # Step 5: Verify data integrity
            if not await self.verify_data_integrity():
                return False
                
            # Step 6: Test same item in different zones
            if not await self.test_same_item_different_zones():
                return False
                
            self.test_results.append("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            self.test_results.append(f"❌ Test execution error: {str(e)}")
            return False
        finally:
            await self.cleanup_session()
            
    def print_results(self):
        """Print all test results"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            print(result)
            
        # Count successes and failures
        successes = sum(1 for result in self.test_results if result.startswith("✅"))
        failures = sum(1 for result in self.test_results if result.startswith("❌"))
        warnings = sum(1 for result in self.test_results if result.startswith("⚠️"))
        
        print("\n" + "=" * 80)
        print(f"📈 FINAL SCORE: {successes} ✅ | {failures} ❌ | {warnings} ⚠️")
        
        if failures == 0:
            print("🎉 ENHANCED INVENTORY SCANNING EXCEL EXPORT: FULLY FUNCTIONAL!")
        else:
            print("🚨 ISSUES DETECTED - NEEDS ATTENTION")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    tester = InventoryScanningTester()
    success = await tester.run_comprehensive_test()
    tester.print_results()
    return success

if __name__ == "__main__":
    asyncio.run(main())