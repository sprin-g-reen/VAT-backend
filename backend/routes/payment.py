from fastapi import APIRouter, Depends
from database.payment import PaymentCreate, PaymentOut
from database.base import SuccessResponse
from services import order_service
from typing import List

router = APIRouter(prefix="/payment", tags=["payment"])

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_payment(data: PaymentCreate):
    payment_id = await order_service.create_payment(data)
    return SuccessResponse(message="Payment recorded", data={"_id": payment_id})

@router.get("/{payment_id}", response_model=SuccessResponse[PaymentOut])
async def get_payment(payment_id: str):
    payment = await order_service.get_payment(payment_id)
    return SuccessResponse(data=payment)
