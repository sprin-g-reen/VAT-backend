from dotenv import load_dotenv
import os
load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-dev-only")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
