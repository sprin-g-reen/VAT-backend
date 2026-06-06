from fastapi import APIRouter, Depends, HTTPException
from database.payment import PaymentCreate, PaymentOut
from database.base import SuccessResponse
from services import order_service
from utils.security import get_current_user_id
from db import db
from config import Config
from typing import List, Optional
from pydantic import BaseModel
import hmac
import hashlib

router = APIRouter(prefix="/payment", tags=["payment"])


class PaymentVerifyRequest(BaseModel):
    order_id: str
    razorpay_payment_id: str
    razorpay_order_id: Optional[str] = None
    razorpay_signature: Optional[str] = None


@router.post("/create", response_model=SuccessResponse[dict], status_code=201)
async def create_payment(data: PaymentCreate):
    payment_id = await order_service.create_payment(data)
    return SuccessResponse(message="Payment recorded", data={"_id": payment_id})


@router.post("/verify", response_model=SuccessResponse[dict])
async def verify_payment(
    data: PaymentVerifyRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    # Retrieve the order
    order = await db.orders.find_one({"_id": data.order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    is_dummy = Config.RAZORPAY_KEY_ID.startswith("rzp_test_dummy") or Config.RAZORPAY_KEY_SECRET == "dummysecret456"
    
    if is_dummy:
        # Bypass signature checks for mock/dummy sandbox verification
        payment_data = PaymentCreate(
            order_id=data.order_id,
            amount_paid=order["total_amount"],
            payment_method="Razorpay (Simulated)",
            transaction_id=data.razorpay_payment_id
        )
        payment_id = await order_service.create_payment(payment_data)
        
        # Update order status to CONFIRMED
        await db.orders.update_one(
            {"_id": data.order_id},
            {"$set": {"status": "CONFIRMED"}}
        )
        
        # Clear cart atomically
        await db.carts.update_one(
            {"_id": current_user_id},
            {"$set": {"items": [], "coupon": None}}
        )
        
        return SuccessResponse(message="Simulated payment verified successfully", data={"payment_id": payment_id})

    # For real keys, verify signature
    if not data.razorpay_order_id or not data.razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing razorpay_order_id or razorpay_signature for verification")
        
    msg = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    generated_signature = hmac.new(
        Config.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(generated_signature, data.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")
        
    payment_data = PaymentCreate(
        order_id=data.order_id,
        amount_paid=order["total_amount"],
        payment_method="Razorpay",
        transaction_id=data.razorpay_payment_id
    )
    payment_id = await order_service.create_payment(payment_data)
    
    # Update order status to CONFIRMED
    await db.orders.update_one(
        {"_id": data.order_id},
        {"$set": {"status": "CONFIRMED"}}
    )
    
    # Clear cart atomically
    await db.carts.update_one(
        {"_id": current_user_id},
        {"$set": {"items": [], "coupon": None}}
    )
    
    return SuccessResponse(message="Payment verified successfully", data={"payment_id": payment_id})


@router.get("/{payment_id}", response_model=SuccessResponse[PaymentOut])
async def get_payment(payment_id: str):
    payment = await order_service.get_payment(payment_id)
    return SuccessResponse(data=payment)
