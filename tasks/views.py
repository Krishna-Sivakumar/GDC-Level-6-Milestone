from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from tasks.forms import TaskForm, TaskUserCreationForm, TaskUserLoginForm
from tasks.models import Task


@transaction.atomic
def cascadeUpdate(priority, id=None):
    if Task.objects.filter(priority=priority).exists():
        temp_tasks = Task.objects.select_for_update().filter(
            priority__gte=priority, deleted=False, completed=False).order_by("priority")

        if id is not None and temp_tasks[0].id == id:
            return

        counter = priority
        for task in temp_tasks:
            if counter != task.priority:
                break
            task.priority += 1
            counter += 1

        Task.objects.bulk_update(temp_tasks, ["priority"])


class TaskEditView(LoginRequiredMixin):
    success_url = "/tasks"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

    def form_valid(self, form):
        incoming_priority = form.cleaned_data.get("priority")
        cascadeUpdate(incoming_priority)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class CurrentTasksView(LoginRequiredMixin, ListView):
    template_name = "current.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super(CurrentTasksView, self).get_context_data(**kwargs)
        context.update({
            "total_count": Task.objects.filter(deleted=False, user=self.request.user).count(),
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count()
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
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count()
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
            "completed_count": Task.objects.filter(deleted=False, completed=True, user=self.request.user).count()
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
        # id is passed so as to avoid cascading if the task's priority has not changed
        cascadeUpdate(incoming_priority, self.get_object().id)
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


class UserCreateView(UserPassesTestMixin, CreateView):
    form_class = TaskUserCreationForm
    template_name = "registration/signup.html"
    success_url = "/user/login"

    def test_func(self):
        return self.request.user.is_anonymous

    def handle_no_permission(self):
        return HttpResponseRedirect("/tasks/")


class UserLoginView(LoginView):
    form_class = TaskUserLoginForm
