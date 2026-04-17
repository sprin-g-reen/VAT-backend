from fastapi import APIRouter, Depends
from database.category import CategoryCreate, CategoryUpdate, CategoryOut
from database.base import SuccessResponse
from services import category_service
from utils.security import get_current_user
from typing import List

router = APIRouter(prefix="/category", tags=["category"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_category(data: CategoryCreate, current_user_id: str = Depends(get_current_user)):
    category_id = await category_service.create_category(data)
    return SuccessResponse(message="Category created", data={"_id": category_id})

@router.get("/all", response_model=SuccessResponse[List[CategoryOut]])
async def get_all_categories():
    categories = await category_service.get_all_categories()
    return SuccessResponse(data=categories)

@router.get("/{category_id}", response_model=SuccessResponse[CategoryOut])
async def get_category(category_id: str):
    category = await category_service.get_category(category_id)
    return SuccessResponse(data=category)

@router.put("/update/{category_id}", response_model=SuccessResponse[dict])
async def update_category(category_id: str, data: CategoryUpdate, current_user_id: str = Depends(get_current_user)):
    await category_service.update_category(category_id, data)
    return SuccessResponse(message="Category updated")

@router.delete("/delete/{category_id}", response_model=SuccessResponse[dict])
async def delete_category(category_id: str, current_user_id: str = Depends(get_current_user)):
    await category_service.delete_category(category_id)
    return SuccessResponse(message="Category deleted")
