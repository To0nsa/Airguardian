import os
from celery import Celery

celery_app = Celery(
    'airguardian',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
)

celery_app.conf.beat_schedule = {
    'fetch-and-process-drones-every-10-seconds': {
        'task': 'app.tasks.fetch_and_process_drones',
        'schedule': 10.0,
    },
}

celery_app.conf.timezone = 'UTC'

import app.tasks.fetch_and_detect
