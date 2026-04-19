from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.config import Settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: Redis, settings: Settings) -> None:
        super().__init__(app)
        self.redis = redis_client
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        identifier = (
            request.headers.get(self.settings.api_key_header)
            or request.headers.get("X-Project-ID")
            or request.client.host
            or "anonymous"
        )
        key = f"rate_limit:{identifier}"
        limit = self.settings.default_rate_limit_per_minute
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 60)
        except Exception:
            return await call_next(request)

        remaining = max(limit - current, 0)

        if current > limit:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded."},
            )
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["Retry-After"] = "60"
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
