from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import ModelForm

from tasks.models import Report, Task


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "priority", "completed"]

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


class ScheduleReportForm(ModelForm):

    time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"type": "time"}
        ),
        required=True,
        help_text="<small><em>Use UTC time</em></small>"
    )

    disabled = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label="Disable daily reports",
        required=False
    )

    class Meta:
        model = Report
        fields = ["time", "disabled"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "bg-slate-100 rounded"
            visible.field.widget.attrs["style"] = "border-color: transparent"
