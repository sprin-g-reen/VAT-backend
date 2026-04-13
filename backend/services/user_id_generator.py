async def generate_user_id(db):
    counter = await db.counters.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )

    return f"{counter['seq']:06d}"