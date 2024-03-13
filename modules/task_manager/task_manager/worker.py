# task_manager/worker.py
import os

from celery import Celery
import sys


# Load celery broker details from ENV.
CELERY_BROKER = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Setup app

app = Celery('tasks',
             broker=CELERY_BROKER,
             result_backend=CELERY_RESULT_BACKEND)

# Import your tasks
app.autodiscover_tasks(['task_manager.tasks','task_manager.tasks.wis2' ])

def main():
    app.start(argv=sys.argv[1:])

if __name__ == '__main__':
    main()
