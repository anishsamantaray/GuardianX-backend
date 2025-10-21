import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 16074))
REDIS_PASSWORD= os.getenv("REDIS_PASSWORD")
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    username="default",
    password=REDIS_PASSWORD
)