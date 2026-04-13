from fastapi import APIRouter, HTTPException
from database.user_auth import ( 
    SignupRequest,
    SigninRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest
)
from utils.security import hash_password, verify_password
from services.user_id_generator import generate_user_id
from db import db
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/auth", tags=["auth"])


# ✅ SIGNUP
@router.post("/signup")
async def signup(data: SignupRequest):

    existing = await db.users.find_one({
        "$or": [
            {"email": data.email},
            {"phone": data.phone}
        ]
    })

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = await generate_user_id(db)

    user = {
        "_id": user_id,
        "name": data.name,
        "phone": data.phone,
        "email": data.email,
        "password": hash_password(data.password),
        "profile_completed": False
    }

    try:
        await db.users.insert_one(user)
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")

    return {
        "msg": "signup successful",
        "user_id": user_id
    }
    print("signup successful")


# ✅ SIGNIN
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
        "user_id": user["_id"]
    }


# ✅ FORGOT PASSWORD
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):

    user = await db.users.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))

    await db.otp.update_one(
        {"email": data.email},
        {
            "$set": {
                "otp": otp,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    # ⚠️ Do NOT return OTP in production
    return {"msg": "OTP sent", "otp": otp}


# ✅ RESET PASSWORD
@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):

    record = await db.otp.find_one({"email": data.email})

    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # 🔥 OTP expiry check (5 min)
    if datetime.utcnow() - record["created_at"] > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="OTP expired")

    await db.users.update_one(
        {"email": data.email},
        {"$set": {"password": hash_password(data.new_password)}}
    )

    return {"msg": "Password updated"}


# ✅ PROFILE UPDATE
@router.post("/profile/{user_id}")
async def update_profile(user_id: str, data: ProfileUpdateRequest):

    if not all([data.name, data.phone, data.email, data.address]):
        raise HTTPException(status_code=400, detail="All fields required")

    result = await db.users.update_one(
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

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"msg": "profile updated"}