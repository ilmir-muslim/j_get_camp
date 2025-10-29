from django import forms

from students.models import Payment
from .models import Expense, Salary


class SalaryForm(forms.ModelForm):
    """
    Форма для редактирования зарплаты сотрудника.
    """

    class Meta:
        model = Salary
        fields = [
            "employee",
            "schedule",
            "payment_type",
            "percent_rate",
            "is_paid",
        ]
        labels = {
            "employee": "Сотрудник",
            "schedule": "Смена",
            "payment_type": "Тип выплаты",
            "percent_rate": "Процент от оплаты",
            "is_paid": "Выплачено",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Для администраторов ограничиваем выбор смен и сотрудников только филиалами их города
        if (
            self.user
            and self.user.is_authenticated
            and self.user.role == "admin"
            and self.user.city
        ):
            self.fields["schedule"].queryset = self.fields["schedule"].queryset.filter(
                branch__city=self.user.city
            )
            self.fields["employee"].queryset = self.fields["employee"].queryset.filter(
                branch__city=self.user.city
            )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["schedule", "category", "comment", "amount"]
        labels = {
            "schedule": "Смена",
            "category": "Категория",
            "comment": "Комментарий",
            "amount": "Сумма",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Для администраторов ограничиваем выбор смен только филиалами их города
        if (
            self.user
            and self.user.is_authenticated
            and self.user.role == "admin"
            and self.user.city
        ):
            self.fields["schedule"].queryset = self.fields["schedule"].queryset.filter(
                branch__city=self.user.city
            )
        # Для менеджеров оставляем все смены


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["student", "amount", "date", "comment"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }
