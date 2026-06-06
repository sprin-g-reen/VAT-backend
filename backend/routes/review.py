from fastapi import APIRouter, Depends
from database.review import ReviewCreate, ReviewOut
from database.base import SuccessResponse
from services import review_service
from utils.security import get_current_user_id
from typing import List

router = APIRouter(prefix="/review", tags=["review"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_review(data: ReviewCreate, current_user_id: str = Depends(get_current_user_id)):
    review_id = await review_service.create_review(data, current_user_id)
    return SuccessResponse(message="Review submitted", data={"_id": review_id})

@router.get("/product/{product_id}", response_model=SuccessResponse[List[ReviewOut]])
async def get_product_reviews(product_id: str, skip: int = 0, limit: int = 10):
    reviews = await review_service.get_product_reviews(product_id, skip, limit)
    return SuccessResponse(data=reviews)

@router.delete("/delete/{review_id}", response_model=SuccessResponse[dict])
async def delete_review(review_id: str, current_user_id: str = Depends(get_current_user_id)):
    await review_service.delete_review(review_id, current_user_id)
    return SuccessResponse(message="Review deleted")
