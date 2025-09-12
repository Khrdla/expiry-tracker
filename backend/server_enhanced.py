from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import json
import pandas as pd
import uuid
from typing import List, Optional, Dict, Any
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import pytz

# Import enhanced models
from models import *

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Enhanced FastAPI app with comprehensive inventory management
app = FastAPI(
    title="Geant Hypermarket Inventory Management System",
    description="Comprehensive inventory management with per-department dashboards, role-based access, and automated alerts",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'inventory_db')]

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'geant-inventory-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Static files and uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Router
api_router = APIRouter(prefix="/api")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Department access control
def get_accessible_departments(user: User) -> List[Department]:
    if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        return [Department.FMG, Department.CGD, Department.OPSS]
    elif user.department:
        return [user.department]
    else:
        return []

async def calculate_product_status(product: dict) -> str:
    """Calculate product status based on quantity and expiry date"""
    if product['quantity'] <= 0:
        return ProductStatus.OUT_OF_STOCK.value
    elif product['quantity'] <= product.get('low_stock_threshold', 10):
        return ProductStatus.LOW_STOCK.value
    
    expiry_date = product.get('expiry_date')
    if expiry_date:
        now = datetime.utcnow()
        if expiry_date < now:
            return ProductStatus.EXPIRED.value
        
        # Get expiry threshold based on section
        settings = await db.email_settings.find_one() or {}
        threshold_days = settings.get('expiry_threshold_days', 7)
        if product.get('section') == Section.BEVERAGE:
            threshold_days = settings.get('beverage_expiry_threshold_days', 15)
        
        if expiry_date < now + timedelta(days=threshold_days):
            return ProductStatus.NEAR_EXPIRY.value
    
    return ProductStatus.IN_STOCK.value

# Authentication Endpoints
@api_router.post("/auth/register")
async def register_user(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    del user_dict['password']
    
    new_user = User(**user_dict)
    user_doc = new_user.dict()
    user_doc['hashed_password'] = hashed_password
    
    await db.users.insert_one(user_doc)
    return {"message": f"User {user.username} registered successfully. Awaiting admin approval."}

@api_router.post("/auth/login")
async def login(login_data: dict):
    username = login_data.get("username")
    password = login_data.get("password")
    
    user_doc = await db.users.find_one({"username": username})
    if not user_doc or not verify_password(password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if user_doc.get('approval_status') != 'approved':
        raise HTTPException(status_code=403, detail="Account pending approval")
    
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/init-admin")
async def init_admin():
    # Create or update first admin user
    first_user = await db.users.find_one()
    if first_user:
        await db.users.update_one(
            {"_id": first_user["_id"]},
            {"$set": {
                "is_admin": True,
                "role": "admin",
                "approval_status": "approved",
                "approved_by": "system",
                "approved_at": datetime.utcnow()
            }}
        )
        return {"message": f"{first_user['username']} has been granted admin privileges and approved"}
    else:
        raise HTTPException(status_code=404, detail="No users found to promote")

# Dashboard Endpoints
@api_router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    accessible_departments = get_accessible_departments(current_user)
    
    # Calculate KPIs for each accessible department
    kpis = []
    for dept in accessible_departments:
        # Get products for this department
        products = await db.products.find({"department": dept.value}).to_list(None)
        
        total_items = len(products)
        expired_items = 0
        near_expiry_items = 0
        out_of_stock_items = 0
        low_stock_items = 0
        total_stock_value = 0.0
        total_quantity = 0
        
        for product in products:
            status = await calculate_product_status(product)
            total_quantity += product.get('quantity', 0)
            total_stock_value += (product.get('quantity', 0) * product.get('purchase_price', 0))
            
            if status == ProductStatus.EXPIRED:
                expired_items += 1
            elif status == ProductStatus.NEAR_EXPIRY:
                near_expiry_items += 1
            elif status == ProductStatus.OUT_OF_STOCK:
                out_of_stock_items += 1
            elif status == ProductStatus.LOW_STOCK:
                low_stock_items += 1
        
        kpi = DepartmentKPI(
            department=dept,
            total_items=total_items,
            expired_items=expired_items,
            near_expiry_items=near_expiry_items,
            out_of_stock_items=out_of_stock_items,
            low_stock_items=low_stock_items,
            total_stock_value=total_stock_value,
            total_quantity=total_quantity
        )
        kpis.append(kpi)
    
    # Get recent alerts
    recent_alerts = []
    alerts_cursor = db.alerts.find({"department": {"$in": [d.value for d in accessible_departments]}}).sort("created_at", -1).limit(10)
    async for alert in alerts_cursor:
        recent_alerts.append(Alert(**alert))
    
    # Calculate stock distribution and expiry status
    stock_distribution = {}
    expiry_status = {"in_stock": 0, "low_stock": 0, "out_of_stock": 0, "expired": 0, "near_expiry": 0}
    
    for kpi in kpis:
        stock_distribution[kpi.department.value] = kpi.total_items
        expiry_status["expired"] += kpi.expired_items
        expiry_status["near_expiry"] += kpi.near_expiry_items
        expiry_status["out_of_stock"] += kpi.out_of_stock_items
        expiry_status["low_stock"] += kpi.low_stock_items
        expiry_status["in_stock"] += (kpi.total_items - kpi.expired_items - kpi.near_expiry_items - kpi.out_of_stock_items - kpi.low_stock_items)
    
    # Get top suppliers
    top_suppliers = []
    suppliers_pipeline = [
        {"$match": {"department": {"$in": [d.value for d in accessible_departments]}}},
        {"$group": {
            "_id": "$supplier",
            "total_items": {"$sum": 1},
            "total_value": {"$sum": {"$multiply": ["$quantity", "$purchase_price"]}},
            "out_of_stock": {"$sum": {"$cond": [{"$lte": ["$quantity", 0]}, 1, 0]}},
            "currency": {"$first": "$purchase_currency"}
        }},
        {"$sort": {"total_items": -1}},
        {"$limit": 5}
    ]
    
    async for supplier_data in db.products.aggregate(suppliers_pipeline):
        supplier_detail = SupplierDetails(
            supplier_name=supplier_data["_id"],
            total_items=supplier_data["total_items"],
            out_of_stock_items=supplier_data["out_of_stock"],
            stock_value=supplier_data["total_value"],
            purchase_currency=Currency(supplier_data.get("currency", "YER"))
        )
        top_suppliers.append(supplier_detail)
    
    return DashboardData(
        user_role=current_user.role,
        accessible_departments=accessible_departments,
        kpis=kpis,
        recent_alerts=recent_alerts,
        stock_distribution=stock_distribution,
        expiry_status=expiry_status,
        top_suppliers=top_suppliers
    )

# Product Management Endpoints
@api_router.get("/products")
async def get_products(
    current_user: User = Depends(get_current_user),
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    accessible_departments = get_accessible_departments(current_user)
    filter_dict = {"department": {"$in": [d.value for d in accessible_departments]}}
    
    if department and department in [d.value for d in accessible_departments]:
        filter_dict["department"] = department
    if section:
        filter_dict["section"] = section
    if supplier:
        filter_dict["supplier"] = {"$regex": supplier, "$options": "i"}
    if search:
        filter_dict["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"item_number": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
            {"supplier": {"$regex": search, "$options": "i"}}
        ]
    
    products_cursor = db.products.find(filter_dict).skip(skip).limit(limit)
    products = []
    
    async for product_doc in products_cursor:
        # Remove ObjectId to avoid serialization issues
        if '_id' in product_doc:
            del product_doc['_id']
        
        # Calculate status for each product
        product_doc["status"] = await calculate_product_status(product_doc)
        products.append(product_doc)
    
    # Filter by status if requested
    if status:
        products = [p for p in products if p.get("status") == status]
    
    return products

@api_router.post("/products")
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    accessible_departments = get_accessible_departments(current_user)
    if product.department not in accessible_departments:
        raise HTTPException(status_code=403, detail="Access denied to this department")
    
    # Check if product with same item_number or barcode exists
    if product.item_number:
        existing = await db.products.find_one({"item_number": product.item_number})
        if existing:
            raise HTTPException(status_code=400, detail="Product with this item number already exists")
    
    if product.barcode:
        existing = await db.products.find_one({"barcode": product.barcode})
        if existing:
            raise HTTPException(status_code=400, detail="Product with this barcode already exists")
    
    new_product = Product(**product.dict())
    product_dict = new_product.dict()
    
    await db.products.insert_one(product_dict)
    
    # Create alert if out of stock
    if product.quantity <= 0:
        alert = Alert(
            alert_type=AlertType.OUT_OF_STOCK,
            department=product.department,
            section=product.section,
            product_id=new_product.id,
            product_name=product.product_name,
            message=f"Product {product.product_name} is out of stock",
            priority="high"
        )
        await db.alerts.insert_one(alert.dict())
    
    return new_product

@api_router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    accessible_departments = get_accessible_departments(current_user)
    if product["department"] not in [d.value for d in accessible_departments]:
        raise HTTPException(status_code=403, detail="Access denied to this product")
    
    update_dict = product_update.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.products.update_one({"id": product_id}, {"$set": update_dict})
    
    # Check for alerts after update
    updated_product = await db.products.find_one({"id": product_id})
    new_status = await calculate_product_status(updated_product)
    
    # Create alerts if needed
    if new_status == ProductStatus.OUT_OF_STOCK:
        alert = Alert(
            alert_type=AlertType.OUT_OF_STOCK,
            department=Department(updated_product["department"]),
            section=Section(updated_product["section"]),
            product_id=product_id,
            product_name=updated_product["product_name"],
            message=f"Product {updated_product['product_name']} is now out of stock",
            priority="high"
        )
        await db.alerts.insert_one(alert.dict())
    
    return {"message": "Product updated successfully"}

# Search endpoint with barcode support
@api_router.get("/search")
async def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    accessible_departments = get_accessible_departments(current_user)
    
    # Enhanced search across multiple fields
    search_filter = {
        "department": {"$in": [d.value for d in accessible_departments]},
        "$or": [
            {"product_name": {"$regex": q, "$options": "i"}},
            {"item_number": {"$regex": q, "$options": "i"}},
            {"barcode": q},  # Exact match for barcode
            {"supplier": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"arabic_description": {"$regex": q, "$options": "i"}}
        ]
    }
    
    products = await db.products.find(search_filter).limit(limit).to_list(limit)
    
    # Calculate status for each product
    for product in products:
        product["status"] = await calculate_product_status(product)
    
    return products

# Import Excel data endpoint
@api_router.post("/import/excel")
async def import_excel_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Map Excel columns to our model
                product_data = {
                    "product_name": str(row.get("Item Name", "")),
                    "item_number": str(row.get("item Number", "")),
                    "department": str(row.get("Department", "")),
                    "section": str(row.get("Section", "")),
                    "family": str(row.get("Family", "")),
                    "sub_family": str(row.get("Sub Family", "")),
                    "supplier_code": str(row.get("supplier Code", "")) if pd.notna(row.get("supplier Code")) else None,
                    "supplier": str(row.get("Supplier", "")),
                    "quantity": int(row.get("Quantity", 0)),
                    "barcode": str(row.get("Barcode", "")) if pd.notna(row.get("Barcode")) else None,
                    "purchase_price": float(row.get("purchase price", 0)) if pd.notna(row.get("purchase price")) else 0,
                    "purchase_currency": str(row.get("Purchase currency ", "YER")).strip(),
                    "selling_price": float(row.get("Selling Price", 0)) if pd.notna(row.get("Selling Price")) else 0,
                    "arabic_description": str(row.get("Arabic Description", "")) if pd.notna(row.get("Arabic Description")) else None,
                    "location": str(row.get("Location", "")) if pd.notna(row.get("Location")) else None,
                    "brand": str(row.get("Brand", "")) if pd.notna(row.get("Brand")) else None
                }
                
                # Validate required fields
                if not product_data["product_name"] or not product_data["department"]:
                    errors.append(f"Row {index + 2}: Missing required fields")
                    continue
                
                # Create product
                product = Product(**product_data)
                
                # Check if product exists (by item_number or barcode)
                existing = None
                if product.item_number:
                    existing = await db.products.find_one({"item_number": product.item_number})
                if not existing and product.barcode:
                    existing = await db.products.find_one({"barcode": product.barcode})
                
                if existing:
                    # Update existing product
                    update_data = product_data.copy()
                    update_data["updated_at"] = datetime.utcnow()
                    await db.products.update_one({"id": existing["id"]}, {"$set": update_data})
                else:
                    # Insert new product
                    await db.products.insert_one(product.dict())
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "message": f"Import completed. {imported_count} products processed.",
            "imported_count": imported_count,
            "errors": errors[:10]  # Limit error list
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing Excel file: {str(e)}")

# Supplier endpoints
@api_router.get("/suppliers", response_model=List[SupplierDetails])
async def get_suppliers(current_user: User = Depends(get_current_user)):
    accessible_departments = get_accessible_departments(current_user)
    
    # Aggregate supplier data
    suppliers_pipeline = [
        {"$match": {"department": {"$in": [d.value for d in accessible_departments]}}},
        {"$group": {
            "_id": {
                "supplier": "$supplier",
                "supplier_code": "$supplier_code",
                "currency": "$purchase_currency"
            },
            "total_items": {"$sum": 1},
            "total_value": {"$sum": {"$multiply": ["$quantity", "$purchase_price"]}},
            "out_of_stock": {"$sum": {"$cond": [{"$lte": ["$quantity", 0]}, 1, 0]}}
        }},
        {"$sort": {"total_items": -1}}
    ]
    
    suppliers = []
    async for supplier_data in db.products.aggregate(suppliers_pipeline):
        supplier_detail = SupplierDetails(
            supplier_name=supplier_data["_id"]["supplier"],
            supplier_code=supplier_data["_id"].get("supplier_code"),
            total_items=supplier_data["total_items"],
            out_of_stock_items=supplier_data["out_of_stock"],
            stock_value=supplier_data["total_value"],
            purchase_currency=Currency(supplier_data["_id"].get("currency", "YER"))
        )
        suppliers.append(supplier_detail)
    
    return suppliers

# Email and Alert System
async def send_email_alert(recipients: List[str], subject: str, body: str, attachments: List = None):
    """Send email alerts using SMTP"""
    try:
        sender_email = os.environ.get('SENDER_EMAIL', 'inventory@geantyemen.com')
        sender_password = os.environ.get('EMAIL_PASSWORD', '')
        
        if not sender_password:
            logger.warning("Email password not configured, skipping email send")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['data'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipients, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {recipients}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

@api_router.post("/alerts/send-daily")
async def send_daily_alerts(background_tasks: BackgroundTasks):
    """Send daily alerts for out-of-stock and near-expiry items"""
    try:
        # Get email settings
        settings = await db.email_settings.find_one() or {}
        if not settings.get('daily_alerts_enabled', True):
            return {"message": "Daily alerts are disabled"}
        
        recipients = [settings.get('default_recipient', 'imad@geantyemen.com')]
        
        # Get all departments
        departments = [Department.FMG, Department.CGD, Department.OPSS]
        
        # Collect alert data
        out_of_stock_items = []
        near_expiry_items = []
        
        for dept in departments:
            products = await db.products.find({"department": dept.value}).to_list(None)
            
            for product in products:
                status = await calculate_product_status(product)
                
                if status == ProductStatus.OUT_OF_STOCK:
                    out_of_stock_items.append({
                        "department": dept.value,
                        "product_name": product["product_name"],
                        "item_number": product.get("item_number", "N/A"),
                        "supplier": product.get("supplier", "N/A"),
                        "section": product["section"]
                    })
                elif status == ProductStatus.NEAR_EXPIRY:
                    near_expiry_items.append({
                        "department": dept.value,
                        "product_name": product["product_name"],
                        "item_number": product.get("item_number", "N/A"),
                        "expiry_date": product.get("expiry_date", datetime.utcnow()).strftime("%Y-%m-%d"),
                        "supplier": product.get("supplier", "N/A"),
                        "section": product["section"]
                    })
        
        # Create email content
        subject = f"Geant Hypermarket - Daily Inventory Alert ({datetime.now().strftime('%Y-%m-%d')})"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #22c55e, #3b82f6); padding: 20px; color: white; text-align: center;">
                <h1>Geant Hypermarket</h1>
                <h2>Daily Inventory Alert Report</h2>
                <p>Date: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div style="padding: 20px;">
                <h3 style="color: #dc2626;">🚨 Out of Stock Items ({len(out_of_stock_items)})</h3>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    <thead style="background-color: #fee2e2;">
                        <tr>
                            <th style="padding: 10px;">Department</th>
                            <th style="padding: 10px;">Product Name</th>
                            <th style="padding: 10px;">Item Number</th>
                            <th style="padding: 10px;">Section</th>
                            <th style="padding: 10px;">Supplier</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for item in out_of_stock_items[:20]:  # Limit to 20 items
            body += f"""
                        <tr>
                            <td style="padding: 8px;">{item['department']}</td>
                            <td style="padding: 8px;">{item['product_name']}</td>
                            <td style="padding: 8px;">{item['item_number']}</td>
                            <td style="padding: 8px;">{item['section']}</td>
                            <td style="padding: 8px;">{item['supplier']}</td>
                        </tr>
            """
        
        body += f"""
                    </tbody>
                </table>
                
                <h3 style="color: #f59e0b;">⚠️ Near Expiry Items ({len(near_expiry_items)})</h3>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    <thead style="background-color: #fef3c7;">
                        <tr>
                            <th style="padding: 10px;">Department</th>
                            <th style="padding: 10px;">Product Name</th>
                            <th style="padding: 10px;">Item Number</th>
                            <th style="padding: 10px;">Expiry Date</th>
                            <th style="padding: 10px;">Section</th>
                            <th style="padding: 10px;">Supplier</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for item in near_expiry_items[:20]:  # Limit to 20 items
            body += f"""
                        <tr>
                            <td style="padding: 8px;">{item['department']}</td>
                            <td style="padding: 8px;">{item['product_name']}</td>
                            <td style="padding: 8px;">{item['item_number']}</td>
                            <td style="padding: 8px;">{item['expiry_date']}</td>
                            <td style="padding: 8px;">{item['section']}</td>
                            <td style="padding: 8px;">{item['supplier']}</td>
                        </tr>
            """
        
        body += """
                    </tbody>
                </table>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
                    <p style="color: #6b7280;">This is an automated alert from Geant Hypermarket Inventory Management System</p>
                    <p style="color: #6b7280;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Aden Time)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email in background
        background_tasks.add_task(send_email_alert, recipients, subject, body)
        
        return {
            "message": "Daily alert email queued for sending",
            "out_of_stock_count": len(out_of_stock_items),
            "near_expiry_count": len(near_expiry_items)
        }
        
    except Exception as e:
        logger.error(f"Error sending daily alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending daily alerts: {str(e)}")

# Export endpoints
@api_router.post("/export/excel")
async def export_to_excel(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export inventory data to Excel with company branding"""
    try:
        accessible_departments = get_accessible_departments(current_user)
        
        # Build filter
        filter_dict = {"department": {"$in": [d.value for d in accessible_departments]}}
        if export_request.department:
            filter_dict["department"] = export_request.department.value
        if export_request.section:
            filter_dict["section"] = export_request.section.value
        if export_request.supplier:
            filter_dict["supplier"] = {"$regex": export_request.supplier, "$options": "i"}
        
        # Get products
        products = await db.products.find(filter_dict).to_list(None)
        
        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#22c55e',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Inventory Report')
        
        # Add company header
        worksheet.merge_range('A1:L1', 'Geant Hypermarket - Inventory Report', 
                            workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'bg_color': '#3b82f6', 'font_color': 'white'}))
        worksheet.merge_range('A2:L2', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                            workbook.add_format({'align': 'center', 'italic': True}))
        
        # Headers
        headers = ['Product Name', 'Item Number', 'Department', 'Section', 'Supplier', 'Quantity', 
                  'Purchase Price', 'Currency', 'Stock Value', 'Location', 'Brand', 'Status']
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Data rows
        for row, product in enumerate(products, start=4):
            status = await calculate_product_status(product)
            stock_value = product.get('quantity', 0) * product.get('purchase_price', 0)
            
            worksheet.write(row, 0, product.get('product_name', ''), cell_format)
            worksheet.write(row, 1, product.get('item_number', ''), cell_format)
            worksheet.write(row, 2, product.get('department', ''), cell_format)
            worksheet.write(row, 3, product.get('section', ''), cell_format)
            worksheet.write(row, 4, product.get('supplier', ''), cell_format)
            worksheet.write(row, 5, product.get('quantity', 0), cell_format)
            worksheet.write(row, 6, product.get('purchase_price', 0), cell_format)
            worksheet.write(row, 7, product.get('purchase_currency', 'YER'), cell_format)
            worksheet.write(row, 8, stock_value, cell_format)
            worksheet.write(row, 9, product.get('location', ''), cell_format)
            worksheet.write(row, 10, product.get('brand', ''), cell_format)
            worksheet.write(row, 11, status.value, cell_format)
        
        # Adjust column widths
        worksheet.set_column('A:A', 25)  # Product Name
        worksheet.set_column('B:B', 15)  # Item Number
        worksheet.set_column('C:L', 12)  # Other columns
        
        workbook.close()
        output.seek(0)
        
        # Return file
        filename = f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return FileResponse(
            path=None,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            content=output.getvalue()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Excel export: {str(e)}")

# Settings endpoints
@api_router.get("/settings/email", response_model=EmailSettings)
async def get_email_settings(current_user: User = Depends(get_admin_user)):
    settings = await db.email_settings.find_one()
    if not settings:
        # Create default settings
        default_settings = EmailSettings()
        await db.email_settings.insert_one(default_settings.dict())
        return default_settings
    return EmailSettings(**settings)

@api_router.put("/settings/email")
async def update_email_settings(
    settings: EmailSettings,
    current_user: User = Depends(get_admin_user)
):
    settings.updated_at = datetime.utcnow()
    await db.email_settings.replace_one({}, settings.dict(), upsert=True)
    return {"message": "Email settings updated successfully"}

@api_router.get("/settings/company", response_model=CompanySettings)
async def get_company_settings(current_user: User = Depends(get_admin_user)):
    settings = await db.company_settings.find_one()
    if not settings:
        default_settings = CompanySettings()
        await db.company_settings.insert_one(default_settings.dict())
        return default_settings
    return CompanySettings(**settings)

@api_router.put("/settings/company")
async def update_company_settings(
    settings: CompanySettings,
    current_user: User = Depends(get_admin_user)
):
    settings.updated_at = datetime.utcnow()
    await db.company_settings.replace_one({}, settings.dict(), upsert=True)
    return {"message": "Company settings updated successfully"}

# Filter options endpoint
@api_router.get("/filters", response_model=FilterOptions)
async def get_filter_options(current_user: User = Depends(get_current_user)):
    accessible_departments = get_accessible_departments(current_user)
    
    # Get unique values for filters
    departments = [{"value": d.value, "label": d.value} for d in accessible_departments]
    
    sections_cursor = db.products.distinct("section", {"department": {"$in": [d.value for d in accessible_departments]}})
    sections = [{"value": s, "label": s} for s in await sections_cursor]
    
    suppliers_cursor = db.products.distinct("supplier", {"department": {"$in": [d.value for d in accessible_departments]}})
    suppliers = [{"value": s, "label": s} for s in await suppliers_cursor if s]
    
    families_cursor = db.products.distinct("family", {"department": {"$in": [d.value for d in accessible_departments]}})
    families = [{"value": f, "label": f} for f in await families_cursor if f]
    
    currencies = [{"value": c.value, "label": c.value} for c in Currency]
    
    return FilterOptions(
        departments=departments,
        sections=sections,
        suppliers=suppliers[:50],  # Limit for performance
        families=families[:50],
        currencies=currencies
    )

# Include router
app.include_router(api_router)

# Health check
@app.get("/")
async def root():
    return {"message": "Geant Hypermarket Inventory Management System API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)