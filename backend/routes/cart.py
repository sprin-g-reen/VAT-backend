from fastapi import APIRouter, HTTPException
from bson import ObjectId
from db import db

router = APIRouter()


@router.post("/add")
async def add_to_cart(user_id: str, product_id: str, quantity: int = 1):

    product = await db.products.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = {
        "product_id": ObjectId(product_id),
        "product_name": product.get("product_name"),
        "price": product.get("price", 0),
        "quantity": quantity
    }

    cart = await db.carts.find_one({"user_id": ObjectId(user_id)})

    if not cart:
        await db.carts.insert_one({
            "user_id": ObjectId(user_id),
            "items": [item]
        })
        return {"msg": "cart created + item added"}

    # check if product exists
    for existing in cart["items"]:
        if str(existing["product_id"]) == product_id:
            await db.carts.update_one(
                {
                    "user_id": ObjectId(user_id),
                    "items.product_id": ObjectId(product_id)
                },
                {
                    "$inc": {"items.$.quantity": quantity}
                }
            )
            return {"msg": "quantity updated"}

    await db.carts.update_one(
        {"user_id": ObjectId(user_id)},
        {"$push": {"items": item}}
    )

    return {"msg": "item added"}

@router.get("/{user_id}")
async def get_cart(user_id: str):

    cart = await db.carts.find_one({"user_id": ObjectId(user_id)})

    if not cart:
        return {"items": []}

    cart["_id"] = str(cart["_id"])
    cart["user_id"] = str(cart["user_id"])

    for item in cart["items"]:
        item["product_id"] = str(item["product_id"])

    return cart

@router.put("/update")
async def update_quantity(user_id: str, product_id: str, quantity: int):

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    result = await db.carts.update_one(
        {
            "user_id": ObjectId(user_id),
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
        {"user_id": ObjectId(user_id)},
        {"$pull": {"items": {"product_id": ObjectId(product_id)}}}
    )

    return {"msg": "item removed"}

@router.delete("/clear/{user_id}")
async def clear_cart(user_id: str):

    await db.carts.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": {"items": []}}
    )

    return {"msg": "cart cleared"}

@router.post("/apply-coupon")
async def apply_coupon(user_id: str, code: str):

    coupon = await db.coupons.find_one({"code": code})

    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon")

    await db.carts.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": {"coupon": coupon}}
    )

    return {"msg": "coupon applied"}

@router.get("/summary/{user_id}")
async def get_summary(user_id: str):

    cart = await db.carts.find_one({"user_id": ObjectId(user_id)})

    if not cart or not cart.get("items"):
        return {
            "subtotal": 0,
            "discount": 0,
            "shipping": 0,
            "total": 0
        }

    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])

    discount = 0
    if "coupon" in cart:
        discount = cart["coupon"].get("discount", 0)

    shipping = 0 if subtotal > 100 else 10

    total = subtotal - discount + shipping

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": total
    }

@router.post("/checkout")
async def checkout(user_id: str):

    cart = await db.carts.find_one({"user_id": ObjectId(user_id)})

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    summary = await get_summary(user_id)

    order = {
        "user_id": ObjectId(user_id),
        "items": cart["items"],
        "total_amount": summary["total"],
        "status": "PENDING"
    }

    result = await db.orders.insert_one(order)

    # clear cart after checkout
    await db.carts.update_one(
        {"user_id": ObjectId(user_id)},
        {"$set": {"items": []}}
    )

    return {"order_id": str(result.inserted_id)}

