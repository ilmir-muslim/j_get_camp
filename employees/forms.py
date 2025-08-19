from django import forms

from core.forms import BaseDateForm
from .models import Employee, EmployeeAttendance


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["full_name", "position", "branch", "schedule", "rate_per_day"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].empty_label = "Выберите филиал"
        self.fields["schedule"].empty_label = "Выберите смену"


class EmployeeAttendanceForm(BaseDateForm):
    """
    Форма для создания и редактирования посещения сотрудника.
    """
    class Meta:
        model = EmployeeAttendance
        fields = ['employee', 'date']
        labels = {
            'employee': 'Сотрудник',
            'date': 'Дата посещения',
        }
