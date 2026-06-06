from dotenv import load_dotenv
import os

basedir = os.path.dirname(__file__)
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-dev-only")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_dummykey123")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "dummysecret456")

if not Config.MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not configured. Set it in backend/.env or in the environment."
    )
