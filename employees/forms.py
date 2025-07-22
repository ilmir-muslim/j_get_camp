from django import forms

from core.forms import BaseDateForm
from .models import Employee, EmployeeAttendance

class EmployeeForm(forms.ModelForm):
    """
    Форма для создания и редактирования сотрудников.
    """
    class Meta:
        model = Employee
        fields = ['full_name', 'position', 'branch', 'schedule', 'rate_per_day']

class EmployeeAttendanceForm(BaseDateForm):
    """
    Форма для создания и редактирования посещения сотрудника.
    """
    class Meta:
        model = EmployeeAttendance
        fields = ['employee', 'date', 'comment']
        labels = {
            'employee': 'Сотрудник',
            'date': 'Дата посещения',
            'comment': 'Комментарий',
        }

