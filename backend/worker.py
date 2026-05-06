import asyncio
import logging
from arq import create_pool
from arq.connections import RedisSettings
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging for worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("arq-worker")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

async def send_otp_email(ctx, email: str, otp: str):
    # Simulate heavy email sending operation
    logger.info(f"DEBUG [Worker]: Sending OTP {otp} to {email}...")
    await asyncio.sleep(2) # Simulate latency
    logger.info(f"DEBUG [Worker]: OTP sent to {email}")

class WorkerSettings:
    functions = [send_otp_email]
    redis_settings = RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD
    )
