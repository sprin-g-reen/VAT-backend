from fastapi import APIRouter, HTTPException
from database.user_auth import (
    SignupRequest,
    SigninRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest
)
from utils.security import hash_password, verify_password
from db import db
import random

router = APIRouter()

@router.post("/signup")
async def signup(data: SignupRequest):
    # check existing
    existing = await db.users.find_one({
        "$or": [
            {"email": data.email},
            {"phone": data.phone}
        ]
    })

    if not existing:
        user = {
            "name": data.name,
            "phone": data.phone,
            "email": data.email,
            "password": hash_password(data.password),
            "profile_completed": False
        }
        result = await db.users.insert_one(user)
        return {"user_id": str(result.inserted_id)}
    
    raise HTTPException(status_code=400, detail="User already exists")


@router.post("/signin")
async def signin(data: SigninRequest):

    user = await db.users.find_one({
        "$or": [
            {"email": data.identifier},
            {"phone": data.identifier}
        ]
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "msg": "login success",
        "user_id": str(user["_id"])
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):

    user = await db.users.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))

    await db.otp.update_one(
        {"email": data.email},
        {"$set": {"otp": otp}},
        upsert=True
    )

    return {"msg": "OTP sent", "otp": otp}   # ⚠️ remove in production

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):

    record = await db.otp.find_one({"email": data.email})

    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db.users.update_one(
        {"email": data.email},
        {"$set": {"password": hash_password(data.new_password)}}
    )

    return {"msg": "Password updated"}

@router.post("/profile/{user_id}")
async def update_profile(user_id: str, data: ProfileUpdateRequest):

    # check empty fields
    if not all([data.name, data.phone, data.email, data.address]):
        raise HTTPException(status_code=400, detail="All fields required")

    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "name": data.name,
                "phone": data.phone,
                "email": data.email,
                "address": data.address,
                "profile_completed": True
            }
        }
    )

    return {"msg": "profile updated"}
