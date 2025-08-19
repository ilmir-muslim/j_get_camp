from ninja import Router
from django.shortcuts import get_object_or_404
from employees.models import Employee, EmployeeAttendance
from employees.schemas import (
    EmployeeAttendanceUpdateSchema,
    EmployeeSchema,
    EmployeeCreateSchema,
    EmployeeAttendanceSchema,
    EmployeeAttendanceCreateSchema,
)

employees_router = Router(tags=["Employees"])
attendances_router = Router(tags=["Attendances"])

@employees_router.get("/", response=list[EmployeeSchema])
def employees_list(request):
    return Employee.objects.all()

@employees_router.get("/{employee_id}/", response=EmployeeSchema)
def employee_detail(request, employee_id: int):
    return Employee.objects.get(id=employee_id)

@employees_router.post("/", response=EmployeeSchema)
def employee_create(request, data: EmployeeCreateSchema):
    employee = Employee.objects.create(**data.dict())
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
        employee=employee,
        date=data.date,
        present=data.present,
        comment=data.comment
    )
    return attendance

@attendances_router.get("/attendances/{attendance_id}/", response=EmployeeAttendanceSchema)
def attendance_detail(request, attendance_id: int):
    return get_object_or_404(EmployeeAttendance, id=attendance_id)

@attendances_router.patch("/attendances/{attendance_id}/", response=EmployeeAttendanceSchema)
def attendance_update(request, attendance_id: int, data: EmployeeAttendanceUpdateSchema):
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