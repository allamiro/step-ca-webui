from celery import Celery

from app.core.config import settings

celery_client = Celery("pki_api", broker=settings.redis_url, backend=settings.redis_url)
