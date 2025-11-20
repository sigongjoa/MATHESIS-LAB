"""
Celery 애플리케이션 설정
"""

from celery import Celery
import os

# Celery 설정
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "rag_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1시간
    task_soft_time_limit=3300,  # 55분
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task 자동 발견
celery_app.autodiscover_tasks(['backend.app.tasks.rag'])
