from celery import Celery

from core.config import settings

celery_app = Celery(
    "gezinsai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Amsterdam",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["workers.tasks"])

# Beat schedule
from workers.beat_schedule import CELERYBEAT_SCHEDULE  # noqa: E402

celery_app.conf.beat_schedule = CELERYBEAT_SCHEDULE
