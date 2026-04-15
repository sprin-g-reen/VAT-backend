import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("api_logger")

def log_api_response(endpoint: str, status_code: int, message: str):
    logger.info(f"Endpoint: {endpoint} | Status: {status_code} | Message: {message}")
