from logging import basicConfig, INFO, StreamHandler, getLogger
import sys

# Configure logging
basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        StreamHandler(sys.stdout)
    ]
)

logger = getLogger("api_logger")

def log_api_response(endpoint: str, status_code: int, message: str):
    logger.info(f"Endpoint: {endpoint} | Status: {status_code} | Message: {message}")
