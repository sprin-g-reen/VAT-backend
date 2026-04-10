from fastapi import APIRouter, HTTPException
from bson import ObjectId
from db import db

router = APIRouter()

async def calculate_summary(cart):

    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])

    discount = 0

    if cart.get("coupon"):
        coupon = cart["coupon"]

        if coupon.get("type") == "percent":
            discount = subtotal * (coupon["discount"] / 100)
        else:
            discount = coupon["discount"]

    shipping = 0 if subtotal > 100 else 10

    total = subtotal - discount + shipping

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": shipping,
        "total": round(total, 2)
    }


@router.post("/add")
async def add_to_cart(user_id: str, product_id: str, quantity: int = 1):

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    product = await db.products.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = {
        "product_id": ObjectId(product_id),
        "product_name": product.get("product_name"),
        "price": product.get("price", 0),
        "quantity": quantity
    }

    cart = await db.carts.find_one({"user_id": user_id})  

    if not cart:
        await db.carts.insert_one({
            "user_id": user_id,
            "items": [item],
            "coupon": None
        })
        return {"msg": "cart created + item added"}

    result = await db.carts.update_one(
        {
            "user_id": user_id,
            "items.product_id": ObjectId(product_id)
        },
        {
            "$inc": {"items.$.quantity": quantity}
        }
    )

    if result.matched_count > 0:
        return {"msg": "quantity updated"}

    await db.carts.update_one(
        {"user_id": user_id},
        {"$push": {"items": item}}
    )

    return {"msg": "item added"}


@router.get("/{user_id}")
async def get_cart(user_id: str):

    cart = await db.carts.find_one({"user_id": user_id})

    if not cart:
        return {"items": []}

    cart["_id"] = str(cart["_id"])

    for item in cart["items"]:
        item["product_id"] = str(item["product_id"])

    return cart


@router.put("/update")
async def update_quantity(user_id: str, product_id: str, quantity: int):

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    result = await db.carts.update_one(
        {
            "user_id": user_id,
            "items.product_id": ObjectId(product_id)
        },
        {
            "$set": {"items.$.quantity": quantity}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"msg": "quantity updated"}


@router.delete("/remove")
async def remove_item(user_id: str, product_id: str):

    await db.carts.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": ObjectId(product_id)}}}
    )

    return {"msg": "item removed"}


@router.delete("/clear/{user_id}")
async def clear_cart(user_id: str):

    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "coupon": None}}
    )

    return {"msg": "cart cleared"}


@router.post("/apply-coupon")
async def apply_coupon(user_id: str, code: str):

    coupon = await db.coupons.find_one({"code": code})

    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon")

    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "coupon": {
                    "code": coupon["code"],
                    "discount": coupon.get("discount", 0),
                    "type": coupon.get("type", "flat")
                }
            }
        }
    )

    return {"msg": "coupon applied"}


@router.get("/summary/{user_id}")
async def get_summary(user_id: str):

    cart = await db.carts.find_one({"user_id": user_id})

    if not cart or not cart.get("items"):
        return {
            "subtotal": 0,
            "discount": 0,
            "shipping": 0,
            "total": 0
        }

    return await calculate_summary(cart)

@router.post("/checkout")
async def checkout(user_id: str):

    cart = await db.carts.find_one({"user_id": user_id})

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    summary = await calculate_summary(cart)

    order = {
        "user_id": user_id,
        "items": cart["items"],
        "total_amount": summary["total"],
        "status": "PENDING"
    }

    result = await db.orders.insert_one(order)

    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "coupon": None}}
    )

    return {"order_id": str(result.inserted_id)}