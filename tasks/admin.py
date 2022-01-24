from django.contrib import admin

# Register your models here.

from tasks.models import Task


class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "priority", "title", "completed", "deleted", "user")


admin.sites.site.register(Task, TaskAdmin)
