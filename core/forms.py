from django import forms

class BaseDateForm(forms.ModelForm):
    """
    Базовая форма для установки input[type="date"] и input[type="datetime-local"] у полей с датами.
    Используется для единообразного отображения полей даты и даты-времени во всех формах проекта.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                field.widget.input_type = "date"
            elif isinstance(field, forms.DateTimeField):
                field.widget.input_type = "datetime-local"
