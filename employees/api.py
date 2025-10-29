# employees / api.py
from ninja import Router

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from branches.models import Branch
from employees.models import Employee, EmployeeAttendance
from employees.schemas import (
    EmployeeAttendanceUpdateSchema,
    EmployeeSchema,
    EmployeeCreateSchema,
    EmployeeAttendanceSchema,
    EmployeeAttendanceCreateSchema,
)
from payroll.models import Salary

employees_router = Router(tags=["Employees"])
attendances_router = Router(tags=["Attendances"])


# Объединяем оба эндпоинта в один с поддержкой фильтрации
@employees_router.get("/", response=list[EmployeeSchema])
def employees_list(request, branch_id: int = None):
    """
    Получить список сотрудников с возможностью фильтрации по филиалу.
    """
    user = request.user
    if user.is_authenticated and user.role == "admin" and user.city:
        # Администратор видит только сотрудников своего города
        queryset = Employee.objects.filter(branch__city=user.city)
    else:
        queryset = Employee.objects.all()

    if branch_id:
        queryset = queryset.filter(branch_id=branch_id)
    return queryset


@employees_router.get("/{employee_id}/", response=EmployeeSchema)
def employee_detail(request, employee_id: int):
    return get_object_or_404(Employee, id=employee_id)


@employees_router.post("/", response=EmployeeSchema)
def employee_create(request, data: EmployeeCreateSchema):
    employee_data = data.dict()

    # Проверяем доступ администратора к филиалу
    user = request.user
    if user.is_authenticated and user.role == "admin" and user.city:
        branch_id = employee_data.get("branch_id")
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id)
                if branch.city != user.city:
                    return JsonResponse({"error": "Доступ запрещен"}, status=403)
            except Branch.DoesNotExist:
                pass

    employee = Employee.objects.create(**employee_data)
    return employee


@employees_router.delete("/{employee_id}/")
def employee_delete(request, employee_id: int):
    Employee.objects.filter(id=employee_id).delete()
    return {"success": True}


@attendances_router.get("/attendances/", response=list[EmployeeAttendanceSchema])
def attendance_list(request):
    return EmployeeAttendance.objects.all()


@attendances_router.post("/attendances/create/", response=EmployeeAttendanceSchema)
def attendance_create(request, data: EmployeeAttendanceCreateSchema):
    employee = get_object_or_404(Employee, id=data.employee_id)
    attendance = EmployeeAttendance.objects.create(
        employee=employee, date=data.date, present=data.present, comment=data.comment
    )
    return attendance


@attendances_router.get(
    "/attendances/{attendance_id}/", response=EmployeeAttendanceSchema
)
def attendance_detail(request, attendance_id: int):
    return get_object_or_404(EmployeeAttendance, id=attendance_id)


@attendances_router.patch(
    "/attendances/{attendance_id}/", response=EmployeeAttendanceSchema
)
def attendance_update(
    request, attendance_id: int, data: EmployeeAttendanceUpdateSchema
):
    attendance = get_object_or_404(EmployeeAttendance, id=attendance_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(attendance, attr, value)
    attendance.save()
    return attendance


@attendances_router.delete("/attendances/{attendance_id}/")
def attendance_delete(request, attendance_id: int):
    attendance = get_object_or_404(EmployeeAttendance, id=attendance_id)
    attendance.delete()
    return {"success": True}


@employees_router.post("/{employee_id}/update_salaries/")
def update_employee_salaries(request, employee_id: int):
    employee = get_object_or_404(Employee, id=employee_id)
    new_rate = request.data.get("rate_per_day")

    # Обновляем все связанные зарплаты
    Salary.objects.filter(employee=employee).update(daily_rate=new_rate)

    return {"success": True}
