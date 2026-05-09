from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_analyzer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Импортируем задачи здесь, чтобы Celery их зарегистрировал
import app.tasks.analysis_tasks  # noqa
