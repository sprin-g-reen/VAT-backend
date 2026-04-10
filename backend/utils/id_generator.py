from pymongo import ReturnDocument


async def generate_user_id(db):
    counter = await db.counters.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    seq = counter["seq"]

    if seq > 999999:
        raise Exception("User limit exceeded (6-digit max)")

    return f"{seq:06d}"