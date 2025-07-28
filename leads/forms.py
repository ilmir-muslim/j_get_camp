from django import forms
from core.forms import BaseDateForm
from .models import Lead


class LeadForm(BaseDateForm):
    """Форма для создания и редактирования лидов."""

    callback_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
        label="Дата перезвона",
    )
    callback_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=False,
        label="Время перезвона",
    )

    class Meta:
        model = Lead
        fields = [
            "status",
            "source",
            "phone",
            "parent_name",
            "interest",
            "comment",
            "callback_date",
            "callback_time",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.callback_date:
            self.initial["callback_date"] = self.instance.callback_date.date()
            self.initial["callback_time"] = self.instance.callback_date.time()

    def save(self, commit=True):
        instance = super().save(commit=False)
        callback_date = self.cleaned_data.get("callback_date")
        callback_time = self.cleaned_data.get("callback_time")

        if callback_date and callback_time:
            from django.utils import timezone

            instance.callback_date = timezone.make_aware(
                timezone.datetime.combine(callback_date, callback_time)
            )
        elif callback_date:
            instance.callback_date = timezone.make_aware(
                timezone.datetime.combine(callback_date, timezone.now().time())
            )
        else:
            instance.callback_date = None

        if commit:
            instance.save()
        return instance
