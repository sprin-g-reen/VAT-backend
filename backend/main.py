import sys
import os
# Add backend directory to path so imports resolve correctly on Vercel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import (

    user_auth,
    cart,
    wishlist,
    product,
    category,
    subcategory,
    banner,
    promo_card,
    content_controller,
    address,
    payment,
    purchase_intent,
    order_fullfilement,
    review,
    analytics_tracker,
)
from admin_routes import (
    admin_auth,
    admin_product,
    admin_category,
    admin_roles,
    admin_create,
    admin_banner,
    admin_promo_card,
    admin_content_controller,
    admin_analytics,
    admin_order,
    admin_review,
)
from db import db, verify_mongodb_connection
from database.base import ErrorResponse, SuccessResponse
from redis_db import redis_client
from dependencies.roles import ensure_default_admin_roles
from config import Config
import time
import psutil
from arq import create_pool
from arq.connections import RedisSettings
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auth-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    # Mandatory MongoDB Check
    if not await verify_mongodb_connection():
        logger.critical("Failed to connect to MongoDB. Exiting...")
        import sys
        sys.exit(1)

    # USERS
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("phone", unique=True, sparse=True)
    await db.users.create_index([("email", 1), ("password", 1)])
    await db.users.create_index([("phone", 1), ("password", 1)])

    # CART
    await db.carts.create_index("items.product_id")

    # WISHLIST
    await db.wishlist.create_index("items.product_id")

    # OTP (with TTL of 5 minutes)
    await db.otp.create_index("email", unique=True)
    await db.otp.create_index("created_at", expireAfterSeconds=300)

    # REFRESH TOKENS (TTL 7 days)
    await db.refresh_tokens.create_index("created_at", expireAfterSeconds=7 * 24 * 3600)

    # PRODUCTS
    await db.products.create_index("category_id")
    await db.products.create_index("subcategory_id")
    await db.products.create_index("product_name")
    await db.products.create_index([("product_name", "text"), ("description", "text")])
    await db.products.create_index([("product_is_active", 1), ("_id", 1)])

    # SUBCATEGORIES
    await db.subcategories.create_index("category_id")

    # REVIEWS
    await db.reviews.create_index("product_id")
    await db.reviews.create_index("user_id")

    # ORDERS
    await db.orders.create_index("user_id")
    await db.orders.create_index("status")

    # PAYMENTS
    await db.payments.create_index("order_id")

    # RETURNS
    await db.returns.create_index("order_id")
    await db.returns.create_index("user_id")

    await db.categories.create_index("category_name")
    await db.categories.create_index("is_active")

    # BANNERS
    await db.banners.create_index("order")
    await db.banners.create_index("status")

    # PROMO CARDS
    await db.promo_cards.create_index("order")
    await db.promo_cards.create_index("status")

    # PAGE ANALYTICS
    await db.page_analytics.create_index("timestamp")
    await db.page_analytics.create_index("page")
    await db.page_analytics.create_index([("page", 1), ("timestamp", 1)])

    # Backfill reserved roles for admin users created before RBAC was introduced.
    await ensure_default_admin_roles()

    # Initialize ARQ pool
    try:
        redis_url = Config.REDIS_URL
        app.state.arq_pool = await asyncio.wait_for(
            create_pool(RedisSettings.from_dsn(redis_url)),
            timeout=10.0  # Increased timeout for stability
        )
        logger.info("Redis connected (ARQ pool initialized)")
    except Exception as e:
        logger.warning(f"Redis skipped (ARQ pool failed): {e}")
        app.state.arq_pool = None

    yield

    # SHUTDOWN
    if hasattr(app.state, "arq_pool") and app.state.arq_pool:
        await app.state.arq_pool.close()
        logger.info("Redis ARQ pool closed")


app = FastAPI(
    title="Auth Service API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: allow the frontend origin(s). For development include http://localhost:3000 and Live Server ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return {"msg": "Auth service running"}


@app.get("/health")
async def health_check():
    redis_status = "ok"
    try:
        client = await redis_client.get_client()
        if not client:
            redis_status = "down"
    except:
        redis_status = "down"

    return {
        "status": "healthy",
        "redis": redis_status
}


@app.get("/metrics")
async def metrics():
    # Basic metrics for monitoring
    process = psutil.Process(os.getpid())
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "uptime": time.time(),
        "memory_usage_mb": process.memory_info().rss / (1024 * 1024),
        "cpu_percent": psutil.cpu_percent(),
        "active_threads": process.num_threads(),
        "arq_pool_connected": hasattr(app.state, "arq_pool") and app.state.arq_pool is not None
    }


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user_auth.router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(product.router)
app.include_router(category.router)
app.include_router(subcategory.router)
app.include_router(banner.router)
app.include_router(promo_card.router)
app.include_router(content_controller.router)
app.include_router(address.router)
app.include_router(payment.router)
app.include_router(purchase_intent.router)
app.include_router(order_fullfilement.router)
app.include_router(review.router)
app.include_router(admin_auth.router)
app.include_router(admin_product.router)
app.include_router(admin_category.router)
app.include_router(admin_roles.router)
app.include_router(admin_create.router)
app.include_router(admin_banner.router)
app.include_router(admin_promo_card.router)
app.include_router(admin_content_controller.router)
app.include_router(admin_analytics.router)
app.include_router(admin_order.router)
app.include_router(admin_review.router)
app.include_router(analytics_tracker.router)



@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc.errors())
        ).model_dump()
    )


