from django import forms

from branches.models import Branch
from core.forms import BaseDateForm
from schedule.models import Schedule
from .models import Employee, EmployeeAttendance, Position


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["full_name", "position", "branch", "schedule", "rate_per_day"]
        widgets = {
            "position": forms.Select(attrs={"class": "form-select"}),
            "branch": forms.Select(attrs={"class": "form-select"}),
            "schedule": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор филиалов для администратора
        if self.user and self.user.role == "admin" and self.user.city:
            self.fields["branch"].queryset = Branch.objects.filter(city=self.user.city)
            self.fields["schedule"].queryset = Schedule.objects.filter(
                branch__city=self.user.city
            )
        elif self.user and self.user.role in ["camp_head", "lab_head"]:
            # Для начальников лагеря/лаборатории ограничиваем выбор своим филиалом
            self.fields["branch"].queryset = Branch.objects.filter(
                id=self.user.branch.id
            )
            self.fields["schedule"].queryset = Schedule.objects.filter(
                branch=self.user.branch
            )

        self.fields["position"].empty_label = "Выберите должность"
        self.fields["branch"].empty_label = "Выберите филиал"
        self.fields["schedule"].empty_label = "Выберите смену"
        self.fields["rate_per_day"].initial = 1000


class EmployeeAttendanceForm(BaseDateForm):
    """
    Форма для создания и редактирования посещения сотрудника.
    """

    class Meta:
        model = EmployeeAttendance
        fields = ["employee", "date"]
        labels = {
            "employee": "Сотрудник",
            "date": "Дата посещения",
        }
