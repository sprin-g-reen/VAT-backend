from fastapi import APIRouter, HTTPException
from typing import List
from db import db
from database.base import SuccessResponse
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/banners", tags=["Banners"])

@router.get("", response_model=SuccessResponse)
async def get_active_banners():
    banners = await db.banners.find({"status": "active"}).sort("order", 1).to_list(100)
    return SuccessResponse(data=mongo_loads(mongo_dumps(banners)))
