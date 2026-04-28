from fastapi import APIRouter, HTTPException, Depends
from database.user import (
    SignupRequest,
    SigninRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest
)
from database.base import SuccessResponse
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user
)
from utils.rate_limiter import rate_limit
from services.user_id_generator import generate_user_id
from db import db
from redis_db import redis_client
from datetime import datetime, timedelta
import random
from utils.circuit_breaker import circuit_breaker

router = APIRouter(prefix="/auth", tags=["auth"])


#  SIGNUP
@router.post("/signup", response_model=SuccessResponse[dict], status_code=201)
async def signup(data: SignupRequest):

    existing = await db.users.find_one({
        "$or": [
            {"email": data.email},
            {"phone": data.phone}
        ]
    })

    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    user_id = await generate_user_id(db)

    user = {
        "_id": user_id,
        "name": data.name,
        "phone": data.phone,
        "email": data.email,
        "password": await hash_password(data.password),
        "profile_completed": False
    }

    try:
        await db.users.insert_one(user)
    except Exception:
        raise HTTPException(status_code=409, detail="User already exists")

    return SuccessResponse(
        message="signup successful",
        data={"user_id": user_id}
    )


#  SIGNIN
@router.post("/signin", response_model=SuccessResponse[dict])
@circuit_breaker(name="mongodb_auth", failure_threshold=10, recovery_timeout=60)
async def signin(data: SigninRequest):

    user = await db.users.find_one({
        "$or": [
            {"email": data.identifier},
            {"phone": data.identifier}
        ]
    }, {"password": 1, "email": 1, "phone": 1})

    # Security: Generic error message to prevent user enumeration
    if not user or not await verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["_id"]})
    refresh_token = create_refresh_token(data={"sub": user["_id"]})

    # Store refresh token in DB
    await db.refresh_tokens.update_one(
        {"_id": user["_id"]},
        {"$set": {"token": refresh_token, "created_at": datetime.utcnow()}},
        upsert=True
    )

    return SuccessResponse(
        message="login success",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user["_id"]
        }
    )


#  REFRESH TOKEN
@router.post("/refresh", response_model=SuccessResponse[dict])
async def refresh(refresh_token: str):
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    stored_token = await db.refresh_tokens.find_one({"_id": user_id})

    if not stored_token or stored_token["token"] != refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})

    # Rotate refresh token
    await db.refresh_tokens.update_one(
        {"_id": user_id},
        {"$set": {"token": new_refresh_token, "created_at": datetime.utcnow()}}
    )

    return SuccessResponse(
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    )


#  LOGOUT
@router.post("/logout", response_model=SuccessResponse[dict])
async def logout(current_user_id: str = Depends(get_current_user)):
    await db.refresh_tokens.delete_one({"_id": current_user_id})
    return SuccessResponse(message="logged out")


from fastapi import Request

#  FORGOT PASSWORD
@router.post("/forgot-password", response_model=SuccessResponse[dict])
async def forgot_password(data: ForgotPasswordRequest, request: Request):

    user = await db.users.find_one({"email": data.email})

    # Security: Generic response even if user not found to prevent enumeration
    if not user:
        return SuccessResponse(message="If an account exists with this email, an OTP has been sent.")

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

    # Offload email sending to arq worker using shared pool
    arq_pool = request.app.state.arq_pool
    await arq_pool.enqueue_job('send_otp_email', data.email, otp)

    return SuccessResponse(message="If an account exists with this email, an OTP has been sent.")


#  RESET PASSWORD
@router.post("/reset-password", response_model=SuccessResponse[dict])
async def reset_password(data: ResetPasswordRequest):

    record = await db.otp.find_one({"email": data.email})

    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    #  OTP expiry check (5 min)
    if datetime.utcnow() - record["created_at"] > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="OTP expired")

    # Get user to invalidate cache
    user = await db.users.find_one({"email": data.email}, {"_id": 1})
    if user:
        await redis_client.delete(f"user_cache:{user['_id']}")

    await db.users.update_one(
        {"email": data.email},
        {"$set": {"password": await hash_password(data.new_password)}}
    )

    return SuccessResponse(message="Password updated")


#  PROFILE UPDATE
@router.post("/profile/{user_id}", response_model=SuccessResponse[dict])
async def update_profile(user_id: str, data: ProfileUpdateRequest, current_user_id: str = Depends(get_current_user)):

    # Authorization: Ensure user is updating their own profile
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

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

    # Invalidate cache
    await redis_client.delete(f"user_cache:{user_id}")

    return SuccessResponse(message="profile updated")
