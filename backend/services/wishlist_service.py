from db import db
from fastapi import HTTPException


# ✅ MOVE ITEM TO CART (ATOMIC + SAFE)
async def move_item_to_cart(user_id: str, product_id: str):

    # 1️⃣ Atomically find and remove the item from the wishlist
    # Using find_one_and_update to get the removed item's details in one go
    wishlist = await db.wishlist.find_one_and_update(
        {"_id": user_id, "items.product_id": product_id},
        {"$pull": {"items": {"product_id": product_id}}},
        projection={"items.$": 1}
    )

    if not wishlist or not wishlist.get("items"):
        return "item already moved or not present"

    item = wishlist["items"][0]

    # 2️⃣ Update or insert into cart
    # Try to increment if exists
    result = await db.carts.update_one(
        {
            "_id": user_id,
            "items.product_id": product_id
        },
        {
            "$inc": {"items.$.quantity": 1}
        }
    )

    # If not in cart, push the whole item
    if result.matched_count == 0:
        await db.carts.update_one(
            {"_id": user_id},
            {
                "$push": {
                    "items": {
                        "product_id": product_id,
                        "product_name": item.get("product_name"),
                        "price": item.get("price", 0),
                        "quantity": 1
                    }
                }
            },
            upsert=True
        )

    return "moved to cart"


# ✅ BULK ADD TO WISHLIST (ATOMIC + NO DUPLICATES)
async def bulk_add_wishlist(user_id: str, product_ids: list):

    if not product_ids:
        raise HTTPException(status_code=400, detail="No products provided")

    # 🔥 fetch valid products using _id (only required fields)
    products = await db.products.find(
        {"_id": {"$in": product_ids}},
        {"product_name": 1, "price": 1}
    ).to_list(length=len(product_ids))

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    # prepare items
    items = [
        {
            "product_id": str(p["_id"]),
            "product_name": p.get("product_name"),
            "price": p.get("price", 0)
        }
        for p in products
    ]

    # ✅ ATOMIC UPSERT + NO DUPLICATES
    await db.wishlist.update_one(
        {"_id": user_id},   # 🔥 use _id only
        {
            "$addToSet": {
                "items": {"$each": items}
            }
        },
        upsert=True
    )

    return "wishlist updated"