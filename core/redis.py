from collections.abc import AsyncIterator

from redis.asyncio import Redis

from core.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> AsyncIterator[Redis]:
    yield redis_client


async def check_redis_health() -> bool:
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
