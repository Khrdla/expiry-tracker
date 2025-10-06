#!/usr/bin/env python3
"""
Detailed PDF Test - Extract and analyze actual PDF text content
"""

import requests
import json
from datetime import datetime
import re

# Configuration
BACKEND_URL = "https://geant-scanner.preview.emergentagent.com/api"
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
    """Create test return form with exact SAR values"""
    return_form_data = {
        "reference_number": f"RTN-SAR-TEST-{int(datetime.now().timestamp())}",
        "product_code": "SAR-369-TEST",
        "product_name": "SAR Currency Test Product",
        "barcode": "3222471081716",
        "quantity": 98.5,
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "GEANT Test Supplier",
        "reason_for_return": "Testing SAR to USD conversion in PDF",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "section_manager_name": "Imad Qejji",
        "notes": "Test: 98.5 × 3.75 = 369.375 SAR should convert to ~$98.50 USD",
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

def extract_pdf_text(pdf_content):
    """Extract readable text from PDF content"""
    try:
        # Try to extract text using simple pattern matching
        text_content = pdf_content.decode('utf-8', errors='ignore')
        
        # Look for text between parentheses (common in PDF text encoding)
        text_patterns = re.findall(r'\((.*?)\)', text_content)
        
        # Also look for direct text
        readable_text = ''.join(c for c in text_content if c.isprintable())
        
        return text_patterns, readable_text
    except Exception as e:
        return [], str(e)

def analyze_pdf_content(session, return_id):
    """Download and analyze PDF content in detail"""
    response = session.get(f"{BACKEND_URL}/export/return-form/{return_id}?format=pdf")
    
    if response.status_code == 200:
        pdf_content = response.content
        
        print(f"📄 Detailed PDF Analysis")
        print(f"Size: {len(pdf_content)} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        
        # Extract text patterns
        text_patterns, readable_text = extract_pdf_text(pdf_content)
        
        print(f"\n🔍 Text Patterns Found ({len(text_patterns)}):")
        for i, pattern in enumerate(text_patterns[:20]):  # Show first 20
            if pattern.strip():
                print(f"  {i+1}: '{pattern}'")
        
        # Search for specific terms
        search_terms = {
            'GEANT': ['GEANT', 'Geant', 'geant'],
            'HYPERMARKET': ['HYPERMARKET', 'Hypermarket', 'hypermarket'],
            'SAR Currency': ['SAR', 'sar'],
            'USD Currency': ['USD', 'usd', '$'],
            'Amount 369': ['369', '369.3', '369.37', '369.375'],
            'Amount 98': ['98.5', '98.50', '98.51', '$98'],
            'Supervisor': ['Mahmoud', 'Badr', 'mahmoud', 'badr'],
            'Exchange Rate': ['0.267', '0.2667', '3.75'],
            'Form Sections': ['FORM DETAILS', 'PRODUCT INFORMATION', 'RETURN VALUE', 'APPROVALS']
        }
        
        print(f"\n🎯 Search Results:")
        for category, terms in search_terms.items():
            found_terms = []
            for term in terms:
                # Search in both text patterns and readable content
                pattern_matches = [p for p in text_patterns if term.lower() in p.lower()]
                content_matches = term.lower() in readable_text.lower()
                
                if pattern_matches or content_matches:
                    found_terms.append(f"{term} ({'patterns' if pattern_matches else 'content'})")
            
            status = "✅" if found_terms else "❌"
            print(f"  {status} {category}: {found_terms if found_terms else 'Not found'}")
        
        # Look for currency calculation
        print(f"\n💰 Currency Calculation Analysis:")
        
        # Search for numbers that might be currency values
        number_patterns = re.findall(r'\b\d+\.?\d*\b', readable_text)
        relevant_numbers = [n for n in number_patterns if float(n) in [98.5, 3.75, 369.375, 369.37, 369.36, 98.50, 98.51, 0.267, 0.2667]]
        
        print(f"  Relevant numbers found: {relevant_numbers}")
        
        # Check for currency symbols and codes
        currency_indicators = []
        if '$' in readable_text:
            currency_indicators.append('Dollar sign ($)')
        if 'SAR' in readable_text:
            currency_indicators.append('SAR code')
        if 'USD' in readable_text:
            currency_indicators.append('USD code')
        
        print(f"  Currency indicators: {currency_indicators}")
        
        # Show a sample of readable content around currency terms
        print(f"\n📝 Content Sample (around currency terms):")
        for term in ['SAR', 'USD', '$', '369', '98.5']:
            if term in readable_text:
                index = readable_text.find(term)
                start = max(0, index - 50)
                end = min(len(readable_text), index + 50)
                sample = readable_text[start:end].replace('\n', ' ').replace('\r', ' ')
                print(f"  Around '{term}': ...{sample}...")
                break
        
        return True
    else:
        print(f"❌ Failed to get PDF: {response.status_code} - {response.text}")
        return False

def main():
    print("🔍 Detailed PDF Content Analysis")
    print("=" * 60)
    
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
    
    # Analyze PDF content
    if analyze_pdf_content(session, return_id):
        print("✅ Detailed PDF analysis completed")
    else:
        print("❌ PDF analysis failed")

if __name__ == "__main__":
    main()