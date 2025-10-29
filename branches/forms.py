from django import forms
from branches.models import Branch


class BranchForm(forms.ModelForm):
    """
    Форма для создания и редактирования филиала.
    """

    class Meta:
        model = Branch
        fields = ["name", "address", "city"]
        labels = {
            "name": "Название",
            "address": "Адрес",
            "city": "Город",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Для администраторов ограничиваем выбор городов только их городом
        user = kwargs.get("initial", {}).get("user")
        if user and user.is_authenticated and user.role == "admin" and user.city:
            self.fields["city"].queryset = self.fields["city"].queryset.filter(
                id=user.city.id
            )
            self.fields["city"].initial = user.city
            self.fields["city"].disabled = True
