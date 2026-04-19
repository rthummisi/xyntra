from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from core.config import get_settings
from core.rate_limiter import RateLimitMiddleware


class FakeRedis:
    def __init__(self, counts: list[int]) -> None:
        self._counts = list(counts)

    async def incr(self, key: str) -> int:
        return self._counts.pop(0)

    async def expire(self, key: str, seconds: int) -> bool:
        return True


def build_test_app(redis_client) -> FastAPI:
    app = FastAPI()
    settings = get_settings()
    app.add_middleware(
        RateLimitMiddleware, redis_client=redis_client, settings=settings
    )

    @app.get("/ping")
    async def ping() -> dict:
        return {"status": "ok"}

    return app


async def test_rate_limiter_sets_headers_on_success() -> None:
    app = build_test_app(FakeRedis([1]))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"]
    assert response.headers["X-RateLimit-Remaining"]


async def test_rate_limiter_sets_retry_after_on_limit() -> None:
    settings = get_settings()
    app = build_test_app(FakeRedis([settings.default_rate_limit_per_minute + 1]))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ping")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "0"
