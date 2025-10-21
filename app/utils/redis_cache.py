import json
from app.utils.redis_client import redis_client

DEFAULT_CACHE_TTL = 3600  # 1 hour


async def get_cache(key: str):
    """Get a cached value from Redis, if present."""
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cache(key: str, value, ttl: int = DEFAULT_CACHE_TTL):
    """Store a value in Redis with an expiry."""
    await redis_client.set(key, json.dumps(value), ex=ttl)