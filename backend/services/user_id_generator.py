import uuid

async def generate_user_id(db):
    # Direct UUID generation to avoid unnecessary database lookups and loops
    return uuid.uuid4().hex[:12]
