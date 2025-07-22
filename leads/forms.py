from core.forms import BaseDateForm
from .models import Lead


class LeadForm(BaseDateForm):
    """
    Форма для создания и редактирования лида.
    """

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
        ]
