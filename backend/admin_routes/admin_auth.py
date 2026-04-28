from fastapi import APIRouter, HTTPException
from db import db
from redis_db import redis_client
from utils.security import create_access_token, verify_password
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login")
async def login(payload: LoginRequest):
    # Optimize: Fetch only necessary fields (projection)
    user = await db.users.find_one(
        {"email": payload.email},
        {"password": 1, "roles": 1, "_id": 1}
    )

    if not user:
        raise HTTPException(400, "Invalid credentials")

    #  ADMIN CHECK - Done before password verification to save CPU/Time
    user_roles = user.get("roles", [])
    if "admin" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(403, "Not an admin")

    if not await verify_password(payload.password, user["password"]):
        raise HTTPException(400, "Invalid credentials")

    # Invalidate user cache on login to ensure fresh data (optional, but good for consistency)
    await redis_client.delete(f"user_cache:{user['_id']}")

    token = create_access_token({"sub": user["_id"]})

    return {"access_token": token}