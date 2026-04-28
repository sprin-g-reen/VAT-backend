from redis.asyncio import Redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class SafeRedis:
    def __init__(self):
        self.client = None

    async def get_client(self):
        if not self.client:
            try:
                self.client = Redis.from_url(REDIS_URL, decode_responses=True)
                await self.client.ping()
            except Exception:
                self.client = None
        return self.client

    async def get(self, key):
        try:
            client = await self.get_client()
            if client:
                return await client.get(key)
        except:
            return None

    async def set(self, key, value, ex=None):
        try:
            client = await self.get_client()
            if client:
                await client.set(key, value, ex=ex)
        except:
            pass


redis_client = SafeRedis()