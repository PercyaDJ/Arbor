"""
ARBOR - Configuration de l'application Celery.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "arbor",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # Sérialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,

    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Limites
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes

    # Beat schedule (synchronisation des feeds)
    beat_schedule={
        "sync-nvd-feed": {
            "task": "app.workers.feed_tasks.sync_nvd",
            "schedule": settings.nvd_sync_interval_hours * 3600,
        },
        "sync-osv-feed": {
            "task": "app.workers.feed_tasks.sync_osv",
            "schedule": settings.osv_sync_interval_hours * 3600,
        },
    },
)

# Auto-découverte des tâches dans les modules workers
celery_app.autodiscover_tasks(["app.workers"])
