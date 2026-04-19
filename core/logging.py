import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.config import Settings

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler()
    formatter: logging.Formatter
    if settings.structured_logging:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] "
            "[request_id=%(request_id)s] %(message)s"
        )
    handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, request_id_header: str) -> None:
        super().__init__(app)
        self.request_id_header = request_id_header
        self.logger = logging.getLogger("xyntra.http")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(self.request_id_header, str(uuid.uuid4()))
        token = request_id_context.set(request_id)
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            request_id_context.reset(token)

        response.headers[self.request_id_header] = request_id
        return response
