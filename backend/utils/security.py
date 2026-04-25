from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from config import Config
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.concurrency import run_in_threadpool

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()


async def hash_password(password: str):
    return await run_in_threadpool(pwd_context.hash, password)


async def verify_password(plain, hashed):
    return await run_in_threadpool(pwd_context.verify, plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    to_encode.update({"type": "access"})
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access"):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def verify_access_token(token: str):
    return verify_token(token, "access")


from db import db

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_access_token(auth.credentials)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")

    user = await db.users.find_one({"_id": user_id})  # ✅ STRING ID

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
