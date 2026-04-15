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
    msg = await bulk_add_wishlist(current_user_id, data.product_ids)
    log_api_response("/wishlist/bulk-add", 200, msg)
    return SuccessResponse(message=msg)


@router.get("/", response_model=SuccessResponse[dict])
async def get_wishlist(current_user_id: str = Depends(get_current_user)):
    wishlist = await db.wishlist.find_one({"user_id": current_user_id})

    if not wishlist:
        return SuccessResponse(data={"items": []})

    wishlist["_id"] = str(wishlist["_id"])
    for item in wishlist["items"]:
        item["product_id"] = str(item["product_id"])

    return SuccessResponse(data=wishlist)


@router.delete("/remove/{product_id}", response_model=SuccessResponse[dict])
async def remove_item(product_id: str, current_user_id: str = Depends(get_current_user)):
    await db.wishlist.update_one(
        {"user_id": current_user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    return SuccessResponse(message="item removed")


@router.delete("/clear", response_model=SuccessResponse[dict])
async def clear_wishlist(current_user_id: str = Depends(get_current_user)):
    await db.wishlist.update_one(
        {"user_id": current_user_id},
        {"$set": {"items": []}}
    )

    return SuccessResponse(message="wishlist cleared")


@router.post("/move-to-cart/{product_id}", response_model=SuccessResponse[dict])
async def move_to_cart(product_id: str, current_user_id: str = Depends(get_current_user)):
    msg = await move_item_to_cart(current_user_id, product_id)
    return SuccessResponse(message=msg)
