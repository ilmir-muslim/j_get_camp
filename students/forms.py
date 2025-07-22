from django import forms

from .models import Student

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


