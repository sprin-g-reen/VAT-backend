from redis.asyncio import Redis
import os
import asyncio
from contextlib import asynccontextmanager

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class SafePipeline:
    def __init__(self, client):
        self.client = client
        self.pipe = None

    async def __aenter__(self):
        if self.client:
            self.pipe = self.client.pipeline()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.pipe:
            await self.pipe.reset()

    def incr(self, key):
        if self.pipe:
            self.pipe.incr(key)

    def expire(self, key, seconds):
        if self.pipe:
            self.pipe.expire(key, seconds)

    async def execute(self):
        if self.pipe:
            return await self.pipe.execute()
        return [1, True] # Default values to skip rate limiting

class SafeRedis:
    def __init__(self):
        self.client = None
        self._last_connect_attempt = 0
        self._retry_interval = 60  # seconds

    async def get_client(self):
        now = asyncio.get_event_loop().time()
        if not self.client and (now - self._last_connect_attempt > self._retry_interval):
            self._last_connect_attempt = now
            try:
                self.client = Redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
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

    async def setex(self, key, seconds, value):
        try:
            client = await self.get_client()
            if client:
                await client.setex(key, seconds, value)
        except:
            pass

    async def incr(self, key):
        try:
            client = await self.get_client()
            if client:
                return await client.incr(key)
        except:
            return 1

    async def delete(self, *keys):
        try:
            client = await self.get_client()
            if client:
                await client.delete(*keys)
        except:
            pass

    async def scan_iter(self, match=None):
        try:
            client = await self.get_client()
            if client:
                async for key in client.scan_iter(match=match):
                    yield key
        except:
            pass
        return

    @asynccontextmanager
    async def pipeline(self, transaction=True):
        client = await self.get_client()
        pipe = SafePipeline(client)
        yield pipe

redis_client = SafeRedis()
