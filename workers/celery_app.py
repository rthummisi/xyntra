from celery import Celery

from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "xyntra",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=[
        "workers.dlq_worker",
        "workers.webhook_worker",
    ],
)
