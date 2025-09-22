#!/usr/bin/env python3
"""
Master Data Importer for Geant Hypermarket
Imports comprehensive product data from Excel master data files
"""

import pandas as pd
import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MasterDataImporter:
    def __init__(self, mongo_url: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.geant_inventory
        self.products_collection = self.db.products
        
    async def import_master_data(self, excel_file_path: str) -> Dict:
        """Import master data from Excel file"""
        try:
            logger.info(f"🚀 Starting master data import from {excel_file_path}")
            
            # Read main product data
            df = pd.read_excel(excel_file_path, sheet_name='Total  value purchase 22sept')
            logger.info(f"📊 Loaded {len(df)} products from Excel")
            
            # Process and clean data
            processed_products = await self._process_products(df)
            
            # Import to database
            import_stats = await self._import_to_database(processed_products)
            
            logger.info(f"✅ Master data import completed!")
            return import_stats
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            raise
    
    async def _process_products(self, df: pd.DataFrame) -> List[Dict]:
        """Process and clean product data"""
        products = []
        
        for index, row in df.iterrows():
            try:
                # Clean and map data
                product = {
                    "id": str(uuid.uuid4()),
                    "item_number": str(row['Item ']).strip() if pd.notna(row['Item ']) else "",
                    "product_name": str(row['Item \nName']).strip() if pd.notna(row['Item \nName']) else "",
                    "barcode": str(row['Bar \nCode']).strip() if pd.notna(row['Bar \nCode']) else "",
                    "brand": str(row['Brand']).strip() if pd.notna(row['Brand']) else "",
                    
                    # Department and classification
                    "department": str(row['Department']).strip() if pd.notna(row['Department']) else "",
                    "section": str(row['Section']).strip() if pd.notna(row['Section']) else "",
                    "family": str(row['Family']).strip() if pd.notna(row['Family']) else "",
                    "sub_family": str(row['Sub Family']).strip() if pd.notna(row['Sub Family']) else "",
                    
                    # Supplier information
                    "supplier_code": str(row['BP \nCode']).strip() if pd.notna(row['BP \nCode']) else "",
                    "supplier": str(row['Supplier \nName']).strip() if pd.notna(row['Supplier \nName']) else "",
                    
                    # Pricing
                    "purchase_price": float(row['Purchase price in YER ']) if pd.notna(row['Purchase price in YER ']) else 0.0,
                    "purchase_currency": "YER",
                    "selling_price": 0.0,  # Will be calculated or set later
                    
                    # Stock information
                    "quantity": int(row['Stock Available']) if pd.notna(row['Stock Available']) else 0,
                    "stock_value_yer": float(row['Total Stock ValueYER']) if pd.notna(row['Total Stock ValueYER']) else 0.0,
                    "stock_value_usd": float(row['Stock Value USD']) if pd.notna(row['Stock Value USD']) else 0.0,
                    "low_stock_threshold": 5,  # Default threshold
                    
                    # Classification
                    "price_group": str(row['Price Group by Family']).strip() if pd.notna(row['Price Group by Family']) else "",
                    
                    # Status determination
                    "status": self._determine_status(int(row['Stock Available']) if pd.notna(row['Stock Available']) else 0),
                    
                    # Location and metadata
                    "location": "IN-STORE",
                    "description": str(row['Item \nName']).strip() if pd.notna(row['Item \nName']) else "",
                    "arabic_description": "",  # Can be added later
                    
                    # Timestamps
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "expiry_date": None,  # Can be set per product later
                    "image_url": None,  # Can be uploaded later
                    
                    # Master data flags
                    "is_master_data": True,
                    "master_data_source": "GM_Full_Stock_230925",
                    "sr_number": int(row['SR \nNo.']) if pd.notna(row['SR \nNo.']) else 0
                }
                
                products.append(product)
                
                if len(products) % 1000 == 0:
                    logger.info(f"📝 Processed {len(products)} products...")
                    
            except Exception as e:
                logger.warning(f"⚠️  Skipping row {index}: {e}")
                continue
        
        logger.info(f"✅ Processed {len(products)} products successfully")
        return products
    
    def _determine_status(self, quantity: int) -> str:
        """Determine product status based on stock quantity"""
        if quantity == 0:
            return "out_of_stock"
        elif quantity <= 5:
            return "low_stock"
        else:
            return "in_stock"
    
    async def _import_to_database(self, products: List[Dict]) -> Dict:
        """Import processed products to database"""
        stats = {
            "total_processed": len(products),
            "imported": 0,
            "updated": 0,
            "errors": 0,
            "departments": set(),
            "sections": set(),
            "suppliers": set()
        }
        
        logger.info(f"💾 Starting database import of {len(products)} products...")
        
        for product in products:
            try:
                # Check if product exists (by barcode or item_number)
                existing = await self.products_collection.find_one({
                    "$or": [
                        {"barcode": product["barcode"]},
                        {"item_number": product["item_number"]}
                    ]
                })
                
                if existing:
                    # Update existing product with master data
                    await self.products_collection.update_one(
                        {"_id": existing["_id"]},
                        {
                            "$set": {
                                **product,
                                "updated_at": datetime.now(timezone.utc),
                                "master_data_synced": True
                            }
                        }
                    )
                    stats["updated"] += 1
                else:
                    # Insert new product
                    await self.products_collection.insert_one(product)
                    stats["imported"] += 1
                
                # Collect stats
                stats["departments"].add(product["department"])
                stats["sections"].add(product["section"])
                stats["suppliers"].add(product["supplier"])
                
                if (stats["imported"] + stats["updated"]) % 500 == 0:
                    logger.info(f"💾 Imported/Updated {stats['imported'] + stats['updated']} products...")
                    
            except Exception as e:
                logger.error(f"❌ Failed to import product {product.get('item_number', 'unknown')}: {e}")
                stats["errors"] += 1
        
        # Convert sets to counts for final stats
        stats["unique_departments"] = len(stats["departments"])
        stats["unique_sections"] = len(stats["sections"])
        stats["unique_suppliers"] = len(stats["suppliers"])
        
        # Remove sets from stats (not JSON serializable)
        del stats["departments"]
        del stats["sections"] 
        del stats["suppliers"]
        
        logger.info(f"✅ Database import completed!")
        logger.info(f"📊 Stats: {stats}")
        
        return stats
    
    async def get_import_summary(self) -> Dict:
        """Get summary of imported master data"""
        try:
            total_products = await self.products_collection.count_documents({})
            master_data_products = await self.products_collection.count_documents({"is_master_data": True})
            
            # Aggregate statistics
            pipeline = [
                {"$match": {"is_master_data": True}},
                {"$group": {
                    "_id": None,
                    "total_stock_value_yer": {"$sum": "$stock_value_yer"},
                    "total_stock_value_usd": {"$sum": "$stock_value_usd"},
                    "total_quantity": {"$sum": "$quantity"},
                    "avg_purchase_price": {"$avg": "$purchase_price"},
                    "departments": {"$addToSet": "$department"},
                    "sections": {"$addToSet": "$section"},
                    "suppliers": {"$addToSet": "$supplier"}
                }}
            ]
            
            result = await self.products_collection.aggregate(pipeline).to_list(1)
            
            if result:
                summary = result[0]
                return {
                    "total_products": total_products,
                    "master_data_products": master_data_products,
                    "total_stock_value_yer": summary.get("total_stock_value_yer", 0),
                    "total_stock_value_usd": summary.get("total_stock_value_usd", 0),
                    "total_quantity": summary.get("total_quantity", 0),
                    "avg_purchase_price": summary.get("avg_purchase_price", 0),
                    "unique_departments": len(summary.get("departments", [])),
                    "unique_sections": len(summary.get("sections", [])),
                    "unique_suppliers": len(summary.get("suppliers", []))
                }
            else:
                return {"error": "No master data found"}
                
        except Exception as e:
            logger.error(f"❌ Failed to get import summary: {e}")
            return {"error": str(e)}

async def main():
    """Main function for testing the importer"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    importer = MasterDataImporter(mongo_url)
    
    # Import master data
    excel_file = '/app/master_data.xlsx'
    if os.path.exists(excel_file):
        stats = await importer.import_master_data(excel_file)
        print(f"📊 Import Stats: {stats}")
        
        # Get summary
        summary = await importer.get_import_summary()
        print(f"📈 Import Summary: {summary}")
    else:
        print(f"❌ Excel file not found: {excel_file}")

if __name__ == "__main__":
    asyncio.run(main())