from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from tasks.models import Task


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "bg-slate-100 rounded"
            visible.field.widget.attrs["style"] = "border-color: transparent"


class TaskUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(TaskUserCreationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "bg-slate-100 rounded"
            visible.field.widget.attrs["style"] = "border-color: transparent"


class TaskUserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(TaskUserLoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "bg-slate-100 rounded"
            visible.field.widget.attrs["style"] = "border-color: transparent"
