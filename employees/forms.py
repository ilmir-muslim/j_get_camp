from django import forms

from branches.models import Branch
from core.forms import BaseDateForm
from schedule.models import Schedule
from students.models import Squad  # Добавить импорт
from .models import Employee, EmployeeAttendance, Position


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "full_name",
            "position",
            "branch",
            "schedule",
            "rate_per_day",
            "squad",
        ]
        widgets = {
            "position": forms.Select(attrs={"class": "form-select"}),
            "branch": forms.Select(attrs={"class": "form-select"}),
            "schedule": forms.Select(attrs={"class": "form-select"}),
            "squad": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.schedule_id = kwargs.pop("schedule_id", None)
        super().__init__(*args, **kwargs)

        # Если передан schedule_id (при редактировании из смены)
        if self.schedule_id:
            # Ограничиваем выбор смен только текущей сменой
            self.fields["schedule"].queryset = Schedule.objects.filter(
                id=self.schedule_id
            )
            # Ограничиваем выбор отрядов только отрядами текущей смены
            self.fields["squad"].queryset = Squad.objects.filter(
                schedule_id=self.schedule_id
            )
            # Делаем поле смены только для чтения
            self.fields["schedule"].widget.attrs["readonly"] = True
            self.fields["schedule"].widget.attrs["class"] = "form-control-plaintext"
        else:
            # Обычная фильтрация (для других случаев)
            if self.user and self.user.role == "admin" and self.user.city:
                self.fields["branch"].queryset = Branch.objects.filter(
                    city=self.user.city
                )
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
        self.fields["squad"].empty_label = "Не выбран"
        self.fields["rate_per_day"].initial = 1000

        # Скрываем поле отряда если нет schedule_id
        if not self.schedule_id and (not self.instance or not self.instance.schedule):
            self.fields["squad"].widget = forms.HiddenInput()
            self.fields["squad"].required = False

    def save(self, commit=True):
        # Если выбран отряд, устанавливаем is_leader = True
        if self.cleaned_data.get("squad"):
            self.instance.is_leader = True
            # Связываем отряд с этим вожатым
            squad = self.cleaned_data["squad"]
            squad.leader = self.instance
            squad.save()
        else:
            # Если отряд не выбран, сбрасываем is_leader
            self.instance.is_leader = False

        return super().save(commit)


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
