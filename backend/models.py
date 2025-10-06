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

class CurrencySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    base_currency: str = "USD"  # Reference currency for conversions
    exchange_rates: Dict[str, float] = {
        "YER": 0.004,  # 1 YER = 0.004 USD
        "SAR": 0.267,  # 1 SAR = 0.267 USD
        "EUR": 1.10,   # 1 EUR = 1.10 USD
        "USD": 1.0     # 1 USD = 1.0 USD
    }
    last_updated: datetime = Field(default_factory=datetime.now)
    updated_by: str  # User ID who updated the rates
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

class CurrencyRateUpdate(BaseModel):
    currency: str
    rate: float
    updated_by: str

class ZoneType(str, Enum):
    SA = "SA"  # Selling Area
    WH = "WH"  # Warehouse

class InventoryScan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_type: ZoneType
    zone_number: int
    barcode: str
    item_number: str
    description: str
    department: str
    section: str
    family: str
    supplier_code: str
    supplier_name: str
    system_stock: float
    unit_cost: float
    qty_scanned_sa: float = 0.0
    qty_scanned_wh: float = 0.0
    total_inventory_scan: float = Field(default=0.0)
    variance_qty: float = Field(default=0.0)
    variance_value: float = Field(default=0.0)
    date_scanned: datetime = Field(default_factory=datetime.now)
    scanned_by: str  # User ID who performed the scan
    created_at: datetime = Field(default_factory=datetime.now)

class InventoryScanRequest(BaseModel):
    zone_type: ZoneType
    zone_number: int
    barcode: str
    quantity_scanned: float

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
    daily_alert_time: str = "07:00"  # 07:00 AM Aden timezone as requested
    timezone: str = "Asia/Aden"  # GMT+3 Yemen timezone
    default_recipient: str = "imad@geantyemen.com"
    department_recipients: Dict[str, List[str]] = {}
    weekly_reports_enabled: bool = True
    daily_alerts_enabled: bool = True
    expiry_threshold_days: int = 7  # Default 7 days
    beverage_expiry_threshold_days: int = 15  # 15 days for S-10 Beverages
    email_failures: List[Dict[str, Any]] = []  # Track email failures for debugging
    last_test_email: Optional[datetime] = None  # Track last test email sent
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
    sections: Optional[List[str]] = []
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

# Waste Management Models
class WasteReason(str, Enum):
    DAMAGED = "damaged"
    EXPIRED = "expired"
    UNSELLABLE = "unsellable"
    CONTAMINATED = "contaminated"
    BROKEN_PACKAGING = "broken_packaging"
    QUALITY_ISSUE = "quality_issue"

class WasteEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    item_number: Optional[str] = None
    barcode: Optional[str] = None
    department: Department
    section: Section
    supplier: str
    quantity_wasted: int
    purchase_price: float
    purchase_currency: Currency
    total_waste_value: float  # quantity_wasted * purchase_price
    waste_reason: WasteReason
    notes: Optional[str] = None
    reported_by: str  # Username who reported the waste
    approved_by: Optional[str] = None  # Manager who approved the waste entry
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None

class WasteEntryCreate(BaseModel):
    product_id: str
    quantity_wasted: int
    waste_reason: WasteReason
    notes: Optional[str] = None

class WasteReport(BaseModel):
    report_period: str  # "daily", "weekly", "yearly"
    start_date: datetime
    end_date: datetime
    department: Optional[Department] = None
    section: Optional[str] = None
    currency_totals: Dict[str, float]  # {"YER": 0.0, "SAR": 0.0, "EUR": 0.0}
    total_entries: int
    total_quantity_wasted: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class WasteReportRequest(BaseModel):
    period: str  # "daily", "weekly", "yearly"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    department: Optional[Department] = None
    section: Optional[str] = None