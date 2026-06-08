from db import db
from database.purchase_intent import OrderCreate, OrderStatusUpdate
from database.payment import PaymentCreate
from database.order_fullfilement import ReturnCreate, ReturnStatusUpdate
from services.id_generator import (
    generate_order_id,
    generate_payment_id,
    generate_purchase_intent_id,
    generate_review_id
)
from fastapi import HTTPException
from datetime import datetime
import logging

logger = logging.getLogger("order-service")

# ORDER SERVICES
async def create_order(data: OrderCreate, user_id: str):
    # In a real app, we'd fetch items from the cart here.
    # For now, we'll implement basic CRUD that allows passing items for testing purposes
    # but the user requested basic CRUD without Razorpay.
    order_id = await generate_order_id(db)
    order = data.model_dump()
    order["_id"] = order_id
    order["user_id"] = user_id
    order["status"] = "PENDING"

    # Ensure items and total_amount are present if provided in the schema,
    # though OrderCreate doesn't have them, OrderOut does.
    # Since we are doing "basic CRUD", we'll allow the service to take what's in data
    # and set defaults if missing.
    if "items" not in order:
        order["items"] = []
    if "total_amount" not in order:
        order["total_amount"] = 0

    order["order_created_at"] = datetime.utcnow()
    order["created_at"] = order["order_created_at"]
    await db.orders.insert_one(order)
    logger.info(f"Created order {order_id} for user {user_id} with total {order.get('total_amount')}")
    return order_id

async def get_order(order_id: str):
    order = await db.orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Retrieve user info to populate customer_name and customer_email
    uid = order.get("user_id")
    if isinstance(uid, dict):
        uid = uid.get("_id")
    if uid:
        user = await db.users.find_one({"_id": uid}, {"name": 1, "email": 1})
        if user:
            order["customer_name"] = user.get("name") or user.get("email", "Guest").split("@")[0]
            order["customer_email"] = user.get("email") or ""
    return order

async def update_order_status(order_id: str, data: OrderStatusUpdate):
    result = await db.orders.update_one(
        {"_id": order_id},
        {"$set": {"status": data.status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

# PAYMENT SERVICES
async def create_payment(data: PaymentCreate):
    payment_id = await generate_payment_id(db)
    payment = data.model_dump()
    payment["_id"] = payment_id
    payment["payment_status"] = "SUCCESS"
    payment["paid_at"] = datetime.utcnow()
    await db.payments.insert_one(payment)
    return payment_id

async def get_payment(payment_id: str):
    payment = await db.payments.find_one({"_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

# RETURN SERVICES (Order Fullfillment)
async def create_return_request(data: ReturnCreate, user_id: str):
    return_id = await generate_purchase_intent_id(db) # Reusing this for return IDs or we can add generate_return_id
    return_req = data.model_dump()
    return_req["_id"] = return_id
    return_req["user_id"] = user_id
    return_req["return_status"] = "REQUESTED"
    return_req["return_created_at"] = datetime.utcnow()
    await db.returns.insert_one(return_req)
    return return_id

async def update_return_status(return_id: str, data: ReturnStatusUpdate):
    result = await db.returns.update_one(
        {"_id": return_id},
        {"$set": {"return_status": data.status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Return request not found")
