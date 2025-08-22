from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from core.utils import role_required
from leads.forms import LeadForm
from .models import Lead


def lead_list(request):
    leads = Lead.objects.all()
    context = {
        "leads": leads,
        "status_choices": Lead.STATUS_CHOICES,
        "source_choices": Lead.SOURCE_CHOICES,
    }
    return render(request, "leads/lead_list.html", context)


@role_required(["manager", "admin"])
def lead_create(request):
    """
    Представление для создания лида.
    """
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lead_list")
    else:
        form = LeadForm()

    return render(request, "leads/lead_form.html", {"form": form})


@role_required(["manager", "admin"])
def lead_edit(request, pk):
    """
    Представление для редактирования лида.
    """
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()

            # Подготавливаем данные для ответа
            lead_data = {
                "id": lead.id,
                "status": lead.status,
                "status_display": lead.get_status_display(),
                "source": lead.source,
                "source_display": lead.get_source_display(),
                "phone": lead.phone,
                "parent_name": lead.parent_name,
                "interest": lead.interest,
                "comment": lead.comment,
                "callback_date": (
                    lead.callback_date.isoformat() if lead.callback_date else None
                ),
                "callback_date_formatted": (
                    lead.callback_date.strftime("%d.%m.%Y %H:%M")
                    if lead.callback_date
                    else None
                ),
                "is_callback_overdue": lead.is_callback_overdue,
                "is_callback_today": lead.is_callback_today,
            }

            return JsonResponse({"success": True, "lead": lead_data})
        else:
            # Если форма невалидна, возвращаем ошибки
            return JsonResponse({"success": False, "errors": form.errors})

    # GET запрос - отображаем форму
    form = LeadForm(instance=lead)

    # Для AJAX запросов возвращаем только форму
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request, "leads/lead_form.html", {"form": form, "lead": lead}
        )

    return render(request, "leads/lead_form.html", {"form": form, "lead": lead})


@role_required(["manager", "admin"])
def lead_delete(request, pk):
    """
    Представление для удаления лида.
    Доступно только менеджеру и администратору.
    """
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        lead.delete()
        return redirect("lead_list")

    return render(request, "leads/lead_confirm_delete.html", {"lead": lead})


@role_required(["manager", "admin"])
def create_lead_ajax(request):
    """
    Создание лида через AJAX.
    """
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "lead": {
                        "id": lead.id,
                        "status": lead.status,
                        "status_display": lead.get_status_display(),
                        "source": lead.source,
                        "source_display": lead.get_source_display(),
                        "added_date": lead.added_date.isoformat(),
                        "added_date_formatted": lead.added_date.strftime("%d.%m.%Y"),
                        "phone": lead.phone,
                        "parent_name": lead.parent_name,
                        "interest": lead.interest,
                        "comment": lead.comment,
                        "callback_date": (
                            lead.callback_date.isoformat()
                            if lead.callback_date
                            else None
                        ),
                        "callback_date_formatted": (
                            lead.callback_date.strftime("%d.%m.%Y")
                            if lead.callback_date
                            else "—"
                        ),
                        "is_callback_overdue": lead.is_callback_overdue,
                        "is_callback_today": lead.is_callback_today,
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "errors": "Неверный запрос"})
