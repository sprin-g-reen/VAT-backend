from fastapi import APIRouter, Depends
from database.order_fullfilement import ReturnCreate, ReturnStatusUpdate, ReturnOut
from database.base import SuccessResponse
from services import order_service
from typing import List

router = APIRouter(prefix="/return", tags=["return"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_return_request(data: ReturnCreate):
    return_id = await order_service.create_return_request(data)
    return SuccessResponse(message="Return request submitted", data={"_id": return_id})

@router.patch("/status/{return_id}", response_model=SuccessResponse[dict])
async def update_return_status(return_id: str, data: ReturnStatusUpdate):
    await order_service.update_return_status(return_id, data)
    return SuccessResponse(message="Return status updated")
