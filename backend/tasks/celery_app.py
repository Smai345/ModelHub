"""
Celery application factory.
"""
from celery import Celery
from backend.core.config import settings

celery_app = Celery(
    "iitg_ml_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.federated",
        "backend.tasks.leaderboard",
        "backend.tasks.notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "rerank-leaderboard-every-hour": {
            "task": "backend.tasks.leaderboard.rerank_leaderboard_task",
            "schedule": 3600.0,
        },
        "cleanup-stale-rounds-daily": {
            "task": "backend.tasks.federated.cleanup_stale_rounds",
            "schedule": 86400.0,
        },
    },
)
