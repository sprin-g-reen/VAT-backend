from fastapi import APIRouter, Depends
from database.subcategory import SubcategoryCreate, SubcategoryUpdate, SubcategoryOut
from database.base import SuccessResponse
from services import subcategory_service
from utils.security import get_current_user
from typing import List

router = APIRouter(prefix="/subcategory", tags=["subcategory"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_subcategory(data: SubcategoryCreate, current_user_id: str = Depends(get_current_user)):
    subcategory_id = await subcategory_service.create_subcategory(data)
    return SuccessResponse(message="Subcategory created", data={"_id": subcategory_id})

@router.get("/all", response_model=SuccessResponse[List[SubcategoryOut]])
async def get_all_subcategories():
    subcategories = await subcategory_service.get_all_subcategories()
    return SuccessResponse(data=subcategories)

@router.get("/{subcategory_id}", response_model=SuccessResponse[SubcategoryOut])
async def get_subcategory(subcategory_id: str):
    subcategory = await subcategory_service.get_subcategory(subcategory_id)
    return SuccessResponse(data=subcategory)

@router.put("/update/{subcategory_id}", response_model=SuccessResponse[dict])
async def update_subcategory(subcategory_id: str, data: SubcategoryUpdate, current_user_id: str = Depends(get_current_user)):
    await subcategory_service.update_subcategory(subcategory_id, data)
    return SuccessResponse(message="Subcategory updated")

@router.delete("/delete/{subcategory_id}", response_model=SuccessResponse[dict])
async def delete_subcategory(subcategory_id: str, current_user_id: str = Depends(get_current_user)):
    await subcategory_service.delete_subcategory(subcategory_id)
    return SuccessResponse(message="Subcategory deleted")
