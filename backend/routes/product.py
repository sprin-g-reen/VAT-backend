from fastapi import APIRouter
from typing import List
from db import db
from database.base import SuccessResponse

router = APIRouter(prefix="/products", tags=["Public Products"])


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_products(skip: int = 0, limit: int = 10):
    limit = min(limit, 100)

    products = await db.products.find(
        {"product_is_active": True}
    ).skip(skip).limit(limit).to_list(limit)

    return SuccessResponse(data=products)