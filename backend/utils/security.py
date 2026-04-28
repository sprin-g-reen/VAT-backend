from passlib.context import CryptContext
import jwt
import logging
from datetime import datetime, timedelta
from config import Config
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.concurrency import run_in_threadpool

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

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
from redis_db import redis_client
from utils.json_helper import mongo_dumps, mongo_loads

logger = logging.getLogger("auth-service")

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_access_token(auth.credentials)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    cache_key = f"user_cache:{user_id}"

    # Try cache first
    cached_user = None

    try:
        cached_user = await redis_client.get(cache_key)
        if cached_user:
            return mongo_loads(cached_user)
    except Exception as e:
        # Redis is down  skip cache
        logger.warning(f"Redis skipped in get_current_user: {e}")

    # DB Fallback
    user = await db.users.find_one({"_id": user_id})  # STRING ID

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Cache for 10 minutes
    await redis_client.setex(cache_key, 600, mongo_dumps(user))
    return user
