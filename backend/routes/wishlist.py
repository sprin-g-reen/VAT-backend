from fastapi import APIRouter, HTTPException, Depends
from db import db
from database.wishlist import AddToWishlistBulkRequest
from database.base import SuccessResponse
from utils.security import get_current_user
from services.wishlist_service import move_item_to_cart, bulk_add_wishlist

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


# ✅ BULK ADD
@router.post("/bulk-add", response_model=SuccessResponse[dict], status_code=201)
async def bulk_add_to_wishlist(
    data: AddToWishlistBulkRequest,
    current_user_id: str = Depends(get_current_user)
):
    if data.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    msg = await bulk_add_wishlist(data.user_id, data.product_ids)
    return SuccessResponse(message=msg)


# ✅ GET WISHLIST
@router.get("/{user_id}", response_model=SuccessResponse[dict])
async def get_wishlist(
    user_id: str,
    current_user_id: str = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        return SuccessResponse(data={"items": []})

    # ✅ normalize output
    wishlist["_id"] = str(wishlist["_id"])
    for item in wishlist.get("items", []):
        item["product_id"] = str(item["product_id"])

    return SuccessResponse(data=wishlist)


# ✅ REMOVE ITEM
@router.delete("/remove/{user_id}/{product_id}", response_model=SuccessResponse[dict])
async def remove_item(
    user_id: str,
    product_id: str,
    current_user_id: str = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.wishlist.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return SuccessResponse(message="item removed")


# ✅ CLEAR WISHLIST
@router.delete("/clear/{user_id}", response_model=SuccessResponse[dict])
async def clear_wishlist(
    user_id: str,
    current_user_id: str = Depends(get_current_user)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$set": {"items": []}}
    )

    return SuccessResponse(message="wishlist cleared")


# ✅ MOVE TO CART (FIXED BODY INPUT)
@router.post("/move-to-cart", response_model=SuccessResponse[dict], status_code=201)
async def move_item_to_cart(user_id: str, product_id: str, current_user_id: str = Depends(get_current_user)):

    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # ✅ STEP 1: ATOMIC REMOVE
    result = await db.wishlist.update_one(
        {"user_id": user_id, "items.product_id": product_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    # 👉 if nothing removed → already moved / not present
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in wishlist")

    # ✅ STEP 2: ATOMIC ADD TO CART
    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "items": {
                    "product_id": product_id,
                    "quantity": 1
                }
            }
        },
        upsert=True
    )

    return SuccessResponse(message="moved to cart")