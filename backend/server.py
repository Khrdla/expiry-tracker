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
    """Automated function to send daily alerts at 06:00 AM Aden time"""
    try:
        logger.info("Starting automated daily alert email...")
        
        # Get email settings
        settings = await db.email_settings.find_one() or {}
        if not settings.get('daily_alerts_enabled', True):
            logger.info("Daily alerts are disabled, skipping automated send")
            return
        
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
        
        # Generate PDF report
        pdf_data = await generate_daily_alert_pdf(out_of_stock_items, near_expiry_items)
        
        # Generate Excel report 
        excel_data = await generate_daily_alert_excel(out_of_stock_items, near_expiry_items)
        
        # Prepare attachments
        attachments = [
            {
                "data": pdf_data,
                "filename": f"Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            },
            {
                "data": excel_data,
                "filename": f"Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            }
        ]
        
        # Create HTML email body
        aden_tz = pytz.timezone('Asia/Aden')
        current_aden_time = datetime.now(aden_tz)
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: linear-gradient(135deg, #22c55e, #3b82f6); padding: 20px; color: white; text-align: center;">
                <h1>🏢 Geant Hypermarket</h1>
                <h2>📊 Daily Inventory Alert Report</h2>
                <p>Automated Report - {current_aden_time.strftime('%Y-%m-%d %H:%M:%S')} (Aden Time)</p>
            </div>
            
            <div style="padding: 30px;">
                <h2>📈 Daily Summary</h2>
                <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold;">Out of Stock Items</td>
                        <td style="padding: 15px; color: #dc2626; font-weight: bold; font-size: 18px;">{len(out_of_stock_items)}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold;">Near Expiry Items</td>
                        <td style="padding: 15px; color: #f59e0b; font-weight: bold; font-size: 18px;">{len(near_expiry_items)}</td>
                    </tr>
                    <tr style="background-color: #f8fafc;">
                        <td style="padding: 15px; font-weight: bold;">Report Generated</td>
                        <td style="padding: 15px;">{current_aden_time.strftime('%Y-%m-%d at %H:%M:%S')} (Asia/Aden)</td>
                    </tr>
                </table>
                
                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                    <h3>📎 Attachments Included:</h3>
                    <ul>
                        <li><strong>PDF Report:</strong> Professional formatted inventory report</li>
                        <li><strong>Excel Report:</strong> Detailed data for analysis and filtering</li>
                    </ul>
                </div>
                
                <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0;">
                    <p><strong>🎯 Next Steps:</strong></p>
                    <ul>
                        <li>Review out-of-stock items for immediate restocking</li>
                        <li>Check near-expiry items for promotional opportunities</li>
                        <li>Contact suppliers for critical inventory items</li>
                    </ul>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
                <p style="color: #666; font-size: 14px;">
                    This is an automated daily report from Geant Hypermarket Inventory Management System<br>
                    Generated on {current_aden_time.strftime('%Y-%m-%d at %H:%M:%S')} (Asia/Aden timezone)<br>
                    Scheduled daily at 06:00 AM Aden time
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email with attachments
        success = await send_email_alert(recipients, subject, body, attachments)
        
        if success:
            logger.info(f"Automated daily alert sent successfully to {recipients}")
            # Update last automated email timestamp
            await db.email_settings.update_one(
                {},
                {"$set": {"last_automated_email": current_aden_time}},
                upsert=True
            )
        else:
            logger.error("Failed to send automated daily alert")
            
    except Exception as e:
        logger.error(f"Error in automated daily alert: {str(e)}")

# Schedule daily alerts for 06:00 AM Aden time
def setup_daily_email_scheduler():
    """Setup automated daily email scheduler"""
    aden_tz = pytz.timezone('Asia/Aden')
    
    # Schedule daily alerts at 06:00 AM Aden time
    scheduler.add_job(
        send_automated_daily_alerts,
        CronTrigger(hour=6, minute=0, timezone=aden_tz),
        id='daily_inventory_alerts',
        name='Daily Inventory Alert Email',
        replace_existing=True
    )
    
    logger.info("Daily email scheduler configured for 06:00 AM Asia/Aden timezone")

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
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (5MB max)
        if image.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
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
        
        return {"message": "Image uploaded successfully", "image_url": image_url}
        
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
    """Generate PDF report for daily alerts"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        
        story = []
        
        # Header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1
        )
        
        story.append(Paragraph("Geant Hypermarket", title_style))
        story.append(Paragraph(f"Daily Inventory Alert Report - {datetime.now().strftime('%Y-%m-%d')}", styles['Heading2']))
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
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
    """Generate Excel report for daily alerts"""
    try:
        import pandas as pd
        from io import BytesIO
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Out of Stock Items', 'Near Expiry Items', 'Report Date', 'Timezone'],
                'Value': [len(out_of_stock_items), len(near_expiry_items), 
                         datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Asia/Aden (GMT+3)']
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Out of Stock sheet
            if out_of_stock_items:
                out_df = pd.DataFrame(out_of_stock_items)
                out_df.to_excel(writer, sheet_name='Out of Stock', index=False)
                
                # Format the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Out of Stock']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#FF6B6B',
                    'font_color': 'white',
                    'border': 1
                })
                
                for col_num, value in enumerate(out_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 20)
            
            # Near Expiry sheet
            if near_expiry_items:
                near_df = pd.DataFrame(near_expiry_items)
                near_df.to_excel(writer, sheet_name='Near Expiry', index=False)
                
                if 'Near Expiry' in writer.sheets:
                    workbook = writer.book
                    worksheet = writer.sheets['Near Expiry']
                    
                    # Add formatting
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#FFB84D',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    for col_num, value in enumerate(near_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
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
        
        # Create email content
        subject = f"Geant Hypermarket - Daily Inventory Alert ({datetime.now().strftime('%Y-%m-%d')})"
        
        # Generate PDF report
        pdf_data = await generate_daily_alert_pdf(out_of_stock_items, near_expiry_items)
        
        # Generate Excel report 
        excel_data = await generate_daily_alert_excel(out_of_stock_items, near_expiry_items)
        
        # Prepare attachments
        attachments = [
            {
                "data": pdf_data,
                "filename": f"Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            },
            {
                "data": excel_data,
                "filename": f"Daily_Inventory_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            }
        ]
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #22c55e, #3b82f6); padding: 20px; color: white; text-align: center;">
                <h1>Expiry Tracker</h1>
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
                    <p style="color: #6b7280;">This is an automated alert from Expiry Tracker Inventory Management System</p>
                    <p style="color: #6b7280;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Aden Time)</p>
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
                    • <strong>Daily Alert Time:</strong> {settings.get('daily_alert_time', '06:00')} AM Aden Time
                </div>
                
                <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0;">
                    <strong>📋 System Configuration:</strong><br>
                    • Daily alerts are scheduled for <strong>06:00 AM Aden time</strong> daily<br>
                    • Email notifications: <strong>{"Enabled" if settings.get('daily_alerts_enabled', True) else "Disabled"}</strong><br>
                    • Default recipient: <strong>{recipients[0]}</strong>
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>If you received this email, the system is working correctly</li>
                    <li>Daily alerts will be sent automatically at 06:00 AM Aden time</li>
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
            "daily_alert_time": settings.get('daily_alert_time', '06:00'),
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
        
        return FileResponse(
            path=None,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            content=output.getvalue()
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
        
        return FileResponse(
            path=None,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            },
            content=output.getvalue()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")

# Expiry Tracker Export
@api_router.post("/export/expiry-tracker")
async def export_expiry_tracker_data(
    current_user: User = Depends(get_current_user)
):
    """Export expiry tracker data"""
    try:
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Expiry Tracker Data')
        
        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'bg_color': '#FF6B35'  # Orange theme for Expiry Tracker
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFE5D9',
            'border': 1,
            'align': 'center'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        # Title
        worksheet.merge_range('A1:K1', 'Geant Hypermarket - Expiry Tracker Export', title_format)
        worksheet.write('A2', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers
        headers = [
            'Product Name', 'Item Number', 'Barcode', 'Department', 'Section', 
            'Supplier', 'Quantity', 'Expiry Date', 'Days Until Expiry', 'Status', 'Notes'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Get products with expiry dates
        accessible_departments = get_accessible_departments(current_user)
        filter_dict = {
            "department": {"$in": [d.value for d in accessible_departments]},
            "expiry_date": {"$exists": True, "$ne": None}
        }
        
        products = await db.products.find(filter_dict).sort("expiry_date", 1).to_list(length=None)
        
        # Write data
        for row, product in enumerate(products, start=4):
            expiry_date = product.get('expiry_date')
            days_until_expiry = ""
            status = "No Date"
            
            if expiry_date:
                if isinstance(expiry_date, str):
                    expiry_date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                else:
                    expiry_date_obj = expiry_date
                
                days_until_expiry = (expiry_date_obj.date() - datetime.now().date()).days
                
                if days_until_expiry < 0:
                    status = "EXPIRED"
                elif days_until_expiry <= 7:
                    status = "NEAR EXPIRY"
                else:
                    status = "GOOD"
            
            worksheet.write(row, 0, product.get('product_name', ''), cell_format)
            worksheet.write(row, 1, product.get('item_number', ''), cell_format)
            worksheet.write(row, 2, product.get('barcode', ''), cell_format)
            worksheet.write(row, 3, product.get('department', ''), cell_format)
            worksheet.write(row, 4, product.get('section', ''), cell_format)
            worksheet.write(row, 5, product.get('supplier', ''), cell_format)
            worksheet.write(row, 6, product.get('quantity', 0), cell_format)
            worksheet.write(row, 7, expiry_date_obj.strftime('%Y-%m-%d') if expiry_date else '', cell_format)
            worksheet.write(row, 8, days_until_expiry if isinstance(days_until_expiry, int) else '', cell_format)
            worksheet.write(row, 9, status, cell_format)
            worksheet.write(row, 10, product.get('notes', ''), cell_format)
        
        # Auto-adjust columns
        worksheet.set_column('A:K', 15)
        worksheet.set_column('A:A', 25)  # Product name wider
        
        workbook.close()
        output.seek(0)
        
        filename = f"expiry_tracker_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return FileResponse(
            path=None,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            content=output.getvalue()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating expiry tracker export: {str(e)}")

# Return Forms Export
@api_router.get("/export/return-forms")
async def export_return_forms(
    current_user: User = Depends(get_current_user)
):
    """Export return forms data"""
    try:
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Return Forms')
        
        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'bg_color': '#DC143C'  # Red theme for Return Forms
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFE4E1',
            'border': 1,
            'align': 'center'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        # Title
        worksheet.merge_range('A1:M1', 'Geant Hypermarket - Return Forms Export', title_format)
        worksheet.write('A2', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers
        headers = [
            'Reference Number', 'Return Date', 'Product Code', 'Product Name', 'Quantity',
            'Purchase Price', 'Currency', 'Supplier', 'Reason for Return', 'Status',
            'Prepared By', 'Section Manager', 'Department Head'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Get return forms from database
        returns = await db.returns.find({}).sort("return_date", -1).to_list(length=None)
        
        # Write data
        for row, return_form in enumerate(returns, start=4):
            worksheet.write(row, 0, return_form.get('reference_number', ''), cell_format)
            worksheet.write(row, 1, return_form.get('return_date', ''), cell_format)
            worksheet.write(row, 2, return_form.get('product_code', ''), cell_format)
            worksheet.write(row, 3, return_form.get('product_name', ''), cell_format)
            worksheet.write(row, 4, return_form.get('quantity', 0), cell_format)
            worksheet.write(row, 5, return_form.get('purchase_price', 0), cell_format)
            worksheet.write(row, 6, return_form.get('purchase_currency', 'YER'), cell_format)
            worksheet.write(row, 7, return_form.get('supplier', ''), cell_format)
            worksheet.write(row, 8, return_form.get('reason_for_return', ''), cell_format)
            worksheet.write(row, 9, return_form.get('status', 'pending'), cell_format)
            worksheet.write(row, 10, return_form.get('prepared_by_supervisor', ''), cell_format)
            worksheet.write(row, 11, return_form.get('section_manager_name', ''), cell_format)
            worksheet.write(row, 12, return_form.get('department_head_name', ''), cell_format)
        
        # Auto-adjust columns
        worksheet.set_column('A:M', 15)
        worksheet.set_column('H:H', 25)  # Reason wider
        
        workbook.close()
        output.seek(0)
        
        filename = f"return_forms_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return FileResponse(
            path=None,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            content=output.getvalue()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating return forms export: {str(e)}")

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
        
        # Define title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkred,
            alignment=1
        )
        
        # Header with logo
        try:
            from reportlab.platypus import Image
            from reportlab.lib.utils import ImageReader
            import os
            
            # Try to add logo if it exists
            logo_path = "/app/frontend/public/geant-logo.jpeg"
            if os.path.exists(logo_path):
                # Create header table with logo and title
                logo_img = Image(logo_path, width=0.8*inch, height=0.8*inch)
                
                header_data = [[logo_img, Paragraph("🏢 Geant Hypermarket", title_style)]]
                header_table = Table(header_data, colWidths=[1*inch, 5*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ]))
                
                story.append(header_table)
            else:
                # Fallback to text header if logo not found
                story.append(Paragraph("🏢 Geant Hypermarket", title_style))
                
        except Exception as e:
            # Fallback to text header if image processing fails
            logger.warning(f"Could not add logo to PDF: {str(e)}")
            story.append(Paragraph("🏢 Geant Hypermarket", title_style))
        
        story.append(Paragraph("Product Return Form", styles['Heading2']))
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
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
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
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey])
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
    # Ensure timezone is set to Asia/Aden and alert time is 06:00 as requested
    settings.timezone = "Asia/Aden"
    settings.daily_alert_time = "06:00"
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

async def generate_waste_report_excel(report_data: dict, period: str):
    """Generate Excel waste report"""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Waste Report - {period.title()}"
    
    # Define styles
    header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    subheader_font = Font(name='Arial', size=12, bold=True)
    currency_font = Font(name='Arial', size=12, bold=True, color='D32F2F')
    border = Border(
        left=Side(border_style='thin'),
        right=Side(border_style='thin'),
        top=Side(border_style='thin'),
        bottom=Side(border_style='thin')
    )
    
    # Header
    ws.merge_cells('A1:D1')
    ws['A1'] = f"GEANT HYPERMARKET - WASTE REPORT ({period.upper()})"
    ws['A1'].font = header_font
    ws['A1'].fill = header_fill
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Report details
    row = 3
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
    
    # Currency totals
    row += 3
    ws[f'A{row}'] = "WASTE VALUE BY CURRENCY"
    ws[f'A{row}'].font = subheader_font
    
    row += 1
    ws[f'A{row}'] = "Currency"
    ws[f'B{row}'] = "Total Waste Value"
    ws[f'A{row}'].font = header_font
    ws[f'B{row}'].font = header_font
    ws[f'A{row}'].fill = header_fill
    ws[f'B{row}'].fill = header_fill
    
    for currency, total in report_data['currency_totals'].items():
        if total > 0:  # Only show currencies with waste
            row += 1
            ws[f'A{row}'] = currency
            ws[f'B{row}'] = f"{total:,.2f} {currency}"
            ws[f'B{row}'].font = currency_font
    
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
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to bytes
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
    """Generate PDF waste report"""
    import io
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"GEANT HYPERMARKET<br/>WASTE REPORT ({period.upper()})", title_style))
    story.append(Spacer(1, 20))
    
    # Report details
    details_data = [
        ['Report Period:', period.title()],
        ['Generated At:', datetime.fromisoformat(report_data['generated_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    if report_data.get('department'):
        details_data.append(['Department:', report_data['department']])
    if report_data.get('section'):
        details_data.append(['Section:', report_data['section']])
    
    details_table = Table(details_data, colWidths=[2*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 30))
    
    # Currency totals
    story.append(Paragraph("WASTE VALUE BY CURRENCY", heading_style))
    
    currency_data = [['Currency', 'Total Waste Value']]
    for currency, total in report_data['currency_totals'].items():
        if total > 0:  # Only show currencies with waste
            currency_data.append([currency, f"{total:,.2f} {currency}"])
    
    if len(currency_data) > 1:
        currency_table = Table(currency_data, colWidths=[2*inch, 3*inch])
        currency_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(currency_table)
    else:
        story.append(Paragraph("No waste entries found for this period.", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # Summary
    story.append(Paragraph("SUMMARY", heading_style))
    summary_data = [
        ['Total Waste Entries:', str(report_data['total_entries'])],
        ['Total Quantity Wasted:', str(report_data['total_quantity_wasted'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    filename = f"waste_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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