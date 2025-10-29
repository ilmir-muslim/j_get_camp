from django import forms

from schedule.models import Schedule

from .models import Balance, Payment, Student


class StudentForm(forms.ModelForm):
    """
    Форма для создания и редактирования ученика.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Фильтрация смен по филиалу для начальников
        if self.request and self.request.user.role in ["camp_head", "lab_head"]:
            user_branch = self.request.user.branch
            if user_branch:
                self.fields["schedule"].queryset = Schedule.objects.filter(
                    branch=user_branch
                )

    class Meta:
        model = Student
        fields = [
            "full_name",
            "phone",
            "parent_name",
            "schedule",  # Убедитесь, что это поле есть
            "attendance_type",
            "default_price",
            "individual_price",
            "price_comment",
        ]
        widgets = {
            "schedule": forms.Select(attrs={"class": "form-select"}),
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
