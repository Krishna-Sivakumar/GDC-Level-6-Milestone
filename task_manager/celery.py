import os
from datetime import timedelta

from django.conf import settings

from celery import Celery
from celery.decorators import periodic_task

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_manager.settings")
app = Celery("task_manager")
app.config_from_object("django.conf:settings")

# Periodic Task


@periodic_task(run_every=timedelta(seconds=60))
def batch_email():

    from django.db.models import Q
    from tasks.models import Report
    from functools import reduce
    from collections import defaultdict
    from tasks.models import Task
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from datetime import timedelta, datetime, timezone

    def user_summary(user):
        def status_reducer(acc, task):
            acc[task.status] += 1
            return acc

        tasks = Task.objects.filter(user=user, completed=False, deleted=False)
        return {
            "name": user.username.capitalize(),
            "status": dict(
                reduce(status_reducer, tasks, defaultdict(int))
            )
        }

    start = datetime.now(timezone.utc) - timedelta(days=1)

    for report in Report.objects.filter((Q(last_updated=None) | Q(last_updated__lte=start)) & Q(disabled=False)):
        send_mail(
            "Daily Status Report",
            render_to_string("report.txt", user_summary(report.user)),
            "tasks@taskmanager.com",
            [report.user.email]
        )
        report.last_updated = datetime.now(timezone.utc).replace(
            hour=report.time.hour, second=report.time.second)
        report.save()
