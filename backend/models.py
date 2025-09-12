from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enhanced models for comprehensive inventory management

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager" 
    STAFF = "staff"

class Department(str, Enum):
    FMG = "01-FMG"  # Fresh & Food Grocery
    CGD = "01-CGD"  # Consumer Goods & Drinks
    OPSS = "01-OPSS"  # Operations & Special Services

class Section(str, Enum):
    BEVERAGE = "S010 - Beverage"
    ULTRA_FRESH = "S014 - Ultra Fresh"
    DELICATEEN = "S016 - Delicateen"
    FROZEN_FOOD = "S018 - Frozen Food"
    DAIRY_PRODUCTS = "S015 - Dairy Products"

class Currency(str, Enum):
    YER = "YER"
    SAR = "SAR"
    EUR = "EUR"
    USD = "USD"

class ProductStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    NEAR_EXPIRY = "near_expiry"

# Enhanced User Model with Role-Based Access
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.STAFF
    department: Optional[Department] = None  # Staff limited to their department
    is_active: bool = True
    approval_status: str = "pending"
    is_admin: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: UserRole = UserRole.STAFF
    department: Optional[Department] = None

class UserApproval(BaseModel):
    user_id: str
    approval_status: str

# Enhanced Product Model
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    item_number: Optional[str] = None
    department: Department
    section: Section
    family: str
    sub_family: str
    supplier_code: Optional[str] = None
    supplier: str
    expiry_date: Optional[datetime] = None
    quantity: int = 0
    barcode: Optional[str] = None
    purchase_price: Optional[float] = 0.0
    purchase_currency: Currency = Currency.YER
    selling_price: Optional[float] = 0.0
    arabic_description: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    status: ProductStatus = ProductStatus.IN_STOCK
    low_stock_threshold: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    product_name: str
    item_number: Optional[str] = None
    department: Department
    section: Section
    family: str
    sub_family: str
    supplier_code: Optional[str] = None
    supplier: str
    expiry_date: Optional[datetime] = None
    quantity: int = 0
    barcode: Optional[str] = None
    purchase_price: Optional[float] = 0.0
    purchase_currency: Currency = Currency.YER
    selling_price: Optional[float] = 0.0
    arabic_description: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    brand: Optional[str] = None
    low_stock_threshold: int = 10

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    expiry_date: Optional[datetime] = None
    low_stock_threshold: Optional[int] = None
    status: Optional[ProductStatus] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Department Dashboard Models
class DepartmentKPI(BaseModel):
    department: Department
    total_items: int = 0
    expired_items: int = 0
    near_expiry_items: int = 0
    out_of_stock_items: int = 0
    low_stock_items: int = 0
    total_stock_value: float = 0.0
    total_quantity: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SupplierDetails(BaseModel):
    supplier_name: str
    supplier_code: Optional[str] = None
    total_items: int = 0
    out_of_stock_items: int = 0
    stock_value: float = 0.0
    purchase_currency: Currency = Currency.YER
    lead_time_days: int = 2  # Default 2 days
    return_policy: str = "Standard return policy"
    replacement_policy: str = "Standard replacement policy"
    contact_info: Optional[str] = None

# Alert and Email Models
class AlertType(str, Enum):
    OUT_OF_STOCK = "out_of_stock"
    NEAR_EXPIRY = "near_expiry"
    EXPIRED = "expired"
    LOW_STOCK = "low_stock"

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType
    department: Department
    section: Section
    product_id: str
    product_name: str
    message: str
    priority: str = "medium"  # low, medium, high, critical
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

class EmailSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    daily_alert_time: str = "08:00"  # 08:00 AM Aden timezone
    timezone: str = "Asia/Aden"
    default_recipient: str = "imad@geantyemen.com"
    department_recipients: Dict[str, List[str]] = {}
    weekly_reports_enabled: bool = True
    daily_alerts_enabled: bool = True
    expiry_threshold_days: int = 7  # Default 7 days
    beverage_expiry_threshold_days: int = 15  # 15 days for S-10 Beverages
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CompanySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = "Geant Hypermarket"
    logo_url: str = "/geant_main_page_logo.png"
    primary_color: str = "#22c55e"  # Green theme
    secondary_color: str = "#3b82f6"  # Blue theme
    accent_color: str = "#f59e0b"  # Orange for alerts
    contact_email: str = "imad@geantyemen.com"
    contact_phone: str = ""
    address: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Export Models
class ExportRequest(BaseModel):
    export_type: str  # "pdf" or "excel"
    department: Optional[Department] = None
    section: Optional[Section] = None
    supplier: Optional[str] = None
    include_images: bool = False
    date_range: Optional[Dict[str, str]] = None

class ReportRequest(BaseModel):
    report_type: str  # "weekly_summary", "out_of_stock", "near_expiry", "supplier_details"
    department: Optional[Department] = None
    email_recipients: Optional[List[str]] = None
    include_charts: bool = True

# Dashboard Response Models
class DashboardData(BaseModel):
    user_role: UserRole
    accessible_departments: List[Department]
    kpis: List[DepartmentKPI]
    recent_alerts: List[Alert]
    stock_distribution: Dict[str, int]
    expiry_status: Dict[str, int]
    top_suppliers: List[SupplierDetails]

class FilterOptions(BaseModel):
    departments: List[Dict[str, str]]
    sections: List[Dict[str, str]]
    suppliers: List[Dict[str, str]]
    families: List[Dict[str, str]]
    currencies: List[Dict[str, str]]