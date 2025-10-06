#!/usr/bin/env python3
"""
Comprehensive Inventory Scanning PDF Export Testing
Testing PDF export functionality with zone-based pages, headers, and professional layout
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import openpyxl
from io import BytesIO
import PyPDF2

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

class InventoryScanningPDFTester:
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
            ("WH", 1, "3222471081273", 60),  # Orange Peach Apricot Nectar (different from SA02)
            
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
        
    async def test_pdf_export_endpoint(self):
        """Test the PDF export endpoint and verify PDF generation"""
        try:
            self.test_results.append("\n📄 TESTING PDF EXPORT ENDPOINT:")
            
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans/export-pdf",
                headers=self.get_auth_headers()
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.test_results.append(f"❌ PDF Export failed: {response.status} - {error_text}")
                    return False, None
                    
                # Get the PDF file content
                pdf_content = await response.read()
                self.test_results.append(f"✅ PDF file downloaded: {len(pdf_content)} bytes")
                
                # Verify Content-Type header
                content_type = response.headers.get('content-type', '')
                if content_type == 'application/pdf':
                    self.test_results.append("✅ Correct Content-Type header for PDF file")
                else:
                    self.test_results.append(f"❌ Incorrect Content-Type: {content_type}")
                
                # Verify filename
                content_disposition = response.headers.get('content-disposition', '')
                if 'Inventory_Scan_Report_PDF_' in content_disposition and '.pdf' in content_disposition:
                    self.test_results.append("✅ Proper PDF filename format with timestamp")
                else:
                    self.test_results.append(f"❌ Unexpected PDF filename: {content_disposition}")
                
                # Verify PDF file is valid
                try:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                    num_pages = len(pdf_reader.pages)
                    self.test_results.append(f"✅ Valid PDF file with {num_pages} pages")
                    return True, pdf_content
                except Exception as pdf_error:
                    self.test_results.append(f"❌ Invalid PDF file: {str(pdf_error)}")
                    return False, None
                
        except Exception as e:
            self.test_results.append(f"❌ PDF Export error: {str(e)}")
            return False, None
            
    async def analyze_pdf_structure(self, pdf_content):
        """Analyze the PDF file structure for zone-based pages and content"""
        try:
            self.test_results.append("\n🔍 ANALYZING PDF STRUCTURE:")
            
            # Load PDF file
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            num_pages = len(pdf_reader.pages)
            
            # Expected zones based on our test data
            expected_zones = ["SA01", "SA02", "WH01", "WH02"]
            self.test_results.append(f"✅ PDF has {num_pages} pages (expected: {len(expected_zones)} zones)")
            
            if num_pages != len(expected_zones):
                self.test_results.append(f"❌ Page count mismatch: expected {len(expected_zones)}, got {num_pages}")
                return False
            
            # Analyze each page
            pages_analysis_success = True
            for page_num in range(num_pages):
                if not await self.analyze_pdf_page(pdf_reader.pages[page_num], page_num + 1, expected_zones[page_num]):
                    pages_analysis_success = False
            
            return pages_analysis_success
            
        except Exception as e:
            self.test_results.append(f"❌ PDF analysis error: {str(e)}")
            return False
    
    async def analyze_pdf_page(self, page, page_num, expected_zone):
        """Analyze individual PDF page structure and content"""
        try:
            self.test_results.append(f"\n📋 ANALYZING PAGE {page_num} (Expected Zone: {expected_zone}):")
            
            # Extract text from page
            page_text = page.extract_text()
            
            # Check for Geant Hypermarket branding
            if "Geant Hypermarket" in page_text:
                self.test_results.append("✅ Company branding (Geant Hypermarket) found")
            else:
                self.test_results.append("❌ Company branding missing")
                return False
            
            # Check for zone number in header
            if f"Zone Number: {expected_zone}" in page_text:
                self.test_results.append(f"✅ Zone number header found: {expected_zone}")
            else:
                self.test_results.append(f"❌ Zone number header missing for {expected_zone}")
                return False
            
            # Check for total SKUs scanned header
            if "Total SKUs Scanned:" in page_text:
                self.test_results.append("✅ Total SKUs scanned header found")
            else:
                self.test_results.append("❌ Total SKUs scanned header missing")
                return False
            
            # Check for generation date header
            if "Generated:" in page_text:
                self.test_results.append("✅ Generation date header found")
            else:
                self.test_results.append("❌ Generation date header missing")
                return False
            
            # Check for table headers
            required_headers = ["Item Number", "Barcode", "Description", "Quantity Scanned"]
            headers_found = 0
            for header in required_headers:
                if header in page_text:
                    headers_found += 1
            
            if headers_found == len(required_headers):
                self.test_results.append("✅ All required table headers found")
            else:
                self.test_results.append(f"❌ Missing table headers: {headers_found}/{len(required_headers)} found")
                return False
            
            # Check for zone title
            if f"Zone {expected_zone} - Inventory Details" in page_text:
                self.test_results.append(f"✅ Zone title found: Zone {expected_zone} - Inventory Details")
            else:
                self.test_results.append(f"❌ Zone title missing for {expected_zone}")
                return False
            
            # Check for zone summary
            if f"Zone {expected_zone} Summary:" in page_text:
                self.test_results.append(f"✅ Zone summary found for {expected_zone}")
            else:
                self.test_results.append(f"❌ Zone summary missing for {expected_zone}")
                return False
            
            # Check for logo placeholder (🏢 emoji or similar)
            if "🏢" in page_text or "logo" in page_text.lower():
                self.test_results.append("✅ Logo placeholder found")
            else:
                self.test_results.append("⚠️ Logo placeholder not detected (may be image)")
            
            return True
            
        except Exception as e:
            self.test_results.append(f"❌ Page analysis error for page {page_num}: {str(e)}")
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
            
    async def test_error_handling_no_data(self):
        """Test PDF export behavior when no inventory scans exist"""
        try:
            self.test_results.append("\n🚫 TESTING ERROR HANDLING WITH NO DATA:")
            
            # First clear all scans
            await self.clear_existing_scans()
            
            # Try to export PDF with no data
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans/export-pdf",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 404:
                    error_data = await response.json()
                    if "No inventory scans found" in error_data.get("detail", ""):
                        self.test_results.append("✅ Proper 404 error when no inventory scans exist")
                        return True
                    else:
                        self.test_results.append(f"❌ Unexpected error message: {error_data}")
                        return False
                elif response.status == 200:
                    self.test_results.append("❌ PDF export should fail when no data exists")
                    return False
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Unexpected error status {response.status}: {error_text}")
                    return False
                
        except Exception as e:
            self.test_results.append(f"❌ Error handling test failed: {str(e)}")
            return False

    async def test_admin_access_control(self):
        """Test that PDF export requires admin authentication"""
        try:
            self.test_results.append("\n🔐 TESTING ADMIN ACCESS CONTROL:")
            
            # Test without authentication
            async with self.session.get(f"{BACKEND_URL}/inventory-scans/export-pdf") as response:
                if response.status == 403 or response.status == 401:
                    self.test_results.append("✅ PDF export properly requires authentication")
                else:
                    self.test_results.append(f"❌ PDF export should require authentication, got status: {response.status}")
                    return False
            
            # Test with valid admin credentials (already authenticated)
            async with self.session.get(
                f"{BACKEND_URL}/inventory-scans/export-pdf",
                headers=self.get_auth_headers()
            ) as response:
                if response.status in [200, 404]:  # 200 if data exists, 404 if no data
                    self.test_results.append("✅ Admin credentials allow PDF export access")
                    return True
                else:
                    error_text = await response.text()
                    self.test_results.append(f"❌ Admin access failed: {response.status} - {error_text}")
                    return False
                
        except Exception as e:
            self.test_results.append(f"❌ Access control test failed: {str(e)}")
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
            
    async def test_same_item_different_zones_pdf(self, pdf_content):
        """Test that same item scanned in different zones appears in respective PDF pages"""
        try:
            self.test_results.append("\n🔄 TESTING SAME ITEM IN DIFFERENT ZONES (PDF):")
            
            # Apple Juice Box 1L (3222471081716) should appear in SA01 and WH01 pages
            # Mountain Water (3222471075722) should appear in SA01 and WH01 pages
            # Lemonade (3222471052747) should appear in SA01 and WH02 pages
            
            test_cases = [
                ("3222471081716", [0, 2], "Apple Juice Box 1L"),  # Pages 1 (SA01) and 3 (WH01)
                ("3222471075722", [0, 2], "Mountain Water 6X50Cl"),  # Pages 1 (SA01) and 3 (WH01)
                ("3222471052747", [0, 3], "Lemonade 150Cl")  # Pages 1 (SA01) and 4 (WH02)
            ]
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            
            for barcode, expected_page_indices, product_name in test_cases:
                pages_found = []
                for page_idx in expected_page_indices:
                    if page_idx < len(pdf_reader.pages):
                        page_text = pdf_reader.pages[page_idx].extract_text()
                        if barcode in page_text:
                            pages_found.append(page_idx + 1)  # Convert to 1-based page numbers
                            self.test_results.append(f"✅ {product_name} ({barcode}) found on page {page_idx + 1}")
                        else:
                            self.test_results.append(f"❌ {product_name} ({barcode}) NOT found on page {page_idx + 1}")
                
                if len(pages_found) == len(expected_page_indices):
                    self.test_results.append(f"✅ {product_name} correctly appears on all expected pages")
                else:
                    self.test_results.append(f"❌ {product_name} missing from some pages")
                    return False
            
            return True
                
        except Exception as e:
            self.test_results.append(f"❌ Cross-zone PDF verification error: {str(e)}")
            return False
            
    async def run_comprehensive_test(self):
        """Run comprehensive test of Inventory Scanning PDF Export"""
        print("🚀 STARTING INVENTORY SCANNING PDF EXPORT TESTING")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Step 1: Authentication
            if not await self.authenticate():
                return False
            
            # Step 2: Test admin access control
            if not await self.test_admin_access_control():
                return False
                
            # Step 3: Test error handling with no data
            if not await self.test_error_handling_no_data():
                return False
                
            # Step 4: Setup multi-zone test data
            if not await self.setup_multi_zone_data():
                return False
                
            # Step 5: Test PDF export endpoint and get PDF content
            pdf_success, pdf_content = await self.test_pdf_export_endpoint()
            if not pdf_success:
                return False
                
            # Step 6: Analyze PDF structure and content
            if not await self.analyze_pdf_structure(pdf_content):
                return False
                
            # Step 7: Verify data integrity
            if not await self.verify_data_integrity():
                return False
                
            # Step 8: Test same item in different zones (PDF verification)
            if not await self.test_same_item_different_zones_pdf(pdf_content):
                return False
                
            self.test_results.append("\n🎉 ALL PDF EXPORT TESTS COMPLETED SUCCESSFULLY!")
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