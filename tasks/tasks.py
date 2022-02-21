from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import reduce

from celery.decorators import periodic_task
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string

from tasks.models import Report, Task


@periodic_task(run_every=timedelta(seconds=5))
def batch_email():
    print("running task...")

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

    report_set = Report.objects.select_for_update().filter(
        last_updated__lte=start,
        disabled=False
    )

    with transaction.atomic():
        for report in report_set:
            send_mail(
                "Daily Status Report",
                render_to_string("report.txt", user_summary(report.user)),
                "tasks@taskmanager.com",
                [report.user.email, "dummy@user.com"]
            )

            report.last_updated = datetime.now(timezone.utc).replace(
                hour=report.time.hour, second=report.time.second)
            report.save()

    # for testing purposes
    return report_set
