from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "vk_saas",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        # Tasks modules to register — fill in as workers are implemented.
        # "app.workers.tasks.mailings",
        # "app.workers.tasks.bot_engine",
        # "app.workers.tasks.agent_rag",
        # "app.workers.tasks.content_posting",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.tz,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)


# Periodic tasks (Celery Beat) — populate as needed.
celery_app.conf.beat_schedule = {
    # "publish-scheduled-posts": {
    #     "task": "app.workers.tasks.content_posting.publish_due_posts",
    #     "schedule": 60.0,  # every minute
    # },
}
