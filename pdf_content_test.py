#!/usr/bin/env python3
"""
PDF Content Detailed Analysis
Extract and analyze the PDF content to verify all requirements
"""

import requests
import PyPDF2
import io
import time

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
    """Create a test return form"""
    return_form_data = {
        "reference_number": f"RTN-{int(time.time())}-PDF-TEST",
        "product_code": "3222471081716",
        "product_name": "Apple Juice Box 1L",
        "barcode": "3222471081716",
        "quantity": 98.5,
        "purchase_price": 3.75,
        "purchase_currency": "SAR",
        "supplier": "ExtenC",
        "reason_for_return": "Quality issue - damaged packaging",
        "selected_supervisor": "Mahmoud Badr",
        "prepared_by_supervisor": "Mahmoud Badr",
        "department_head": "Idder EL-Fermi",
        "general_manager": "Ahmed Massouni",
        "section_manager_name": "Imad Qejji",
        "supervisor_approved": True,
        "supervisor_signature": "Mahmoud_Badr_signature",
        "supervisor_timestamp": "2024-01-15T10:30:00",
        "section_manager_approved": True,
        "section_manager_signature": "Imad_Qejji_signature", 
        "section_manager_timestamp": "2024-01-15T11:00:00"
    }
    
    response = session.post(f"{BACKEND_URL}/return-forms", json=return_form_data)
    if response.status_code == 200:
        return response.json().get("id")
    return None

def analyze_pdf_content(session, form_id):
    """Download and analyze PDF content"""
    response = session.get(f"{BACKEND_URL}/export/return-form/{form_id}?format=pdf")
    
    if response.status_code != 200:
        print(f"❌ Failed to download PDF: {response.status_code}")
        return
    
    pdf_content = response.content
    print(f"✅ PDF Downloaded: {len(pdf_content)} bytes")
    
    # Extract text from PDF
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        print(f"📄 PDF Pages: {len(pdf_reader.pages)}")
        
        full_text = ""
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            full_text += page_text
            print(f"\n📄 PAGE {i+1} CONTENT:")
            print("-" * 50)
            print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
        
        print("\n" + "="*80)
        print("🔍 DETAILED CONTENT ANALYSIS")
        print("="*80)
        
        # Check for specific requirements
        requirements = {
            "Department Head (Idder EL-Fermi)": "Idder EL-Fermi" in full_text,
            "General Manager (Ahmed Massouni)": "Ahmed Massouni" in full_text,
            "Finance Department": "Finance Department" in full_text or "Finance" in full_text,
            "Supervisor (Mahmoud Badr)": "Mahmoud Badr" in full_text,
            "GEANT Branding": "GEANT" in full_text or "Geant" in full_text,
            "Product Name (Apple Juice Box 1L)": "Apple Juice Box 1L" in full_text,
            "SAR Currency": "SAR" in full_text,
            "Quantity (98.5)": "98.5" in full_text,
            "Price (3.75)": "3.75" in full_text,
            "Signature Sections": "Signature" in full_text or "signature" in full_text,
            "Manual Signature Layout": any(word in full_text for word in ["Department Head", "General Manager", "Finance"])
        }
        
        print("📋 REQUIREMENTS CHECK:")
        for req, status in requirements.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {req}")
        
        passed = sum(requirements.values())
        total = len(requirements)
        print(f"\n📊 OVERALL SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
        
        # Save PDF for manual inspection
        with open("/app/test_return_form.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"\n💾 PDF saved as /app/test_return_form.pdf for manual inspection")
        
    except Exception as e:
        print(f"❌ Error analyzing PDF: {str(e)}")

def main():
    print("🔍 PDF CONTENT DETAILED ANALYSIS")
    print("="*50)
    
    # Authenticate
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Create test return form
    form_id = create_test_return_form(session)
    if not form_id:
        print("❌ Failed to create return form")
        return
    
    print(f"✅ Return form created: {form_id}")
    
    # Analyze PDF
    analyze_pdf_content(session, form_id)

if __name__ == "__main__":
    main()