from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from contextlib import asynccontextmanager
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
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Initialize scheduler
scheduler = AsyncIOScheduler()

async def send_automated_daily_alerts():
    """Automated function to send consolidated daily reports at 07:00 AM Aden time"""
    try:
        logger.info("Starting consolidated daily reports email...")
        
        # Get email settings
        settings = await db.email_settings.find_one() or {}
        if not settings.get('daily_alerts_enabled', True):
            logger.info("Daily alerts are disabled, skipping automated send")
            return
        
        recipients = [settings.get('default_recipient', 'imad@geantyemen.com')]
        
        # Get all departments
        departments = [Department.FMG, Department.CGD, Department.OPSS]
        aden_tz = pytz.timezone('Asia/Aden')
        current_aden_time = datetime.now(aden_tz)
        
        # 1. Collect inventory alert data
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
        
        # 2. Get waste report data (weekly summary)
        waste_data = {"currency_totals": {"YER": 0, "SAR": 0, "EUR": 0}, "total_entries": 0}
        try:
            # Get weekly waste report
            end_date = current_aden_time
            start_date = end_date - timedelta(days=7)
            
            waste_entries = await db.waste_entries.find({
                "created_at": {
                    "$gte": start_date.replace(tzinfo=None),
                    "$lt": end_date.replace(tzinfo=None)
                }
            }).to_list(None)
            
            waste_totals = {"YER": 0, "SAR": 0, "EUR": 0}
            for entry in waste_entries:
                currency = entry.get("purchase_currency", "YER")
                waste_value = entry.get("waste_value", 0)
                if currency in waste_totals:
                    waste_totals[currency] += waste_value
            
            waste_data = {
                "currency_totals": waste_totals,
                "total_entries": len(waste_entries),
                "period": "Last 7 Days"
            }
        except Exception as e:
            logger.warning(f"Could not fetch waste data: {str(e)}")
        
        # 3. Get return forms count (last 7 days)
        return_forms_count = 0
        try:
            return_forms = await db.return_forms.find({
                "created_at": {
                    "$gte": (current_aden_time - timedelta(days=7)).replace(tzinfo=None),
                    "$lt": current_aden_time.replace(tzinfo=None)
                }
            }).to_list(None)
            return_forms_count = len(return_forms)
        except Exception as e:
            logger.warning(f"Could not fetch return forms data: {str(e)}")
        
        # 4. Generate all report attachments
        attachments = []
        
        # Daily Inventory Report (PDF & Excel)
        try:
            pdf_data = await generate_daily_alert_pdf(out_of_stock_items, near_expiry_items)
            excel_data = await generate_daily_alert_excel(out_of_stock_items, near_expiry_items)
            
            attachments.extend([
                {
                    "data": pdf_data,
                    "filename": f"Daily_Inventory_Report_{current_aden_time.strftime('%Y%m%d')}.pdf"
                },
                {
                    "data": excel_data,
                    "filename": f"Daily_Inventory_Report_{current_aden_time.strftime('%Y%m%d')}.xlsx"
                }
            ])
        except Exception as e:
            logger.warning(f"Could not generate daily inventory reports: {str(e)}")
        
        # Weekly Waste Report (if data exists)
        if waste_data["total_entries"] > 0:
            try:
                from io import BytesIO
                import xlsxwriter
                
                # Generate waste report Excel
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                
                # Add company branding
                branding = get_company_branding()
                worksheet = workbook.add_worksheet('Waste Report')
                add_logo_to_excel(workbook, worksheet, branding)
                
                # Header format
                header_format = workbook.add_format({
                    'bold': True, 'bg_color': branding['primary_color'], 'color': 'white',
                    'align': 'center', 'border': 1
                })
                
                # Write waste summary
                worksheet.write('A8', 'Weekly Waste Report Summary', header_format)
                worksheet.write('A10', 'Currency')
                worksheet.write('B10', 'Total Waste Value')
                
                row = 11
                for currency, value in waste_data["currency_totals"].items():
                    if value > 0:
                        worksheet.write(row, 0, currency)
                        worksheet.write(row, 1, value)
                        row += 1
                
                worksheet.write(row + 1, 0, 'Total Entries')
                worksheet.write(row + 1, 1, waste_data["total_entries"])
                
                workbook.close()
                waste_excel_data = output.getvalue()
                
                attachments.append({
                    "data": waste_excel_data,
                    "filename": f"Weekly_Waste_Report_{current_aden_time.strftime('%Y%m%d')}.xlsx"
                })
                
            except Exception as e:
                logger.warning(f"Could not generate waste report: {str(e)}")
        
        # 5. Create consolidated email subject and body
        subject = f"Geant Hypermarket - Consolidated Daily Reports ({current_aden_time.strftime('%Y-%m-%d')})"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: linear-gradient(135deg, #22c55e, #3b82f6); padding: 20px; color: white; text-align: center;">
                <h1>🏢 Geant Hypermarket</h1>
                <h2>📊 Consolidated Daily Reports</h2>
                <p>Automated Report - {current_aden_time.strftime('%Y-%m-%d %H:%M:%S')} (Aden Time)</p>
            </div>
            
            <div style="padding: 30px;">
                <h2>📈 Daily Business Summary</h2>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold; color: #dc2626;">📦 Out of Stock Items</td>
                        <td style="padding: 15px; color: #dc2626; font-weight: bold; font-size: 18px;">{len(out_of_stock_items)}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold; color: #f59e0b;">⏰ Near Expiry Items</td>
                        <td style="padding: 15px; color: #f59e0b; font-weight: bold; font-size: 18px;">{len(near_expiry_items)}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold; color: #ef4444;">🗑️ Waste Entries (7 days)</td>
                        <td style="padding: 15px; color: #ef4444; font-weight: bold; font-size: 18px;">{waste_data['total_entries']}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold; color: #8b5cf6;">🔄 Return Forms (7 days)</td>
                        <td style="padding: 15px; color: #8b5cf6; font-weight: bold; font-size: 18px;">{return_forms_count}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold;">📅 Report Generated</td>
                        <td style="padding: 15px;">{current_aden_time.strftime('%Y-%m-%d at %H:%M:%S')} (Asia/Aden)</td>
                    </tr>
                </table>
                
                {f'''
                <h3 style="color: #ef4444;">💰 Weekly Waste Value Summary</h3>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    {"".join([f'<tr><td style="padding: 10px; font-weight: bold;">{currency}</td><td style="padding: 10px;">{value:,.2f}</td></tr>' 
                              for currency, value in waste_data["currency_totals"].items() if value > 0])}
                </table>
                ''' if waste_data['total_entries'] > 0 else ''}
                
                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                    <h3>📎 All Reports Included in This Email:</h3>
                    <ul>
                        <li><strong>📄 Daily Inventory Report (PDF):</strong> Professional formatted daily inventory alerts</li>
                        <li><strong>📊 Daily Inventory Report (Excel):</strong> Detailed data for analysis and filtering</li>
                        {f'<li><strong>🗑️ Weekly Waste Report (Excel):</strong> Waste tracking and value analysis</li>' if waste_data['total_entries'] > 0 else ''}
                    </ul>
                    <p style="margin-top: 10px; color: #3b82f6;"><strong>📧 All reports consolidated in one email as requested!</strong></p>
                </div>
                
                <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0;">
                    <p><strong>🎯 Action Items:</strong></p>
                    <ul>
                        <li>Review out-of-stock items for immediate restocking</li>
                        <li>Check near-expiry items for promotional opportunities</li>
                        <li>Analyze waste patterns to reduce losses</li>
                        <li>Follow up on pending return forms</li>
                        <li>Contact suppliers for critical inventory items</li>
                    </ul>
                </div>
                
                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                    <p><strong>⚙️ Future Configuration Available:</strong></p>
                    <p>Report selection and timing can be customized through the Settings panel as needed.</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
                <p style="color: #666; font-size: 14px;">
                    This is an automated consolidated daily report from Geant Hypermarket Inventory Management System<br>
                    Generated on {current_aden_time.strftime('%Y-%m-%d at %H:%M:%S')} (Asia/Aden timezone)<br>
                    Scheduled daily at 07:00 AM Aden time - All reports in one email
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send consolidated email with all attachments
        success = await send_email_alert(recipients, subject, body, attachments)
        
        if success:
            logger.info(f"Consolidated daily reports sent successfully to {recipients} with {len(attachments)} attachments")
            # Update last automated email timestamp
            await db.email_settings.update_one(
                {},
                {"$set": {"last_automated_email": current_aden_time}},
                upsert=True
            )
        else:
            logger.error("Failed to send consolidated daily reports")
            
    except Exception as e:
        logger.error(f"Error in consolidated daily reports: {str(e)}")

# Schedule daily alerts for 07:00 AM Aden time
def setup_daily_email_scheduler():
    """Setup automated daily email scheduler"""
    aden_tz = pytz.timezone('Asia/Aden')
    
    # Schedule daily alerts at 07:00 AM Aden time
    scheduler.add_job(
        send_automated_daily_alerts,
        CronTrigger(hour=7, minute=0, timezone=aden_tz),
        id='daily_inventory_alerts',
        name='Daily Inventory Alert Email',
        replace_existing=True
    )
    
    logger.info("Daily email scheduler configured for 07:00 AM Asia/Aden timezone")

# Start scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    setup_daily_email_scheduler()
    logger.info("Email scheduler started successfully")
    yield
    # Shutdown
    scheduler.shutdown()
    logger.info("Email scheduler stopped")

app = FastAPI(
    title="Geant Hypermarket Inventory Management API",
    description="Advanced inventory management system with automated alerts",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware - Enhanced for mobile compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRFToken",
        "Cache-Control",
        "Pragma",
        "User-Agent",
        "DNT",
        "If-Modified-Since",
        "Keep-Alive",
        "Origin",
        "X-Requested-With",
        "Content-Range",
        "Range"
    ],
    expose_headers=[
        "Content-Length",
        "Content-Range",
        "Content-Type",
        "Cache-Control",
        "Expires",
        "Last-Modified"
    ],
    max_age=3600,
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
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")
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
        # Handle ObjectId or other non-datetime objects
        if not isinstance(expiry_date, datetime):
            # Skip expiry calculation if not a valid datetime
            return ProductStatus.IN_STOCK.value
            
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
    
    # Get all available sections for accessible departments
    sections = []
    section_docs = await db.products.distinct("section", {"department": {"$in": [d.value for d in accessible_departments]}})
    sections = [section for section in section_docs if section]  # Filter out None values
    
    return DashboardData(
        user_role=current_user.role,
        accessible_departments=accessible_departments,
        sections=sections,
        kpis=kpis,
        recent_alerts=recent_alerts,
        stock_distribution=stock_distribution,
        expiry_status=expiry_status,
        top_suppliers=top_suppliers
    )

# Product Management Endpoints
# Test endpoint for debugging
@api_router.get("/test-products")
async def test_products():
    """Simple test endpoint to debug ObjectId issues"""
    try:
        # Get just 5 products without any processing
        products = []
        async for product_doc in db.products.find().limit(5):
            # Create simple dict with just basic fields
            simple_product = {
                "product_name": product_doc.get("product_name", ""),
                "department": product_doc.get("department", ""),
                "quantity": product_doc.get("quantity", 0),
                "purchase_price": product_doc.get("purchase_price", 0),
                "purchase_currency": product_doc.get("purchase_currency", "")
            }
            products.append(simple_product)
        
        return {"count": len(products), "products": products}
        
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return {"error": str(e), "count": 0, "products": []}

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
    import json
    from bson import ObjectId
    from datetime import datetime
    
    try:
        # Simplify department access - just use strings
        accessible_dept_strings = ["01-FMG", "01-CGD", "01-OPSS"]
        
        # Build department filter
        if department and department in accessible_dept_strings:
            filter_dict = {"department": department}
        else:
            # Use $or instead of $in
            filter_dict = {"$or": [{"department": dept} for dept in accessible_dept_strings]}
        
        if section:
            filter_dict["section"] = section
        if supplier:
            filter_dict["supplier"] = {"$regex": supplier, "$options": "i"}
        if search:
            search_conditions = [
                {"product_name": {"$regex": search, "$options": "i"}},
                {"item_number": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}},
                {"supplier": {"$regex": search, "$options": "i"}}
            ]
            if "$or" in filter_dict:
                filter_dict = {"$and": [{"$or": filter_dict["$or"]}, {"$or": search_conditions}]}
            else:
                filter_dict["$or"] = search_conditions
        
        products_cursor = db.products.find(filter_dict).skip(skip).limit(limit)
        products = []
        
        async for product_doc in products_cursor:
            # Create a clean product dict with only safe values
            clean_product = {}
            
            # Copy only safe string/number fields
            safe_fields = [
                'id', 'product_name', 'item_number', 'department', 'section', 
                'family', 'sub_family', 'supplier_code', 'supplier', 'quantity',
                'barcode', 'purchase_price', 'purchase_currency', 'selling_price',
                'arabic_description', 'description', 'location', 'brand', 'image_url'
            ]
            
            for field in safe_fields:
                if field in product_doc:
                    value = product_doc[field]
                    # Only include if it's a basic type
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        clean_product[field] = value
            
            # Add status
            clean_product["status"] = "in_stock"  # Simple default status for now
            
            products.append(clean_product)
        
        # Filter by status if requested
        if status:
            products = [p for p in products if p.get("status") == status]
        
        return products
        
    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return []

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

# Excel lookup endpoint
@api_router.get("/excel-lookup")
async def excel_lookup(
    query: str = Query(..., description="Product name or barcode to search"),
    current_user: User = Depends(get_current_user)
):
    """Lookup product in Excel sheet by name or barcode"""
    try:
        import pandas as pd
        import os
        
        # Check if Excel file exists
        excel_path = '/app/items_import_template.xlsx'
        if not os.path.exists(excel_path):
            raise HTTPException(status_code=404, detail="Excel template not found")
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip()
        
        # Search by product name (case-insensitive) or barcode
        query_lower = str(query).lower().strip()
        
        # Try multiple search strategies
        matches = []
        
        # 1. Exact match on Item Name
        exact_name_match = df[df['Item Name'].str.lower().str.strip() == query_lower]
        if not exact_name_match.empty:
            matches.extend(exact_name_match.to_dict('records'))
        
        # 2. Partial match on Item Name (contains)
        if not matches:
            partial_name_match = df[df['Item Name'].str.lower().str.contains(query_lower, na=False)]
            if not partial_name_match.empty:
                matches.extend(partial_name_match.head(5).to_dict('records'))  # Limit to 5 results
        
        # 3. Exact match on Barcode
        if 'Barcode' in df.columns:
            barcode_match = df[df['Barcode'].astype(str).str.strip() == str(query).strip()]
            if not barcode_match.empty:
                matches.extend(barcode_match.to_dict('records'))
        
        # 4. Exact match on item Number
        if 'item Number' in df.columns:
            item_number_match = df[df['item Number'].astype(str).str.strip() == str(query).strip()]
            if not item_number_match.empty:
                matches.extend(item_number_match.to_dict('records'))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in matches:
            # Use item name + item number as unique identifier
            identifier = f"{match.get('Item Name', '')}-{match.get('item Number', '')}"
            if identifier not in seen:
                seen.add(identifier)
                unique_matches.append(match)
        
        if not unique_matches:
            return {"found": False, "message": "No products found matching the search query"}
        
        # Return the best match (first one) with standardized field names
        best_match = unique_matches[0]
        
        # Standardize the response format
        standardized_match = {
            "found": True,
            "product_name": str(best_match.get('Item Name', '')),
            "item_number": str(best_match.get('item Number', '')),
            "department": str(best_match.get('Department', '')),
            "section": str(best_match.get('Section', '')),
            "family": str(best_match.get('Family', '')),
            "sub_family": str(best_match.get('Sub Family', '')),
            "supplier_code": str(best_match.get('supplier Code', '')) if pd.notna(best_match.get('supplier Code')) else '',
            "supplier": str(best_match.get('Supplier', '')),
            "barcode": str(best_match.get('Barcode', '')) if pd.notna(best_match.get('Barcode')) else '',
            "purchase_price": float(best_match.get('purchase price', 0)) if pd.notna(best_match.get('purchase price')) else 0.0,
            "purchase_currency": str(best_match.get('Purchase currency', best_match.get('Purchase currency ', 'YER'))).strip() if pd.notna(best_match.get('Purchase currency', best_match.get('Purchase currency '))) else 'YER',
            "selling_price": float(best_match.get('Selling Price', 0)) if pd.notna(best_match.get('Selling Price')) else 0.0,
            "arabic_description": str(best_match.get('Arabic Description', '')) if pd.notna(best_match.get('Arabic Description')) else '',
            "location": str(best_match.get('Location', '')) if pd.notna(best_match.get('Location')) else '',
            "brand": str(best_match.get('Brand', '')) if pd.notna(best_match.get('Brand')) else '',
            "all_matches": len(unique_matches),
            "search_query": query
        }
        
        return standardized_match
        
    except Exception as e:
        logger.error(f"Error in Excel lookup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel lookup failed: {str(e)}")

# Barcode lookup endpoint
@api_router.get("/barcode/{barcode}")
async def get_product_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user)
):
    """Get product details by barcode scan"""
    from bson import ObjectId
    
    accessible_departments = get_accessible_departments(current_user)
    
    # Find product by exact barcode match
    product = await db.products.find_one({
        "barcode": barcode,
        "department": {"$in": [d.value for d in accessible_departments]}
    })
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Remove ObjectId for serialization
    if '_id' in product:
        del product['_id']
    
    # Handle ObjectId fields in the document
    for key, value in list(product.items()):
        if isinstance(value, ObjectId):
            del product[key]
        elif isinstance(value, datetime):
            product[key] = value.isoformat()
    
    # Calculate status
    product["status"] = await calculate_product_status(product)
    
    return product

# Return Form endpoints
@api_router.post("/returns")
async def create_return_form(
    return_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new return form"""
    try:
        # Add additional fields
        return_form = {
            **return_data,
            "id": str(uuid.uuid4()),
            "created_by": current_user.username,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        # Store in database
        await db.return_forms.insert_one(return_form)
        
        return {"message": "Return form created successfully", "id": return_form["id"]}
        
    except Exception as e:
        logger.error(f"Error creating return form: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create return form")

@api_router.get("/returns")
async def get_return_forms(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get return forms"""
    try:
        forms_cursor = db.return_forms.find().skip(skip).limit(limit).sort("created_at", -1)
        forms = []
        
        async for form in forms_cursor:
            if '_id' in form:
                del form['_id']
            
            # Convert datetime objects to ISO strings
            for key, value in form.items():
                if isinstance(value, datetime):
                    form[key] = value.isoformat()
            
            forms.append(form)
        
        return forms
        
    except Exception as e:
        logger.error(f"Error fetching return forms: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch return forms")

# Update product endpoint
@api_router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    try:
        from bson import ObjectId
        
        # Find the existing product
        existing_product = await db.products.find_one({"id": product_id})
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update the product
        updated_data = {
            **product_data,
            "updated_at": datetime.utcnow()
        }
        
        await db.products.update_one(
            {"id": product_id},
            {"$set": updated_data}
        )
        
        # Get the updated product
        updated_product = await db.products.find_one({"id": product_id})
        
        # Clean the response
        if '_id' in updated_product:
            del updated_product['_id']
        
        # Handle ObjectId fields
        for key, value in list(updated_product.items()):
            if isinstance(value, ObjectId):
                del updated_product[key]
            elif isinstance(value, datetime):
                updated_product[key] = value.isoformat()
        
        return updated_product
        
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update product")

# Image upload endpoint
@api_router.post("/products/{product_id}/image")
async def upload_product_image(
    product_id: str,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload product image"""
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (5MB max)
    if image.size and image.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # Check if product exists
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        # Create uploads directory if it doesn't exist
        import os
        uploads_dir = "/app/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        filename = f"{product_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(uploads_dir, filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Update product with image URL
        image_url = f"/uploads/{filename}"
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"image_url": image_url, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": "Image uploaded successfully", "image_url": image_url}
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400, 404) without converting to 500
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

# Serve images through API endpoint
@api_router.get("/uploads/{filename}")
async def serve_image(filename: str):
    """Serve uploaded images through API endpoint"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        file_path = f"/app/uploads/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(
            file_path,
            media_type="image/jpeg",  # You might want to detect this dynamically
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

# Search endpoint with barcode support
@api_router.get("/search")
async def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    from bson import ObjectId
    from datetime import datetime
    
    try:
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
        
        products_cursor = db.products.find(search_filter).limit(limit)
        products = []
        
        async for product_doc in products_cursor:
            # Create a clean product dict with only safe values
            clean_product = {}
            
            # Copy only safe string/number fields
            safe_fields = [
                'id', 'product_name', 'item_number', 'department', 'section', 
                'family', 'sub_family', 'supplier_code', 'supplier', 'quantity',
                'barcode', 'purchase_price', 'purchase_currency', 'selling_price',
                'arabic_description', 'description', 'location', 'brand', 'image_url'
            ]
            
            for field in safe_fields:
                if field in product_doc:
                    value = product_doc[field]
                    # Only include if it's a basic type
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        clean_product[field] = value
            
            # Add status
            clean_product["status"] = await calculate_product_status(product_doc)
            
            products.append(clean_product)
        
        return products
        
    except Exception as e:
        logger.error(f"Error in search_products: {str(e)}")
        return []

# Clear products endpoint (for re-import)
@api_router.delete("/products/clear")
async def clear_all_products(
    current_user: User = Depends(get_current_user)
):
    """Clear all products (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.products.delete_many({})
        return {"message": f"Cleared {result.deleted_count} products successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing products: {str(e)}")

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
                    "purchase_currency": str(row.get("Purchase currency", row.get("Purchase currency ", "YER"))).strip() if pd.notna(row.get("Purchase currency", row.get("Purchase currency "))) else "YER",
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
        demo_mode = os.environ.get('EMAIL_DEMO_MODE', 'false').lower() == 'true'
        
        if not sender_password:
            logger.warning("Email password not configured, email sending disabled")
            # Log this as an email failure for debugging
            try:
                aden_tz = pytz.timezone('Asia/Aden')
                current_aden_time = datetime.now(aden_tz)
                await db.email_settings.update_one(
                    {},
                    {"$push": {"email_failures": {
                        "timestamp": current_aden_time,
                        "error": "EMAIL_PASSWORD not configured in environment variables",
                        "type": "configuration_error",
                        "recipients": recipients,
                        "subject": subject[:50] + "..." if len(subject) > 50 else subject
                    }}},
                    upsert=True
                )
            except Exception as log_error:
                logger.error(f"Failed to log email failure: {log_error}")
            return False
        
        # Demo mode - simulate successful email without actually sending
        if demo_mode and sender_password == "demo_mode_email_testing":
            logger.info(f"DEMO MODE: Simulating email send to {recipients}")
            logger.info(f"DEMO MODE: Subject: {subject}")
            logger.info(f"DEMO MODE: Body preview: {body[:100]}...")
            
            # Log successful demo email
            try:
                aden_tz = pytz.timezone('Asia/Aden')
                current_aden_time = datetime.now(aden_tz)
                await db.email_settings.update_one(
                    {},
                    {"$set": {"last_successful_email": current_aden_time}},
                    upsert=True
                )
            except Exception as log_error:
                logger.error(f"Failed to log demo email: {log_error}")
            
            return True
        
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
        
        # Log successful email
        try:
            aden_tz = pytz.timezone('Asia/Aden')
            current_aden_time = datetime.now(aden_tz)
            await db.email_settings.update_one(
                {},
                {"$set": {"last_successful_email": current_aden_time}},
                upsert=True
            )
        except Exception as log_error:
            logger.error(f"Failed to log successful email: {log_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        
        # Log the email failure for debugging
        try:
            aden_tz = pytz.timezone('Asia/Aden')
            current_aden_time = datetime.now(aden_tz)
            await db.email_settings.update_one(
                {},
                {"$push": {"email_failures": {
                    "timestamp": current_aden_time,
                    "error": str(e),
                    "type": "smtp_error",
                    "recipients": recipients,
                    "subject": subject[:50] + "..." if len(subject) > 50 else subject
                }}},
                upsert=True
            )
        except Exception as log_error:
            logger.error(f"Failed to log email failure: {log_error}")
        
        return False

async def generate_daily_alert_pdf(out_of_stock_items, near_expiry_items):
    """Generate PDF report for daily alerts with company branding"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get company branding
        branding = get_company_branding()
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        story = []
        
        # Add company logo and header using helper function
        add_logo_to_pdf_story(story)
        
        # Document title with company colors
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.Color(*branding['pdf_primary_color']),
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"DAILY INVENTORY ALERT REPORT", title_style))
        story.append(Paragraph(f"{datetime.now().strftime('%Y-%m-%d')}", styles['Heading3']))
        story.append(Spacer(1, 20))
        
        # Summary
        summary_data = [
            ['Report Summary', ''],
            ['Out of Stock Items', str(len(out_of_stock_items))],
            ['Near Expiry Items', str(len(near_expiry_items))],
            ['Report Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Timezone', 'Asia/Aden (GMT+3)']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*branding['pdf_primary_color'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Out of Stock Items
        if out_of_stock_items:
            story.append(Paragraph("🚨 Out of Stock Items", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            out_of_stock_data = [['Department', 'Product Name', 'Item Number', 'Section', 'Supplier']]
            for item in out_of_stock_items[:50]:  # Limit to 50 items for PDF
                out_of_stock_data.append([
                    item['department'],
                    item['product_name'][:30] + '...' if len(item['product_name']) > 30 else item['product_name'],
                    item['item_number'],
                    item['section'][:15] + '...' if len(item['section']) > 15 else item['section'],
                    item['supplier'][:20] + '...' if len(item['supplier']) > 20 else item['supplier']
                ])
            
            out_table = Table(out_of_stock_data, colWidths=[1*inch, 2*inch, 1*inch, 1*inch, 1.5*inch])
            out_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(out_table)
            story.append(Spacer(1, 20))
        
        # Near Expiry Items
        if near_expiry_items:
            story.append(Paragraph("⚠️ Near Expiry Items", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            near_expiry_data = [['Department', 'Product Name', 'Item Number', 'Expiry Date', 'Section']]
            for item in near_expiry_items[:50]:  # Limit to 50 items for PDF
                near_expiry_data.append([
                    item['department'],
                    item['product_name'][:30] + '...' if len(item['product_name']) > 30 else item['product_name'],
                    item['item_number'],
                    item['expiry_date'],
                    item['section'][:20] + '...' if len(item['section']) > 20 else item['section']
                ])
            
            near_table = Table(near_expiry_data, colWidths=[1*inch, 2*inch, 1*inch, 1*inch, 1.5*inch])
            near_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(near_table)
        
        # Build PDF
        doc.build(story)
        pdf_data = output.getvalue()
        output.close()
        
        return pdf_data
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return b""

async def generate_daily_alert_excel(out_of_stock_items, near_expiry_items):
    """Generate Excel report for daily alerts with company branding"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Get company branding
        branding = get_company_branding()
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define company-branded formats
            company_header_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_color': branding['excel_header_color'],
                'align': 'center',
                'valign': 'vcenter'
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': branding['excel_header_color'],
                'font_color': 'white',
                'border': 1
            })
            
            # Summary sheet
            summary_data = {
                'Metric': ['Company', 'Report Type', 'Out of Stock Items', 'Near Expiry Items', 'Report Date', 'Timezone'],
                'Value': [branding['company_name'], 'Daily Stock Alert', len(out_of_stock_items), len(near_expiry_items), 
                         datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Asia/Aden (GMT+3)']
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=2)
            
            # Add company header to summary sheet
            summary_worksheet = writer.sheets['Summary']
            summary_worksheet.merge_range('A1:B1', f'{branding["company_name"]} - DAILY STOCK ALERT', company_header_format)
            
            # Style summary headers
            for col_num, value in enumerate(summary_df.columns.values):
                summary_worksheet.write(2, col_num, value, header_format)
                summary_worksheet.set_column(col_num, col_num, 25)
            
            # Out of Stock sheet
            if out_of_stock_items:
                out_df = pd.DataFrame(out_of_stock_items)
                out_df.to_excel(writer, sheet_name='Out of Stock', index=False, startrow=2)
                
                # Format the worksheet with company branding
                worksheet = writer.sheets['Out of Stock']
                
                # Add company header
                worksheet.merge_range('A1:F1', f'{branding["company_name"]} - OUT OF STOCK ITEMS', company_header_format)
                
                # Style headers
                for col_num, value in enumerate(out_df.columns.values):
                    worksheet.write(2, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 20)
            
            # Near Expiry sheet
            if near_expiry_items:
                near_df = pd.DataFrame(near_expiry_items)
                near_df.to_excel(writer, sheet_name='Near Expiry', index=False, startrow=2)
                
                if 'Near Expiry' in writer.sheets:
                    worksheet = writer.sheets['Near Expiry']
                    
                    # Add company header
                    worksheet.merge_range('A1:F1', f'{branding["company_name"]} - NEAR EXPIRY ITEMS', company_header_format)
                    
                    # Define warning header format
                    warning_header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#FF8C00',  # Orange for warnings
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    for col_num, value in enumerate(near_df.columns.values):
                        worksheet.write(2, col_num, value, warning_header_format)
                        worksheet.set_column(col_num, col_num, 20)
        
        excel_data = output.getvalue()
        output.close()
        
        return excel_data
        
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        return b""

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
        
        # Get company branding
        branding = get_company_branding()
        
        # Create email content with company branding
        subject = f"{branding['company_name']} - Daily Inventory Alert ({datetime.now().strftime('%Y-%m-%d')})"
        
        # Generate PDF report
        pdf_data = await generate_daily_alert_pdf(out_of_stock_items, near_expiry_items)
        
        # Generate Excel report 
        excel_data = await generate_daily_alert_excel(out_of_stock_items, near_expiry_items)
        
        # Prepare attachments
        attachments = [
            {
                "data": pdf_data,
                "filename": f"{branding['company_name']}_Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            },
            {
                "data": excel_data,
                "filename": f"{branding['company_name']}_Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            }
        ]
        
        body = f"""
        <html>
        <head>
            <style>
                .company-header {{
                    background: linear-gradient(135deg, {branding['primary_color']}, {branding['secondary_color']});
                    padding: 20px;
                    color: white;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content-area {{
                    padding: 20px;
                    background-color: {branding['background_color']};
                }}
                .out-of-stock-table {{
                    background-color: #fee2e2;
                    color: #dc2626;
                }}
                .near-expiry-table {{
                    background-color: #fef3c7;
                    color: #f59e0b;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #f3f4f6;
                    border-radius: 8px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
            <div class="company-header">
                <h1 style="margin: 0; font-size: 28px;">{branding['company_name']}</h1>
                <h2 style="margin: 10px 0; font-size: 20px;">Daily Inventory Alert Report</h2>
                <p style="margin: 0; font-size: 16px;">Date: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="content-area">
                <h3 style="color: #dc2626; display: flex; align-items: center; gap: 10px;">
                    🚨 Out of Stock Items ({len(out_of_stock_items)})
                </h3>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px; border-radius: 8px; overflow: hidden;">
                    <thead class="out-of-stock-table">
                        <tr>
                            <th style="padding: 12px; font-weight: bold;">Department</th>
                            <th style="padding: 12px; font-weight: bold;">Product Name</th>
                            <th style="padding: 12px; font-weight: bold;">Item Number</th>
                            <th style="padding: 12px; font-weight: bold;">Section</th>
                            <th style="padding: 12px; font-weight: bold;">Supplier</th>
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
                
                <h3 style="color: #f59e0b; display: flex; align-items: center; gap: 10px;">
                    ⚠️ Near Expiry Items ({len(near_expiry_items)})
                </h3>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px; border-radius: 8px; overflow: hidden;">
                    <thead class="near-expiry-table">
                        <tr>
                            <th style="padding: 12px; font-weight: bold;">Department</th>
                            <th style="padding: 12px; font-weight: bold;">Product Name</th>
                            <th style="padding: 12px; font-weight: bold;">Item Number</th>
                            <th style="padding: 12px; font-weight: bold;">Expiry Date</th>
                            <th style="padding: 12px; font-weight: bold;">Section</th>
                            <th style="padding: 12px; font-weight: bold;">Supplier</th>
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
                
                <div class="footer">
                    <p style="margin: 0 0 10px 0; font-weight: bold;">📧 {branding['company_name']} Inventory Management System</p>
                    <p style="margin: 0 0 5px 0;">This is an automated daily inventory alert</p>
                    <p style="margin: 0;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Aden Time)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email with attachments in background
        background_tasks.add_task(send_email_alert, recipients, subject, body, attachments)
        
        return {
            "message": "Daily alert email queued for sending",
            "out_of_stock_count": len(out_of_stock_items),
            "near_expiry_count": len(near_expiry_items)
        }
        
    except Exception as e:
        logger.error(f"Error sending daily alerts: {str(e)}")
        # Log the error in email settings for debugging
        try:
            await db.email_settings.update_one(
                {},
                {"$push": {"email_failures": {
                    "timestamp": datetime.now(pytz.timezone("Asia/Aden")),
                    "error": str(e),
                    "type": "daily_alert"
                }}},
                upsert=True
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error sending daily alerts: {str(e)}")

@api_router.post("/alerts/send-test-email")
async def send_test_email(background_tasks: BackgroundTasks, current_user: User = Depends(get_admin_user)):
    """Send a test email immediately to verify email functionality"""
    try:
        # Get email settings
        settings = await db.email_settings.find_one() or {}
        
        recipients = [settings.get('default_recipient', 'imad@geantyemen.com')]
        
        # Create test email content with current Aden time
        aden_tz = pytz.timezone('Asia/Aden')
        current_aden_time = datetime.now(aden_tz)
        
        subject = f"Test Email - Geant Hypermarket Inventory System"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: linear-gradient(135deg, #22c55e, #3b82f6); padding: 20px; color: white; text-align: center;">
                <h1>📧 Test Email - Geant Hypermarket</h1>
                <p>Email System Verification</p>
            </div>
            
            <div style="padding: 30px;">
                <h2>✅ Email System Status: Working</h2>
                
                <div style="background-color: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                    <strong>🕰️ Test Email Details:</strong><br>
                    • <strong>Sent Time (Aden):</strong> {current_aden_time.strftime('%Y-%m-%d %H:%M:%S %Z')}<br>
                    • <strong>Timezone:</strong> Asia/Aden (GMT+3)<br>
                    • <strong>Recipient:</strong> {recipients[0]}<br>
                    • <strong>Daily Alert Time:</strong> {settings.get('daily_alert_time', '07:00')} AM Aden Time
                </div>
                
                <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0;">
                    <strong>📋 System Configuration:</strong><br>
                    • Daily alerts are scheduled for <strong>07:00 AM Aden time</strong> daily<br>
                    • Email notifications: <strong>{"Enabled" if settings.get('daily_alerts_enabled', True) else "Disabled"}</strong><br>
                    • Default recipient: <strong>{recipients[0]}</strong>
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>If you received this email, the system is working correctly</li>
                    <li>Daily alerts will be sent automatically at 07:00 AM Aden time</li>
                    <li>Check the Settings panel for email configuration options</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
                <p style="color: #666; font-size: 14px;">
                    This is an automated test email from Geant Hypermarket Inventory Management System<br>
                    Generated on {current_aden_time.strftime('%Y-%m-%d at %H:%M:%S')} (Asia/Aden timezone)
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send test email
        success = await send_email_alert(recipients, subject, body)
        
        if success:
            # Update last test email timestamp
            await db.email_settings.update_one(
                {},
                {
                    "$set": {"last_test_email": current_aden_time},
                    "$push": {"email_failures": {
                        "$each": [],
                        "$slice": -10  # Keep only last 10 entries
                    }}
                },
                upsert=True
            )
            
            return {
                "message": "Test email sent successfully",
                "sent_to": recipients,
                "aden_time": current_aden_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "timezone": "Asia/Aden (GMT+3)"
            }
        else:
            # Log the failure
            await db.email_settings.update_one(
                {},
                {"$push": {"email_failures": {
                    "timestamp": current_aden_time,
                    "error": "Email send function returned False",
                    "type": "test_email"
                }}},
                upsert=True
            )
            raise HTTPException(status_code=500, detail="Failed to send test email")
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        # Log the error
        try:
            aden_tz = pytz.timezone('Asia/Aden')
            current_aden_time = datetime.now(aden_tz)
            await db.email_settings.update_one(
                {},
                {"$push": {"email_failures": {
                    "timestamp": current_aden_time,
                    "error": str(e),
                    "type": "test_email"
                }}},
                upsert=True
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")

@api_router.get("/alerts/email-status")
async def get_email_status(current_user: User = Depends(get_admin_user)):
    """Get email system status and recent failures for debugging"""
    try:
        settings = await db.email_settings.find_one() or {}
        
        # Get Aden timezone info
        aden_tz = pytz.timezone('Asia/Aden')
        current_aden_time = datetime.now(aden_tz)
        
        # Check email configuration
        sender_email = os.environ.get('SENDER_EMAIL', 'inventory@geantyemen.com')
        email_password_configured = bool(os.environ.get('EMAIL_PASSWORD'))
        demo_mode = os.environ.get('EMAIL_DEMO_MODE', 'false').lower() == 'true'
        demo_password = os.environ.get('EMAIL_PASSWORD') == "demo_mode_email_testing"
        
        return {
            "current_aden_time": current_aden_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            "timezone": "Asia/Aden (GMT+3)",
            "daily_alert_time": settings.get('daily_alert_time', '07:00'),
            "daily_alerts_enabled": settings.get('daily_alerts_enabled', True),
            "default_recipient": settings.get('default_recipient', 'imad@geantyemen.com'),
            "sender_email": sender_email,
            "last_test_email": settings.get('last_test_email'),
            "last_successful_email": settings.get('last_successful_email'),
            "recent_failures": settings.get('email_failures', [])[-5:],  # Last 5 failures
            "email_configured": email_password_configured,
            "demo_mode": demo_mode and demo_password,
            "configuration_help": {
                "smtp_server": "smtp.gmail.com:587",
                "required_env": "EMAIL_PASSWORD",
                "current_sender": sender_email,
                "demo_mode_active": demo_mode and demo_password
            } if not (email_password_configured and not demo_password) else None
        }
        
    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting email status: {str(e)}")

# Helper functions for exports
async def generate_dashboard_data(current_user: User):
    """Generate dashboard data for exports"""
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
        
        for product in products:
            status = await calculate_product_status(product)
            total_stock_value += (product.get('quantity', 0) * product.get('purchase_price', 0))
            
            if status == ProductStatus.EXPIRED.value:
                expired_items += 1
            elif status == ProductStatus.NEAR_EXPIRY.value:
                near_expiry_items += 1
            elif status == ProductStatus.OUT_OF_STOCK.value:
                out_of_stock_items += 1
            elif status == ProductStatus.LOW_STOCK.value:
                low_stock_items += 1
        
        kpi = {
            'department': dept.value,
            'total_items': total_items,
            'expired_items': expired_items,
            'near_expiry_items': near_expiry_items,
            'out_of_stock_items': out_of_stock_items,
            'low_stock_items': low_stock_items,
            'total_stock_value': total_stock_value
        }
        kpis.append(kpi)
    
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
        {"$limit": 10}
    ]
    
    async for supplier_data in db.products.aggregate(suppliers_pipeline):
        supplier_detail = {
            'supplier_name': supplier_data["_id"],
            'total_items': supplier_data["total_items"],
            'out_of_stock_items': supplier_data["out_of_stock"],
            'stock_value': supplier_data["total_value"],
            'purchase_currency': supplier_data.get("currency", "YER")
        }
        top_suppliers.append(supplier_detail)
    
    return {
        'kpis': kpis,
        'top_suppliers': top_suppliers
    }

def get_stock_status(quantity: int, expiry_date=None, section=None):
    """Get stock status for a product"""
    if quantity <= 0:
        return ProductStatus.OUT_OF_STOCK
    elif quantity <= 10:  # Low stock threshold
        return ProductStatus.LOW_STOCK
    
    if expiry_date:
        if isinstance(expiry_date, str):
            try:
                expiry_date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            except:
                return ProductStatus.IN_STOCK
        elif isinstance(expiry_date, datetime):
            expiry_date_obj = expiry_date
        else:
            return ProductStatus.IN_STOCK
        
        now = datetime.utcnow()
        if expiry_date_obj < now:
            return ProductStatus.EXPIRED
        
        # Check if near expiry (7 days default, 15 for beverages)
        threshold_days = 15 if section == "BEVERAGE" else 7
        if expiry_date_obj < now + timedelta(days=threshold_days):
            return ProductStatus.NEAR_EXPIRY
    
    return ProductStatus.IN_STOCK

# Export endpoints
@api_router.post("/export/excel")
async def export_to_excel(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export inventory data to Excel with company branding"""
    try:
        import xlsxwriter
        from io import BytesIO
        
        # Create a BytesIO object to write the Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Inventory Report')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })
        
        # Add title
        worksheet.merge_range('A1:L1', 'Geant Hypermarket - Inventory Report', title_format)
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        worksheet.write('A3', f'Generated by: {current_user.full_name or current_user.username}')
        
        # Headers
        headers = [
            'Product Name', 'Item Number', 'Department', 'Section', 'Supplier',
            'Quantity', 'Purchase Price', 'Currency', 'Stock Value', 'Location', 'Brand', 'Status'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # Get products
        accessible_departments = get_accessible_departments(current_user)
        filter_dict = {"department": {"$in": [d.value for d in accessible_departments]}}
        
        if export_request.department:
            filter_dict["department"] = export_request.department.value
        if export_request.section:
            filter_dict["section"] = export_request.section.value
        if export_request.supplier:
            filter_dict["supplier"] = {"$regex": export_request.supplier, "$options": "i"}
            
        products = await db.products.find(filter_dict).to_list(length=None)
        
        # Write data
        for row, product in enumerate(products, start=5):
            status = get_stock_status(product.get('quantity', 0), 
                                   product.get('expiry_date'), 
                                   product.get('section'))
            stock_value = (product.get('quantity', 0) or 0) * (product.get('purchase_price', 0) or 0)
            
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

# Dashboard KPI Export
@api_router.get("/export/dashboard/excel")
async def export_dashboard_excel(
    current_user: User = Depends(get_current_user)
):
    """Export dashboard KPIs to Excel"""
    try:
        import xlsxwriter
        from io import BytesIO
        
        # Get dashboard data
        dashboard_data = await generate_dashboard_data(current_user)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'bg_color': '#4F81BD',
            'color': 'white'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center'
        })
        
        # KPIs Sheet
        kpi_sheet = workbook.add_worksheet('KPI Summary')
        kpi_sheet.merge_range('A1:G1', 'Geant Hypermarket - KPI Dashboard Export', title_format)
        kpi_sheet.write('A2', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # KPI Headers
        kpi_headers = ['Department', 'Total Items', 'Out of Stock', 'Low Stock', 'Near Expiry', 'Expired', 'Stock Value (YER)']
        for col, header in enumerate(kpi_headers):
            kpi_sheet.write(3, col, header, header_format)
        
        # KPI Data
        for row, kpi in enumerate(dashboard_data['kpis'], start=4):
            kpi_sheet.write(row, 0, kpi['department'], cell_format)
            kpi_sheet.write(row, 1, kpi['total_items'], cell_format)
            kpi_sheet.write(row, 2, kpi['out_of_stock_items'], cell_format)
            kpi_sheet.write(row, 3, kpi['low_stock_items'], cell_format)
            kpi_sheet.write(row, 4, kpi['near_expiry_items'], cell_format)
            kpi_sheet.write(row, 5, kpi['expired_items'], cell_format)
            kpi_sheet.write(row, 6, f"{kpi['total_stock_value']:.2f}", cell_format)
        
        # Suppliers Sheet  
        supplier_sheet = workbook.add_worksheet('Top Suppliers')
        supplier_sheet.merge_range('A1:E1', 'Top Suppliers Report', title_format)
        
        supplier_headers = ['Supplier', 'Total Items', 'Out of Stock', 'Stock Value', 'Currency']
        for col, header in enumerate(supplier_headers):
            supplier_sheet.write(2, col, header, header_format)
        
        for row, supplier in enumerate(dashboard_data['top_suppliers'], start=3):
            supplier_sheet.write(row, 0, supplier['supplier_name'], cell_format)
            supplier_sheet.write(row, 1, supplier['total_items'], cell_format)
            supplier_sheet.write(row, 2, supplier['out_of_stock_items'], cell_format)
            supplier_sheet.write(row, 3, f"{supplier['stock_value']:.2f}", cell_format)
            supplier_sheet.write(row, 4, supplier['purchase_currency'], cell_format)
        
        # Auto-adjust column widths
        kpi_sheet.set_column('A:G', 15)
        supplier_sheet.set_column('A:E', 15)
        
        workbook.close()
        output.seek(0)
        
        filename = f"dashboard_kpi_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard export: {str(e)}")

# Dashboard KPI PDF Export
@api_router.get("/export/dashboard/pdf")
async def export_dashboard_pdf(
    current_user: User = Depends(get_current_user)
):
    """Export dashboard KPIs to PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get dashboard data
        dashboard_data = await generate_dashboard_data(current_user)
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1  # Center
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Geant Hypermarket - KPI Dashboard Report", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Generated by: {current_user.full_name or current_user.username}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # KPI Table
        story.append(Paragraph("Department KPI Summary", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        kpi_data = [['Department', 'Total Items', 'Out of Stock', 'Low Stock', 'Near Expiry', 'Stock Value']]
        for kpi in dashboard_data['kpis']:
            kpi_data.append([
                kpi['department'],
                str(kpi['total_items']),
                str(kpi['out_of_stock_items']),
                str(kpi['low_stock_items']),
                str(kpi['near_expiry_items']),
                f"{kpi['total_stock_value']:.2f} YER"
            ])
        
        kpi_table = Table(kpi_data)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(kpi_table)
        story.append(Spacer(1, 20))
        
        # Top Suppliers Table
        story.append(Paragraph("Top Suppliers", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        supplier_data = [['Supplier', 'Total Items', 'Out of Stock', 'Stock Value', 'Currency']]
        for supplier in dashboard_data['top_suppliers'][:10]:  # Top 10
            supplier_data.append([
                supplier['supplier_name'][:30] + '...' if len(supplier['supplier_name']) > 30 else supplier['supplier_name'],
                str(supplier['total_items']),
                str(supplier['out_of_stock_items']),
                f"{supplier['stock_value']:.2f}",
                supplier['purchase_currency']
            ])
        
        supplier_table = Table(supplier_data)
        supplier_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(supplier_table)
        
        doc.build(story)
        output.seek(0)
        
        filename = f"dashboard_kpi_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        return Response(
            content=output.getvalue(),
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")

# Expiry Tracker Export
@api_router.post("/export/expiry-tracker")
async def export_expiry_tracker_data(
    current_user: User = Depends(get_current_user)
):
    """Export expiry tracker data with enhanced formatting (original currency only)"""
    try:
        from enhanced_export_system import EnhancedOtherReportsExporter
        
        # Get products with expiry data
        products = []
        async for product in db.products.find({}):
            if product.get('expiry_date'):
                products.append(product)
        
        # Use enhanced exporter
        exporter = EnhancedOtherReportsExporter(db)
        excel_data = await exporter.generate_expiry_tracker_excel(products)
        
        filename = f"expiry_tracker_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Enhanced expiry tracker export failed: {e}")
        # Fallback to original implementation
        import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Get company branding
        branding = get_company_branding()
        
        worksheet = workbook.add_worksheet('Expiry Tracker')
        
        # Define formats with company colors
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': branding['excel_header_color'],
            'border': 1,
            'align': 'center'
        })
        
        company_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': branding['excel_header_color'],
            'align': 'center'
        })
        
        # Company header
        worksheet.merge_range('A1:G1', branding['company_name'], company_format)
        worksheet.merge_range('A2:G2', 'EXPIRY TRACKER REPORT', header_format)
        
        # Headers  
        headers = [
            'Product Name', 'Department', 'Expiry Date', 'Days Until Expiry',
            'Quantity', 'Value (Original Currency)', 'Status'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Get and process products
        row = 4
        async for product in db.products.find({}):
            if product.get('expiry_date'):
                # Calculate value in original currency
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
                
                worksheet.write(row, 0, product.get('product_name', ''))
                worksheet.write(row, 1, product.get('department', ''))
                worksheet.write(row, 2, product.get('expiry_date', 'N/A'))
                worksheet.write(row, 3, days_until_expiry)
                worksheet.write(row, 4, product.get('quantity', 0))
                worksheet.write(row, 5, f"{value:,.2f} {currency}")
                worksheet.write(row, 6, product.get('status', 'Unknown'))
                
                row += 1
        
        workbook.close()
        output.seek(0)
        
        filename = f"expiry_tracker_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating expiry tracker export: {str(e)}")

# Return Forms Export
@api_router.get("/export/return-form/{form_id}")
async def export_return_form_with_approvals(
    form_id: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user)
):
    """Export return form with enhanced approvals and signatures"""
    try:
        # Get return form data
        return_form = await db.return_forms.find_one({"id": form_id})
        if not return_form:
            raise HTTPException(status_code=404, detail="Return form not found")
        
        # Check approval requirements
        if not return_form.get("supervisor_approved") or not return_form.get("section_manager_approved"):
            raise HTTPException(
                status_code=400, 
                detail="Both Supervisor and Section Manager approvals required before export"
            )
        
        if format.lower() == "pdf":
            return await generate_enhanced_return_form_pdf(return_form)
        elif format.lower() == "excel":
            return await generate_enhanced_return_form_excel(return_form)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'excel'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

async def generate_enhanced_return_form_pdf(return_form: dict):
    """Generate enhanced PDF with approvals, signatures and proper formatting"""
    try:
        import io
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Get company branding
        branding = get_company_branding()
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.Color(*branding['pdf_primary_color']),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.Color(*branding['pdf_secondary_color']),
            fontName='Helvetica-Bold'
        )
        
        normal_style = styles['Normal']
        
        # Build story
        story = []
        
        # Add company logo
        try:
            if os.path.exists('/app/frontend/public/geant-logo.jpeg'):
                logo = Image('/app/frontend/public/geant-logo.jpeg', width=1*inch, height=1*inch)
                story.append(logo)
                story.append(Spacer(1, 12))
        except:
            # Add company name if logo fails
            story.append(Paragraph(branding['company_name'], title_style))
        
        # Title and reference
        story.append(Paragraph("SUPPLIER RETURN FORM", title_style))
        story.append(Spacer(1, 20))
        
        # Form header information
        header_data = [
            ["Reference Number:", return_form.get('reference_number', 'N/A')],
            ["Return Date:", return_form.get('return_date', 'N/A')],
            ["Prepared by:", return_form.get('prepared_by_supervisor', 'N/A')]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Product details section
        story.append(Paragraph("Product Information", subtitle_style))
        
        # Calculate USD value
        try:
            # Get current exchange rates
            rates_response = await fetch_current_exchange_rates()
            rates = rates_response.get('exchange_rates', {'YER': 0.004, 'SAR': 0.267, 'EUR': 1.10, 'USD': 1.0})
            
            price = float(return_form.get('purchase_price', 0))
            quantity = float(return_form.get('quantity', 0))
            currency = return_form.get('purchase_currency', 'YER')
            rate = rates.get(currency, 1.0)
            
            total_original = price * quantity
            total_usd = total_original * rate
        except:
            total_original = 0
            total_usd = 0
            currency = return_form.get('purchase_currency', 'YER')
        
        product_data = [
            ["Product Code:", return_form.get('product_code', 'N/A')],
            ["Product Name:", return_form.get('product_name', 'N/A')],
            ["Barcode:", return_form.get('barcode', 'N/A')],
            ["Supplier:", return_form.get('supplier', 'N/A')],
            ["Quantity:", return_form.get('quantity', 'N/A')],
            ["Purchase Price:", f"{return_form.get('purchase_price', 0)} {currency}"],
            ["Total Value:", f"{total_original:.2f} {currency}"],
            ["USD Equivalent:", f"${total_usd:.2f} USD"],
            ["Reason for Return:", return_form.get('reason_for_return', 'N/A')],
        ]
        
        product_table = Table(product_data, colWidths=[2*inch, 4*inch])
        product_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
            # Highlight USD value
            ('TEXTCOLOR', (1, -2), (1, -1), colors.Color(0.8, 0.2, 0.2)),
            ('FONTNAME', (1, -2), (1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(product_table)
        story.append(Spacer(1, 30))
        
        # Enhanced Approvals & Signatures Section
        story.append(Paragraph("Approvals & Signatures", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Digital signatures with timestamps
        approval_data = [
            ["Role", "Name", "Digital Signature", "Timestamp"],
            [
                "Prepared by Supervisor",
                return_form.get('prepared_by_supervisor', 'N/A'),
                return_form.get('supervisor_signature', 'N/A'),
                return_form.get('supervisor_timestamp', 'N/A')
            ],
            [
                "Section Manager",
                return_form.get('section_manager_name', 'N/A'),
                return_form.get('section_manager_signature', 'N/A'),
                return_form.get('section_manager_timestamp', 'N/A')
            ]
        ]
        
        approval_table = Table(approval_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
        approval_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*branding['pdf_primary_color'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Highlight timestamps
            ('TEXTCOLOR', (3, 1), (3, -1), colors.Color(0.2, 0.6, 0.2)),
            ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(approval_table)
        story.append(Spacer(1, 20))
        
        # Manual signature lines (empty for manual signing after printing)
        story.append(Paragraph("Manual Signatures (to be signed after printing)", subtitle_style))
        
        manual_sig_data = [
            ["Department Head", "", "Finance Department", ""],
            ["", "", "", ""],
            ["Signature: ____________________", "Date: __________", "Signature: ____________________", "Date: __________"],
            ["", "", "", ""],
            ["Print Name: ____________________", "", "Print Name: ____________________", ""],
        ]
        
        manual_table = Table(manual_sig_data, colWidths=[2.5*inch, 1*inch, 2.5*inch, 1*inch])
        manual_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ]))
        
        story.append(manual_table)
        story.append(Spacer(1, 20))
        
        # Footer note
        footer_text = f"Generated on {datetime.now().strftime('%d/%m/%Y – %H:%M')} | Export authorized after required approvals"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        filename = f"return_form_{return_form.get('reference_number', 'unknown')}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

async def generate_enhanced_return_form_excel(return_form: dict):
    """Generate enhanced Excel with approvals, signatures and proper formatting"""
    try:
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Return Form"
        
        # Get company branding
        branding = get_company_branding()
        
        # Styles
        header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color=branding['excel_header_color'], end_color=branding['excel_header_color'], fill_type='solid')
        subheader_font = Font(name='Arial', size=12, bold=True, color=branding['excel_header_color'])
        company_font = Font(name='Arial', size=16, bold=True, color=branding['excel_header_color'])
        signature_font = Font(name='Arial', size=10, bold=True, color='008000')  # Green for timestamps
        border = Border(
            left=Side(border_style='thin'),
            right=Side(border_style='thin'),
            top=Side(border_style='thin'),
            bottom=Side(border_style='thin')
        )
        
        current_row = 1
        
        # Add logo placeholder
        ws.merge_cells(f'A{current_row}:B{current_row + 2}')
        ws[f'A{current_row}'] = "LOGO"
        ws[f'A{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
        
        # Company header
        ws.merge_cells(f'C{current_row}:F{current_row}')
        ws[f'C{current_row}'] = branding['company_name']
        ws[f'C{current_row}'].font = company_font
        ws[f'C{current_row}'].alignment = Alignment(horizontal='center')
        
        current_row += 1
        ws.merge_cells(f'C{current_row}:F{current_row}')
        ws[f'C{current_row}'] = "SUPPLIER RETURN FORM"
        ws[f'C{current_row}'].font = header_font
        ws[f'C{current_row}'].fill = header_fill
        ws[f'C{current_row}'].alignment = Alignment(horizontal='center')
        
        current_row += 3
        
        # Form information
        ws[f'A{current_row}'] = "Reference Number:"
        ws[f'B{current_row}'] = return_form.get('reference_number', 'N/A')
        ws[f'A{current_row}'].font = subheader_font
        
        current_row += 1
        ws[f'A{current_row}'] = "Return Date:"
        ws[f'B{current_row}'] = return_form.get('return_date', 'N/A')
        ws[f'A{current_row}'].font = subheader_font
        
        current_row += 1
        ws[f'A{current_row}'] = "Prepared by:"
        ws[f'B{current_row}'] = return_form.get('prepared_by_supervisor', 'N/A')
        ws[f'A{current_row}'].font = subheader_font
        
        current_row += 3
        
        # Product Information
        ws.merge_cells(f'A{current_row}:F{current_row}')
        ws[f'A{current_row}'] = "PRODUCT INFORMATION"
        ws[f'A{current_row}'].font = header_font
        ws[f'A{current_row}'].fill = header_fill
        ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
        
        current_row += 1
        
        # Product details
        product_fields = [
            ("Product Code:", return_form.get('product_code', 'N/A')),
            ("Product Name:", return_form.get('product_name', 'N/A')),
            ("Barcode:", return_form.get('barcode', 'N/A')),
            ("Supplier:", return_form.get('supplier', 'N/A')),
            ("Quantity:", return_form.get('quantity', 'N/A')),
            ("Purchase Price:", f"{return_form.get('purchase_price', 0)} {return_form.get('purchase_currency', 'YER')}"),
            ("Reason for Return:", return_form.get('reason_for_return', 'N/A')),
        ]
        
        # Calculate USD value
        try:
            rates_response = await fetch_current_exchange_rates()
            rates = rates_response.get('exchange_rates', {'YER': 0.004, 'SAR': 0.267, 'EUR': 1.10, 'USD': 1.0})
            
            price = float(return_form.get('purchase_price', 0))
            quantity = float(return_form.get('quantity', 0))
            currency = return_form.get('purchase_currency', 'YER')
            rate = rates.get(currency, 1.0)
            
            total_original = price * quantity
            total_usd = total_original * rate
            
            product_fields.append(("Total Value (Original):", f"{total_original:.2f} {currency}"))
            product_fields.append(("Total Value (USD):", f"${total_usd:.2f} USD"))
        except:
            product_fields.append(("Total Value:", f"{return_form.get('total_value', '0.00')} {return_form.get('purchase_currency', 'YER')}"))
        
        for label, value in product_fields:
            ws[f'A{current_row}'] = label
            ws[f'B{current_row}'] = value
            ws[f'A{current_row}'].font = subheader_font
            current_row += 1
        
        current_row += 2
        
        # Enhanced Approvals & Signatures
        ws.merge_cells(f'A{current_row}:F{current_row}')
        ws[f'A{current_row}'] = "APPROVALS & SIGNATURES"
        ws[f'A{current_row}'].font = header_font
        ws[f'A{current_row}'].fill = header_fill
        ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
        
        current_row += 2
        
        # Digital signatures with timestamps
        digital_approvals = [
            ("Prepared by Supervisor", return_form.get('prepared_by_supervisor', 'N/A'), 
             return_form.get('supervisor_signature', 'N/A'), return_form.get('supervisor_timestamp', 'N/A')),
            ("Section Manager", return_form.get('section_manager_name', 'N/A'), 
             return_form.get('section_manager_signature', 'N/A'), return_form.get('section_manager_timestamp', 'N/A')),
        ]
        
        # Headers
        ws[f'A{current_row}'] = "Role"
        ws[f'B{current_row}'] = "Name"
        ws[f'C{current_row}'] = "Digital Signature"
        ws[f'D{current_row}'] = "Timestamp"
        
        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{current_row}'].font = header_font
            ws[f'{col}{current_row}'].fill = header_fill
        
        current_row += 1
        
        for role, name, signature, timestamp in digital_approvals:
            ws[f'A{current_row}'] = role
            ws[f'B{current_row}'] = name
            ws[f'C{current_row}'] = signature
            ws[f'D{current_row}'] = timestamp
            ws[f'D{current_row}'].font = signature_font  # Green timestamp
            current_row += 1
        
        current_row += 2
        
        # Manual signature section
        ws.merge_cells(f'A{current_row}:F{current_row}')
        ws[f'A{current_row}'] = "MANUAL SIGNATURES (To be signed after printing)"
        ws[f'A{current_row}'].font = subheader_font
        
        current_row += 2
        
        # Manual signature table
        ws[f'A{current_row}'] = "Department Head"
        ws[f'D{current_row}'] = "Finance Department"
        
        current_row += 2
        ws[f'A{current_row}'] = "Signature: ____________________"
        ws[f'B{current_row}'] = "Date: __________"
        ws[f'D{current_row}'] = "Signature: ____________________"
        ws[f'E{current_row}'] = "Date: __________"
        
        current_row += 2
        ws[f'A{current_row}'] = "Print Name: ____________________"
        ws[f'D{current_row}'] = "Print Name: ____________________"
        
        # Apply borders
        for row_num in range(1, current_row + 1):
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                cell = ws[f'{col}{row_num}']
                if cell.value:
                    cell.border = border
        
        # Auto-adjust columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = max(adjusted_width, 12)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"return_form_{return_form.get('reference_number', 'unknown')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Excel generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

async def fetch_current_exchange_rates():
    """Helper function to get current exchange rates"""
    try:
        settings = await db.currency_settings.find_one(
            {"is_active": True}, 
            sort=[("last_updated", -1)]
        )
        
        if settings and "exchange_rates" in settings:
            return {
                "base_currency": settings["base_currency"],
                "exchange_rates": settings["exchange_rates"]
            }
    except Exception:
        pass
    
    # Fallback rates
    return {
        "base_currency": "USD",
        "exchange_rates": {
            "YER": 0.004,
            "SAR": 0.267,
            "EUR": 1.10,
            "USD": 1.0
        }
    }

# Return Form PDF Export (Individual)
@api_router.get("/export/return-form/{return_id}/pdf")
async def export_return_form_pdf(
    return_id: str,
    current_user: User = Depends(get_current_user)
):
    """Export individual return form as PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        # Get return form from database
        return_form = await db.return_forms.find_one({"id": return_id})
        if not return_form:
            raise HTTPException(status_code=404, detail="Return form not found")
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        story = []
        
        # Get company branding
        branding = get_company_branding()
        
        # Define title style with company colors
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.Color(*branding['pdf_primary_color']),
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        # Add company logo and header using helper function
        add_logo_to_pdf_story(story)
        
        # Document title
        story.append(Paragraph("PRODUCT RETURN FORM", title_style))
        story.append(Spacer(1, 20))
        
        # Reference info
        ref_data = [
            ['Reference Number:', return_form.get('reference_number', '')],
            ['Return Date:', return_form.get('return_date', '')],
            ['Status:', return_form.get('status', 'pending').upper()]
        ]
        
        ref_table = Table(ref_data, colWidths=[2*inch, 3*inch])
        ref_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(*branding['pdf_accent_color'])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ]))
        
        story.append(ref_table)
        story.append(Spacer(1, 20))
        
        # Item details
        story.append(Paragraph("Item Details", styles['Heading3']))
        item_data = [
            ['Product Code:', return_form.get('product_code', '')],
            ['Product Name:', return_form.get('product_name', '')],
            ['Product Barcode:', return_form.get('barcode', '') or 'N/A'],  # Added barcode field
            ['Quantity:', str(return_form.get('quantity', 0))],
            ['Purchase Price:', f"{return_form.get('purchase_price', 0)} {return_form.get('purchase_currency', 'YER')}"],
            ['Total Value:', f"{return_form.get('total_value', '0.00')} {return_form.get('purchase_currency', 'YER')}"],  # Added total value
            ['Supplier:', return_form.get('supplier', '')],
            ['Reason for Return:', return_form.get('reason_for_return', '')]
        ]
        
        item_table = Table(item_data, colWidths=[2*inch, 4*inch])
        item_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(*branding['pdf_accent_color'])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(*branding['pdf_primary_color']))
        ]))
        
        story.append(item_table)
        story.append(Spacer(1, 30))
        
        # Signatures
        story.append(Paragraph("Approvals & Signatures", styles['Heading3']))
        
        sig_data = [
            ['Prepared by Supervisor:', return_form.get('prepared_by_supervisor', ''), 'Signature: _______________'],
            ['Section Manager:', return_form.get('section_manager_name', ''), 'Signature: _______________'],
            ['Department Head:', return_form.get('department_head_name', ''), 'Signature: _______________'],
            ['Finance Department:', '', 'Signature: _______________']
        ]
        
        sig_table = Table(sig_data, colWidths=[2*inch, 2*inch, 2*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(*branding['pdf_accent_color'])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(*branding['pdf_primary_color'])),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.97, 0.95)])
        ]))
        
        story.append(sig_table)
        
        # Notes
        if return_form.get('notes'):
            story.append(Spacer(1, 20))
            story.append(Paragraph("Additional Notes", styles['Heading3']))
            story.append(Paragraph(return_form.get('notes', ''), styles['Normal']))
        
        doc.build(story)
        output.seek(0)
        
        filename = f"return_form_{return_form.get('reference_number', return_id)}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        from fastapi.responses import Response
        
        return Response(
            content=output.getvalue(),
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating return form PDF: {str(e)}")

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
    # Ensure timezone is set to Asia/Aden and alert time is 07:00 as requested
    settings.timezone = "Asia/Aden"
    settings.daily_alert_time = "07:00"
    settings.updated_at = datetime.now(pytz.timezone('Asia/Aden'))
    
    await db.email_settings.replace_one({}, settings.dict(), upsert=True)
    return {
        "message": "Email settings updated successfully",
        "timezone": settings.timezone,
        "daily_alert_time": settings.daily_alert_time,
        "aden_time_now": datetime.now(pytz.timezone('Asia/Aden')).strftime('%Y-%m-%d %H:%M:%S %Z')
    }

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

# =============================================================================
# WASTE MANAGEMENT API ENDPOINTS
# =============================================================================

@api_router.post("/waste/entries")
async def create_waste_entry(waste_data: WasteEntryCreate, current_user: User = Depends(get_current_user)):
    """Create a new waste entry for damaged/unsellable products"""
    try:
        # Get product details from database
        product = await db.products.find_one({"id": waste_data.product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Calculate total waste value
        total_waste_value = float(waste_data.quantity_wasted) * float(product.get('purchase_price', 0))
        
        # Create waste entry
        waste_entry = {
            "id": str(uuid.uuid4()),
            "product_id": waste_data.product_id,
            "product_name": product.get('product_name', ''),
            "item_number": product.get('item_number'),
            "barcode": product.get('barcode'),
            "department": product.get('department'),
            "section": product.get('section'),
            "supplier": product.get('supplier', ''),
            "quantity_wasted": waste_data.quantity_wasted,
            "purchase_price": float(product.get('purchase_price', 0)),
            "purchase_currency": product.get('purchase_currency', 'YER'),
            "total_waste_value": total_waste_value,
            "waste_reason": waste_data.waste_reason,
            "notes": waste_data.notes,
            "reported_by": current_user.username,
            "approved_by": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None
        }
        
        # Insert into database
        result = await db.waste_entries.insert_one(waste_entry)
        
        return {"message": "Waste entry created successfully", "id": waste_entry["id"]}
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create waste entry: {str(e)}")

@api_router.get("/waste/reports")
async def get_waste_reports(
    period: str = "daily",  # daily, weekly, yearly
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get waste reports with currency breakdown (YER, SAR, EUR)"""
    try:
        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        elif period == "daily":
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "weekly":
            # Get start of current week (Monday)
            days_since_monday = now.weekday()
            start_dt = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = (start_dt + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "yearly":
            start_dt = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Use 'daily', 'weekly', or 'yearly'")
        
        # Build query filter
        query = {
            "created_at": {
                "$gte": start_dt.isoformat(),
                "$lte": end_dt.isoformat()
            }
        }
        
        if department:
            query["department"] = department
        if section:
            query["section"] = section
        
        # Get waste entries from database
        waste_entries = await db.waste_entries.find(query).to_list(length=None)
        
        # Calculate currency totals
        currency_totals = {"YER": 0.0, "SAR": 0.0, "EUR": 0.0}
        total_entries = len(waste_entries)
        total_quantity_wasted = 0
        
        for entry in waste_entries:
            currency = entry.get('purchase_currency', 'YER')
            waste_value = float(entry.get('total_waste_value', 0))
            
            if currency in currency_totals:
                currency_totals[currency] += waste_value
            
            total_quantity_wasted += int(entry.get('quantity_wasted', 0))
        
        # Prepare report data
        report_data = {
            "report_period": period,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "department": department,
            "section": section,
            "currency_totals": currency_totals,
            "total_entries": total_entries,
            "total_quantity_wasted": total_quantity_wasted,
            "generated_at": now.isoformat()
        }
        
        return report_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate waste report: {str(e)}")

@api_router.get("/waste/entries")
async def get_waste_entries(
    skip: int = 0,
    limit: int = 50,
    department: Optional[str] = None,
    section: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get waste entries with pagination and filtering"""
    try:
        query = {}
        
        if department:
            query["department"] = department
        if section:
            query["section"] = section
        
        # Get total count
        total_count = await db.waste_entries.count_documents(query)
        
        # Get waste entries with pagination
        waste_entries_cursor = db.waste_entries.find(query).skip(skip).limit(limit).sort([("created_at", -1)])
        waste_entries = []
        
        async for entry in waste_entries_cursor:
            # Clean ObjectId fields for JSON serialization
            if '_id' in entry:
                del entry['_id']
            
            # Handle datetime objects
            for key, value in list(entry.items()):
                if isinstance(value, datetime):
                    entry[key] = value.isoformat()
            
            waste_entries.append(entry)
        
        return {
            "waste_entries": waste_entries,
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get waste entries: {str(e)}")

@api_router.get("/export/waste-report/{period}")
async def export_waste_report(
    period: str,
    format: str = "excel",  # excel or pdf
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[str] = None,
    section: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export waste report to Excel or PDF"""
    try:
        # Get report data
        report_data = await get_waste_reports(
            period=period,
            start_date=start_date,
            end_date=end_date,
            department=department,
            section=section,
            current_user=current_user
        )
        
        if format.lower() == "excel":
            return await generate_waste_report_excel(report_data, period)
        elif format.lower() == "pdf":
            return await generate_waste_report_pdf(report_data, period)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'excel' or 'pdf'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export waste report: {str(e)}")

# =============================================================================
# REPORT BRANDING HELPER FUNCTIONS
# =============================================================================

def get_company_branding():
    """Get consistent company branding for all reports"""
    return {
        'company_name': 'GEANT HYPERMARKET',
        'logo_path': '/app/backend/geant-logo.jpeg',
        'primary_color': '#1B4332',  # Dark green
        'secondary_color': '#2D6A4F',  # Medium green  
        'accent_color': '#40916C',  # Light green
        'text_color': '#081C15',  # Dark text
        'background_color': '#F8F9FA',  # Light background
        'excel_header_color': '1B4332',  # Excel hex without #
        'pdf_primary_color': (0.106, 0.263, 0.196),  # RGB for ReportLab (27,67,50)
        'pdf_secondary_color': (0.176, 0.416, 0.310),  # RGB for ReportLab (45,106,79)
        'pdf_accent_color': (0.251, 0.569, 0.424)  # RGB for ReportLab (64,145,108)
    }

def add_logo_to_excel(worksheet, row=1, col=1):
    """Add company logo to Excel worksheet"""
    try:
        from openpyxl.drawing import image
        import os
        
        branding = get_company_branding()
        if os.path.exists(branding['logo_path']):
            # Add logo
            logo = image.Image(branding['logo_path'])
            logo.width = 60  # Resize logo
            logo.height = 60
            
            # Position logo
            cell = worksheet.cell(row=row, column=col)
            worksheet.add_image(logo, cell.coordinate)
            
            # Add extra rows for logo space
            for i in range(3):
                worksheet.row_dimensions[row + i].height = 25
                
            return True
    except Exception as e:
        print(f"Could not add logo to Excel: {str(e)}")
        return False
    
    return False

def add_logo_to_pdf_story(story):
    """Add company logo to PDF story array"""
    try:
        from reportlab.platypus import Image, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import os
        
        branding = get_company_branding()
        styles = getSampleStyleSheet()
        
        if os.path.exists(branding['logo_path']):
            # Create logo image
            logo_img = Image(branding['logo_path'], width=1.2*inch, height=1.2*inch)
            
            # Create company header with logo
            from reportlab.lib.styles import ParagraphStyle
            company_style = ParagraphStyle(
                'CompanyHeader',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.Color(*branding['pdf_primary_color']),
                alignment=1,  # Center
                fontName='Helvetica-Bold'
            )
            
            # Header table with logo and company name
            header_data = [
                [logo_img, Paragraph(branding['company_name'], company_style)]
            ]
            
            header_table = Table(header_data, colWidths=[1.5*inch, 5*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            story.append(header_table)
            return True
            
    except Exception as e:
        print(f"Could not add logo to PDF: {str(e)}")
        # Fallback to text header
        try:
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib import colors
            
            branding = get_company_branding()
            styles = getSampleStyleSheet()
            
            fallback_style = ParagraphStyle(
                'CompanyFallback',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.Color(*branding['pdf_primary_color']),
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph(branding['company_name'], fallback_style))
            return True
        except:
            return False
    
    return False

async def generate_waste_report_excel(report_data: dict, period: str):
    """Generate Excel waste report with enhanced formatting and USD conversion"""
    try:
        from enhanced_export_system import EnhancedWasteReportExporter
        
        exporter = EnhancedWasteReportExporter(db)
        excel_data = await exporter.generate_excel(report_data, period)
        
        filename = f"waste_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Error in enhanced waste report export: {e}")
        # Fallback to original implementation if enhanced fails
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = f"Waste Report - {period.title()}"
        
        # Get company branding
        branding = get_company_branding()
        
        # Define styles with company colors
        header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color=branding['excel_header_color'], end_color=branding['excel_header_color'], fill_type='solid')
        subheader_font = Font(name='Arial', size=12, bold=True, color=branding['excel_header_color'])
        currency_font = Font(name='Arial', size=12, bold=True, color='D32F2F')
        company_font = Font(name='Arial', size=16, bold=True, color=branding['excel_header_color'])
        border = Border(
            left=Side(border_style='thin'),
            right=Side(border_style='thin'),
            top=Side(border_style='thin'),
            bottom=Side(border_style='thin')
        )
        
        # Add company logo (will add extra rows if successful)
        logo_added = add_logo_to_excel(ws, row=1, col=1)
        start_row = 4 if logo_added else 1
        
        # Company header
        if logo_added:
            ws.merge_cells(f'B1:F1')
            ws['B1'] = branding['company_name']
            ws['B1'].font = company_font
            ws['B1'].alignment = Alignment(horizontal='center', vertical='center')
            
            ws.merge_cells(f'B2:F2')
            ws['B2'] = f"WASTE REPORT - {period.upper()}"
            ws['B2'].font = header_font
            ws['B2'].fill = header_fill
            ws['B2'].alignment = Alignment(horizontal='center', vertical='center')
        else:
            # Fallback without logo
            ws.merge_cells(f'A{start_row}:F{start_row}')
            ws[f'A{start_row}'] = f"{branding['company_name']} - WASTE REPORT ({period.upper()})"
            ws[f'A{start_row}'].font = header_font
            ws[f'A{start_row}'].fill = header_fill
            ws[f'A{start_row}'].alignment = Alignment(horizontal='center')
            start_row += 1
        
        # Report details
        row = start_row + 2
        ws[f'A{row}'] = "Report Period:"
        ws[f'B{row}'] = period.title()
        ws[f'A{row}'].font = subheader_font
        
        row += 1
        ws[f'A{row}'] = "Generated At:"
        ws[f'B{row}'] = datetime.fromisoformat(report_data['generated_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        
        if report_data.get('department'):
            row += 1
            ws[f'A{row}'] = "Department:"
            ws[f'B{row}'] = report_data['department']
        
        if report_data.get('section'):
            row += 1
            ws[f'A{row}'] = "Section:"
            ws[f'B{row}'] = report_data['section']
        
        # Currency totals with USD conversion
        row += 3
        ws[f'A{row}'] = "WASTE VALUE BY CURRENCY (WITH USD CONVERSION)"
        ws[f'A{row}'].font = subheader_font
        
        row += 1
        ws[f'A{row}'] = "Currency"
        ws[f'B{row}'] = "Original Amount"
        ws[f'C{row}'] = "USD Equivalent"
        ws[f'D{row}'] = "Exchange Rate"
        
        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{row}'].font = header_font
            ws[f'{col}{row}'].fill = header_fill
        
        # Exchange rates
        exchange_rates = {'YER': 0.004, 'SAR': 0.267, 'EUR': 1.10, 'USD': 1.0}
        total_usd = 0
        
        for currency, total in report_data['currency_totals'].items():
            if total > 0:  # Only show currencies with waste
                row += 1
                rate = exchange_rates.get(currency, 1.0)
                usd_amount = total * rate
                total_usd += usd_amount
                
                ws[f'A{row}'] = currency
                ws[f'B{row}'] = f"{total:,.2f} {currency}"
                ws[f'C{row}'] = f"{usd_amount:,.2f} USD"
                ws[f'D{row}'] = f"{rate:.4f}"
                
                ws[f'B{row}'].font = currency_font
                ws[f'C{row}'].font = currency_font
        
        # Total USD row
        if len(report_data['currency_totals']) > 1:
            row += 1
            ws[f'A{row}'] = "TOTAL"
            ws[f'B{row}'] = ""
            ws[f'C{row}'] = f"{total_usd:,.2f} USD"
            ws[f'D{row}'] = ""
            ws[f'A{row}'].font = header_font
            ws[f'C{row}'].font = header_font
        
        # Summary
        row += 3
        ws[f'A{row}'] = "SUMMARY"
        ws[f'A{row}'].font = subheader_font
        
        row += 1
        ws[f'A{row}'] = "Total Waste Entries:"
        ws[f'B{row}'] = report_data['total_entries']
        
        row += 1
        ws[f'A{row}'] = "Total Quantity Wasted:"
        ws[f'B{row}'] = report_data['total_quantity_wasted']
        
        # Apply borders
        for row_num in range(1, row + 1):
            for col in ['A', 'B', 'C', 'D']:
                cell = ws[f'{col}{row_num}']
                if cell.value:
                    cell.border = border
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = None
            
            # Find the first non-merged cell to get column letter
            for cell in column:
                try:
                    if hasattr(cell, 'column_letter'):
                        column_letter = cell.column_letter
                        break
                except:
                    continue
            
            if column_letter:
                # Calculate max length
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and cell.value:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to response
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"waste_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

async def generate_waste_report_pdf(report_data: dict, period: str):
    """Generate enhanced PDF waste report with USD conversion and error handling"""
    try:
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = io.BytesIO()
        
        # Create PDF document with proper margins
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=72, 
            leftMargin=72, 
            topMargin=72, 
            bottomMargin=72
        )
        styles = getSampleStyleSheet()
        
        # Get company branding
        branding = get_company_branding()
        
        # Custom styles with company colors
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.Color(*branding['pdf_primary_color']),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.Color(*branding['pdf_secondary_color']),
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica'
        )
        
        # Build story
        story = []
        
        # Company header
        story.append(Paragraph(branding['company_name'], title_style))
        story.append(Paragraph(f"WASTE REPORT - {period.upper()}", title_style))
        story.append(Spacer(1, 30))
        
        # Report metadata
        story.append(Paragraph("Report Details", subtitle_style))
        
        # Safe date handling
        try:
            if report_data.get('generated_at'):
                generated_time = datetime.fromisoformat(report_data['generated_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y – %H:%M')
            else:
                generated_time = datetime.now().strftime('%d/%m/%Y – %H:%M')
        except:
            generated_time = datetime.now().strftime('%d/%m/%Y – %H:%M')
        
        metadata_data = [
            ["Report Period:", period.title()],
            ["Generated At:", generated_time],
            ["Report Type:", "Waste Management Analysis"]
        ]
        
        # Add optional filters
        if report_data.get('department') and report_data['department'] != 'all':
            metadata_data.append(["Department:", str(report_data['department'])])
        
        if report_data.get('section') and report_data['section'] != 'all':
            metadata_data.append(["Section:", str(report_data['section'])])
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.Color(*branding['pdf_primary_color'])),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Get current exchange rates with fallback
        try:
            rates_response = await fetch_current_exchange_rates()
            exchange_rates = rates_response.get('exchange_rates', {
                'YER': 0.004, 'SAR': 0.267, 'EUR': 1.10, 'USD': 1.0
            })
        except:
            exchange_rates = {'YER': 0.004, 'SAR': 0.267, 'EUR': 1.10, 'USD': 1.0}
        
        # Currency totals with USD conversion
        story.append(Paragraph("Waste Value by Currency (with USD Conversion)", subtitle_style))
        
        currency_data = [["Currency", "Original Amount", "USD Equivalent", "Exchange Rate"]]
        total_usd = 0
        
        # Safe handling of currency totals
        currency_totals = report_data.get('currency_totals', {})
        if not currency_totals:
            currency_totals = {'USD': 0}
        
        for currency, total in currency_totals.items():
            if total > 0:
                rate = exchange_rates.get(currency, 1.0)
                usd_amount = total * rate
                total_usd += usd_amount
                
                currency_data.append([
                    currency,
                    f"{total:,.2f} {currency}",
                    f"${usd_amount:,.2f} USD",
                    f"{rate:.4f}"
                ])
        
        # Add total USD row if multiple currencies
        if len(currency_totals) > 1:
            currency_data.append(["TOTAL", "", f"${total_usd:,.2f} USD", ""])
        
        currency_table = Table(currency_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
        currency_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*branding['pdf_primary_color'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Highlight USD values
            ('TEXTCOLOR', (2, 1), (2, -1), colors.Color(0.8, 0.2, 0.2)),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            
            # Total row styling
            ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(currency_table)
        story.append(Spacer(1, 30))
        
        # Summary statistics
        story.append(Paragraph("Report Summary", subtitle_style))
        
        summary_data = [
            ["Total Waste Entries:", str(report_data.get('total_entries', 0))],
            ["Total Quantity Wasted:", str(report_data.get('total_quantity_wasted', 0))],
            ["Total USD Value:", f"${total_usd:,.2f} USD"],
            ["Report Generated:", generated_time]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.Color(*branding['pdf_primary_color'])),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
            
            # Highlight USD total
            ('TEXTCOLOR', (1, -2), (1, -2), colors.Color(0.8, 0.2, 0.2)),
            ('FONTNAME', (1, -2), (1, -2), 'Helvetica-Bold'),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"Generated by {branding['company_name']} Inventory Management System | {generated_time}"
        story.append(Paragraph(footer_text, normal_style))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        filename = f"waste_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# =============================================================================
# SYSTEM RESET API ENDPOINT
# =============================================================================

@api_router.post("/system/reset")
async def reset_system_data(current_user: User = Depends(get_admin_user)):
    """Reset all system data to zero - ADMIN ONLY"""
    try:
        # Collections to clear
        collections_to_clear = [
            'products',
            'waste_entries', 
            'alerts',
            'return_forms'
        ]
        
        reset_summary = {
            'cleared_collections': {},
            'total_documents_deleted': 0,
            'reset_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Clear each collection and count deleted documents
        for collection_name in collections_to_clear:
            collection = getattr(db, collection_name)
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            
            # Delete all documents
            result = await collection.delete_many({})
            
            reset_summary['cleared_collections'][collection_name] = {
                'documents_before': count_before,
                'documents_deleted': result.deleted_count
            }
            
            reset_summary['total_documents_deleted'] += result.deleted_count
        
        # Reset any settings that might have cached data
        # Keep user accounts and email settings intact
        
        return {
            "message": "✅ SYSTEM RESET COMPLETED - All data cleared successfully",
            "reset_summary": reset_summary,
            "status": "success",
            "next_steps": [
                "Dashboard will show zero entries for all metrics",
                "All product, waste, alert, and return form data cleared",
                "User accounts and system settings preserved",
                "Ready for fresh data entry"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ System reset failed: {str(e)}")

@api_router.get("/system/status")
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get current system data counts"""
    try:
        status = {
            'data_counts': {},
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        # Count documents in each collection
        collections_to_check = ['products', 'waste_entries', 'alerts', 'return_forms', 'users']
        
        for collection_name in collections_to_check:
            collection = getattr(db, collection_name)
            count = await collection.count_documents({})
            status['data_counts'][collection_name] = count
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@api_router.post("/system/import-excel")
async def import_excel_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """Import product data from Excel file - ADMIN ONLY"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
        
        # Read Excel file
        content = await file.read()
        
        # Parse Excel with pandas
        try:
            # Try reading as xlsx first, then xls
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(content), engine='xlrd')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")
        
        # Validate required columns
        required_columns = [
            'product_name', 'department', 'section', 'family', 'sub_family', 
            'supplier', 'purchase_price', 'purchase_currency'
        ]
        
        # Check for required columns (case-insensitive)
        df_columns_lower = [col.lower().strip() for col in df.columns]
        missing_columns = []
        
        for req_col in required_columns:
            if req_col.lower() not in df_columns_lower:
                missing_columns.append(req_col)
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}. Required columns: {', '.join(required_columns)}"
            )
        
        # Normalize column names (lowercase and strip)
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Import statistics
        import_stats = {
            'total_rows': len(df),
            'successful_imports': 0,
            'failed_imports': 0,
            'errors': [],
            'imported_products': [],
            'skipped_rows': []
        }
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('product_name')) or str(row.get('product_name')).strip() == '':
                    import_stats['skipped_rows'].append(f"Row {index + 2}: Empty product name")
                    continue
                
                # Prepare product data
                product_data = {
                    'id': str(uuid.uuid4()),
                    'product_name': str(row.get('product_name', '')).strip(),
                    'item_number': str(row.get('item_number', '')).strip() if pd.notna(row.get('item_number')) else None,
                    'department': str(row.get('department', '')).strip(),
                    'section': str(row.get('section', '')).strip(),
                    'family': str(row.get('family', '')).strip(),
                    'sub_family': str(row.get('sub_family', '')).strip(),
                    'supplier_code': str(row.get('supplier_code', '')).strip() if pd.notna(row.get('supplier_code')) else None,
                    'supplier': str(row.get('supplier', '')).strip(),
                    'barcode': str(row.get('barcode', '')).strip() if pd.notna(row.get('barcode')) else None,
                    'purchase_price': float(row.get('purchase_price', 0)) if pd.notna(row.get('purchase_price')) else 0.0,
                    'purchase_currency': str(row.get('purchase_currency', 'YER')).strip().upper(),
                    'selling_price': float(row.get('selling_price', 0)) if pd.notna(row.get('selling_price')) else 0.0,
                    'quantity': int(row.get('quantity', 0)) if pd.notna(row.get('quantity')) else 0,
                    'low_stock_threshold': int(row.get('low_stock_threshold', 10)) if pd.notna(row.get('low_stock_threshold')) else 10,
                    'arabic_description': str(row.get('arabic_description', '')).strip() if pd.notna(row.get('arabic_description')) else None,
                    'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                    'location': str(row.get('location', '')).strip() if pd.notna(row.get('location')) else None,
                    'brand': str(row.get('brand', '')).strip() if pd.notna(row.get('brand')) else None,
                    'status': 'in_stock',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Handle expiry date if present
                if 'expiry_date' in df.columns and pd.notna(row.get('expiry_date')):
                    try:
                        expiry_date = pd.to_datetime(row.get('expiry_date'))
                        product_data['expiry_date'] = expiry_date.isoformat()
                    except:
                        product_data['expiry_date'] = None
                else:
                    product_data['expiry_date'] = None
                
                # Validate department
                valid_departments = ['01-FMG', '01-CGD', '01-OPSS']
                if product_data['department'] not in valid_departments:
                    raise ValueError(f"Invalid department '{product_data['department']}'. Must be one of: {', '.join(valid_departments)}")
                
                # Validate currency
                valid_currencies = ['YER', 'SAR', 'EUR', 'USD']
                if product_data['purchase_currency'] not in valid_currencies:
                    raise ValueError(f"Invalid currency '{product_data['purchase_currency']}'. Must be one of: {', '.join(valid_currencies)}")
                
                # Check for duplicate barcode if provided
                if product_data['barcode']:
                    existing_barcode = await db.products.find_one({"barcode": product_data['barcode']})
                    if existing_barcode:
                        raise ValueError(f"Product with barcode '{product_data['barcode']}' already exists")
                
                # Check for duplicate item_number if provided
                if product_data['item_number']:
                    existing_item = await db.products.find_one({"item_number": product_data['item_number']})
                    if existing_item:
                        raise ValueError(f"Product with item number '{product_data['item_number']}' already exists")
                
                # Calculate product status
                if product_data['quantity'] <= 0:
                    product_data['status'] = 'out_of_stock'
                elif product_data['quantity'] <= product_data['low_stock_threshold']:
                    product_data['status'] = 'low_stock'
                else:
                    product_data['status'] = 'in_stock'
                
                # Insert product into database
                await db.products.insert_one(product_data)
                
                import_stats['successful_imports'] += 1
                import_stats['imported_products'].append({
                    'row': index + 2,
                    'product_name': product_data['product_name'],
                    'department': product_data['department'],
                    'barcode': product_data['barcode']
                })
                
            except Exception as row_error:
                import_stats['failed_imports'] += 1
                error_msg = f"Row {index + 2} ({row.get('product_name', 'Unknown')}): {str(row_error)}"
                import_stats['errors'].append(error_msg)
                continue
        
        # Generate summary message
        success_rate = (import_stats['successful_imports'] / import_stats['total_rows']) * 100 if import_stats['total_rows'] > 0 else 0
        
        return {
            "message": f"✅ Excel import completed! {import_stats['successful_imports']}/{import_stats['total_rows']} products imported successfully ({success_rate:.1f}% success rate)",
            "import_summary": import_stats,
            "status": "success" if import_stats['successful_imports'] > 0 else "warning",
            "recommendations": [
                "Check the dashboard to see imported products",
                "Review any failed imports in the error list",
                "Verify product data accuracy",
                "Set up alerts for out-of-stock items if needed"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Excel import failed: {str(e)}")

@api_router.get("/system/import-template")
async def download_import_template(current_user: User = Depends(get_current_user)):
    """Download Excel template for product import"""
    try:
        # Create sample Excel template
        template_data = {
            'product_name': ['Apple Juice Box 1L', 'Bread Loaf White', 'Milk UHT 1L'],
            'item_number': ['ITEM001', 'ITEM002', 'ITEM003'],
            'department': ['01-CGD', '01-FMG', '01-FMG'],
            'section': ['S010 - Beverage', 'S016 - Delicateen', 'S015 - Dairy Products'],
            'family': ['Beverages', 'Bakery', 'Dairy'],
            'sub_family': ['Fruit Juices', 'Bread', 'Milk'],
            'supplier_code': ['SUP001', 'SUP002', 'SUP003'],
            'supplier': ['Supplier A', 'Supplier B', 'Supplier C'],
            'barcode': ['3222471081716', '1234567890123', '9876543210987'],
            'purchase_price': [2.50, 1.25, 3.00],
            'purchase_currency': ['EUR', 'YER', 'SAR'],
            'selling_price': [350, 175, 12],
            'quantity': [50, 100, 75],
            'low_stock_threshold': [10, 20, 15],
            'expiry_date': ['2024-12-31', '2024-11-15', '2024-10-30'],
            'arabic_description': ['عصير تفاح', 'خبز أبيض', 'حليب طويل الأمد'],
            'description': ['Fresh apple juice', 'White bread loaf', 'UHT milk'],
            'location': ['A1-B2', 'C3-D4', 'E5-F6'],
            'brand': ['Brand A', 'Brand B', 'Brand C']
        }
        
        # Create DataFrame
        template_df = pd.DataFrame(template_data)
        
        # Create Excel file in memory with company branding
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, sheet_name='Products', index=False)
            
            # Apply company branding to Products sheet
            from openpyxl.styles import Font, PatternFill, Alignment
            
            workbook = writer.book
            products_sheet = writer.sheets['Products']
            
            # Add logo and branding to products sheet
            branding = get_company_branding()
            add_logo_to_excel(products_sheet, row=1, col=1)
            
            # Add company header
            products_sheet.merge_cells('B1:F1')
            products_sheet['B1'] = f"{branding['company_name']} - PRODUCT IMPORT TEMPLATE"
            products_sheet['B1'].font = Font(name='Arial', size=14, bold=True, color=branding['excel_header_color'])
            products_sheet['B1'].alignment = Alignment(horizontal='center', vertical='center')
            
            # Style the header row
            for col in range(1, len(template_df.columns) + 1):
                cell = products_sheet.cell(row=5, column=col)  # Row 5 because logo takes 3 rows
                cell.fill = PatternFill(start_color=branding['excel_header_color'], end_color=branding['excel_header_color'], fill_type='solid')
                cell.font = Font(color='FFFFFF', bold=True)
            
            # Add instructions sheet
            instructions_data = {
                'Column Name': [
                    'product_name', 'item_number', 'department', 'section', 'family', 'sub_family',
                    'supplier_code', 'supplier', 'barcode', 'purchase_price', 'purchase_currency',
                    'selling_price', 'quantity', 'low_stock_threshold', 'expiry_date',
                    'arabic_description', 'description', 'location', 'brand'
                ],
                'Required': [
                    'YES', 'Optional', 'YES', 'YES', 'YES', 'YES',
                    'Optional', 'YES', 'Optional', 'YES', 'YES',
                    'Optional', 'Optional', 'Optional', 'Optional',
                    'Optional', 'Optional', 'Optional', 'Optional'
                ],
                'Description': [
                    'Product name (required)', 'Internal item number', 'Department: 01-FMG, 01-CGD, 01-OPSS',
                    'Section name', 'Product family', 'Product sub-family',
                    'Supplier code', 'Supplier name', 'Product barcode (must be unique)',
                    'Purchase price (number)', 'Currency: YER, SAR, EUR, USD',
                    'Selling price (number)', 'Current quantity in stock', 'Low stock alert threshold',
                    'Expiry date (YYYY-MM-DD format)', 'Arabic product description', 'English description',
                    'Storage location', 'Product brand'
                ]
            }
            
            instructions_df = pd.DataFrame(instructions_data)
            instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
            
            # Apply branding to Instructions sheet
            instructions_sheet = writer.sheets['Instructions']
            add_logo_to_excel(instructions_sheet, row=1, col=1)
            
            # Add company header to instructions
            instructions_sheet.merge_cells('B1:D1')
            instructions_sheet['B1'] = f"{branding['company_name']} - IMPORT INSTRUCTIONS"
            instructions_sheet['B1'].font = Font(name='Arial', size=14, bold=True, color=branding['excel_header_color'])
            instructions_sheet['B1'].alignment = Alignment(horizontal='center', vertical='center')
            
            # Style the instructions header row
            for col in range(1, len(instructions_df.columns) + 1):
                cell = instructions_sheet.cell(row=5, column=col)  # Row 5 because logo takes 3 rows
                cell.fill = PatternFill(start_color=branding['excel_header_color'], end_color=branding['excel_header_color'], fill_type='solid')
                cell.font = Font(color='FFFFFF', bold=True)
        
        output.seek(0)
        filename = f"product_import_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

# Master Data Import Endpoints
@api_router.post("/master-data/import")
async def import_master_data(
    current_user: User = Depends(get_current_user)
):
    """Import master data from Excel file"""
    try:
        from master_data_importer import MasterDataImporter
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required for master data import")
        
        # Initialize importer
        mongo_url = os.environ.get('MONGO_URL')
        importer = MasterDataImporter(mongo_url)
        
        # Check if master data file exists
        excel_file = '/app/master_data.xlsx'
        if not os.path.exists(excel_file):
            raise HTTPException(status_code=404, detail="Master data file not found. Please upload the Excel file first.")
        
        # Import data
        stats = await importer.import_master_data(excel_file)
        
        return {
            "message": "Master data import completed successfully",
            "stats": stats,
            "timestamp": datetime.now(timezone.utc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Master data import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.get("/master-data/summary")
async def get_master_data_summary(
    current_user: User = Depends(get_current_user)
):
    """Get summary of imported master data"""
    try:
        from master_data_importer import MasterDataImporter
        
        mongo_url = os.environ.get('MONGO_URL')
        importer = MasterDataImporter(mongo_url)
        
        summary = await importer.get_import_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get master data summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@api_router.post("/master-data/upload")
async def upload_master_data_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload master data Excel file"""
    try:
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required for file upload")
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Save uploaded file
        file_path = f'/app/master_data.xlsx'
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return {
            "message": "Master data file uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "timestamp": datetime.now(timezone.utc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Enhanced Analytics Endpoints for Visual Charts
@api_router.get("/analytics/department-breakdown")
async def get_department_breakdown(
    current_user: User = Depends(get_current_user)
):
    """Get detailed department breakdown for visual charts"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$department",
                    "total_products": {"$sum": 1},
                    "total_stock": {"$sum": "$quantity"},
                    "total_value_yer": {"$sum": "$stock_value_yer"},
                    "total_value_usd": {"$sum": "$stock_value_usd"},
                    "avg_price": {"$avg": "$purchase_price"},
                    "low_stock_items": {
                        "$sum": {"$cond": [{"$eq": ["$status", "low_stock"]}, 1, 0]}
                    },
                    "out_of_stock_items": {
                        "$sum": {"$cond": [{"$eq": ["$status", "out_of_stock"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"total_value_yer": -1}}
        ]
        
        result = await db.products.aggregate(pipeline).to_list(None)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get department breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get department breakdown")

@api_router.get("/analytics/stock-levels")
async def get_stock_levels_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get stock levels analytics for visual charts"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_value": {"$sum": "$stock_value_yer"},
                    "departments": {"$addToSet": "$department"}
                }
            }
        ]
        
        status_breakdown = await db.products.aggregate(pipeline).to_list(None)
        
        # Get stock distribution by range
        stock_ranges_pipeline = [
            {
                "$bucket": {
                    "groupBy": "$quantity",
                    "boundaries": [0, 1, 5, 10, 25, 50, 100],
                    "default": "100+",
                    "output": {
                        "count": {"$sum": 1},
                        "total_value": {"$sum": "$stock_value_yer"}
                    }
                }
            }
        ]
        
        stock_ranges = await db.products.aggregate(stock_ranges_pipeline).to_list(None)
        
        return {
            "status_breakdown": status_breakdown,
            "stock_ranges": stock_ranges
        }
        
    except Exception as e:
        logger.error(f"Failed to get stock analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get stock analytics")

@api_router.get("/analytics/supplier-performance")
async def get_supplier_performance(
    current_user: User = Depends(get_current_user)
):
    """Get supplier performance analytics"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$supplier",
                    "total_products": {"$sum": 1},
                    "total_stock_value": {"$sum": "$stock_value_yer"},
                    "avg_price": {"$avg": "$purchase_price"},
                    "departments": {"$addToSet": "$department"},
                    "out_of_stock_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "out_of_stock"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"total_stock_value": -1}},
            {"$limit": 20}  # Top 20 suppliers
        ]
        
        result = await db.products.aggregate(pipeline).to_list(None)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get supplier performance: {str(e)}")
# =============================================================================
# CURRENCY MANAGEMENT ENDPOINTS
# =============================================================================

@api_router.get("/currency/settings")
async def get_currency_settings(current_user: User = Depends(get_current_user)):
    """Get current currency settings and exchange rates"""
    try:
        # Get the latest currency settings
        settings = await db.currency_settings.find_one(
            {"is_active": True}, 
            sort=[("last_updated", -1)]
        )
        
        if not settings:
            # Create default settings if none exist
            default_settings = {
                "id": str(uuid.uuid4()),
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.004,
                    "SAR": 0.267,
                    "EUR": 1.10,
                    "USD": 1.0
                },
                "last_updated": datetime.now(),
                "updated_by": current_user.id,
                "created_at": datetime.now(),
                "is_active": True
            }
            
            await db.currency_settings.insert_one(default_settings)
            settings = default_settings
        
        # Remove MongoDB ObjectId for JSON serialization
        if "_id" in settings:
            del settings["_id"]
        
        return {
            "settings": settings,
            "supported_currencies": ["YER", "SAR", "EUR", "USD"],
            "base_currency": settings["base_currency"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get currency settings: {str(e)}")

@api_router.put("/currency/settings")
async def update_currency_settings(
    settings_update: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update currency settings and exchange rates"""
    try:
        # Validate user permissions (managers and admins only)
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(status_code=403, detail="Only managers and admins can update currency settings")
        
        # Validate exchange rates
        exchange_rates = settings_update.get("exchange_rates", {})
        base_currency = settings_update.get("base_currency", "USD")
        
        # Ensure base currency has rate 1.0
        if base_currency in exchange_rates:
            exchange_rates[base_currency] = 1.0
        
        # Validate all rates are positive numbers
        for currency, rate in exchange_rates.items():
            if not isinstance(rate, (int, float)) or rate <= 0:
                raise HTTPException(status_code=400, detail=f"Invalid exchange rate for {currency}: {rate}")
        
        # Deactivate old settings
        await db.currency_settings.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        
        # Create new settings entry
        new_settings = {
            "id": str(uuid.uuid4()),
            "base_currency": base_currency,
            "exchange_rates": exchange_rates,
            "last_updated": datetime.now(),
            "updated_by": current_user.id,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        await db.currency_settings.insert_one(new_settings)
        
        # Log the update
        print(f"Currency settings updated by {current_user.username}: {exchange_rates}")
        
        return {
            "success": True,
            "message": "Currency settings updated successfully",
            "settings": {k: v for k, v in new_settings.items() if k != "_id"},
            "updated_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update currency settings: {str(e)}")

@api_router.get("/currency/rates")
async def get_current_exchange_rates():
    """Get current exchange rates for public use"""
    try:
        settings = await db.currency_settings.find_one(
            {"is_active": True}, 
            sort=[("last_updated", -1)]
        )
        
        if not settings:
            # Return default rates if no settings exist
            return {
                "base_currency": "USD",
                "exchange_rates": {
                    "YER": 0.004,
                    "SAR": 0.267,
                    "EUR": 1.10,
                    "USD": 1.0
                },
                "last_updated": datetime.now().isoformat()
            }
        
        return {
            "base_currency": settings["base_currency"],
            "exchange_rates": settings["exchange_rates"],
            "last_updated": settings["last_updated"].isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get exchange rates: {str(e)}")

@api_router.post("/currency/rates/quick-update")
async def quick_update_rate(
    rate_update: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Quick update for a single currency rate"""
    try:
        # Validate user permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(status_code=403, detail="Only managers and admins can update exchange rates")
        
        currency = rate_update.get("currency")
        rate = rate_update.get("rate")
        
        if not currency or not rate:
            raise HTTPException(status_code=400, detail="Currency and rate are required")
        
        if not isinstance(rate, (int, float)) or rate <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid rate value: {rate}")
        
        # Get current settings
        current_settings = await db.currency_settings.find_one(
            {"is_active": True}, 
            sort=[("last_updated", -1)]
        )
        
        if not current_settings:
            raise HTTPException(status_code=404, detail="No currency settings found")
        
        # Update the specific rate
        exchange_rates = current_settings["exchange_rates"].copy()
        exchange_rates[currency] = float(rate)
        
        # Deactivate old settings
        await db.currency_settings.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        
        # Create new settings with updated rate
        new_settings = {
            "id": str(uuid.uuid4()),
            "base_currency": current_settings["base_currency"],
            "exchange_rates": exchange_rates,
            "last_updated": datetime.now(),
            "updated_by": current_user.id,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        await db.currency_settings.insert_one(new_settings)
        
        return {
            "success": True,
            "message": f"Exchange rate for {currency} updated to {rate}",
            "currency": currency,
            "new_rate": rate,
            "updated_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update exchange rate: {str(e)}")

        raise HTTPException(status_code=500, detail="Failed to get supplier performance")

# Include router after all endpoints are defined
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