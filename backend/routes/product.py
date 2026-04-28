from fastapi import APIRouter
from typing import List
from db import db
from redis_db import redis_client
from database.base import SuccessResponse
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/products", tags=["Public Products"])


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_products(skip: int = 0, limit: int = 10):
    limit = min(limit, 100)
    # Fetch current version
    version = await redis_client.get("products_version") or "0"
    cache_key = f"products:v{version}:skip={skip}:limit={limit}"

    # Try cache
    cached_products = await redis_client.get(cache_key)
    if cached_products:
        return SuccessResponse(data=mongo_loads(cached_products))

    products = await db.products.find(
        {"product_is_active": True}
    ).skip(skip).limit(limit).to_list(limit)

    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, mongo_dumps(products))

    return SuccessResponse(data=products)