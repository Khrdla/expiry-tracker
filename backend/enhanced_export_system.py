"""
Enhanced Export System for Geant Hypermarket Inventory Management

This module provides comprehensive export functionality with:
1. Clean structured reports (Excel & PDF) 
2. Proper currency handling with USD conversion for waste reports
3. Company branding and theming
4. No merged/overlapping/missing cells
5. Professional formatting
"""

import io
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

# Excel libraries
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.drawing import image
from openpyxl.utils import get_column_letter
from openpyxl.chart import PieChart, BarChart, Reference

# PDF libraries  
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class CurrencyConverter:
    """Handle currency conversions with exchange rates"""
    
    def __init__(self):
        # Default exchange rates (YER/SAR/EUR to USD)
        # These should ideally come from master data or external API
        self.exchange_rates = {
            'YER': 0.004,   # 1 YER = 0.004 USD (250 YER = 1 USD)
            'SAR': 0.267,   # 1 SAR = 0.267 USD (3.75 SAR = 1 USD)  
            'EUR': 1.10,    # 1 EUR = 1.10 USD
            'USD': 1.0      # 1 USD = 1 USD
        }
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """Convert amount from source currency to USD"""
        if from_currency not in self.exchange_rates:
            raise ValueError(f"Unsupported currency: {from_currency}")
        
        return round(amount * self.exchange_rates[from_currency], 2)
    
    def get_exchange_rate(self, from_currency: str) -> float:
        """Get exchange rate from source currency to USD"""
        return self.exchange_rates.get(from_currency, 1.0)

class CompanyBranding:
    """Centralized company branding configuration"""
    
    @staticmethod
    def get_branding():
        return {
            'company_name': 'GEANT HYPERMARKET',
            'company_subtitle': 'Inventory Management System',
            'logo_path': '/app/backend/geant-logo.jpeg',
            'primary_color': '#1B4332',      # Dark green
            'secondary_color': '#2D6A4F',    # Medium green
            'accent_color': '#40916C',       # Light green
            'text_color': '#081C15',         # Dark text
            'background_color': '#F8F9FA',   # Light background
            'excel_header_color': '1B4332',  # Excel hex without #
            'excel_accent_color': '40916C',
            'pdf_primary_color': (0.106, 0.263, 0.196),    # RGB for ReportLab
            'pdf_secondary_color': (0.176, 0.416, 0.310),  # RGB for ReportLab
            'pdf_accent_color': (0.251, 0.569, 0.424)      # RGB for ReportLab
        }

class EnhancedExcelExporter:
    """Enhanced Excel export with proper formatting and branding"""
    
    def __init__(self):
        self.branding = CompanyBranding.get_branding()
        self.converter = CurrencyConverter()
    
    def create_styled_workbook(self, title: str) -> tuple:
        """Create a workbook with company styling"""
        wb = Workbook()
        ws = wb.active
        ws.title = title
        
        # Define company styles
        header_style = NamedStyle(name="header")
        header_style.font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        header_style.fill = PatternFill(start_color=self.branding['excel_header_color'], 
                                       end_color=self.branding['excel_header_color'], 
                                       fill_type='solid')
        header_style.alignment = Alignment(horizontal='center', vertical='center')
        header_style.border = self._get_border()
        
        subheader_style = NamedStyle(name="subheader") 
        subheader_style.font = Font(name='Arial', size=11, bold=True, color=self.branding['excel_header_color'])
        subheader_style.alignment = Alignment(horizontal='left', vertical='center')
        subheader_style.border = self._get_border()
        
        currency_style = NamedStyle(name="currency")
        currency_style.font = Font(name='Arial', size=10, bold=False)
        currency_style.alignment = Alignment(horizontal='right', vertical='center')
        currency_style.border = self._get_border()
        currency_style.number_format = '#,##0.00'
        
        # Add styles to workbook
        try:
            wb.add_named_style(header_style)
            wb.add_named_style(subheader_style)
            wb.add_named_style(currency_style)
        except ValueError:
            pass  # Style already exists
        
        return wb, ws
    
    def _get_border(self):
        """Get consistent border style"""
        return Border(
            left=Side(border_style='thin'),
            right=Side(border_style='thin'),
            top=Side(border_style='thin'),
            bottom=Side(border_style='thin')
        )
    
    def add_company_header(self, ws, start_row: int = 1) -> int:
        """Add company header with logo and title"""
        current_row = start_row
        
        # Add logo if exists
        logo_added = self._add_logo(ws, current_row, 1)
        if logo_added:
            # Company name beside logo
            ws.merge_cells(f'B{current_row}:F{current_row}')
            ws[f'B{current_row}'] = self.branding['company_name']
            ws[f'B{current_row}'].font = Font(name='Arial', size=16, bold=True, color=self.branding['excel_header_color'])
            ws[f'B{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
            current_row += 1
            
            # Subtitle
            ws.merge_cells(f'B{current_row}:F{current_row}')
            ws[f'B{current_row}'] = self.branding['company_subtitle']
            ws[f'B{current_row}'].font = Font(name='Arial', size=11, italic=True)
            ws[f'B{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
            current_row += 2
        else:
            # Fallback header without logo
            ws.merge_cells(f'A{current_row}:F{current_row}')
            ws[f'A{current_row}'] = self.branding['company_name']
            ws[f'A{current_row}'].style = "header"
            current_row += 1
        
        return current_row
    
    def _add_logo(self, ws, row: int, col: int) -> bool:
        """Add company logo to worksheet"""
        try:
            if os.path.exists(self.branding['logo_path']):
                logo = image.Image(self.branding['logo_path'])
                logo.width = 60
                logo.height = 60
                
                cell = ws.cell(row=row, column=col)
                ws.add_image(logo, cell.coordinate)
                
                # Make logo row taller
                ws.row_dimensions[row].height = 45
                return True
        except Exception as e:
            print(f"Could not add logo: {e}")
        
        return False
    
    def add_report_metadata(self, ws, start_row: int, report_type: str, period: str, 
                           filters: Dict = None) -> int:
        """Add report metadata section"""
        current_row = start_row
        
        # Report title
        ws.merge_cells(f'A{current_row}:F{current_row}')
        ws[f'A{current_row}'] = f"{report_type.upper()} REPORT"
        ws[f'A{current_row}'].style = "header"
        current_row += 2
        
        # Report details
        ws[f'A{current_row}'] = "Report Period:"
        ws[f'B{current_row}'] = period.title()
        ws[f'A{current_row}'].style = "subheader"
        current_row += 1
        
        ws[f'A{current_row}'] = "Generated At:"
        ws[f'B{current_row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ws[f'A{current_row}'].style = "subheader"
        current_row += 1
        
        # Add filters if provided
        if filters:
            for key, value in filters.items():
                if value and value != 'all':
                    ws[f'A{current_row}'] = f"{key.replace('_', ' ').title()}:"
                    ws[f'B{current_row}'] = value
                    ws[f'A{current_row}'].style = "subheader"
                    current_row += 1
        
        return current_row + 1
    
    def create_data_table(self, ws, start_row: int, headers: List[str], 
                         data: List[List[Any]], title: str = None) -> int:
        """Create a clean data table with headers"""
        current_row = start_row
        
        # Optional table title
        if title:
            ws[f'A{current_row}'] = title
            ws[f'A{current_row}'].style = "subheader"
            current_row += 2
        
        # Headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.style = "header"
        
        current_row += 1
        
        # Data rows
        for row_data in data:
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=current_row, column=col_num)
                cell.value = value
                cell.border = self._get_border()
                
                # Apply currency formatting for numeric values
                if isinstance(value, (int, float)) and col_num > 1:
                    cell.style = "currency"
            
            current_row += 1
        
        return current_row + 1
    
    def auto_adjust_columns(self, ws):
        """Auto-adjust column widths for better readability"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            
            # Set width with reasonable limits
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = max(adjusted_width, 10)

class EnhancedWasteReportExporter(EnhancedExcelExporter):
    """Specialized exporter for waste reports with USD conversion"""
    
    def generate_excel(self, report_data: Dict, period: str) -> bytes:
        """Generate enhanced waste report Excel with USD conversion"""
        wb, ws = self.create_styled_workbook(f"Waste Report - {period.title()}")
        
        # Add company header
        current_row = self.add_company_header(ws)
        
        # Add report metadata
        filters = {
            'department': report_data.get('department'),
            'section': report_data.get('section')
        }
        current_row = self.add_report_metadata(ws, current_row, "WASTE", period, filters)
        
        # Currency totals with USD conversion
        current_row = self._add_currency_summary(ws, current_row, report_data['currency_totals'])
        
        # Waste entries detail (if available)
        if 'entries' in report_data and report_data['entries']:
            current_row = self._add_waste_entries_table(ws, current_row, report_data['entries'])
        
        # Summary statistics
        current_row = self._add_summary_section(ws, current_row, report_data)
        
        # Auto-adjust columns
        self.auto_adjust_columns(ws)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def _add_currency_summary(self, ws, start_row: int, currency_totals: Dict) -> int:
        """Add currency summary with USD conversion"""
        current_row = start_row
        
        # Prepare data with USD conversion
        headers = ["Currency", "Original Amount", "USD Equivalent", "Exchange Rate"]
        data = []
        total_usd = 0
        
        for currency, amount in currency_totals.items():
            if amount > 0:
                usd_amount = self.converter.convert_to_usd(amount, currency)
                exchange_rate = self.converter.get_exchange_rate(currency)
                total_usd += usd_amount
                
                data.append([
                    currency,
                    f"{amount:,.2f} {currency}",
                    f"{usd_amount:,.2f} USD",
                    f"{exchange_rate:.4f}"
                ])
        
        # Add total USD row
        if len(data) > 1:
            data.append(["TOTAL", "", f"{total_usd:,.2f} USD", ""])
        
        current_row = self.create_data_table(ws, current_row, headers, data, 
                                           "WASTE VALUE BY CURRENCY (WITH USD CONVERSION)")
        
        return current_row
    
    def _add_waste_entries_table(self, ws, start_row: int, entries: List[Dict]) -> int:
        """Add detailed waste entries table"""
        headers = [
            "Product Name", "Department", "Quantity", 
            "Original Value", "USD Value", "Reason", "Date"
        ]
        
        data = []
        for entry in entries:
            original_value = entry.get('waste_value', 0)
            currency = entry.get('currency', 'USD')
            usd_value = self.converter.convert_to_usd(original_value, currency)
            
            data.append([
                entry.get('product_name', 'Unknown'),
                entry.get('department', ''),
                entry.get('quantity_wasted', 0),
                f"{original_value:,.2f} {currency}",
                f"{usd_value:,.2f} USD",
                entry.get('waste_reason', ''),
                entry.get('created_at', '')[:10] if entry.get('created_at') else ''
            ])
        
        return self.create_data_table(ws, start_row, headers, data, 
                                    "DETAILED WASTE ENTRIES")
    
    def _add_summary_section(self, ws, start_row: int, report_data: Dict) -> int:
        """Add summary statistics section"""
        current_row = start_row
        
        ws[f'A{current_row}'] = "REPORT SUMMARY"
        ws[f'A{current_row}'].style = "subheader"
        current_row += 2
        
        # Summary data
        summary_data = [
            ["Total Entries:", report_data.get('total_entries', 0)],
            ["Total Quantity Wasted:", report_data.get('total_quantity_wasted', 0)],
            ["Report Period:", report_data.get('period', 'Unknown')],
            ["Generated At:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        for label, value in summary_data:
            ws[f'A{current_row}'] = label
            ws[f'B{current_row}'] = value
            ws[f'A{current_row}'].style = "subheader"
            current_row += 1
        
        return current_row + 2

class EnhancedOtherReportsExporter(EnhancedExcelExporter):
    """Exporter for all other reports (Return, Expiry, Supplier) - Original currency only"""
    
    def generate_return_forms_excel(self, return_forms: List[Dict]) -> bytes:
        """Generate return forms report (original currency only)"""
        wb, ws = self.create_styled_workbook("Return Forms Report")
        
        # Add company header
        current_row = self.add_company_header(ws)
        
        # Report metadata
        current_row = self.add_report_metadata(ws, current_row, "RETURN FORMS", "All Periods")
        
        # Return forms table
        headers = [
            "Return ID", "Product Name", "Supplier", "Quantity", 
            "Value (Original Currency)", "Reason", "Status", "Date"
        ]
        
        data = []
        for form in return_forms:
            value = form.get('purchase_price', 0) * form.get('quantity', 0)
            currency = form.get('purchase_currency', 'USD')
            
            data.append([
                form.get('reference_number', ''),
                form.get('product_name', ''),
                form.get('supplier', ''),
                form.get('quantity', 0),
                f"{value:,.2f} {currency}",
                form.get('reason_for_return', ''),
                form.get('status', 'Pending'),
                form.get('created_at', '')[:10] if form.get('created_at') else ''
            ])
        
        current_row = self.create_data_table(ws, current_row, headers, data)
        
        # Auto-adjust columns
        self.auto_adjust_columns(ws)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def generate_expiry_tracker_excel(self, products: List[Dict]) -> bytes:
        """Generate expiry tracker report (original currency only)"""
        wb, ws = self.create_styled_workbook("Expiry Tracker Report")
        
        # Add company header
        current_row = self.add_company_header(ws)
        
        # Report metadata
        current_row = self.add_report_metadata(ws, current_row, "EXPIRY TRACKER", "Current")
        
        # Products table
        headers = [
            "Product Name", "Department", "Expiry Date", "Days Until Expiry",
            "Quantity", "Value (Original Currency)", "Status"
        ]
        
        data = []
        for product in products:
            value = product.get('purchase_price', 0) * product.get('quantity', 0)
            currency = product.get('purchase_currency', 'USD')
            
            # Calculate days until expiry
            days_until_expiry = "N/A"
            if product.get('expiry_date'):
                try:
                    expiry_date = datetime.fromisoformat(product['expiry_date'].replace('Z', '+00:00'))
                    days_until_expiry = (expiry_date - datetime.now(timezone.utc)).days
                except:
                    pass
            
            data.append([
                product.get('product_name', ''),
                product.get('department', ''),
                product.get('expiry_date', 'N/A'),
                days_until_expiry,
                product.get('quantity', 0),
                f"{value:,.2f} {currency}",
                product.get('status', 'Unknown')
            ])
        
        current_row = self.create_data_table(ws, current_row, headers, data)
        
        # Auto-adjust columns
        self.auto_adjust_columns(ws)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

# Export factory function
def get_exporter(report_type: str):
    """Factory function to get appropriate exporter"""
    if report_type.lower() == 'waste':
        return EnhancedWasteReportExporter()
    else:
        return EnhancedOtherReportsExporter()