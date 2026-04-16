from db import db
from fastapi import HTTPException


# ✅ MOVE ITEM TO CART (ATOMIC + SAFE)
async def move_item_to_cart(user_id: str, product_id: str):

    # 1️⃣ ATOMIC REMOVE FROM WISHLIST
    # Fetch the item before pulling it to get details like name and price
    wishlist = await db.wishlist.find_one(
        {"_id": user_id, "items.product_id": product_id},
        {"items.$": 1}
    )

    if not wishlist or not wishlist.get("items"):
        raise HTTPException(status_code=404, detail="Item not found in wishlist")

    item = wishlist["items"][0]

    # Remove from wishlist
    await db.wishlist.update_one(
        {"_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    # 2️⃣ UPDATE CART (increment if exists)
    result = await db.carts.update_one(
        {
            "_id": user_id,
            "items.product_id": product_id
        },
        {
            "$inc": {"items.$.quantity": 1}
        }
    )

    # 3️⃣ IF ITEM NOT IN CART → ADD IT
    if result.matched_count == 0:
        await db.carts.update_one(
            {"_id": user_id},
            {
                "$addToSet": {   # ✅ prevents duplicates
                    "items": {
                        "product_id": item["product_id"],
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

    # 🔥 fetch valid products using _id (Optimize: only fetch needed fields)
    products = await db.products.find(
        {"_id": {"$in": product_ids}},
        {"_id": 1, "product_name": 1, "price": 1}
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