from fastapi import APIRouter, Query
from typing import List
from db import db
from redis_db import redis_client
from database.base import SuccessResponse
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/categories", tags=["Public Categories"])


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    # Fetch current version
    version = await redis_client.get("categories_version") or "0"
    cache_key = f"categories:v{version}:skip={skip}:limit={limit}"

    # Try cache
    cached_categories = await redis_client.get(cache_key)
    if cached_categories:
        return SuccessResponse(data=mongo_loads(cached_categories))

    categories = await db.categories.find(
        {"is_active": True},
        {"category_name": 1, "is_active": 1, "_id": 1}
    ).skip(skip).limit(limit).to_list(limit)

    # Cache for 10 minutes
    await redis_client.setex(cache_key, 600, mongo_dumps(categories))

    return SuccessResponse(data=categories)