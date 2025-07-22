from django import forms
from core.forms import BaseDateForm
from .models import Schedule, COLOR_CHOICES


class ScheduleForm(BaseDateForm):
    class Meta:
        model = Schedule
        fields = ['name', 'branch', 'start_date', 'end_date', 'theme', 'color']
        widgets = {
            'start_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'end_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'color': forms.Select(choices=COLOR_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['start_date', 'end_date']:
            if self.instance and getattr(self.instance, field):
                self.fields[field].initial = getattr(self.instance, field).strftime('%Y-%m-%d')
