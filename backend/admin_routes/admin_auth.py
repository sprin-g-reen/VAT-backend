from fastapi import APIRouter, HTTPException
from db import db
from utils.security import create_access_token, verify_password
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login")
async def login(payload: LoginRequest):
    user = await db.users.find_one({"email": payload.email})

    if not user:
        raise HTTPException(400, "Invalid credentials")

    if not await verify_password(payload.password, user["password"]):
        raise HTTPException(400, "Invalid credentials")

    # 🔥 ADMIN CHECK
    if "admin" not in user.get("roles", []) and "super_admin" not in user.get("roles", []):
        raise HTTPException(403, "Not an admin")

    token = create_access_token({"sub": user["_id"]})

    return {"access_token": token}