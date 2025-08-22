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
            "daily_rate",
            "percent_rate",
            "total_payment",
            "is_paid",
        ]
        labels = {
            "employee": "Сотрудник",
            "schedule": "Смена",
            "payment_type": "Тип выплаты",
            "daily_rate": "Ставка за день",
            "percent_rate": "Процент от оплаты",
            "total_payment": "Итоговая сумма выплаты",
            "is_paid": "Выплачено",
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['schedule', 'category', 'comment', 'amount']
        labels = {
            'schedule': 'Смена',
            'category': 'Категория',
            'comment': 'Комментарий',
            'amount': 'Сумма',
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'date', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
