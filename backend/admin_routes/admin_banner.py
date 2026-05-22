from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime

from database.banner import BannerCreate, BannerUpdate, BannerOut
from database.base import SuccessResponse
from db import db
from redis_db import redis_client
from dependencies.roles import require_permission
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/admin/banners", tags=["Admin Banners"])

# Ensure uploads directory exists
UPLOAD_DIR = "static/uploads/banners"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/all", response_model=SuccessResponse)
async def get_all_banners(user=Depends(require_permission("view_banner"))):
    banners = await db.banners.find().sort("order", 1).to_list(100)
    return SuccessResponse(data=mongo_loads(mongo_dumps(banners)))

@router.post("/create", response_model=SuccessResponse)
async def create_banner(banner: BannerCreate, user=Depends(require_permission("create_banner"))):
    banner_dict = banner.model_dump()
    banner_dict["_id"] = f"BNR{uuid.uuid4().hex[:8].upper()}"
    banner_dict["created_at"] = datetime.utcnow()
    banner_dict["updated_at"] = datetime.utcnow()
    
    await db.banners.insert_one(banner_dict)
    
    # Invalidate cache if any
    await redis_client.incr("banners_version")
    
    return SuccessResponse(message="Banner created successfully", data=mongo_loads(mongo_dumps(banner_dict)))

@router.put("/update/{banner_id}", response_model=SuccessResponse)
async def update_banner(banner_id: str, banner: BannerUpdate, user=Depends(require_permission("update_banner"))):
    update_data = {k: v for k, v in banner.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.banners.update_one({"_id": banner_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    await redis_client.incr("banners_version")
    return SuccessResponse(message="Banner updated successfully")

@router.delete("/delete/{banner_id}", response_model=SuccessResponse)
async def delete_banner(banner_id: str, user=Depends(require_permission("delete_banner"))):
    result = await db.banners.delete_one({"_id": banner_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    await redis_client.incr("banners_version")
    return SuccessResponse(message="Banner deleted successfully")

@router.post("/upload")
async def upload_banner_image(file: UploadFile = File(...), user=Depends(require_permission("create_banner"))):
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG, PNG and WEBP are allowed")
    
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Check size after save (faster than manual chunking for typical sizes)
        if os.path.getsize(filepath) > 5 * 1024 * 1024:
            os.remove(filepath)
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
            
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=str(e))
        raise e
    
    # Return URL (relative to static mount)
    image_url = f"/static/uploads/banners/{filename}"
    return {"imageUrl": image_url}
