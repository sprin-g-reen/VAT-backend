from fastapi import APIRouter, HTTPException, Depends
from db import db
from database.wishlist import AddToWishlistBulkRequest
from database.base import SuccessResponse
from utils.security import get_current_user
from utils.logging import log_api_response
from services.wishlist_service import move_item_to_cart, bulk_add_wishlist

router = APIRouter(prefix="/wishlist", tags=["wishlist"])

@router.post("/bulk-add", response_model=SuccessResponse[dict])
async def bulk_add_to_wishlist(data: AddToWishlistBulkRequest, current_user_id: str = Depends(get_current_user)):
    if data.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    msg = await bulk_add_wishlist(data.user_id, data.product_ids)
    log_api_response("/wishlist/bulk-add", 200, msg)
    return SuccessResponse(message=msg)


@router.get("/{user_id}", response_model=SuccessResponse[dict])
async def get_wishlist(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        return SuccessResponse(data={"items": []})

    wishlist["_id"] = str(wishlist["_id"])
    for item in wishlist["items"]:
        item["product_id"] = str(item["product_id"])

    return SuccessResponse(data=wishlist)


@router.delete("/remove", response_model=SuccessResponse[dict])
async def remove_item(user_id: str, product_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    return SuccessResponse(message="item removed")


@router.delete("/clear/{user_id}", response_model=SuccessResponse[dict])
async def clear_wishlist(user_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$set": {"items": []}}
    )

    return SuccessResponse(message="wishlist cleared")


@router.post("/move-to-cart", response_model=SuccessResponse[dict])
async def move_to_cart(user_id: str, product_id: str, current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    msg = await move_item_to_cart(user_id, product_id)
    return SuccessResponse(message=msg)
