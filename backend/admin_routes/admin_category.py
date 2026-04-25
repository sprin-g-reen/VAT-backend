from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from database.category import CategoryCreate, CategoryUpdate, CategoryOut
from database.base import SuccessResponse
from services import category_service
from dependencies.roles import require_permission
from db import db

router = APIRouter(prefix="/admin/category", tags=["Admin Category"])


# ✅ CREATE CATEGORY
@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_category(
    data: CategoryCreate,
    user=Depends(require_permission("create_category"))
):
    category_id = await category_service.create_category(data)

    return SuccessResponse(
        message="Category created",
        data={"_id": category_id}
    )


# ✅ GET ALL CATEGORIES (OPTIMIZED)
@router.get("/all", response_model=SuccessResponse[List[CategoryOut]])
async def get_all_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    user=Depends(require_permission("view_category"))
):
    query = {"is_active": True}

    # 🔍 SEARCH SUPPORT
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    categories = await db.categories.find(
        query,
        {"name": 1, "is_active": 1, "_id": 1}
    ).skip(skip).limit(limit).to_list(limit)

    # ✅ normalize _id
    for c in categories:
        c["_id"] = str(c["_id"])

    return SuccessResponse(data=categories)


# ✅ GET SINGLE CATEGORY
@router.get("/{category_id}", response_model=SuccessResponse[CategoryOut])
async def get_category(
    category_id: str,
    user=Depends(require_permission("view_category"))
):
    category = await category_service.get_category_by_id(category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return SuccessResponse(data=category)


# ✅ UPDATE CATEGORY
@router.put("/update/{category_id}", response_model=SuccessResponse[dict])
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    user=Depends(require_permission("update_category"))
):
    await category_service.update_category(category_id, data)

    return SuccessResponse(message="Category updated")


# ✅ SOFT DELETE
@router.delete("/delete/{category_id}", response_model=SuccessResponse[dict])
async def delete_category(
    category_id: str,
    user=Depends(require_permission("delete_category"))
):
    await category_service.update_category(
        category_id,
        CategoryUpdate(is_active=False)
    )

    return SuccessResponse(message="Category deactivated")


# ✅ TOGGLE STATUS
@router.patch("/status/{category_id}", response_model=SuccessResponse[dict])
async def toggle_category_status(
    category_id: str,
    user=Depends(require_permission("update_category"))
):
    category = await category_service.get_category_by_id(category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_status = not category.get("is_active", True)

    await category_service.update_category(
        category_id,
        CategoryUpdate(is_active=new_status)
    )

    return SuccessResponse(
        message="Status updated",
        data={"is_active": new_status}
    )