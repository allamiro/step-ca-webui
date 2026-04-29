import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("worker", broker=redis_url, backend=redis_url)
celery_app.conf.task_routes = {
    "worker.tasks.certificates.*": {"queue": "pki"},
    "worker.tasks.provisioners.*": {"queue": "pki"},
    "worker.tasks.ca_init.*": {"queue": "pki"},
}
celery_app.conf.broker_connection_retry_on_startup = True

celery_app.autodiscover_tasks(["worker.tasks"])
import worker.tasks.provisioners  # noqa: E402, F401
import worker.tasks.ca_init  # noqa: E402, F401
