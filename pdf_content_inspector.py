#!/usr/bin/env python3
"""
PDF Content Inspector - Examine actual PDF content to understand what's missing
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://inventory-master-78.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def authenticate():
    """Get authentication token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def create_test_return_form(session):
    """Create test return form"""
    return_form_data = {
        "reference_number": f"RTN-INSPECT-{int(datetime.now().timestamp())}",
        "product_code": "SAR-INSPECT-001",
        "product_name": "Test Product for Content Inspection",
        "barcode": "3222471081716",
        "quantity": 98.5,
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "Test Supplier for GEANT",
        "reason_for_return": "Content inspection test",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "section_manager_name": "Imad Qejji",
        "notes": "Test return form for content inspection - Total: 369.375 SAR",
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
        return data.get("id")
    return None

def inspect_pdf_content(session, return_id):
    """Download and inspect PDF content"""
    response = session.get(f"{BACKEND_URL}/export/return-form/{return_id}?format=pdf")
    
    if response.status_code == 200:
        pdf_content = response.content
        
        print(f"📄 PDF Content Analysis")
        print(f"Size: {len(pdf_content)} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        
        # Convert to string for text analysis (ignore encoding errors)
        try:
            text_content = pdf_content.decode('utf-8', errors='ignore')
        except:
            text_content = str(pdf_content)
        
        print(f"\n🔍 Content Analysis:")
        
        # Check for GEANT branding
        geant_variations = ['GEANT', 'Geant', 'geant', 'HYPERMARKET', 'Hypermarket', 'hypermarket']
        found_branding = []
        for brand in geant_variations:
            if brand.encode() in pdf_content:
                found_branding.append(brand)
        print(f"GEANT Branding found: {found_branding}")
        
        # Check for currency information
        currency_terms = ['SAR', 'USD', '$', 'sar', 'usd']
        found_currencies = []
        for curr in currency_terms:
            if curr.encode() in pdf_content:
                found_currencies.append(curr)
        print(f"Currency terms found: {found_currencies}")
        
        # Check for amounts
        amounts = ['369', '98.5', '98.50', '98.51', '3.75', '0.2667']
        found_amounts = []
        for amount in amounts:
            if amount.encode() in pdf_content:
                found_amounts.append(amount)
        print(f"Amount values found: {found_amounts}")
        
        # Check for supervisor name
        supervisor_terms = ['Mahmoud', 'Badr', 'mahmoud', 'badr']
        found_supervisor = []
        for term in supervisor_terms:
            if term.encode() in pdf_content:
                found_supervisor.append(term)
        print(f"Supervisor terms found: {found_supervisor}")
        
        # Check for PDF structure
        pdf_terms = ['ReportLab', 'reportlab', '/Producer', '/Creator', 'Table', 'Form Details', 'Product Information']
        found_structure = []
        for term in pdf_terms:
            if term.encode() in pdf_content:
                found_structure.append(term)
        print(f"PDF structure terms found: {found_structure}")
        
        # Show first 500 characters of readable content
        readable_chars = ''.join(c for c in text_content if c.isprintable())[:500]
        print(f"\n📝 First 500 readable characters:")
        print(readable_chars)
        
        # Show PDF header
        print(f"\n📋 PDF Header (first 100 bytes):")
        print(pdf_content[:100])
        
        return True
    else:
        print(f"❌ Failed to get PDF: {response.status_code} - {response.text}")
        return False

def main():
    print("🔍 PDF Content Inspector")
    print("=" * 50)
    
    # Authenticate
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated successfully")
    
    # Create test return form
    return_id = create_test_return_form(session)
    if not return_id:
        print("❌ Failed to create test return form")
        return
    
    print(f"✅ Created test return form: {return_id}")
    
    # Inspect PDF content
    if inspect_pdf_content(session, return_id):
        print("✅ PDF content inspection completed")
    else:
        print("❌ PDF content inspection failed")

if __name__ == "__main__":
    main()