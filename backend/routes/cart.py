from fastapi import APIRouter, HTTPException, Depends
from db import db
from database.cart import AddToCartBulkRequest, CartSyncRequest, CheckoutRequest, CartOut
from database.base import SuccessResponse
from utils.security import get_current_user_id
from services.cart_service import calculate_summary, bulk_add_items, checkout_cart, sync_cart_items
from typing import Optional
from config import Config
import base64
import urllib.request
import json
import logging

logger = logging.getLogger("cart-route")

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/bulk-add", response_model=SuccessResponse[dict], status_code=201)
async def bulk_add_to_cart(
    data: AddToCartBulkRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    #  use user_id from token
    msg = await bulk_add_items(current_user_id, data.product_ids)
    return SuccessResponse(message=msg)


@router.post("/sync", response_model=SuccessResponse[dict])
async def sync_cart(
    data: CartSyncRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    msg = await sync_cart_items(current_user_id, data.items)
    return SuccessResponse(message=msg)


@router.get("/", response_model=SuccessResponse[CartOut])
async def get_cart(current_user_id: str = Depends(get_current_user_id)):

    cart = await db.carts.find_one({"_id": current_user_id})

    if not cart:
        return SuccessResponse(data={"items": []})

    return SuccessResponse(data=cart)


@router.put("/update/{product_id}", response_model=SuccessResponse[dict])
async def update_quantity(
    product_id: str,
    quantity: int = 1,
    current_user_id: str = Depends(get_current_user_id)
):

    if quantity == 0:
        await db.carts.update_one(
            {"_id": current_user_id},
            {"$pull": {"items": {"product_id": product_id}}}
        )
        return SuccessResponse(message="item removed")

    if quantity < 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    result = await db.carts.update_one(
        {
            "_id": current_user_id,
            "items.product_id": product_id
        },
        {
            "$set": {"items.$.quantity": quantity}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return SuccessResponse(message="quantity updated")


@router.delete("/remove/{product_id}", response_model=SuccessResponse[dict])
async def remove_item(product_id: str, current_user_id: str = Depends(get_current_user_id)):

    await db.carts.update_one(
        {"_id": current_user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    return SuccessResponse(message="item removed")


@router.post("/checkout", response_model=SuccessResponse[dict], status_code=201)
async def checkout(
    data: Optional[CheckoutRequest] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    address_dict = data.address if data else None
    order_id = await checkout_cart(current_user_id, address_dict)
    
    # Retrieve order details to get total amount
    order = await db.orders.find_one({"_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found after creation")
        
    total_amount = order.get("total_amount", 0.0)
    amount_in_paise = int(total_amount * 100)
    
    razorpay_order_id = None
    
    # Check if we are using a dummy key
    is_dummy_key = Config.RAZORPAY_KEY_ID.startswith("rzp_test_dummy")
    
    if not is_dummy_key:
        url = "https://api.razorpay.com/v1/orders"
        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order_id,
            "payment_capture": 1,
            "notes": {
                "order_id": order_id,
                "user_id": current_user_id
            }
        }
        
        try:
            req_body = json.dumps(payload).encode("utf-8")
            auth_str = f"{Config.RAZORPAY_KEY_ID}:{Config.RAZORPAY_KEY_SECRET}"
            auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=req_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth_b64}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                res_body = response.read().decode("utf-8")
                res_data = json.loads(res_body)
                razorpay_order_id = res_data.get("id")
                logger.info(f"Created Razorpay order: {razorpay_order_id} for order: {order_id}")
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            # Fail silently and let client trigger fallback mock sandbox modal
            razorpay_order_id = None

    return SuccessResponse(data={
        "order_id": order_id,
        "razorpay_key_id": Config.RAZORPAY_KEY_ID,
        "amount": amount_in_paise,
        "currency": "INR",
        "razorpay_order_id": razorpay_order_id
    })