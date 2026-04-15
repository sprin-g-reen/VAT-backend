import importlib
import sys

py_logging = importlib.import_module("logging")

# Configure logging
py_logging.basicConfig(
    level=py_logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        py_logging.StreamHandler(sys.stdout)
    ]
)

logger = py_logging.getLogger("api_logger")

def log_api_response(endpoint: str, status_code: int, message: str):
    logger.info(f"Endpoint: {endpoint} | Status: {status_code} | Message: {message}")
