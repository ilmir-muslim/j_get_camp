from datetime import date
from ninja import Router
from .models import Schedule, COLOR_CHOICES
from branches.models import Branch
from .schemas import ScheduleSchema, ScheduleCreateSchema
from django.shortcuts import get_object_or_404

router = Router(tags=["Schedules"])
filters_router = Router(tags=["Schedule filters"])

@router.get("/", response=list[ScheduleSchema])
def list_schedules(request):
    return Schedule.objects.all()

@router.get("/{schedule_id}/", response=ScheduleSchema)
def get_schedule(request, schedule_id: int):
    return get_object_or_404(Schedule, id=schedule_id)

@router.post("/", response=ScheduleSchema)
def create_schedule(request, data: ScheduleCreateSchema):
    branch = get_object_or_404(Branch, id=data.branch_id)
    
    # Проверка допустимых цветов
    color = data.color if data.color and data.color in dict(COLOR_CHOICES) else "#cce6ff"
    
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
    schedule.delete()
    return {"success": True}

