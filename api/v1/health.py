from fastapi import APIRouter, status
from pydantic import BaseModel

from core.database import check_database_health
from core.redis import check_redis_health

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadyResponse:
    database_ok, redis_ok = await check_database_health(), await check_redis_health()
    if database_ok and redis_ok:
        return ReadyResponse(status="ready", database="ok", redis="ok")
    return ReadyResponse(
        status="degraded",
        database="ok" if database_ok else "unavailable",
        redis="ok" if redis_ok else "unavailable",
    )
