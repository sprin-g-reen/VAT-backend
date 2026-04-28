from fastapi import APIRouter, HTTPException, Depends
from db import db
from database.cart import AddToCartBulkRequest
from database.base import SuccessResponse
from utils.security import get_current_user
from services.cart_service import calculate_summary, bulk_add_items, checkout_cart

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/bulk-add", response_model=SuccessResponse[dict], status_code=201)
async def bulk_add_to_cart(
    data: AddToCartBulkRequest,
    current_user_id: str = Depends(get_current_user)
):
    #  use user_id from token
    msg = await bulk_add_items(current_user_id, data.product_ids)
    return SuccessResponse(message=msg)


@router.get("/", response_model=SuccessResponse[dict])
async def get_cart(current_user_id: str = Depends(get_current_user)):

    cart = await db.carts.find_one({"_id": current_user_id})

    if not cart:
        return SuccessResponse(data={"items": []})

    return SuccessResponse(data=cart)


@router.put("/update/{product_id}", response_model=SuccessResponse[dict])
async def update_quantity(
    product_id: str,
    quantity: int = 1,
    current_user_id: str = Depends(get_current_user)
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
async def remove_item(product_id: str, current_user_id: str = Depends(get_current_user)):

    await db.carts.update_one(
        {"_id": current_user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    return SuccessResponse(message="item removed")


@router.post("/checkout", response_model=SuccessResponse[dict], status_code=201)
async def checkout(current_user_id: str = Depends(get_current_user)):

    order_id = await checkout_cart(current_user_id)
    return SuccessResponse(data={"order_id": order_id})