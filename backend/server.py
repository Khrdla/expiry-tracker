from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Giant Hypermarket Inventory Tracker", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class StockTransactionType(str, Enum):
    RECEIVED = "received"
    SOLD = "sold"
    ADJUSTED = "adjusted"
    DAMAGED = "damaged"
    EXPIRED = "expired"

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

# Models
class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    category_id: str
    supplier_id: str
    unit_price: float
    cost_price: float
    status: ProductStatus = ProductStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    category_id: str
    supplier_id: str
    unit_price: float
    cost_price: float
    status: ProductStatus = ProductStatus.ACTIVE

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[str] = None
    supplier_id: Optional[str] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    status: Optional[ProductStatus] = None

class Inventory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    current_stock: int = 0
    min_stock: int = 10
    max_stock: int = 1000
    location: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    location: Optional[str] = None

class StockTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    transaction_type: StockTransactionType
    quantity: int
    reason: Optional[str] = None
    reference: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class StockTransactionCreate(BaseModel):
    product_id: str
    transaction_type: StockTransactionType
    quantity: int
    reason: Optional[str] = None
    reference: Optional[str] = None

class DashboardStats(BaseModel):
    total_products: int
    total_categories: int
    total_suppliers: int
    low_stock_items: int
    total_inventory_value: float
    recent_transactions: int

# Basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Giant Hypermarket Inventory Tracker API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Dashboard endpoint
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    try:
        # Get counts
        total_products = await db.products.count_documents({"status": {"$ne": "discontinued"}})
        total_categories = await db.categories.count_documents({})
        total_suppliers = await db.suppliers.count_documents({})
        
        # Get low stock items
        low_stock_pipeline = [
            {
                "$lookup": {
                    "from": "inventory",
                    "localField": "id",
                    "foreignField": "product_id",
                    "as": "inventory"
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$lt": [
                            {"$arrayElemAt": ["$inventory.current_stock", 0]},
                            {"$arrayElemAt": ["$inventory.min_stock", 0]}
                        ]
                    }
                }
            }
        ]
        low_stock_cursor = db.products.aggregate(low_stock_pipeline)
        low_stock_items = len(await low_stock_cursor.to_list(None))
        
        # Calculate total inventory value
        inventory_value_pipeline = [
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "id",
                    "as": "product"
                }
            },
            {
                "$project": {
                    "value": {
                        "$multiply": [
                            "$current_stock",
                            {"$arrayElemAt": ["$product.cost_price", 0]}
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_value": {"$sum": "$value"}
                }
            }
        ]
        value_cursor = db.inventory.aggregate(inventory_value_pipeline)
        value_result = await value_cursor.to_list(1)
        total_inventory_value = value_result[0]["total_value"] if value_result else 0.0
        
        # Recent transactions (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_transactions = await db.stock_transactions.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        return DashboardStats(
            total_products=total_products,
            total_categories=total_categories,
            total_suppliers=total_suppliers,
            low_stock_items=low_stock_items,
            total_inventory_value=total_inventory_value,
            recent_transactions=recent_transactions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

# Category endpoints
@api_router.post("/categories", response_model=Category)
async def create_category(category: CategoryCreate):
    try:
        category_dict = category.dict()
        category_obj = Category(**category_dict)
        await db.categories.insert_one(category_obj.dict())
        return category_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating category: {str(e)}")

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    try:
        categories = await db.categories.find().to_list(1000)
        return [Category(**cat) for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@api_router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str):
    try:
        category = await db.categories.find_one({"id": category_id})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return Category(**category)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category: {str(e)}")

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, category_update: CategoryCreate):
    try:
        update_data = category_update.dict(exclude_unset=True)
        result = await db.categories.update_one(
            {"id": category_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        
        updated_category = await db.categories.find_one({"id": category_id})
        return Category(**updated_category)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    try:
        # Check if category has products
        product_count = await db.products.count_documents({"category_id": category_id})
        if product_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete category with existing products")
        
        result = await db.categories.delete_one({"id": category_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return {"message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting category: {str(e)}")

# Supplier endpoints
@api_router.post("/suppliers", response_model=Supplier)
async def create_supplier(supplier: SupplierCreate):
    try:
        supplier_dict = supplier.dict()
        supplier_obj = Supplier(**supplier_dict)
        await db.suppliers.insert_one(supplier_obj.dict())
        return supplier_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating supplier: {str(e)}")

@api_router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers():
    try:
        suppliers = await db.suppliers.find().to_list(1000)
        return [Supplier(**sup) for sup in suppliers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching suppliers: {str(e)}")

@api_router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str):
    try:
        supplier = await db.suppliers.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return Supplier(**supplier)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching supplier: {str(e)}")

@api_router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: str, supplier_update: SupplierCreate):
    try:
        update_data = supplier_update.dict(exclude_unset=True)
        result = await db.suppliers.update_one(
            {"id": supplier_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        updated_supplier = await db.suppliers.find_one({"id": supplier_id})
        return Supplier(**updated_supplier)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating supplier: {str(e)}")

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    try:
        # Check if supplier has products
        product_count = await db.products.count_documents({"supplier_id": supplier_id})
        if product_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete supplier with existing products")
        
        result = await db.suppliers.delete_one({"id": supplier_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return {"message": "Supplier deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting supplier: {str(e)}")

# Product endpoints
@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    try:
        # Validate category and supplier exist
        category = await db.categories.find_one({"id": product.category_id})
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        
        supplier = await db.suppliers.find_one({"id": product.supplier_id})
        if not supplier:
            raise HTTPException(status_code=400, detail="Supplier not found")
        
        # Check if SKU already exists
        existing_product = await db.products.find_one({"sku": product.sku})
        if existing_product:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
        
        product_dict = product.dict()
        product_obj = Product(**product_dict)
        await db.products.insert_one(product_obj.dict())
        
        # Create initial inventory record
        inventory_obj = Inventory(product_id=product_obj.id)
        await db.inventory.insert_one(inventory_obj.dict())
        
        return product_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating product: {str(e)}")

@api_router.get("/products", response_model=List[Dict[str, Any]])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    status: Optional[ProductStatus] = None
):
    try:
        # Build filter
        filter_dict = {}
        if search:
            filter_dict["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"sku": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        if category_id:
            filter_dict["category_id"] = category_id
        if supplier_id:
            filter_dict["supplier_id"] = supplier_id
        if status:
            filter_dict["status"] = status
        
        # Aggregation pipeline to join with category, supplier, and inventory
        pipeline = [
            {"$match": filter_dict},
            {"$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "id",
                "as": "category"
            }},
            {"$lookup": {
                "from": "suppliers",
                "localField": "supplier_id",
                "foreignField": "id",
                "as": "supplier"
            }},
            {"$lookup": {
                "from": "inventory",
                "localField": "id",
                "foreignField": "product_id",
                "as": "inventory"
            }},
            {"$addFields": {
                "category_name": {"$arrayElemAt": ["$category.name", 0]},
                "supplier_name": {"$arrayElemAt": ["$supplier.name", 0]},
                "current_stock": {"$arrayElemAt": ["$inventory.current_stock", 0]},
                "min_stock": {"$arrayElemAt": ["$inventory.min_stock", 0]},
                "max_stock": {"$arrayElemAt": ["$inventory.max_stock", 0]}
            }},
            {"$project": {
                "category": 0,
                "supplier": 0,
                "inventory": 0,
                "_id": 0
            }},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        products = await db.products.aggregate(pipeline).to_list(limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@api_router.get("/products/{product_id}", response_model=Dict[str, Any])
async def get_product(product_id: str):
    try:
        pipeline = [
            {"$match": {"id": product_id}},
            {"$lookup": {
                "from": "categories",
                "localField": "category_id",
                "foreignField": "id",
                "as": "category"
            }},
            {"$lookup": {
                "from": "suppliers",
                "localField": "supplier_id",
                "foreignField": "id",
                "as": "supplier"
            }},
            {"$lookup": {
                "from": "inventory",
                "localField": "id",
                "foreignField": "product_id",
                "as": "inventory"
            }},
            {"$addFields": {
                "category_name": {"$arrayElemAt": ["$category.name", 0]},
                "supplier_name": {"$arrayElemAt": ["$supplier.name", 0]},
                "current_stock": {"$arrayElemAt": ["$inventory.current_stock", 0]},
                "min_stock": {"$arrayElemAt": ["$inventory.min_stock", 0]},
                "max_stock": {"$arrayElemAt": ["$inventory.max_stock", 0]}
            }},
            {"$project": {
                "category": 0,
                "supplier": 0,
                "inventory": 0,
                "_id": 0
            }}
        ]
        
        products = await db.products.aggregate(pipeline).to_list(1)
        if not products:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return products[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductUpdate):
    try:
        update_data = product_update.dict(exclude_unset=True)
        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.utcnow()
        
        # Validate category and supplier if provided
        if "category_id" in update_data:
            category = await db.categories.find_one({"id": update_data["category_id"]})
            if not category:
                raise HTTPException(status_code=400, detail="Category not found")
        
        if "supplier_id" in update_data:
            supplier = await db.suppliers.find_one({"id": update_data["supplier_id"]})
            if not supplier:
                raise HTTPException(status_code=400, detail="Supplier not found")
        
        result = await db.products.update_one(
            {"id": product_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        updated_product = await db.products.find_one({"id": product_id})
        return Product(**updated_product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    try:
        # Check if product exists
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete related inventory and transactions
        await db.inventory.delete_many({"product_id": product_id})
        await db.stock_transactions.delete_many({"product_id": product_id})
        
        # Delete the product
        await db.products.delete_one({"id": product_id})
        
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

# Inventory endpoints
@api_router.get("/inventory", response_model=List[Dict[str, Any]])
async def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    low_stock_only: bool = False
):
    try:
        pipeline = [
            {"$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }},
            {"$addFields": {
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_sku": {"$arrayElemAt": ["$product.sku", 0]},
                "unit_price": {"$arrayElemAt": ["$product.unit_price", 0]},
                "cost_price": {"$arrayElemAt": ["$product.cost_price", 0]},
                "is_low_stock": {"$lt": ["$current_stock", "$min_stock"]}
            }},
            {"$project": {"product": 0, "_id": 0}}
        ]
        
        if low_stock_only:
            pipeline.append({"$match": {"is_low_stock": True}})
        
        pipeline.extend([
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        inventory = await db.inventory.aggregate(pipeline).to_list(limit)
        return inventory
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inventory: {str(e)}")

@api_router.get("/inventory/{product_id}", response_model=Dict[str, Any])
async def get_product_inventory(product_id: str):
    try:
        pipeline = [
            {"$match": {"product_id": product_id}},
            {"$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }},
            {"$addFields": {
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_sku": {"$arrayElemAt": ["$product.sku", 0]},
                "unit_price": {"$arrayElemAt": ["$product.unit_price", 0]},
                "cost_price": {"$arrayElemAt": ["$product.cost_price", 0]},
                "is_low_stock": {"$lt": ["$current_stock", "$min_stock"]}
            }},
            {"$project": {"product": 0, "_id": 0}}
        ]
        
        inventory = await db.inventory.aggregate(pipeline).to_list(1)
        if not inventory:
            raise HTTPException(status_code=404, detail="Product inventory not found")
        
        return inventory[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product inventory: {str(e)}")

@api_router.put("/inventory/{product_id}", response_model=Inventory)
async def update_inventory(product_id: str, inventory_update: InventoryUpdate):
    try:
        update_data = inventory_update.dict(exclude_unset=True)
        update_data["last_updated"] = datetime.utcnow()
        
        result = await db.inventory.update_one(
            {"product_id": product_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product inventory not found")
        
        updated_inventory = await db.inventory.find_one({"product_id": product_id})
        return Inventory(**updated_inventory)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating inventory: {str(e)}")

# Stock transaction endpoints
@api_router.post("/stock-transactions", response_model=StockTransaction)
async def create_stock_transaction(transaction: StockTransactionCreate):
    try:
        # Validate product exists
        product = await db.products.find_one({"id": transaction.product_id})
        if not product:
            raise HTTPException(status_code=400, detail="Product not found")
        
        # Create transaction
        transaction_dict = transaction.dict()
        transaction_obj = StockTransaction(**transaction_dict)
        await db.stock_transactions.insert_one(transaction_obj.dict())
        
        # Update inventory based on transaction type
        inventory = await db.inventory.find_one({"product_id": transaction.product_id})
        if not inventory:
            raise HTTPException(status_code=400, detail="Product inventory not found")
        
        current_stock = inventory["current_stock"]
        
        if transaction.transaction_type in [StockTransactionType.RECEIVED]:
            new_stock = current_stock + transaction.quantity
        elif transaction.transaction_type in [StockTransactionType.SOLD, StockTransactionType.DAMAGED, StockTransactionType.EXPIRED]:
            new_stock = max(0, current_stock - transaction.quantity)
        else:  # ADJUSTED
            new_stock = transaction.quantity
        
        await db.inventory.update_one(
            {"product_id": transaction.product_id},
            {
                "$set": {
                    "current_stock": new_stock,
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        return transaction_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating stock transaction: {str(e)}")

@api_router.get("/stock-transactions", response_model=List[Dict[str, Any]])
async def get_stock_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[str] = None
):
    try:
        filter_dict = {}
        if product_id:
            filter_dict["product_id"] = product_id
        
        pipeline = [
            {"$match": filter_dict},
            {"$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }},
            {"$addFields": {
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_sku": {"$arrayElemAt": ["$product.sku", 0]}
            }},
            {"$project": {"product": 0, "_id": 0}},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        transactions = await db.stock_transactions.aggregate(pipeline).to_list(limit)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock transactions: {str(e)}")

# Reports endpoints
@api_router.get("/reports/low-stock", response_model=List[Dict[str, Any]])
async def get_low_stock_report():
    try:
        pipeline = [
            {"$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }},
            {"$match": {
                "$expr": {"$lt": ["$current_stock", "$min_stock"]}
            }},
            {"$addFields": {
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_sku": {"$arrayElemAt": ["$product.sku", 0]},
                "unit_price": {"$arrayElemAt": ["$product.unit_price", 0]},
                "shortage": {"$subtract": ["$min_stock", "$current_stock"]}
            }},
            {"$project": {"product": 0, "_id": 0}},
            {"$sort": {"shortage": -1}}
        ]
        
        low_stock_items = await db.inventory.aggregate(pipeline).to_list(1000)
        return low_stock_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating low stock report: {str(e)}")

@api_router.get("/reports/inventory-value")
async def get_inventory_value_report():
    try:
        pipeline = [
            {"$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }},
            {"$addFields": {
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_sku": {"$arrayElemAt": ["$product.sku", 0]},
                "cost_price": {"$arrayElemAt": ["$product.cost_price", 0]},
                "unit_price": {"$arrayElemAt": ["$product.unit_price", 0]},
                "inventory_cost_value": {"$multiply": ["$current_stock", {"$arrayElemAt": ["$product.cost_price", 0]}]},
                "inventory_retail_value": {"$multiply": ["$current_stock", {"$arrayElemAt": ["$product.unit_price", 0]}]}
            }},
            {"$project": {"product": 0}},
            {"$sort": {"inventory_cost_value": -1}}
        ]
        
        inventory_values = await db.inventory.aggregate(pipeline).to_list(1000)
        
        total_cost_value = sum(item["inventory_cost_value"] or 0 for item in inventory_values)
        total_retail_value = sum(item["inventory_retail_value"] or 0 for item in inventory_values)
        
        return {
            "items": inventory_values,
            "summary": {
                "total_cost_value": total_cost_value,
                "total_retail_value": total_retail_value,
                "potential_profit": total_retail_value - total_cost_value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating inventory value report: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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