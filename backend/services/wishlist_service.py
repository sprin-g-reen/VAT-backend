from db import db
from fastapi import HTTPException
from pymongo import ReturnDocument


#  BULK ADD (ATOMIC + NO DUPLICATES)
async def bulk_add_wishlist(user_id: str, product_ids: list):

    if not product_ids:
        raise HTTPException(status_code=400, detail="No products provided")

    products = await db.products.find({
        "_id": {"$in": product_ids}
    }).to_list(length=len(product_ids))

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    items = [
        {
            "product_id": str(p["_id"]),
            "product_name": p.get("product_name"),
            "price": p.get("price", 0)
        }
        for p in products
    ]

    await db.wishlist.update_one(
        {"_id": user_id},
        {"$addToSet": {"items": {"$each": items}}},
        upsert=True
    )

    return "items added to wishlist"


#  MOVE TO CART (FULL ATOMIC FLOW)
async def move_item_to_cart(user_id: str, product_id: str):

    #  ATOMIC: remove item from wishlist and return it
    wishlist = await db.wishlist.find_one_and_update(
        {"_id": user_id, "items.product_id": product_id},
        {"$pull": {"items": {"product_id": product_id}}},
        return_document=ReturnDocument.BEFORE
    )

    if not wishlist:
        raise HTTPException(status_code=404, detail="Item not in wishlist")

    item = next(
        (i for i in wishlist["items"] if i["product_id"] == product_id),
        None
    )

    #  ATOMIC CART UPDATE
    await db.carts.update_one(
        {"_id": user_id, "items.product_id": product_id},
        {"$inc": {"items.$.quantity": 1}}
    )

    await db.carts.update_one(
        {"_id": user_id, "items.product_id": {"$ne": product_id}},
        {
            "$push": {
                "items": {
                    "product_id": product_id,
                    "product_name": item["product_name"],
                    "price": item["price"],
                    "quantity": 1
                }
            }
        },
        upsert=True
    )

    return "moved to cart"