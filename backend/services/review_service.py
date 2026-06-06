from db import db
from database.review import ReviewCreate
from services.id_generator import generate_review_id
from fastapi import HTTPException
from datetime import datetime


async def create_review(data: ReviewCreate, user_id: str):
    # Verify product exists
    product = await db.products.find_one({"_id": data.product_id}, {"_id": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Fetch user name for the review
    user = await db.users.find_one({"_id": user_id}, {"name": 1, "email": 1})
    user_name = "Anonymous"
    if user:
        user_name = user.get("name") or user.get("email", "Anonymous").split("@")[0]

    review_id = await generate_review_id(db)
    review = data.model_dump()
    review["_id"] = review_id
    review["user_id"] = user_id
    review["user_name"] = user_name
    review["review_at"] = datetime.utcnow()
    await db.reviews.insert_one(review)
    return review_id


async def get_product_reviews(product_id: str, skip: int = 0, limit: int = 10):
    limit = min(limit, 100)
    reviews = await db.reviews.find({"product_id": product_id}).sort("review_at", -1).skip(skip).limit(limit).to_list(limit)
    return reviews


async def get_product_rating(product_id: str):
    pipeline = [
        {"$match": {"product_id": product_id}},
        {
            "$group": {
                "_id": "$product_id",
                "average_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1}
            }
        }
    ]
    cursor = db.reviews.aggregate(pipeline)
    result = await cursor.to_list(1)
    if result:
        return {
            "average_rating": round(result[0]["average_rating"], 1),
            "review_count": result[0]["review_count"]
        }
    return {"average_rating": 0.0, "review_count": 0}


async def delete_review(review_id: str, user_id: str):
    result = await db.reviews.delete_one({"_id": review_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")


async def get_all_reviews(skip: int = 0, limit: int = 1000):
    """Fetch all reviews for admin panel with product and user details."""
    reviews = await db.reviews.find().sort("review_at", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich with product names
    product_ids = list(set(r.get("product_id") for r in reviews if r.get("product_id")))
    products = []
    if product_ids:
        products = await db.products.find(
            {"_id": {"$in": product_ids}},
            {"_id": 1, "product_name": 1}
        ).to_list(len(product_ids))
    product_map = {p["_id"]: p.get("product_name", "Unknown") for p in products}

    # Enrich with user names (fallback if user_name not stored)
    user_ids = list(set(r.get("user_id") for r in reviews if r.get("user_id")))
    users = []
    if user_ids:
        users = await db.users.find(
            {"_id": {"$in": user_ids}},
            {"_id": 1, "name": 1, "email": 1}
        ).to_list(len(user_ids))
    user_map = {u["_id"]: u for u in users}

    for review in reviews:
        # Add product name
        review["product_name"] = product_map.get(review.get("product_id"), "Unknown Product")
        # Ensure user_name is present
        if not review.get("user_name"):
            u_info = user_map.get(review.get("user_id"), {})
            review["user_name"] = u_info.get("name") or u_info.get("email", "Anonymous").split("@")[0]

    return reviews


async def admin_delete_review(review_id: str):
    """Admin delete — no ownership check."""
    result = await db.reviews.delete_one({"_id": review_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
