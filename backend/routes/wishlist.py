from fastapi import APIRouter, HTTPException
from bson import ObjectId
from db import db

router = APIRouter()

@router.post("/add")
async def add_to_wishlist(user_id: str, product_id: str):

    product = await db.products.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = {
        "product_id": ObjectId(product_id),
        "product_name": product.get("product_name"),
        "price": product.get("price", 0)
    }

    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        await db.wishlist.insert_one({
            "user_id": user_id,
            "items": [item]
        })
        return {"msg": "wishlist created + item added"}

    exists = await db.wishlist.find_one({
        "user_id": user_id,
        "items.product_id": ObjectId(product_id)
    })

    if exists:
        return {"msg": "already in wishlist"}

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$push": {"items": item}}
    )

    return {"msg": "added to wishlist"}


@router.get("/{user_id}")
async def get_wishlist(user_id: str):

    wishlist = await db.wishlist.find_one({"user_id": user_id})

    if not wishlist:
        return {"items": []}

    wishlist["_id"] = str(wishlist["_id"])

    for item in wishlist["items"]:
        item["product_id"] = str(item["product_id"])

    return wishlist

@router.delete("/remove")
async def remove_item(user_id: str, product_id: str):

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": ObjectId(product_id)}}}
    )

    return {"msg": "item removed"}

@router.delete("/clear/{user_id}")
async def clear_wishlist(user_id: str):

    await db.wishlist.update_one(
        {"user_id": user_id},
        {"$set": {"items": []}}
    )

    return {"msg": "wishlist cleared"}

@router.post("/move-to-cart")
async def move_to_cart(user_id: str, product_id: str):

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
        {"$pull": {"items": {"product_id": ObjectId(product_id)}}}
    )

    return {"msg": "moved to cart"}