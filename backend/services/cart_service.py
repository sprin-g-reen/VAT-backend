from db import db
from fastapi import HTTPException
from datetime import datetime


#  CALCULATE SUMMARY (OFFLOADED TO MONGODB)
async def calculate_summary(user_id: str):
    pipeline = [
        {"$match": {"_id": user_id}},
        {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$_id",
                "subtotal": {
                    "$sum": {"$multiply": ["$items.price", "$items.quantity"]}
                },
                "coupon": {"$first": "$coupon"}
            }
        },
        {
            "$project": {
                "subtotal": {"$round": ["$subtotal", 2]},
                "discount": {
                    "$cond": [
                        {"$not": ["$coupon"]},
                        0,
                        {
                            "$cond": [
                                {"$eq": ["$coupon.type", "percent"]},
                                {"$multiply": ["$subtotal", {"$divide": ["$coupon.discount", 100]}]},
                                "$coupon.discount"
                            ]
                        }
                    ]
                },
                "shipping": {
                    "$cond": [{"$gt": ["$subtotal", 100]}, 0, 10]
                }
            }
        },
        {
            "$project": {
                "subtotal": 1,
                "discount": {"$round": ["$discount", 2]},
                "shipping": 1,
                "total": {"$round": [{"$add": [{"$subtract": ["$subtotal", "$discount"]}, "$shipping"]}, 2]}
            }
        }
    ]

    result = await db.carts.aggregate(pipeline).to_list(1)

    if not result:
        return {
            "subtotal": 0,
            "discount": 0,
            "shipping": 10,
            "total": 10
        }

    return result[0]


#  BULK ADD TO CART (ATOMIC + NO DUPLICATES)
async def bulk_add_items(user_id: str, product_ids: list):
    if not product_ids:
        raise HTTPException(status_code=400, detail="No products provided")

    #  fetch valid products (only required fields)
    products = await db.products.find(
        {"_id": {"$in": product_ids}},
        {"product_name": 1, "price": 1}
    ).to_list(length=len(product_ids))

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    #  prepare items
    items = [
        {
            "product_id": str(p["_id"]),
            "product_name": p.get("product_name"),
            "price": p.get("price", 0),
            "quantity": 1
        }
        for p in products
    ]

    #  ATOMIC UPSERT (no find_one)
    await db.carts.update_one(
        {"_id": user_id},
        {
            "$addToSet": {
                "items": {"$each": items}
            }
        },
        upsert=True
    )

    return "items added to cart"


#  UPDATE QUANTITY (ATOMIC)
async def update_cart_quantity(user_id: str, product_id: str, quantity: int):

    if quantity < 1:
        # remove item if quantity = 0
        await db.carts.update_one(
            {"_id": user_id},
            {"$pull": {"items": {"product_id": product_id}}}
        )
        return "item removed"

    result = await db.carts.update_one(
        {
            "_id": user_id,
            "items.product_id": product_id
        },
        {
            "$set": {"items.$.quantity": quantity}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return "quantity updated"


#  REMOVE ITEM (ATOMIC)
async def remove_item_from_cart(user_id: str, product_id: str):

    result = await db.carts.update_one(
        {"_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return "item removed"


#  CHECKOUT (SAFE)
async def checkout_cart(user_id: str):

    # Use aggregation to get both cart items and summary in one go
    pipeline = [
        {"$match": {"_id": user_id}},
        {"$unwind": {"path": "$items", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$_id",
                "items": {"$push": "$items"},
                "subtotal": {
                    "$sum": {"$multiply": ["$items.price", "$items.quantity"]}
                },
                "coupon": {"$first": "$coupon"}
            }
        },
        {
            "$project": {
                "items": {
                    "$filter": {
                        "input": "$items",
                        "as": "item",
                        "cond": {"$ne": ["$$item", {}]}
                    }
                },
                "subtotal": {"$round": ["$subtotal", 2]},
                "discount": {
                    "$cond": [
                        {"$not": ["$coupon"]},
                        0,
                        {
                            "$cond": [
                                {"$eq": ["$coupon.type", "percent"]},
                                {"$multiply": ["$subtotal", {"$divide": ["$coupon.discount", 100]}]},
                                "$coupon.discount"
                            ]
                        }
                    ]
                },
                "shipping": {
                    "$cond": [{"$gt": ["$subtotal", 100]}, 0, 10]
                }
            }
        },
        {
            "$project": {
                "items": 1,
                "total": {"$round": [{"$add": [{"$subtract": ["$subtotal", "$discount"]}, "$shipping"]}, 2]}
            }
        }
    ]

    result = await db.carts.aggregate(pipeline).to_list(1)

    if not result or not result[0].get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart_data = result[0]

    from services.id_generator import generate_order_id
    order_id = await generate_order_id(db)

    order = {
        "_id": order_id,
        "user_id": user_id,
        "items": cart_data["items"],
        "total_amount": cart_data["total"],
        "status": "PENDING",
        "created_at": datetime.utcnow()
    }

    result = await db.orders.insert_one(order)

    #  clear cart atomically
    await db.carts.update_one(
        {"_id": user_id},
        {"$set": {"items": [], "coupon": None}}
    )

    return str(result.inserted_id)