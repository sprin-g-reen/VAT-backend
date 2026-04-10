from fastapi import FastAPI
from routes import user_auth
from db import db

app = FastAPI(
    title="Auth Service API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"msg": "Auth service running 🚀"}


app.include_router(user_auth.router, prefix="/auth", tags=["Auth"])

@app.on_event("startup")
async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("phone", unique=True)
    await db.cart.create_index("user_id", unique=True)
    await db.wishlist.create_index("user_id", unique=True)
