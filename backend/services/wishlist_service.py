from db import db
from fastapi import HTTPException

async def move_item_to_cart(user_id: str, product_id: str):
    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist empty")

    item = next(
        (i for i in wishlist["items"] if str(i["product_id"]) == product_id),
        None
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await db.carts.update_one(
        {
            "user_id": user_id,
            "items.product_id": item["product_id"]
        },
        {
            "$inc": {"items.$.quantity": 1}
        }
    )

    if result.matched_count == 0:
        await db.carts.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "items": {
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "price": item["price"],
                        "quantity": 1
                    }
                }
            },
            upsert=True
        )

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )
    return "moved to cart"

async def bulk_add_wishlist(user_id: str, product_ids: list):
    if not product_ids:
        raise HTTPException(status_code=400, detail="No products provided")

    products = await db.products.find({
        "product_id": {"$in": product_ids}
    }).to_list(length=len(product_ids))

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    items = [
        {
            "product_id": p["product_id"],
            "product_name": p.get("product_name"),
            "price": p.get("price", 0)
        }
        for p in products
    ]

    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        await db.wishlist.insert_one({
            "user_id": user_id,
            "items": items
        })
        return "wishlist created with items"

    await db.wishlist.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {
                "items": {"$each": items}
            }
        }
    )
    return "bulk items added"
