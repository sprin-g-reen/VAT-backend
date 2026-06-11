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
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except OSError:
    UPLOAD_DIR = "/tmp/static/uploads/banners"
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
        # Read file bytes in memory
        file_bytes = await file.read()
        
        # Check size in memory
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
            
        # Write to local disk (if allowed by OS/container)
        try:
            with open(filepath, "wb") as buffer:
                buffer.write(file_bytes)
        except OSError:
            # Continue even if writing to local disk fails (e.g. read-only file system on Vercel)
            pass
            
        # Save to MongoDB for persistent access across serverless functions
        image_url = f"/static/uploads/banners/{filename}"
        await db.fs_files.insert_one({
            "_id": image_url,
            "filename": filename,
            "content_type": file.content_type,
            "data": file_bytes,
            "uploaded_at": datetime.utcnow()
        })
            
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=str(e))
        raise e
    
    return {"imageUrl": image_url}

@router.post("/move-up/{banner_id}", response_model=SuccessResponse)
async def move_banner_up(banner_id: str, user=Depends(require_permission("update_banner"))):
    """Move a banner up in the display order (decrease order value)"""
    banner = await db.banners.find_one({"_id": banner_id})
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    current_order = banner.get("order", 1)
    
    # Find the banner with the next lower order
    prev_banner = await db.banners.find_one(
        {"order": {"$lt": current_order}},
        sort=[("order", -1)]
    )
    
    if prev_banner:
        # Swap orders
        prev_order = prev_banner.get("order", 1)
        await db.banners.update_one({"_id": banner_id}, {"$set": {"order": prev_order, "updated_at": datetime.utcnow()}})
        await db.banners.update_one({"_id": prev_banner["_id"]}, {"$set": {"order": current_order, "updated_at": datetime.utcnow()}})
    
    await redis_client.incr("banners_version")
    return SuccessResponse(message="Banner moved up successfully")

@router.post("/move-down/{banner_id}", response_model=SuccessResponse)
async def move_banner_down(banner_id: str, user=Depends(require_permission("update_banner"))):
    """Move a banner down in the display order (increase order value)"""
    banner = await db.banners.find_one({"_id": banner_id})
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    current_order = banner.get("order", 1)
    
    # Find the banner with the next higher order
    next_banner = await db.banners.find_one(
        {"order": {"$gt": current_order}},
        sort=[("order", 1)]
    )
    
    if next_banner:
        # Swap orders
        next_order = next_banner.get("order", 1)
        await db.banners.update_one({"_id": banner_id}, {"$set": {"order": next_order, "updated_at": datetime.utcnow()}})
        await db.banners.update_one({"_id": next_banner["_id"]}, {"$set": {"order": current_order, "updated_at": datetime.utcnow()}})
    
    await redis_client.incr("banners_version")
    return SuccessResponse(message="Banner moved down successfully")
