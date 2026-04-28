from fastapi import APIRouter, HTTPException, Depends, Query
from db import db
from database.wishlist import AddToWishlistBulkRequest
from database.base import SuccessResponse
from utils.security import get_current_user
from services.wishlist_service import move_item_to_cart, bulk_add_wishlist

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


#  BULK ADD
@router.post("/bulk-add", response_model=SuccessResponse[dict])
async def bulk_add_to_wishlist(
    data: AddToWishlistBulkRequest,
    current_user_id: str = Depends(get_current_user)
):
    msg = await bulk_add_wishlist(current_user_id, data.product_ids)
    return SuccessResponse(message=msg)


#  GET WISHLIST
@router.get("/", response_model=SuccessResponse[dict])
async def get_wishlist(current_user_id: str = Depends(get_current_user)):

    wishlist = await db.wishlist.find_one(
        {"_id": current_user_id},
        {"items": 1}
    )

    if not wishlist:
        return SuccessResponse(data={"items": []})

    return SuccessResponse(data=wishlist)


#  REMOVE ITEM
@router.delete("/remove/{product_id}", response_model=SuccessResponse[dict])
async def remove_item(
    product_id: str,
    current_user_id: str = Depends(get_current_user)
):
    result = await db.wishlist.update_one(
        {"_id": current_user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return SuccessResponse(message="item removed")


#  CLEAR WISHLIST
@router.delete("/clear", response_model=SuccessResponse[dict])
async def clear_wishlist(current_user_id: str = Depends(get_current_user)):

    await db.wishlist.update_one(
        {"_id": current_user_id},
        {"$set": {"items": []}}
    )

    return SuccessResponse(message="wishlist cleared")


#  MOVE TO CART (QUERY PARAM)
@router.post("/move-to-cart", response_model=SuccessResponse[dict])
async def move_to_cart_api(
    product_id: str = Query(...),
    current_user_id: str = Depends(get_current_user)
):
    msg = await move_item_to_cart(current_user_id, product_id)
    return SuccessResponse(message=msg)