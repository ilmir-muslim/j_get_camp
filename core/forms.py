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
        fields = ["subject", "description", "screenshot"]
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
            "screenshot": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",  # Ограничиваем тип файлов
                }
            ),
        }
        labels = {
            "subject": "Тема обращения",
            "description": "Описание проблемы",
            "screenshot": "Скриншот (опционально)",
        }

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get("screenshot")
        if screenshot:
            # Проверяем размер файла (максимум 5MB)
            if screenshot.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 5MB")

            # Проверяем тип файла
            valid_types = ["image/jpeg", "image/png", "image/gif", "image/bmp"]
            if screenshot.content_type not in valid_types:
                raise forms.ValidationError(
                    "Поддерживаются только изображения (JPEG, PNG, GIF, BMP)"
                )

        return screenshot


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

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.admin_notes:
            instance.has_unread_admin_response = True
        if commit:
            instance.save()
        return instance
