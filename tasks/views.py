from datetime import datetime, timedelta, timezone

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           ChoiceFilter, DateFromToRangeFilter,
                                           DjangoFilterBackend, FilterSet,
                                           ModelChoiceFilter)
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from tasks.forms import (ScheduleReportForm, TaskForm, TaskUserCreationForm,
                         TaskUserLoginForm)
from tasks.models import STATUS_CHOICES, Report, Task, TaskHistory


@transaction.atomic
def cascadeUpdate(priority, user, task=None):
    if Task.objects.filter(priority=priority, deleted=False, completed=False, user=user).exists():
        temp_tasks = Task.objects.select_for_update().filter(
            priority__gte=priority, deleted=False, completed=False, user=user).order_by("priority")

        to_be_changed = []

        counter = priority
        for task in temp_tasks:
            if counter != task.priority:
                break
            task.priority += 1
            to_be_changed.append(task)
            counter += 1

        Task.objects.bulk_update(to_be_changed, ["priority"])


class TaskEditView(LoginRequiredMixin):
    success_url = "/tasks"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

    def form_valid(self, form):
        incoming_priority = form.cleaned_data.get("priority")
        incoming_status = form.cleaned_data.get("status")
        cascadeUpdate(incoming_priority, self.request.user)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()

        current_task = Task.objects.get(id=self.object.id)
        TaskHistory.objects.create(
            to_status=incoming_status, task=current_task)
        return HttpResponseRedirect(self.get_success_url())


class CurrentTasksView(LoginRequiredMixin, ListView):
    template_name = "current.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super(CurrentTasksView, self).get_context_data(**kwargs)
        context.update({
            "total_count": Task.objects.filter(deleted=False, user=self.request.user).count(),
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count(),
            "report_id": Report.objects.filter(user=self.request.user)[0].id,
        })
        return context

    def get_queryset(self):
        return Task.objects.filter(deleted=False, completed=False, user=self.request.user).order_by("priority")


class CompletedTasksView(LoginRequiredMixin, ListView):
    template_name = "completed.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super(CompletedTasksView, self).get_context_data(**kwargs)
        context.update({
            "total_count": Task.objects.filter(deleted=False, user=self.request.user).count(),
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count(),
            "report_id": Report.objects.filter(user=self.request.user)[0].id,
        })
        return context

    def get_queryset(self):
        return Task.objects.filter(deleted=False, completed=True, user=self.request.user).order_by("priority")


class AllTasksView(LoginRequiredMixin, ListView):
    template_name = "all.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super(AllTasksView, self).get_context_data(**kwargs)
        context.update({
            "total_count": Task.objects.filter(deleted=False, user=self.request.user).count(),
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count(),
            "report_id": Report.objects.filter(user=self.request.user)[0].id,
        })
        return context

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user).order_by("completed", "priority")


class AddTaskView(TaskEditView, CreateView):
    form_class = TaskForm
    template_name = "forms/add.html"


class UpdateTaskView(TaskEditView, UpdateView):
    form_class = TaskForm
    template_name = "forms/update.html"

    def form_valid(self, form):
        incoming_priority = form.cleaned_data.get("priority")
        incoming_status = form.cleaned_data.get("status")
        current_task = Task.objects.get(id=self.object.id)
        if incoming_priority != current_task.priority:
            cascadeUpdate(incoming_priority, self.request.user)
        if incoming_status != current_task.status:
            TaskHistory.objects.create(
                from_status=current_task.status, to_status=incoming_status, task=current_task)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class DeleteTaskView(DeleteView):
    template_name = "forms/delete.html"
    success_url = "/tasks"
    queryset = Task.objects.filter(deleted=False)

    def form_valid(self, form):
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ScheduleReportView(LoginRequiredMixin, UpdateView):
    form_class = ScheduleReportForm
    success_url = "/tasks"
    template_name = "forms/report.html"

    queryset = Report.objects.all()

    def form_valid(self, form):
        self.object = form.save()

        # last_updated is set to the same day so that the next report is sent the following day

        target = datetime.now().replace(hour=self.object.time.hour,
                                        minute=self.object.time.minute, second=0).time()

        self.object.last_updated = datetime.now(timezone.utc).replace(
            hour=self.object.time.hour,
            minute=self.object.time.minute,
            second=0
        ) - (
            # last_updated is set to the day before if the current time hasn't passed the report time
            timedelta(days=1) if target >= datetime.now().time()
            else timedelta(days=0)
        )

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class UserCreateView(UserPassesTestMixin, CreateView):
    form_class = TaskUserCreationForm
    template_name = "registration/signup.html"
    success_url = "/user/login"

    def form_valid(self, form):
        self.object = form.save()
        Report.objects.create(user=self.object)
        return HttpResponseRedirect(self.get_success_url())

    def test_func(self):
        return self.request.user.is_anonymous

    def handle_no_permission(self):
        return HttpResponseRedirect("/tasks/")


class UserLoginView(LoginView):
    form_class = TaskUserLoginForm


# API Section


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class TaskSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class TaskFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    status = ChoiceFilter(choices=STATUS_CHOICES)
    completed = BooleanFilter()


class TaskApiViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.filter(deleted=False)
    serializer_class = TaskSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskHistorySerializer(ModelSerializer):
    class Meta:
        model = TaskHistory
        fields = "__all__"


class TaskHistoryFilter(FilterSet):
    task = ModelChoiceFilter(queryset=Task.objects.filter(deleted=False))
    timestamp = DateFromToRangeFilter()
    from_status = ChoiceFilter(choices=STATUS_CHOICES)
    to_status = ChoiceFilter(choices=STATUS_CHOICES)


class TaskHistoryApiViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskHistorySerializer
    queryset = TaskHistory.objects.all()

    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskHistoryFilter
