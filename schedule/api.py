from ninja import Router
from .models import Schedule
from .schemas import ScheduleSchema, ScheduleCreateSchema
from branches.models import Branch

router = Router(tags=["Schedules"])

@router.get("/", response=list[ScheduleSchema])
def list_schedules(request):
    return Schedule.objects.all()

@router.get("/{schedule_id}/", response=ScheduleSchema)
def get_schedule(request, schedule_id: int):
    schedule = Schedule.objects.get(id=schedule_id)
    return schedule

@router.post("/", response=ScheduleSchema)
def create_schedule(request, data: ScheduleCreateSchema):
    branch = Branch.objects.get(id=data.branch_id)
    schedule = Schedule.objects.create(
        branch=branch,
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        theme=data.theme,
        color=data.color if data.color else "#cce6ff",  # Используем цвет, если передан
    )
    return schedule


@router.put("/{schedule_id}/", response=ScheduleSchema)
def update_schedule(request, schedule_id: int, data: ScheduleCreateSchema):
    schedule = Schedule.objects.get(id=schedule_id)
    branch = Branch.objects.get(id=data.branch_id)
    
    schedule.branch = branch
    schedule.name = data.name
    schedule.start_date = data.start_date
    schedule.end_date = data.end_date
    schedule.theme = data.theme
    if data.color:
        schedule.color = data.color
    schedule.save()
    
    return schedule


@router.delete("/{schedule_id}/")
def delete_schedule(request, schedule_id: int):
    Schedule.objects.filter(id=schedule_id).delete()
    return {"success": True}