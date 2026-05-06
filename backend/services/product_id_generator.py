import uuid

async def generate_product_id(db):
    # Using UUID to avoid database bottleneck from counters collection
    return f"PRD{uuid.uuid4().hex[:12].upper()}"
