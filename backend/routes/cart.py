from fastapi import APIRouter, HTTPException, Depends
from db import db
from database.cart import AddToCartBulkRequest
from database.base import SuccessResponse
from utils.security import get_current_user
from utils.logging import log_api_response
from services.cart_service import calculate_summary, bulk_add_items, checkout_cart

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/bulk-add", response_model=SuccessResponse[dict])
async def bulk_add_to_cart(data: AddToCartBulkRequest, current_user_id: str = Depends(get_current_user)):
    if data.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    msg = await bulk_add_items(data.user_id, data.product_ids)
    log_api_response("/cart/bulk-add", 200, msg)
    return SuccessResponse(message=msg)


@router.get("/{user_id}", response_model=SuccessResponse[dict])
async def get_cart(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    cart = await db.carts.find_one({"user_id": user_id})

    if not cart:
        return SuccessResponse(data={"items": []})

    cart["_id"] = str(cart["_id"])
    for item in cart["items"]:
        item["product_id"] = str(item["product_id"])

    return SuccessResponse(data=cart)


@router.put("/update", response_model=SuccessResponse[dict])
async def update_quantity(user_id: str, product_id: str, quantity: int, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    result = await db.carts.update_one(
        {
            "user_id": user_id,
            "items.product_id": product_id
        },
        {
            "$set": {"items.$.quantity": quantity}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return SuccessResponse(message="quantity updated")


@router.delete("/remove", response_model=SuccessResponse[dict])
async def remove_item(user_id: str, product_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.carts.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    return SuccessResponse(message="item removed")


@router.delete("/clear/{user_id}", response_model=SuccessResponse[dict])
async def clear_cart(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "coupon": None}}
    )

    return SuccessResponse(message="cart cleared")


@router.post("/apply-coupon", response_model=SuccessResponse[dict])
async def apply_coupon(user_id: str, code: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    coupon = await db.coupons.find_one({"code": code})
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon")

    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "coupon": {
                    "code": coupon["code"],
                    "discount": coupon.get("discount", 0),
                    "type": coupon.get("type", "flat")
                }
            }
        }
    )

    return SuccessResponse(message="coupon applied")


@router.get("/summary/{user_id}", response_model=SuccessResponse[dict])
async def get_summary(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    cart = await db.carts.find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        return SuccessResponse(data={
            "subtotal": 0,
            "discount": 0,
            "shipping": 0,
            "total": 0
        })

    summary = await calculate_summary(cart)
    return SuccessResponse(data=summary)


@router.post("/checkout", response_model=SuccessResponse[dict])
async def checkout(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    order_id = await checkout_cart(user_id)
    return SuccessResponse(data={"order_id": order_id})
