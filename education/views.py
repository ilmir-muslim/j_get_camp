import urllib
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse

from core.utils import role_required
from education.forms import RegulationForm
from .models import Regulation


@role_required(["manager", "admin", "camp_head", "lab_head"])
def regulation_list(request):
    """
    Список обучающих материалов и регламентов.
    """
    regulations = Regulation.objects.all()
    return render(request, 'education/regulation_list.html', {'regulations': regulations})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def regulation_create(request):
    if request.method == "POST":
        form = RegulationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Сохраняем форму, которая уже содержит файл
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Материал успешно добавлен"}
                )
            return redirect("regulation_list")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors.get_json_data()}
                )
    else:
        form = RegulationForm()

    # Для AJAX-запросов возвращаем только форму
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "education/regulation_form.html", {"form": form}, request=request
        )
        return JsonResponse({"html": html})

    return render(request, "education/regulation_form.html", {"form": form})


@role_required(["manager", "admin", "camp_head", "lab_head"])
def regulation_download(request, pk):
    regulation = get_object_or_404(Regulation, pk=pk)
    filename = regulation.file.name.split("/")[-1]  # оригинальное имя на диске
    response = FileResponse(regulation.file.open("rb"))
    # заставляем браузер скачать именно с этим именем
    response["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{urllib.parse.quote(filename)}"
    )
    return response


@role_required(["manager", "admin", "camp_head", "lab_head"])
def regulation_delete(request, pk):
    """
    Удаление обучающего материала.
    """
    regulation = get_object_or_404(Regulation, pk=pk)
    if request.method == "POST":
        regulation.delete()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("regulation_list")

    # Если запрос не POST, то возвращаем ошибку для AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": False, "error": "Метод не разрешен"}, status=405
        )

    return render(
        request, "education/regulation_confirm_delete.html", {"regulation": regulation}
    )
