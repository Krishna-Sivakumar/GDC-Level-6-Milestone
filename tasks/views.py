from django.http import HttpResponseRedirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from tasks.models import Task


def cascadeUpdate(priority, id=None):
    if Task.objects.filter(priority=priority).count() > 0:
        temp_tasks = Task.objects.filter(
            priority__gte=priority, deleted=False, completed=False).order_by("priority")

        if id is not None and temp_tasks[0].id == id:
            return

        counter = priority
        for task in temp_tasks:
            if counter != task.priority:
                break
            task.priority += 1
            task.save()
            counter += 1


class TaskEditView(LoginRequiredMixin):
    success_url = "/tasks"
    fields = ["title", "description", "priority", "completed"]

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
    template_name = "add.html"


class UpdateTaskView(TaskEditView, UpdateView):
    template_name = "update.html"

    def form_valid(self, form):
        incoming_priority = form.cleaned_data.get("priority")
        # id is passed so as to avoid cascading if the task's priority has not changed
        cascadeUpdate(incoming_priority, self.get_object().id)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class DeleteTaskView(DeleteView):
    template_name = "delete.html"
    success_url = "/tasks"
    queryset = Task.objects.filter(deleted=False)

    def form_valid(self, form):
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class UserCreateView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = "/user/login"
