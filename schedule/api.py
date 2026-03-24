from ninja import Router
from django.db.models import Sum
from django.shortcuts import get_object_or_404

from .models import Schedule, COLOR_CHOICES
from branches.models import Branch
from .schemas import ScheduleSchema, ScheduleCreateSchema
from students.models import Payment

router = Router(tags=["Schedules"])
filters_router = Router(tags=["Schedule filters"])


@router.get("/", response=list[ScheduleSchema])
def list_schedules(request):
    user = request.user

    if hasattr(user, "role") and user.role == "admin" and user.city:
        return Schedule.objects.filter(branch__city=user.city)

    if hasattr(user, "role") and user.role in ["camp_head", "lab_head"]:
        return Schedule.objects.filter(branch=user.branch)

    return Schedule.objects.all()


@router.get("/{schedule_id}/", response=ScheduleSchema)
def get_schedule(request, schedule_id: int):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Проверка доступа для администраторов
    user = request.user
    if (
        hasattr(user, "role")
        and user.role == "admin"
        and user.city
        and schedule.branch.city != user.city
    ):
        from django.http import JsonResponse

        return JsonResponse({"error": "Доступ запрещен"}, status=403)

    return schedule


@router.get("/{schedule_id}/", response=ScheduleSchema)
def get_schedule(request, schedule_id: int):
    return get_object_or_404(Schedule, id=schedule_id)


@router.post("/", response=ScheduleSchema)
def create_schedule(request, data: ScheduleCreateSchema):
    branch = get_object_or_404(Branch, id=data.branch_id)

    # Проверка доступа для администраторов
    user = request.user
    if (
        hasattr(user, "role")
        and user.role == "admin"
        and user.city
        and branch.city != user.city
    ):
        from django.http import JsonResponse

        return JsonResponse({"error": "Доступ запрещен"}, status=403)

    # Проверка допустимых цветов
    color = (
        data.color if data.color and data.color in dict(COLOR_CHOICES) else "#cce6ff"
    )

    schedule = Schedule.objects.create(
        branch=branch,
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        theme=data.theme,
        color=color,
    )
    return schedule


@router.put("/{schedule_id}/", response=ScheduleSchema)
def update_schedule(request, schedule_id: int, data: ScheduleCreateSchema):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    branch = get_object_or_404(Branch, id=data.branch_id)

    # Проверка доступа для администраторов
    user = request.user
    if hasattr(user, "role") and user.role == "admin" and user.city:
        if schedule.branch.city != user.city or branch.city != user.city:
            from django.http import JsonResponse

            return JsonResponse({"error": "Доступ запрещен"}, status=403)

    # Проверка допустимых цветов
    if data.color and data.color in dict(COLOR_CHOICES):
        schedule.color = data.color

    schedule.branch = branch
    schedule.name = data.name
    schedule.start_date = data.start_date
    schedule.end_date = data.end_date
    schedule.theme = data.theme
    schedule.save()

    return schedule


@router.delete("/{schedule_id}/")
def delete_schedule(request, schedule_id: int):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Проверка доступа для администраторов
    user = request.user
    if (
        hasattr(user, "role")
        and user.role == "admin"
        and user.city
        and schedule.branch.city != user.city
    ):
        from django.http import JsonResponse

        return JsonResponse({"error": "Доступ запрещен"}, status=403)

    schedule.delete()
    return {"success": True}


@router.get("/{schedule_id}/balance/")
def get_schedule_balance(request, schedule_id: int):


    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Расчет доходов (платежи студентов за эту смену)
    total_income = (
        Payment.objects.filter(schedule=schedule).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )

    # Расчет расходов по смене
    total_expenses = schedule.expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    balance = total_income - total_expenses
    return {"balance": balance}
