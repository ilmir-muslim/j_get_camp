from django import forms
from branches.models import Branch
from core.forms import BaseDateForm
from django.core.exceptions import ValidationError
from employees.models import Employee
from students.models import Payment, Student
from .models import Schedule, COLOR_CHOICES


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["name", "branch", "start_date", "end_date", "theme", "color"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "color": forms.Select(choices=COLOR_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ограничение выбора филиалов для администраторов
        if self.user and self.user.role == "admin" and self.user.city:
            self.fields["branch"].queryset = Branch.objects.filter(city=self.user.city)

        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.initial["start_date"] = self.instance.start_date.strftime(
                    "%Y-%m-%d"
                )
            if self.instance.end_date:
                self.initial["end_date"] = self.instance.end_date.strftime("%Y-%m-%d")
        else:
            self.fields["color"].initial = "#cce6ff"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("Дата начала не может быть позже даты окончания!")

        return cleaned_data

class ScheduleStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['attendance_dates', 'individual_price', 'price_comment']

class ScheduleEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['position', 'rate_per_day']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'date', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
