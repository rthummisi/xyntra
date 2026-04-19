import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from api.v1.analytics import router as analytics_router
from api.v1.approvals import router as approvals_router
from api.v1.artifacts import router as artifacts_router
from api.v1.cache import router as cache_router
from api.v1.chat import router as chat_router
from api.v1.cli import router as cli_router
from api.v1.compare import router as compare_router
from api.v1.context import router as context_router
from api.v1.evals import router as evals_router
from api.v1.events import router as events_router
from api.v1.health import router as health_router
from api.v1.memory import router as memory_router
from api.v1.openai_compat import router as openai_compat_router
from api.v1.policies import router as policies_router
from api.v1.projects import router as projects_router
from api.v1.prompts import router as prompts_router
from api.v1.providers import router as providers_router
from api.v1.replay import router as replay_router
from api.v1.router import router as routing_router
from api.v1.security import router as security_router
from api.v1.sessions import router as sessions_router
from api.v1.tasks import router as tasks_router
from api.v1.webhooks import router as webhooks_router
from core.config import get_settings
from core.logging import RequestContextMiddleware, configure_logging
from core.ollama_provisioner import provision_ollama_models
from core.rate_limiter import RateLimitMiddleware
from core.redis import redis_client

settings = get_settings()
ROOT_DIR = Path(__file__).resolve().parent
START_SCRIPT = ROOT_DIR / "scripts" / "start_xyntra.sh"


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings)
    logger = logging.getLogger("xyntra.bootstrap")
    logger.info("application_starting")
    await provision_ollama_models(settings)
    yield
    await redis_client.aclose()
    logger.info("application_stopped")


app = FastAPI(
    title="xyntra",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    RequestContextMiddleware,
    request_id_header=settings.request_id_header,
)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client, settings=settings)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(openai_compat_router)
app.include_router(approvals_router, prefix=settings.api_v1_prefix)
app.include_router(projects_router, prefix=settings.api_v1_prefix)
app.include_router(artifacts_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(cache_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)
app.include_router(cli_router, prefix=settings.api_v1_prefix)
app.include_router(compare_router, prefix=settings.api_v1_prefix)
app.include_router(context_router, prefix=settings.api_v1_prefix)
app.include_router(evals_router, prefix=settings.api_v1_prefix)
app.include_router(events_router, prefix=settings.api_v1_prefix)
app.include_router(memory_router, prefix=settings.api_v1_prefix)
app.include_router(policies_router, prefix=settings.api_v1_prefix)
app.include_router(providers_router, prefix=settings.api_v1_prefix)
app.include_router(prompts_router, prefix=settings.api_v1_prefix)
app.include_router(routing_router, prefix=settings.api_v1_prefix)
app.include_router(replay_router, prefix=settings.api_v1_prefix)
app.include_router(security_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)
app.include_router(tasks_router, prefix=settings.api_v1_prefix)
app.include_router(webhooks_router, prefix=settings.api_v1_prefix)


def run() -> None:
    if len(sys.argv) == 1 or sys.argv[1] == "start":
        _run_start_script(sys.argv[2:] if len(sys.argv) > 2 else [])
        return

    if sys.argv[1] == "api":
        _run_api()
        return

    if sys.argv[1] in {"-h", "--help", "help"}:
        _print_help()
        return

    raise SystemExit(f"Unsupported command: {sys.argv[1]}")


def _run_start_script(extra_args: list[str]) -> None:
    if not START_SCRIPT.exists():
        raise SystemExit(f"Startup script not found: {START_SCRIPT}")
    subprocess.run(
        [str(START_SCRIPT), *extra_args],
        cwd=ROOT_DIR,
        check=True,
    )


def _run_api() -> None:
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


def _print_help() -> None:
    print(
        "\n".join(
            [
                "xyntra commands:",
                "  xyntra         Start the full local stack",
                "  xyntra start   Start the full local stack",
                "  xyntra api     Run only the FastAPI server in the current process",
            ]
        )
    )
