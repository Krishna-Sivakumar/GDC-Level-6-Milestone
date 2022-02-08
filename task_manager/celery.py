import os
from django.conf import settings
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_manager.settings")
app = Celery("task_manager", include=["tasks.tasks"])
app.config_from_object("django.conf:settings")
