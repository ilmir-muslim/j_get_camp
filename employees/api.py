from ninja import Router
from employees.models import Employee, EmployeeAttendance
from employees.schemas import (
    EmployeeSchema,
    EmployeeCreateSchema,
    EmployeeAttendanceSchema,
    EmployeeAttendanceCreateSchema,
)

router = Router(tags=["Employees"])

@router.get("/", response=list[EmployeeSchema])
def employee_list(request):
    return Employee.objects.all()

@router.get("/{employee_id}/", response=EmployeeSchema)
def employee_detail(request, employee_id: int):
    return Employee.objects.get(id=employee_id)

@router.post("/", response=EmployeeSchema)
def employee_create(request, data: EmployeeCreateSchema):
    employee = Employee.objects.create(**data.dict())
    return employee

@router.put("/{employee_id}/", response=EmployeeSchema)
def employee_update(request, employee_id: int, data: EmployeeCreateSchema):
    employee = Employee.objects.get(id=employee_id)
    for attr, value in data.dict().items():
        setattr(employee, attr, value)
    employee.save()
    return employee

@router.delete("/{employee_id}/")
def employee_delete(request, employee_id: int):
    Employee.objects.filter(id=employee_id).delete()
    return {"success": True}

@router.get("/attendances/", response=list[EmployeeAttendanceSchema])
def attendance_list(request):
    return EmployeeAttendance.objects.all()

@router.post("/attendances/", response=EmployeeAttendanceSchema)
def attendance_create(request, data: EmployeeAttendanceCreateSchema):
    attendance = EmployeeAttendance.objects.create(**data.dict())
    return attendance

@router.put("/attendances/{attendance_id}/", response=EmployeeAttendanceSchema)
def attendance_update(request, attendance_id: int, data: EmployeeAttendanceCreateSchema):
    attendance = EmployeeAttendance.objects.get(id=attendance_id)
    for attr, value in data.dict().items():
        setattr(attendance, attr, value)
    attendance.save()
    return attendance

@router.delete("/attendances/{attendance_id}/")
def attendance_delete(request, attendance_id: int):
    EmployeeAttendance.objects.filter(id=attendance_id).delete()
    return {"success": True}
