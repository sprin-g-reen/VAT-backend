from db import db
from database.subcategory import SubcategoryCreate, SubcategoryUpdate
from services.id_generator import generate_subcategory_id
from fastapi import HTTPException

async def create_subcategory(data: SubcategoryCreate):
    # Check if category exists
    category = await db.categories.find_one({"_id": data.category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    subcategory_id = await generate_subcategory_id(db)
    subcategory = data.model_dump()
    subcategory["_id"] = subcategory_id
    await db.subcategories.insert_one(subcategory)
    return subcategory_id

async def get_all_subcategories():
    return await db.subcategories.find().to_list(100)

async def get_subcategory(subcategory_id: str):
    subcategory = await db.subcategories.find_one({"_id": subcategory_id})
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return subcategory

async def update_subcategory(subcategory_id: str, data: SubcategoryUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    if data.category_id:
        category = await db.categories.find_one({"_id": data.category_id})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    result = await db.subcategories.update_one({"_id": subcategory_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subcategory not found")

async def delete_subcategory(subcategory_id: str):
    result = await db.subcategories.delete_one({"_id": subcategory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subcategory not found")
