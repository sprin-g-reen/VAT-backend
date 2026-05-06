import uuid

async def generate_id(db, collection_name: str, prefix: str, padding: int = 6):
    # Using UUID to avoid database bottleneck from counters collection
    return f"{prefix}{uuid.uuid4().hex[:12].upper()}"

async def generate_category_id(db):
    return await generate_id(db, "category", "CAT")

async def generate_subcategory_id(db):
    return await generate_id(db, "subcategory", "SUB")

async def generate_review_id(db):
    return await generate_id(db, "review", "REV")

async def generate_order_id(db):
    return await generate_id(db, "order", "ORD")

async def generate_payment_id(db):
    return await generate_id(db, "payment", "PAY")

async def generate_purchase_intent_id(db):
    return await generate_id(db, "purchase_intent", "PI")

async def generate_return_id(db):
    return await generate_id(db, "return", "RET")
