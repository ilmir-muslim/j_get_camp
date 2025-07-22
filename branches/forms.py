from django import forms
from branches.models import Branch

class BranchForm(forms.ModelForm):
    """
    Форма для создания и редактирования филиала.
    """
    class Meta:
        model = Branch
        fields = ['name', 'address']
        labels = {
            'name': 'Название',
            'address': 'Адрес',
        }
