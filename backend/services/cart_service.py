from db import db
from fastapi import HTTPException
from datetime import datetime

async def calculate_summary(cart):
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in cart.get("items", []))
    discount = 0

    if cart.get("coupon"):
        coupon = cart["coupon"]
        if coupon.get("type") == "percent":
            discount = subtotal * (coupon.get("discount", 0) / 100)
        else:
            discount = coupon.get("discount", 0)

    shipping = 0 if subtotal > 100 else 10
    total = subtotal - discount + shipping

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": shipping,
        "total": round(total, 2)
    }

async def bulk_add_items(user_id: str, product_ids: list):
    if not product_ids:
        raise HTTPException(status_code=400, detail="No products provided")

    products = await db.products.find({
        "product_id": {"$in": product_ids}
    }).to_list(length=len(product_ids))

    if not products:
        raise HTTPException(status_code=404, detail="No valid products found")

    cart = await db.carts.find_one({"user_id": user_id})

    if not cart:
        items = [
            {
                "product_id": p["product_id"],
                "product_name": p.get("product_name"),
                "price": p.get("price", 0),
                "quantity": 1
            }
            for p in products
        ]
        await db.carts.insert_one({
            "user_id": user_id,
            "items": items,
            "coupon": None
        })
        return "cart created with items"

    existing_items = {item["product_id"]: item for item in cart["items"]}
    for p in products:
        pid = p["product_id"]
        if pid in existing_items:
            existing_items[pid]["quantity"] += 1
        else:
            existing_items[pid] = {
                "product_id": pid,
                "product_name": p.get("product_name"),
                "price": p.get("price", 0),
                "quantity": 1
            }

    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": list(existing_items.values())}}
    )
    return "bulk items added to cart"

async def checkout_cart(user_id: str):
    cart = await db.carts.find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    summary = await calculate_summary(cart)
    order = {
        "user_id": user_id,
        "items": cart["items"],
        "total_amount": summary["total"],
        "status": "PENDING",
        "created_at": datetime.utcnow()
    }

    result = await db.orders.insert_one(order)
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "coupon": None}}
    )

    return str(result.inserted_id)
