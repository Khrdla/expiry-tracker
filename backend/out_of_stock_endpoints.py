# New endpoints for out-of-stock functionality
# This content will be added to server.py

# NEW: Out-of-stock endpoints
@api_router.get("/products/out-of-stock")
async def get_out_of_stock_products(
    section: Optional[str] = Query(None, description="Filter by section"),
    supplier: Optional[str] = Query(None, description="Filter by supplier"),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get all out-of-stock products (quantity = 0) with filtering"""
    try:
        query = {"quantity": 0}  # Out of stock = exactly 0
        
        if section:
            query["section"] = {"$regex": section, "$options": "i"}
        if supplier:
            query["supplier"] = {"$regex": supplier, "$options": "i"}
        
        products = await db.products.find(query).limit(limit).to_list(limit)
        result = []
        for product in products:
            # Ensure all products have id field (backward compatibility for imported products)
            if "id" not in product and "_id" in product:
                product["id"] = str(product["_id"])
            
            # Remove MongoDB _id to avoid serialization issues
            if "_id" in product:
                del product["_id"]
            
            # Add out-of-stock status and currency formatting
            product["is_out_of_stock"] = True
            product["stock_status"] = "Out of Stock"
            
            # Format currency display
            if product.get("purchase_price") and product.get("purchase_currency"):
                product["purchase_price_formatted"] = f"{product['purchase_price']:.2f} {product['purchase_currency']}"
            
            if product.get("selling_price"):
                product["selling_price_formatted"] = f"{product['selling_price']:.2f} YER"  # Default currency for selling
            
            result.append(product)
        
        return {
            "out_of_stock_products": result,
            "total_count": len(result),
            "filters_applied": {
                "section": section,
                "supplier": supplier
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching out-of-stock products: {str(e)}")

@api_router.get("/suppliers/dashboard")
async def get_suppliers_dashboard(
    section: Optional[str] = Query(None, description="Filter by section first"),
    current_user: User = Depends(get_current_user)
):
    """Enhanced supplier dashboard with section → supplier filtering"""
    try:
        base_match = {}
        if section:
            base_match["section"] = {"$regex": section, "$options": "i"}
        
        # High Stock Value Suppliers (ranked by total stock value)
        high_value_pipeline = [
            {"$match": {**base_match, "purchase_price": {"$exists": True, "$ne": None, "$gt": 0}}},
            {
                "$group": {
                    "_id": "$supplier",
                    "total_stock_value": {"$sum": {"$multiply": ["$quantity", "$purchase_price"]}},
                    "total_products": {"$sum": 1},
                    "total_quantity": {"$sum": "$quantity"},
                    "purchase_currency": {"$first": "$purchase_currency"},  # Get first currency found
                    "avg_purchase_price": {"$avg": "$purchase_price"}
                }
            },
            {"$sort": {"total_stock_value": -1}},
            {"$limit": 10}
        ]
        
        # Zero Stock Suppliers (list with counts of zero-stock items)
        zero_stock_pipeline = [
            {"$match": {**base_match, "quantity": 0}},
            {
                "$group": {
                    "_id": "$supplier",
                    "zero_stock_count": {"$sum": 1},
                    "zero_stock_items": {"$push": "$product_name"}
                }
            },
            {"$sort": {"zero_stock_count": -1}}
        ]
        
        # Execute pipelines
        high_value_suppliers = await db.products.aggregate(high_value_pipeline).to_list(10)
        zero_stock_suppliers = await db.products.aggregate(zero_stock_pipeline).to_list(100)
        
        # Format results
        formatted_high_value = []
        for supplier in high_value_suppliers:
            currency = supplier.get("purchase_currency", "YER")
            formatted_high_value.append({
                "supplier": supplier["_id"],
                "total_stock_value": round(supplier["total_stock_value"], 2),
                "total_stock_value_formatted": f"{supplier['total_stock_value']:,.2f} {currency}",
                "total_products": supplier["total_products"],
                "total_quantity": supplier["total_quantity"],
                "currency": currency,
                "avg_purchase_price": round(supplier.get("avg_purchase_price", 0), 2)
            })
        
        formatted_zero_stock = []
        for supplier in zero_stock_suppliers:
            formatted_zero_stock.append({
                "supplier": supplier["_id"],
                "zero_stock_count": supplier["zero_stock_count"],
                "zero_stock_items": supplier["zero_stock_items"][:5]  # Limit to first 5 items for display
            })
        
        return {
            "high_stock_value_suppliers": formatted_high_value,
            "zero_stock_suppliers": formatted_zero_stock,
            "filters_applied": {
                "section": section
            },
            "summary": {
                "total_high_value_suppliers": len(formatted_high_value),
                "total_zero_stock_suppliers": len(formatted_zero_stock),
                "section_filter": section or "All Sections"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating supplier dashboard: {str(e)}")

# NEW: Export functionality for out-of-stock products
@api_router.get("/export/out-of-stock-excel")
async def export_out_of_stock_excel(
    section: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Export out-of-stock products to Excel with proper formatting"""
    try:
        # Get out-of-stock products
        response = await get_out_of_stock_products(section=section, supplier=supplier, limit=1000, current_user=current_user)
        products = response["out_of_stock_products"]
        
        if not products:
            raise HTTPException(status_code=404, detail="No out-of-stock products found")
        
        # Create Excel file
        df_data = []
        for product in products:
            df_data.append({
                'Item Name': product.get('product_name', ''),
                'Item Number': product.get('item_number', ''),
                'Department': product.get('department', ''),
                'Section': product.get('section', ''),
                'Family': product.get('family', ''),
                'Sub Family': product.get('sub_family', ''),
                'Supplier': product.get('supplier', ''),
                'Supplier Code': product.get('supplier_code', ''),
                'Barcode': product.get('barcode', ''),
                'Quantity': product.get('quantity', 0),
                'Purchase Price': product.get('purchase_price', ''),
                'Purchase Currency': product.get('purchase_currency', 'YER'),
                'Selling Price': product.get('selling_price', ''),
                'Stock Status': 'OUT OF STOCK',
                'Location': product.get('location', ''),
                'Brand': product.get('brand', ''),
                'Description': product.get('description', ''),
                'Arabic Description': product.get('arabic_description', ''),
                'Expiry Date': product.get('expiry_date', ''),
                'Image URL': product.get('image_url', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Out of Stock Products', index=False)
        
        output.seek(0)
        
        # Generate filename
        filter_suffix = ""
        if section:
            filter_suffix += f"_section_{section}"
        if supplier:
            filter_suffix += f"_supplier_{supplier.replace(' ', '_')}"
        
        filename = f"out_of_stock_products{filter_suffix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting out-of-stock products: {str(e)}")