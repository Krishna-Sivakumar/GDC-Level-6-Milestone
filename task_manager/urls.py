"""task_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework.routers import SimpleRouter
from tasks.views import (AddTaskView, AllTasksView, CompletedTasksView, ScheduleReportView,
                         CurrentTasksView, DeleteTaskView, TaskApiViewset, TaskHistoryApiViewset,
                         UpdateTaskView, UserCreateView, UserLoginView)

router = SimpleRouter()
router.register("api/task", TaskApiViewset)
router.register("api/history", TaskHistoryApiViewset)

urlpatterns = [
    path("", CurrentTasksView.as_view()),
    path("admin/", admin.site.urls),
    path("tasks/", CurrentTasksView.as_view()),
    path("completed_tasks/", CompletedTasksView.as_view()),
    path("all_tasks/", AllTasksView.as_view()),
    path("add-task/", AddTaskView.as_view()),
    path("update-task/<pk>/", UpdateTaskView.as_view()),
    path("delete-task/<pk>/", DeleteTaskView.as_view()),
    path("user/login/", UserLoginView.as_view(redirect_authenticated_user=True)),
    path("user/signup/", UserCreateView.as_view()),
    path("user/logout/", LogoutView.as_view()),
    path("user/report/<pk>/", ScheduleReportView.as_view()),
] + router.urls
