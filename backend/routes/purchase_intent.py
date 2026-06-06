from fastapi import APIRouter, Depends
from database.purchase_intent import OrderCreate, OrderStatusUpdate, OrderOut
from database.base import SuccessResponse
from services import order_service
from utils.security import get_current_user_id
from typing import List
from db import db

router = APIRouter(prefix="/order", tags=["order"])

@router.get("/user/all", response_model=SuccessResponse[List[OrderOut]])
async def get_user_orders(current_user_id: str = Depends(get_current_user_id)):
    orders = await db.orders.find({"user_id": current_user_id}).to_list(length=100)
    return SuccessResponse(data=orders)

@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_order(data: OrderCreate, current_user_id: str = Depends(get_current_user_id)):
    order_id = await order_service.create_order(data, current_user_id)
    return SuccessResponse(message="Order created", data={"_id": order_id})

@router.get("/{order_id}", response_model=SuccessResponse[OrderOut])
async def get_order(order_id: str):
    order = await order_service.get_order(order_id)
    return SuccessResponse(data=order)

@router.patch("/status/{order_id}", response_model=SuccessResponse[dict])
async def update_order_status(order_id: str, data: OrderStatusUpdate):
    await order_service.update_order_status(order_id, data)
    return SuccessResponse(message="Order status updated")
