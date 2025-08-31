from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, timedelta
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models for Expiry Tracker
class InventoryItem(BaseModel):
    id: Optional[str] = None
    department: str = "FMCG"
    section: str
    supplier_name: str
    item_code: str
    barcode: str
    item_name: str
    stock_available: int
    expiry_date: date
    product_image: Optional[str] = None  # base64 encoded image
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryItemCreate(BaseModel):
    department: str = "FMCG"
    section: str
    supplier_name: str
    item_code: str
    barcode: str
    item_name: str
    stock_available: int
    expiry_date: date
    product_image: Optional[str] = None

class InventoryItemUpdate(BaseModel):
    department: Optional[str] = None
    section: Optional[str] = None
    supplier_name: Optional[str] = None
    item_code: Optional[str] = None
    barcode: Optional[str] = None
    item_name: Optional[str] = None
    stock_available: Optional[int] = None
    expiry_date: Optional[date] = None
    product_image: Optional[str] = None

class ExpiryAlert(BaseModel):
    total_items: int
    expiring_soon: int  # within 7 days
    expired: int
    items_expiring_soon: List[InventoryItem]
    expired_items: List[InventoryItem]

# Helper function to convert ObjectId to string
def serialize_item(item):
    if item:
        item["id"] = str(item["_id"])
        del item["_id"]
        # Convert datetime objects to ISO format strings for JSON serialization
        if "expiry_date" in item:
            if isinstance(item["expiry_date"], datetime):
                item["expiry_date"] = item["expiry_date"].date().isoformat()
            elif isinstance(item["expiry_date"], date):
                item["expiry_date"] = item["expiry_date"].isoformat()
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
        if "updated_at" in item and isinstance(item["updated_at"], datetime):
            item["updated_at"] = item["updated_at"].isoformat()
    return item

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Expiry Tracker API", "version": "1.0.0"}

# Create new inventory item
@api_router.post("/inventory", response_model=dict)
async def create_inventory_item(item: InventoryItemCreate):
    item_dict = item.dict()
    item_dict["created_at"] = datetime.utcnow()
    item_dict["updated_at"] = datetime.utcnow()
    
    # Convert date to datetime for MongoDB compatibility
    if isinstance(item_dict.get("expiry_date"), date):
        item_dict["expiry_date"] = datetime.combine(item_dict["expiry_date"], datetime.min.time())
    
    result = await db.inventory.insert_one(item_dict)
    created_item = await db.inventory.find_one({"_id": result.inserted_id})
    
    return serialize_item(created_item)

# Get all inventory items with optional filtering
@api_router.get("/inventory", response_model=List[dict])
async def get_inventory_items(
    section: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    expired_only: Optional[bool] = Query(False)
):
    query = {}
    
    if section:
        query["section"] = section
    if supplier:
        query["supplier_name"] = supplier
    
    items = await db.inventory.find(query).to_list(1000)
    items = [serialize_item(item) for item in items]
    
    if expired_only:
        today = date.today()
        items = [item for item in items if datetime.fromisoformat(item["expiry_date"]).date() < today]
    
    return items

# Get single inventory item by ID
@api_router.get("/inventory/{item_id}", response_model=dict)
async def get_inventory_item(item_id: str):
    try:
        item = await db.inventory.find_one({"_id": ObjectId(item_id)})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return serialize_item(item)
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")

# Update inventory item
@api_router.put("/inventory/{item_id}", response_model=dict)
async def update_inventory_item(item_id: str, item_update: InventoryItemUpdate):
    try:
        update_data = {k: v for k, v in item_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Convert date to datetime for MongoDB compatibility
        if "expiry_date" in update_data and isinstance(update_data["expiry_date"], date):
            update_data["expiry_date"] = datetime.combine(update_data["expiry_date"], datetime.min.time())
        
        result = await db.inventory.update_one(
            {"_id": ObjectId(item_id)}, 
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
            
        updated_item = await db.inventory.find_one({"_id": ObjectId(item_id)})
        return serialize_item(updated_item)
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")

# Delete inventory item
@api_router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    try:
        result = await db.inventory.delete_one({"_id": ObjectId(item_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")

# Get expiry alerts and analytics
@api_router.get("/analytics/expiry-alerts", response_model=dict)
async def get_expiry_alerts():
    today = date.today()
    from datetime import timedelta
    alert_date = today + timedelta(days=7)
    
    # Get all items
    all_items = await db.inventory.find().to_list(1000)
    all_items = [serialize_item(item) for item in all_items]
    
    expiring_soon = []
    expired_items = []
    
    for item in all_items:
        expiry_date = datetime.fromisoformat(item["expiry_date"]).date()
        if expiry_date < today:
            expired_items.append(item)
        elif expiry_date <= alert_date:
            expiring_soon.append(item)
    
    return {
        "total_items": len(all_items),
        "expiring_soon": len(expiring_soon),
        "expired": len(expired_items),
        "items_expiring_soon": expiring_soon,
        "expired_items": expired_items
    }

# Get analytics by supplier
@api_router.get("/analytics/by-supplier", response_model=dict)
async def get_analytics_by_supplier():
    pipeline = [
        {
            "$group": {
                "_id": "$supplier_name",
                "total_items": {"$sum": 1},
                "total_stock": {"$sum": "$stock_available"},
                "items": {"$push": "$$ROOT"}
            }
        }
    ]
    
    result = await db.inventory.aggregate(pipeline).to_list(1000)
    
    # Process expiry status for each supplier
    today = date.today()
    for supplier in result:
        expired_count = 0
        expiring_soon_count = 0
        
        for item in supplier["items"]:
            expiry_date = item["expiry_date"]
            if isinstance(expiry_date, str):
                expiry_date = datetime.fromisoformat(expiry_date).date()
                
            if expiry_date < today:
                expired_count += 1
            elif expiry_date <= today + timedelta(days=7):
                expiring_soon_count += 1
        
        supplier["expired_items"] = expired_count
        supplier["expiring_soon"] = expiring_soon_count
        del supplier["items"]  # Remove detailed items to reduce response size
    
    return {"suppliers": result}

# Get analytics by section/category
@api_router.get("/analytics/by-section", response_model=dict)
async def get_analytics_by_section():
    pipeline = [
        {
            "$group": {
                "_id": "$section",
                "total_items": {"$sum": 1},
                "total_stock": {"$sum": "$stock_available"},
                "items": {"$push": "$$ROOT"}
            }
        }
    ]
    
    result = await db.inventory.aggregate(pipeline).to_list(1000)
    
    # Process expiry status for each section
    today = date.today()
    from datetime import timedelta
    
    for section in result:
        expired_count = 0
        expiring_soon_count = 0
        
        for item in section["items"]:
            expiry_date = item["expiry_date"]
            if isinstance(expiry_date, str):
                expiry_date = datetime.fromisoformat(expiry_date).date()
                
            if expiry_date < today:
                expired_count += 1
            elif expiry_date <= today + timedelta(days=7):
                expiring_soon_count += 1
        
        section["expired_items"] = expired_count
        section["expiring_soon"] = expiring_soon_count
        del section["items"]  # Remove detailed items to reduce response size
    
    return {"sections": result}

# Search by barcode
@api_router.get("/search/barcode/{barcode}", response_model=dict)
async def search_by_barcode(barcode: str):
    item = await db.inventory.find_one({"barcode": barcode})
    if not item:
        raise HTTPException(status_code=404, detail="Item with this barcode not found")
    return serialize_item(item)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()