# app/celery.py

'''
Configure the Celery application for Airguardian:
- Broker and result backend from environment variables
- Connection retry policies for broker failures
- Default retry strategies for tasks
- Acknowledgement and prefetch settings to ensure reliability
- Beat schedule for periodic tasks
'''  
import os
from celery import Celery

# Initialize Celery app with broker and backend URLs
celery_app = Celery(
    'airguardian',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),  # Redis broker URL
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),  # Redis result backend URL
    broker_connection_retry=True,          # Retry connecting to broker on startup
    broker_connection_max_retries=5,       # Maximum connection retry attempts
)

# Default retry behavior for all tasks
celery_app.conf.task_default_retry_delay = 60   # Seconds to wait before retrying a failed task
celery_app.conf.task_default_max_retries = 3    # Max retry attempts per task

# Automatically retry tasks on any Exception, with exponential backoff and jitter
celery_app.conf.task_annotations = {
    '*': {
        'autoretry_for': ('Exception',),  # Retry on any Exception
        'retry_backoff': True,            # Exponential back-off between retries
        'retry_jitter': True,             # Add randomness to retry intervals
    }
}

# Ensure tasks are acknowledged only after successful execution
celery_app.conf.task_acks_late = True
# Limit prefetch to one task at a time to avoid losing in-flight tasks if a worker crashes
celery_app.conf.worker_prefetch_multiplier = 1

# Periodic task scheduling (Beat)
celery_app.conf.beat_schedule = {
    'fetch-and-process-drones-every-10-seconds': {
        'task': 'app.tasks.fetch_and_process_drones',  # Task name to run
        'schedule': 10.0,                              # Interval in seconds
    },
}
# Use UTC for all scheduled tasks
celery_app.conf.timezone = 'UTC'

# Import tasks to register them with Celery
import app.tasks.fetch_and_detect

