from django import forms

from core.models import Ticket
from core.telegram import send_telegram_message

import logging

logger = logging.getLogger(__name__)

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


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["subject", "description"]
        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Кратко опишите проблему",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Подробное описание проблемы, шаги для воспроизведения и т.д.",
                }
            ),
        }
        labels = {
            "subject": "Тема обращения",
            "description": "Описание проблемы",
        }


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status", "admin_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "admin_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Заметки для пользователя или внутренние пометки",
                }
            ),
        }
