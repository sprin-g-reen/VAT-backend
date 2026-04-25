from db import db
from database.category import CategoryCreate, CategoryUpdate
from services.id_generator import generate_category_id
from fastapi import HTTPException

async def create_category(data: CategoryCreate):
    category_id = await generate_category_id(db)
    category = data.model_dump()
    category["_id"] = category_id
    await db.categories.insert_one(category)
    return category_id

async def get_all_categories(skip: int = 0, limit: int = 10):
    limit = min(limit, 100)
    return await db.categories.find(
        {"is_active": True},
        {"name": 1, "is_active": 1, "_id": 1}
    ).skip(skip).limit(limit).to_list(limit)

async def get_category(category_id: str):
    category = await db.categories.find_one({"_id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

async def update_category(category_id: str, data: CategoryUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await db.categories.update_one({"_id": category_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")

async def delete_category(category_id: str):
    result = await db.categories.delete_one({"_id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
