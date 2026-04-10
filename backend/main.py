from fastapi import FastAPI
from backend.routes import user_auth

app = FastAPI(
    title="Auth Service API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"msg": "Auth service running 🚀"}


app.include_router(user_auth.router, prefix="/auth", tags=["Auth"])