from django import forms

from .models import Payment, Student

class StudentForm(forms.ModelForm):
    """
    Форма для создания и редактирования ученика.
    """
    class Meta:
        model = Student
        fields = [
            'full_name',
            'phone',
            'parent_name',
            'schedule',
            'attendance_type',
            'default_price',
            'individual_price',
            'price_comment',
        ]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["student", "schedule", "amount", "date", "comment"]
        widgets = {
            "student": forms.HiddenInput(),
            "schedule": forms.HiddenInput(),
        }
