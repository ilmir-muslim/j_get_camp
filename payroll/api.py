from ninja import Router

from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.core.exceptions import PermissionDenied

from students.models import Payment
from .models import Expense, Salary
from .schemas import (
    ExpenseSchema,
    ExpenseCreateSchema,
    SalarySchema,
    SalaryCreateSchema,
)
from employees.models import Employee
from schedule.models import Schedule

router = Router(tags=["Payroll"])


# Expense Endpoints
@router.get("/expenses/", response=list[ExpenseSchema])
def list_expenses(request):
    return Expense.objects.all()


@router.post("/expenses/", response=ExpenseSchema)
def create_expense(request, data: ExpenseCreateSchema):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    expense = Expense.objects.create(**data.dict())
    return expense


@router.delete("/expenses/{expense_id}/")
def delete_expense(request, expense_id: int):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    Expense.objects.filter(id=expense_id).delete()
    return {"success": True}


# Salary Endpoints
@router.get("/salaries/", response=list[SalarySchema])
def list_salaries(request):
    return Salary.objects.all()


@router.post("/salaries/", response=SalarySchema)
def create_salary(request, data: SalaryCreateSchema):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    employee = get_object_or_404(Employee, id=data.employee_id)
    schedule = get_object_or_404(Schedule, id=data.schedule_id)

    salary = Salary(employee=employee, schedule=schedule, **data.dict())
    salary.save()  # Расчет произойдет автоматически в методе save()
    return salary


@router.put("/salaries/{salary_id}/", response=SalarySchema)
def update_salary(request, salary_id: int, data: SalaryCreateSchema):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    salary = get_object_or_404(Salary, id=salary_id)

    for attr, value in data.dict().items():
        setattr(salary, attr, value)

    salary.save()  # Расчет произойдет автоматически
    return salary


@router.delete("/salaries/{salary_id}/")
def delete_salary(request, salary_id: int):
    if request.user.role in ["camp_head", "lab_head"]:
        raise PermissionDenied
    Salary.objects.filter(id=salary_id).delete()
    return {"success": True}
