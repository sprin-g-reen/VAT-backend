from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Any
import uuid
from datetime import datetime

from database.content_controller import ContentControllerCreate, ContentControllerUpdate, ContentControllerOut
from database.base import SuccessResponse
from db import db
from redis_db import redis_client
from dependencies.roles import require_permission
from utils.json_helper import mongo_dumps, mongo_loads

router = APIRouter(prefix="/admin/content-controller", tags=["Admin Content Controller"])

@router.get("/all", response_model=SuccessResponse)
async def admin_get_all_content(user=Depends(require_permission("view_content"))):
    content = await db.content_controller.find().sort([("section_name", 1), ("display_order", 1)]).to_list(1000)
    return SuccessResponse(data=mongo_loads(mongo_dumps(content)))

@router.post("/create", response_model=SuccessResponse)
async def admin_create_content(content: ContentControllerCreate, user=Depends(require_permission("create_content"))):
    content_dict = content.model_dump()
    content_dict["_id"] = f"CONT{uuid.uuid4().hex[:8].upper()}"
    content_dict["created_at"] = datetime.utcnow()
    content_dict["updated_at"] = datetime.utcnow()
    
    await db.content_controller.insert_one(content_dict)
    
    # Invalidate cache if any (we might add it to storefront fetch later)
    await redis_client.incr("content_version")
    
    return SuccessResponse(message="Content created successfully", data=mongo_loads(mongo_dumps(content_dict)))

@router.put("/update/{content_id}", response_model=SuccessResponse)
async def admin_update_content(content_id: str, content: ContentControllerUpdate, user=Depends(require_permission("update_content"))):
    update_data = {k: v for k, v in content.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.content_controller.update_one({"_id": content_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    
    await redis_client.incr("content_version")
    return SuccessResponse(message="Content updated successfully")

@router.delete("/delete/{content_id}", response_model=SuccessResponse)
async def admin_delete_content(content_id: str, user=Depends(require_permission("delete_content"))):
    result = await db.content_controller.delete_one({"_id": content_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    
    await redis_client.incr("content_version")
    return SuccessResponse(message="Content deleted successfully")

@router.post("/bulk-update", response_model=SuccessResponse)
async def admin_bulk_update(items: List[dict] = Body(...), user=Depends(require_permission("update_content"))):
    # Useful for reordering
    for item in items:
        if "_id" in item:
            item_id = item.pop("_id")
            item["updated_at"] = datetime.utcnow()
            await db.content_controller.update_one({"_id": item_id}, {"$set": item})
            
    await redis_client.incr("content_version")
    return SuccessResponse(message="Bulk update successful")
