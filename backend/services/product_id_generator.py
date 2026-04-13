async def generate_product_id(db):
    counter = await db.counters.find_one_and_update(
        {"_id": "product_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )

    return f"PRD{counter['seq']:06d}"