from fastapi import APIRouter, Query
from typing import List
from db import db
from database.base import SuccessResponse

router = APIRouter(prefix="/categories", tags=["Public Categories"])


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    categories = await db.categories.find(
        {"is_active": True},
        {"name": 1}
    ).skip(skip).limit(limit).to_list(limit)

    return SuccessResponse(data=categories)