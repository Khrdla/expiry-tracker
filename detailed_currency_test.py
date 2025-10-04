#!/usr/bin/env python3
"""
Detailed Currency Display Verification
Extract and analyze the exact PDF content to verify currency simplification
"""

import requests
import json
import PyPDF2
import io
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def authenticate():
    """Authenticate and return session with token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print(f"✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def create_test_return_form(session):
    """Create a test return form with exact specifications"""
    return_form_data = {
        "reference_number": f"RTN-CURRENCY-TEST-{int(datetime.now().timestamp())}",
        "product_code": "3222471081716",
        "product_name": "Apple Juice Box 1L",
        "barcode": "3222471081716",
        "quantity": 98.5,
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "ExtenC",
        "reason_for_return": "Currency display simplification test",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "section_manager_name": "Imad Qejji",
        "notes": "Test: 98.5 x 3.75 SAR = 369.375 SAR",
        "supervisor_approved": True,
        "supervisor_signature": "Mahmoud_Badr_signature",
        "supervisor_timestamp": datetime.now().isoformat(),
        "section_manager_approved": True,
        "section_manager_signature": "Imad_Qejji_signature", 
        "section_manager_timestamp": datetime.now().isoformat()
    }
    
    response = session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
    
    if response.status_code == 200:
        data = response.json()
        form_id = data.get("id")
        print(f"✅ Return form created: {form_id}")
        print(f"   Product: Apple Juice Box 1L")
        print(f"   Quantity: 98.5")
        print(f"   Price: 3.75 SAR")
        print(f"   Expected Total: 369.375 SAR")
        return form_id
    else:
        print(f"❌ Return form creation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def get_pdf_and_analyze(session, form_id):
    """Get PDF and analyze currency display"""
    response = session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
    
    if response.status_code == 200:
        pdf_content = response.content
        pdf_size = len(pdf_content)
        print(f"✅ PDF generated successfully: {pdf_size} bytes")
        
        # Extract text from PDF
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pdf_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                pdf_text += page_text
                print(f"   Page {page_num + 1} text length: {len(page_text)} chars")
            
            print(f"   Total PDF text length: {len(pdf_text)} chars")
            
            # Analyze currency content
            analyze_currency_content(pdf_text)
            
            return True
            
        except Exception as e:
            print(f"❌ PDF text extraction failed: {str(e)}")
            return False
    else:
        print(f"❌ PDF generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def analyze_currency_content(pdf_text):
    """Analyze the PDF text for currency-related content"""
    print(f"\n📋 CURRENCY CONTENT ANALYSIS:")
    print("=" * 50)
    
    # Split into lines for analysis
    lines = pdf_text.split('\n')
    
    # Find currency-related lines
    currency_lines = []
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if any(keyword in line_clean.lower() for keyword in ['sar', 'usd', 'total', 'value', 'exchange', 'rate', 'equivalent']):
            currency_lines.append(f"Line {i+1}: {line_clean}")
    
    print(f"Currency-related lines found ({len(currency_lines)}):")
    for line in currency_lines:
        print(f"   {line}")
    
    # Check for specific requirements
    print(f"\n🎯 REQUIREMENT VERIFICATION:")
    
    # Should be present
    has_sar_currency = any('sar' in line.lower() for line in lines)
    has_total_value = any('total' in line.lower() and 'value' in line.lower() for line in lines)
    has_369_sar = any('369' in line and 'sar' in line.lower() for line in lines)
    
    # Should NOT be present
    has_usd_equivalent = any('usd equivalent' in line.lower() for line in lines)
    has_exchange_rate = any('exchange rate' in line.lower() for line in lines)
    has_usd_conversion = any('$98.51' in line or '$369.36' in line for line in lines)
    
    print(f"✅ SAR Currency Present: {has_sar_currency}")
    print(f"✅ Total Value Present: {has_total_value}")
    print(f"✅ 369 SAR Present: {has_369_sar}")
    print(f"❌ USD Equivalent Present: {has_usd_equivalent} (should be False)")
    print(f"❌ Exchange Rate Present: {has_exchange_rate} (should be False)")
    print(f"❌ USD Conversion Present: {has_usd_conversion} (should be False)")
    
    # Overall success
    currency_simplified = has_sar_currency and not has_usd_equivalent and not has_exchange_rate and not has_usd_conversion
    print(f"\n🏆 CURRENCY SIMPLIFICATION SUCCESS: {currency_simplified}")
    
    # Show specific currency values found
    print(f"\n💰 CURRENCY VALUES FOUND:")
    for line in lines:
        if any(keyword in line.lower() for keyword in ['369', 'sar', 'total']):
            line_clean = line.strip()
            if line_clean:
                print(f"   {line_clean}")
    
    return currency_simplified

def main():
    print("🔍 DETAILED CURRENCY DISPLAY VERIFICATION")
    print("=" * 60)
    print(f"Testing Return Form PDF Currency Simplification")
    print(f"Expected: Only supplier currency (SAR), no USD conversion")
    print("=" * 60)
    
    # 1. Authenticate
    session = authenticate()
    if not session:
        return
    
    # 2. Create test return form
    form_id = create_test_return_form(session)
    if not form_id:
        return
    
    # 3. Generate PDF and analyze
    success = get_pdf_and_analyze(session, form_id)
    
    print("\n" + "=" * 60)
    if success:
        print("🏁 DETAILED VERIFICATION COMPLETE")
    else:
        print("❌ VERIFICATION FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()