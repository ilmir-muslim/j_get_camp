from django import forms

from schedule.models import Schedule

from .models import Balance, Payment, Squad, Student


class SquadForm(forms.ModelForm):
    """Форма для создания отряда"""

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
            # Ограничиваем выбор вожатых только сотрудниками текущей смены
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
    """
    Форма для создания и редактирования ученика.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.schedule_id = kwargs.pop("schedule_id", None)  # Добавляем параметр
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
            # Делаем поле смены только для чтения, так как мы в контексте смены
            self.fields["schedule"].widget.attrs["readonly"] = True
            self.fields["schedule"].widget.attrs["class"] = "form-control-plaintext"
        else:
            # Обычная фильтрация (для других случаев)
            if self.request and self.request.user.role in ["camp_head", "lab_head"]:
                user_branch = self.request.user.branch
                if user_branch:
                    self.fields["schedule"].queryset = Schedule.objects.filter(
                        branch=user_branch
                    )
                    self.fields["squad"].queryset = Squad.objects.filter(
                        schedule__branch=user_branch
                    )
            elif self.request and self.request.user.role == "admin":
                user_city = self.request.user.city
                if user_city:
                    self.fields["schedule"].queryset = Schedule.objects.filter(
                        branch__city=user_city
                    )
                    self.fields["squad"].queryset = Squad.objects.filter(
                        schedule__branch__city=user_city
                    )

    class Meta:
        model = Student
        fields = [
            "squad",  # Добавить это поле ПЕРВЫМ
            "full_name",
            "phone",
            "parent_name",
            "schedule",
            "attendance_type",
            "default_price",
            "individual_price",
            "price_comment",
        ]
        widgets = {
            "schedule": forms.Select(attrs={"class": "form-select"}),
            "squad": forms.Select(attrs={"class": "form-select"}),
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
        # Устанавливаем начальное значение для operation_type
        self.fields["operation_type"].initial = "deposit"
