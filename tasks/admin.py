from django.contrib import admin

# Register your models here.

from tasks.models import Task, Report


class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "priority", "title", "completed", "deleted", "user")


class ReportAdmin(admin.ModelAdmin):
    list_display = ("user", "time")


admin.sites.site.register(Task, TaskAdmin)
admin.sites.site.register(Report, ReportAdmin)
