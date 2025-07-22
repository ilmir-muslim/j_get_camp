from django import forms
from education.models import Regulation

class RegulationForm(forms.ModelForm):
    """
    Форма для создания и редактирования обучающего материала (регламента).
    """
    class Meta:
        model = Regulation
        fields = ['title', 'file']
        labels = {
            'title': 'Название',
            'file': 'Файл (PDF)',
        }
