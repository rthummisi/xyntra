import asyncio
import logging

import httpx

from core.config import Settings


async def provision_ollama_models(settings: Settings) -> None:
    if not settings.ollama_auto_provision:
        return

    logger = logging.getLogger("xyntra.ollama")
    async with httpx.AsyncClient(
        base_url=settings.local_ollama_base_url,
        timeout=30.0,
    ) as client:
        for model in settings.ollama_default_models:
            try:
                response = await client.post(
                    "/api/pull",
                    json={"name": model, "stream": False},
                )
                response.raise_for_status()
                logger.info("ollama_model_pull_requested", extra={"model": model})
            except httpx.HTTPError:
                logger.warning("ollama_model_pull_failed", extra={"model": model})
            await asyncio.sleep(0)
