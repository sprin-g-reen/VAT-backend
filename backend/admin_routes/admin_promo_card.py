from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime

from database.promo_card import PromoCardCreate, PromoCardUpdate, PromoCardOut
from database.base import SuccessResponse
from db import db
from redis_db import redis_client
from dependencies.roles import require_permission
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/admin/promo-cards", tags=["Admin Promo Cards"])

# Ensure uploads directory exists
UPLOAD_DIR = "static/uploads/promo-cards"
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except OSError:
    UPLOAD_DIR = "/tmp/static/uploads/promo-cards"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/all", response_model=SuccessResponse)
async def get_all_promo_cards(user=Depends(require_permission("view_content"))):
    cards = await db.promo_cards.find().sort("order", 1).to_list(100)
    return SuccessResponse(data=mongo_loads(mongo_dumps(cards)))

@router.post("/create", response_model=SuccessResponse)
async def create_promo_card(card: PromoCardCreate, user=Depends(require_permission("create_content"))):
    card_dict = card.model_dump()
    card_dict["_id"] = f"PRM{uuid.uuid4().hex[:8].upper()}"
    card_dict["created_at"] = datetime.utcnow()
    card_dict["updated_at"] = datetime.utcnow()
    
    await db.promo_cards.insert_one(card_dict)
    
    await redis_client.incr("content_version")
    
    return SuccessResponse(message="Promo card created successfully", data=mongo_loads(mongo_dumps(card_dict)))

@router.put("/update/{card_id}", response_model=SuccessResponse)
async def update_promo_card(card_id: str, card: PromoCardUpdate, user=Depends(require_permission("update_content"))):
    update_data = {k: v for k, v in card.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.promo_cards.update_one({"_id": card_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promo card not found")
    
    await redis_client.incr("content_version")
    return SuccessResponse(message="Promo card updated successfully")

@router.delete("/delete/{card_id}", response_model=SuccessResponse)
async def delete_promo_card(card_id: str, user=Depends(require_permission("delete_content"))):
    result = await db.promo_cards.delete_one({"_id": card_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promo card not found")
    
    await redis_client.incr("content_version")
    return SuccessResponse(message="Promo card deleted successfully")

@router.post("/upload")
async def upload_promo_image(file: UploadFile = File(...), user=Depends(require_permission("create_content"))):
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
        image_url = f"/static/uploads/promo-cards/{filename}"
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
