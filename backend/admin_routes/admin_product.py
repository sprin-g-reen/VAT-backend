from fastapi import APIRouter, Depends, HTTPException
from typing import List

from database.product import ProductCreate, ProductUpdate
from database.base import SuccessResponse
from services.product_id_generator import generate_product_id
from db import db
from redis_db import redis_client

from dependencies.roles import require_permission

router = APIRouter(prefix="/admin/product", tags=["Admin Product"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_product(
    data: ProductCreate,
    user=Depends(require_permission("create_product"))
):
    product_id = await generate_product_id(db)

    product = data.model_dump()
    product["_id"] = product_id

    #  default status (important for public UI)
    product["product_is_active"] = True

    await db.products.insert_one(product)

    # Invalidate public product cache by incrementing version
    await redis_client.incr("products_version")

    return SuccessResponse(
        message="Product created",
        data={"_id": product_id}
    )

@router.put("/update/{product_id}", response_model=SuccessResponse[dict])
async def update_product(
    product_id: str,
    data: ProductUpdate,
    user=Depends(require_permission("update_product"))
):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    result = await db.products.update_one(
        {"_id": product_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    # Invalidate public product cache by incrementing version
    await redis_client.incr("products_version")

    return SuccessResponse(message="Product updated")

@router.delete("/delete/{product_id}", response_model=SuccessResponse[dict])
async def delete_product(
    product_id: str,
    user=Depends(require_permission("delete_product"))
):
    result = await db.products.delete_one({"_id": product_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    # Invalidate public product cache by incrementing version
    await redis_client.incr("products_version")

    return SuccessResponse(message="Product deleted")

@router.get("/all", response_model=SuccessResponse[List[dict]])
async def get_all_products(
    skip: int = 0,
    limit: int = 10,
    user=Depends(require_permission("view_product"))
):
    limit = min(limit, 100)

    # Optimize: Added projection to avoid sending large fields (like description or image arrays) in list view if not needed
    # Assuming list view only needs a subset of fields
    projection = {
        "product_name": 1,
        "category_id": 1,
        "subcategory_id": 1,
        "price": 1,
        "stock_quantity": 1,
        "product_is_active": 1,
        "_id": 1
    }

    products = await db.products.find({}, projection).skip(skip).limit(limit).to_list(limit)

    return SuccessResponse(data=products)

@router.get("/{product_id}", response_model=SuccessResponse[dict])
async def get_product(
    product_id: str,
    user=Depends(require_permission("view_product"))
):
    product = await db.products.find_one({"_id": product_id})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return SuccessResponse(data=product)

@router.patch("/status/{product_id}", response_model=SuccessResponse[dict])
async def toggle_product_status(
    product_id: str,
    user=Depends(require_permission("update_product"))
):
    product = await db.products.find_one({"_id": product_id})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_status = not product.get("product_is_active", True)

    await db.products.update_one(
        {"_id": product_id},
        {"$set": {"product_is_active": new_status}}
    )

    # Invalidate public product cache by incrementing version
    await redis_client.incr("products_version")

    return SuccessResponse(
        message="Status updated",
        data={"product_is_active": new_status}
    )