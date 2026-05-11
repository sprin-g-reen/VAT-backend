import asyncio
import logging
from arq.connections import RedisSettings
from config import Config

# Configure logging for worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("arq-worker")

REDIS_URL = Config.REDIS_URL

async def send_otp_email(ctx, email: str, otp: str):
    # Simulate heavy email sending operation
    logger.info(f"DEBUG [Worker]: Sending OTP {otp} to {email}...")
    await asyncio.sleep(2) # Simulate latency
    logger.info(f"DEBUG [Worker]: OTP sent to {email}")

class WorkerSettings:
    functions = [send_otp_email]
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
