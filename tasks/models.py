from django.contrib.auth.models import User
from django.db import models

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save


STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    priority = models.IntegerField(null=False)

    def __str__(self):
        return f"{self.title}: {self.priority} | {self.user}"


class TaskHistory(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    from_status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, null=True)
    to_status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now=True)


@receiver(pre_save, sender=Task)
def generateHistory(instance, **kwargs):
    try:
        task = Task.objects.get(pk=instance.id)
    except:
        task = None

    if task is not None and task.status != instance.status:
        TaskHistory.objects.create(
            task=task,
            from_status=task.status,
            to_status=instance.status
        )
