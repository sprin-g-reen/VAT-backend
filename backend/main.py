from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routes import (
    user_auth,
    cart,
    wishlist,
    product,
    category,
    subcategory,
    address,
    review,
    purchase_intent,
    payment,
    order_fullfilement
)
from db import db
from database.base import ErrorResponse

app = FastAPI(
    title="Auth Service API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"msg": "Auth service running 🚀"}


app.include_router(user_auth.router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(product.router)
app.include_router(category.router)
app.include_router(subcategory.router)
app.include_router(address.router)
app.include_router(review.router)
app.include_router(purchase_intent.router)
app.include_router(payment.router)
app.include_router(order_fullfilement.router)


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


@app.on_event("startup")
async def create_indexes():

    # USERS
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("phone", unique=True, sparse=True)

    # CART
    await db.carts.create_index("user_id", unique=True)
    await db.carts.create_index("items.product_id")

    # WISHLIST
    await db.wishlist.create_index("user_id", unique=True)
    await db.wishlist.create_index("items.product_id")