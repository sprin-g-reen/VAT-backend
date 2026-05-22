from fastapi import APIRouter, HTTPException
from typing import List, Optional
from db import db
from database.base import SuccessResponse
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/content-controller", tags=["Content Controller"])

@router.get("", response_model=SuccessResponse)
async def get_all_content():
    content = await db.content_controller.find({"is_active": True}).sort("display_order", 1).to_list(1000)
    return SuccessResponse(data=mongo_loads(mongo_dumps(content)))

@router.get("/{section}", response_model=SuccessResponse)
async def get_section_content(section: str):
    content = await db.content_controller.find({"section_name": section, "is_active": True}).sort("display_order", 1).to_list(1000)
    return SuccessResponse(data=mongo_loads(mongo_dumps(content)))
