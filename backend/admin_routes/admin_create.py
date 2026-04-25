from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List

from db import db
from utils.security import hash_password

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

class CreateAdminUser(BaseModel):
    email: EmailStr
    password: str
    roles: List[str] = ["admin"]   # default role

@router.post("/create")
async def create_admin_user(payload: CreateAdminUser):

    # check if user exists
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(400, "User already exists")

    # hash password
    hashed_password = await hash_password(payload.password)

    user = {
        "_id": payload.email,   # or your custom ID generator
        "email": payload.email,
        "password": hashed_password,
        "roles": payload.roles
    }

    await db.users.insert_one(user)

    return {
        "message": "Admin user created",
        "email": payload.email
    }