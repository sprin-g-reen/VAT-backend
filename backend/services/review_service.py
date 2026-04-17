from db import db
from database.review import ReviewCreate
from services.id_generator import generate_review_id
from fastapi import HTTPException

async def create_review(data: ReviewCreate):
    # Verify product exists
    product = await db.products.find_one({"_id": data.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review_id = await generate_review_id(db)
    review = data.model_dump()
    review["_id"] = review_id
    await db.reviews.insert_one(review)
    return review_id

async def get_product_reviews(product_id: str):
    return await db.reviews.find({"product_id": product_id}).to_list(100)

async def delete_review(review_id: str, user_id: str):
    result = await db.reviews.delete_one({"_id": review_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
