#!/usr/bin/env python3
"""
PDF Content Analysis for Multi-Item FOC Return Forms
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://geant-inventory-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "imadqejji"
ADMIN_PASSWORD = "066380531I"

def authenticate():
    """Authenticate and get token"""
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", 
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def create_test_form(session):
    """Create a test multi-item FOC form"""
    return_form_data = {
        "reference_number": f"RTN-PDF-ANALYSIS-{int(time.time())}",
        "supplier": "ExtenC",
        "items": [
            {
                "product_name": "Apple Juice Box 1L",
                "barcode": "3222471081716",
                "quantity": 50,
                "purchase_price": 3.75,
                "purchase_currency": "SAR",
                "is_foc": False,
                "foc_reason": None,
                "supplier": "ExtenC",
                "total_value": 187.50
            },
            {
                "product_name": "Orange Juice Box 1L", 
                "barcode": "3222471052747",
                "quantity": 25,
                "purchase_price": 0.0,
                "purchase_currency": "SAR",
                "is_foc": True,
                "foc_reason": "Promotional sample",
                "supplier": "ExtenC",
                "total_value": 0.0
            }
        ],
        "summary": {
            "total_items": 2,
            "normal_items": 1,
            "foc_items": 1,
            "total_quantity": 75,
            "total_value": 187.50,
            "supplier": "ExtenC"
        },
        "reason_for_return": "PDF content analysis test",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "section_manager_name": "Imad Qejji",
        "supervisor_approved": True,
        "supervisor_signature": "mahmoud_badr_signature",
        "supervisor_timestamp": datetime.now().isoformat(),
        "section_manager_approved": True,
        "section_manager_signature": "imad_qejji_signature",
        "section_manager_timestamp": datetime.now().isoformat(),
        "notes": "PDF content analysis test form"
    }
    
    response = session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("id")
    return None

def analyze_pdf_content(session, form_id):
    """Download and analyze PDF content"""
    response = session.get(f"{BACKEND_URL}/export/return-form/{form_id}/pdf")
    
    if response.status_code != 200:
        print(f"❌ PDF download failed: {response.status_code}")
        return
    
    pdf_content = response.content
    pdf_size = len(pdf_content)
    
    print(f"📄 PDF Analysis Results:")
    print(f"   Size: {pdf_size} bytes")
    print(f"   Valid PDF: {pdf_content.startswith(b'%PDF')}")
    
    # Try to extract text using PyPDF2 if available
    try:
        import PyPDF2
        from io import BytesIO
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        text_content = ""
        
        for page in pdf_reader.pages:
            text_content += page.extract_text()
        
        print(f"   Extracted text length: {len(text_content)} characters")
        
        # Check for specific content
        content_checks = {
            "Apple Juice": "Apple Juice" in text_content,
            "Orange Juice": "Orange Juice" in text_content,
            "GEANT": "GEANT" in text_content or "Geant" in text_content,
            "FOC": "FOC" in text_content,
            "Free": "Free" in text_content,
            "Promotional": "Promotional" in text_content,
            "ExtenC": "ExtenC" in text_content,
            "Mahmoud Badr": "Mahmoud Badr" in text_content,
            "187.50": "187.50" in text_content,
            "SAR": "SAR" in text_content
        }
        
        print(f"   Content Analysis:")
        for item, found in content_checks.items():
            status = "✅" if found else "❌"
            print(f"     {status} {item}: {found}")
        
        # Show first 500 characters of extracted text
        print(f"\n📝 First 500 characters of extracted text:")
        print(f"   {text_content[:500]}...")
        
    except ImportError:
        print("   PyPDF2 not available for text extraction")
        
        # Basic binary content analysis
        content_checks = {
            "Apple Juice": b"Apple Juice" in pdf_content or b"Apple" in pdf_content,
            "Orange Juice": b"Orange Juice" in pdf_content or b"Orange" in pdf_content,
            "GEANT": b"GEANT" in pdf_content or b"Geant" in pdf_content,
            "FOC": b"FOC" in pdf_content,
            "ExtenC": b"ExtenC" in pdf_content,
            "Mahmoud": b"Mahmoud" in pdf_content,
            "SAR": b"SAR" in pdf_content
        }
        
        print(f"   Binary Content Analysis:")
        for item, found in content_checks.items():
            status = "✅" if found else "❌"
            print(f"     {status} {item}: {found}")

def main():
    print("🔍 PDF CONTENT ANALYSIS FOR MULTI-ITEM FOC FORMS")
    print("=" * 60)
    
    # Authenticate
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Create test form
    form_id = create_test_form(session)
    if not form_id:
        print("❌ Failed to create test form")
        return
    
    print(f"✅ Test form created: {form_id}")
    
    # Analyze PDF content
    analyze_pdf_content(session, form_id)
    
    print("\n" + "=" * 60)
    print("🏁 PDF CONTENT ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()