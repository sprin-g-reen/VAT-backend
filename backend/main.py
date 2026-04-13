from fastapi import FastAPI
from routes import user_auth,cart,wishlist
from db import db

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

@app.on_event("startup")
async def create_indexes():

    # USERS
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("phone", unique=True, sparse=True)

    # COUNTERS
    await db.counters.create_index("_id", unique=True)

    # CART
    await db.cart.create_index("user_id")
    await db.cart.create_index("items.product_id")

    # WISHLIST
    await db.wishlist.create_index("user_id")
    await db.wishlist.create_index("items.product_id")