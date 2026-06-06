import asyncio
import uuid
import sys
import os
from datetime import datetime

# Ensure backend project root is on sys.path so `from db import db` works
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import db

async def insert_test_order():
    order_id = "ORD" + uuid.uuid4().hex[:12].upper()
    order = {
        "_id": order_id,
        "user_id": "test-user-123",
        "items": [
            {
                "product_id": "PROD_TEST_1",
                "name": "Test Product",
                "quantity": 1,
                "price": 199.0,
            }
        ],
        "total_amount": 199.0,
        "status": "PENDING",
        "order_created_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }
    result = await db.orders.insert_one(order)
    print("Inserted test order _id:", order_id)

if __name__ == "__main__":
    asyncio.run(insert_test_order())
