from django import forms
from .models import Balance, Payment, Squad, Student, StudentSchedule


class SquadForm(forms.ModelForm):
    class Meta:
        model = Squad
        fields = ["name", "leader"]
        widgets = {
            "name": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "20", "step": "1"}
            ),
            "leader": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.schedule = kwargs.pop("schedule", None)
        super().__init__(*args, **kwargs)
        if self.schedule:
            self.fields["leader"].queryset = self.schedule.employee_set.filter(
                is_leader=True
            )
            self.fields["leader"].empty_label = "Не назначен"
            self.fields["leader"].required = False
        self.fields["name"].label = "Номер отряда"
        self.fields["leader"].label = "Вожатый"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if (
            self.schedule
            and Squad.objects.filter(name=name, schedule=self.schedule).exists()
        ):
            raise forms.ValidationError(
                f"Отряд с номером {name} уже существует в этой смене"
            )
        return name


class StudentForm(forms.ModelForm):
    """Форма для создания/редактирования базовых данных ученика (без привязки к смене)"""

    class Meta:
        model = Student
        fields = [
            "full_name",
            "phone",
            "parent_name",
            "squad",
        ]
        widgets = {
            "squad": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            user = self.request.user
            if user.role in ["camp_head", "lab_head"]:
                user_branch = user.branch
                if user_branch:
                    self.fields["squad"].queryset = Squad.objects.filter(
                        schedule__branch=user_branch
                    )
            elif user.role == "admin":
                user_city = user.city
                if user_city:
                    self.fields["squad"].queryset = Squad.objects.filter(
                        schedule__branch__city=user_city
                    )


class StudentScheduleForm(forms.ModelForm):
    """Форма для настройки параметров участия студента в конкретной смене"""

    class Meta:
        model = StudentSchedule
        fields = [
            "attendance_type",
            "default_price",
            "individual_price",
            "price_comment",
            "special_notes",
        ]
        widgets = {
            "attendance_type": forms.Select(attrs={"class": "form-select"}),
            "default_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "individual_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "price_comment": forms.TextInput(attrs={"class": "form-control"}),
            "special_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "date", "comment"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "comment": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs.update(
            {"min": "0", "step": "0.01", "class": "form-control"}
        )
        self.fields["date"].widget.attrs.update({"class": "form-control"})
        self.fields["comment"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Комментарий к платежу"}
        )


class BalanceForm(forms.ModelForm):
    class Meta:
        model = Balance
        fields = ["amount", "comment", "operation_type"]
        widgets = {
            "operation_type": forms.HiddenInput(),
            "comment": forms.TextInput(attrs={"placeholder": "Причина пополнения..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs.update({"min": "0", "step": "0.01"})
        self.fields["operation_type"].initial = "deposit"
