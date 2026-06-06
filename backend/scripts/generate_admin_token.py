import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import db
from utils.security import create_access_token

async def gen():
    admin = await db.users.find_one({"roles": {"$in": ["admin", "super_admin"]}})
    if not admin:
        print("No admin user found in users collection")
        return
    token = create_access_token({"sub": admin["_id"]})
    print("Admin user id:", admin["_id"])
    print("Token:\n", token)

if __name__ == '__main__':
    asyncio.run(gen())
