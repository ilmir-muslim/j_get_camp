from datetime import datetime, timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from branches.models import Branch
from core.utils import role_required
from schedule.forms import ScheduleForm
from .models import Schedule, COLOR_CHOICES


@role_required(["manager", "admin"])
def schedule_create(request):
    initial = {}

    # Предзаполняем данные из параметров URL
    if "branch" in request.GET:
        try:
            initial["branch"] = Branch.objects.get(pk=request.GET["branch"])
        except Branch.DoesNotExist:
            pass

    if "start_date" in request.GET and "end_date" in request.GET:
        initial["start_date"] = request.GET["start_date"]
        initial["end_date"] = request.GET["end_date"]

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            return redirect("schedule_calendar")
    else:
        form = ScheduleForm(initial=initial)

    return render(request, "schedule/schedule_form.html", {"form": form})


@role_required(["manager", "admin"])
def schedule_delete(request, pk):
    """
    Представление для удаления смены.
    Доступно только менеджеру и администратору.
    """
    schedule_obj = get_object_or_404(Schedule, pk=pk)

    if request.method == "POST":
        schedule_obj.delete()
        return redirect("schedule_calendar")

    return render(
        request, "schedule/schedule_confirm_delete.html", {"schedule": schedule_obj}
    )


@role_required(["manager", "admin", "camp_head", "lab_head"])
def schedule_calendar(request):
    # Определяем месяц для отображения
    month = request.GET.get("month")
    if month:
        try:
            current_date = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    # Рассчитываем первый и последний день месяца
    first_day = current_date.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)
    last_day = next_month - timedelta(days=1)

    # Рассчитываем предыдущий и следующий месяц
    prev_month = (first_day - timedelta(days=1)).strftime("%Y-%m")
    next_month = next_month.strftime("%Y-%m")

    # Создаем список недель (понедельник-пятница)
    weeks = []
    current = first_day
    while current <= last_day:
        # Находим понедельник текущей недели
        if current.weekday() == 0:  # 0 = понедельник
            monday = current
        else:
            monday = current - timedelta(days=current.weekday())

        # Пятница - через 4 дня от понедельника
        friday = monday + timedelta(days=4)
        if friday > last_day:
            friday = last_day

        weeks.append((monday, friday))

        # Переходим к следующей неделе
        current = friday + timedelta(days=3)  # Пропускаем выходные

    # Получаем филиалы
    branches = Branch.objects.all()

    # Создаем матрицу расписаний: {branch_id: {week_start: [schedule1, schedule2]}}
    matrix = {}
    for branch in branches:
        branch_schedules = {}
        for week_start, week_end in weeks:
            schedules = Schedule.objects.filter(
                branch=branch, start_date__lte=week_end, end_date__gte=week_start
            )
            branch_schedules[week_start] = schedules
        matrix[branch.id] = branch_schedules

    # Создаем список заголовков для столбцов (недели)
    week_headers = []
    for week_start, week_end in weeks:
        week_headers.append(
            f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}"
        )

    context = {
        "current_date": current_date,
        "prev_month": prev_month,
        "next_month": next_month,
        "weeks": weeks,
        "week_headers": week_headers,  # Добавлено
        "branches": branches,
        "matrix": matrix,
        "color_choices": COLOR_CHOICES,
    }
    return render(request, "schedule/schedule_calendar.html", context)


def schedule_quick_edit(request, pk=None):
    schedule = get_object_or_404(Schedule, pk=pk) if pk else None

    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return HttpResponse(status=200)
        else:
            return render(request, "schedule/schedule_quick_form.html", {"form": form})

    # GET-запрос: создаём форму
    if schedule:
        # Существующая смена — только instance
        form = ScheduleForm(instance=schedule)
    else:
        # Новая смена — используем initial
        initial = {}
        if request.GET.get("branch"):
            initial["branch"] = request.GET["branch"]
        if request.GET.get("week_start") and request.GET.get("week_end"):
            initial["start_date"] = request.GET["week_start"]
            initial["end_date"] = request.GET["week_end"]
        form = ScheduleForm(initial=initial)

    return render(request, "schedule/schedule_quick_form.html", {"form": form})