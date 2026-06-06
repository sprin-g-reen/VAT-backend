from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from db import db
from redis_db import redis_client
from database.base import SuccessResponse
from utils.json_helper import mongo_dumps, mongo_loads
from services import review_service

router = APIRouter(prefix="/products", tags=["Public Products"])


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_products(
    skip: int = 0,
    limit: int = 10,
    category_id: Optional[str] = Query(None, description="Filter products by category ID"),
    popular: Optional[bool] = Query(None, description="Filter only popular products")
):
    limit = min(limit, 100)
    # Fetch current version
    version = await redis_client.get("products_version") or "0"
    cache_key = f"products:v{version}:skip={skip}:limit={limit}:cat={category_id}:popular={popular}"

    # Try cache
    cached_products = await redis_client.get(cache_key)
    if cached_products:
        return SuccessResponse(data=mongo_loads(cached_products))

    projection = {
        "product_name": 1,
        "category_id": 1,
        "subcategory_id": 1,
        "price": 1,
        "original_price": 1,
        "discounted_price": 1,
        "mrp": 1,
        "sale_price": 1,
        "stock_quantity": 1,
        "product_is_active": 1,
        "product_is_popular": 1,
        "images": 1,
        "main_image": 1,
        "additional_images": 1,
        "description": 1,
        "variants": 1,
        "_id": 1
    }

    query = {"product_is_active": True}
    if category_id:
        query["category_id"] = category_id
    if popular is not None:
        query["product_is_popular"] = popular

    products = await db.products.find(
        query,
        projection
    ).skip(skip).limit(limit).to_list(limit)

    # Add rating info to each product
    for prod in products:
        rating_info = await review_service.get_product_rating(prod["_id"])
        prod["rating"] = rating_info["average_rating"]
        prod["review_count"] = rating_info["review_count"]

    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, mongo_dumps(products))

    return SuccessResponse(data=products)


@router.get("/{product_id}", response_model=SuccessResponse[dict])
async def get_product(product_id: str):
    product = await db.products.find_one({"_id": product_id, "product_is_active": True})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Add rating info
    rating_info = await review_service.get_product_rating(product_id)
    product["rating"] = rating_info["average_rating"]
    product["review_count"] = rating_info["review_count"]

    return SuccessResponse(data=mongo_loads(mongo_dumps(product)))
