from ninja import Router
from .models import Expense, Salary
from .schemas import ExpenseSchema, ExpenseCreateSchema, SalarySchema, SalaryCreateSchema
from employees.models import Employee
from schedule.models import Schedule

router = Router(tags=["Payroll"])

# Expense Endpoints
@router.get("/expenses/", response=list[ExpenseSchema])
def list_expenses(request):
    return Expense.objects.all()

@router.post("/expenses/", response=ExpenseSchema)
def create_expense(request, data: ExpenseCreateSchema):
    expense = Expense.objects.create(**data.dict())
    return expense

@router.delete("/expenses/{expense_id}/")
def delete_expense(request, expense_id: int):
    Expense.objects.filter(id=expense_id).delete()
    return {"success": True}

# Salary Endpoints
@router.get("/salaries/", response=list[SalarySchema])
def list_salaries(request):
    return Salary.objects.all()

@router.post("/salaries/", response=SalarySchema)
def create_salary(request, data: SalaryCreateSchema):
    # Calculate total payment based on payment type
    employee = Employee.objects.get(id=data.employee_id)
    schedule = Schedule.objects.get(id=data.schedule_id)
    
    salary_data = data.dict()
    if data.payment_type == "fixed":
        salary_data["total_payment"] = data.days_worked * data.daily_rate
    elif data.payment_type == "percent":
        # Percent calculation would require additional business logic
        salary_data["total_payment"] = data.percent_rate
    elif data.payment_type == "combined":
        salary_data["total_payment"] = (data.days_worked * data.daily_rate) + data.percent_rate
    
    salary = Salary.objects.create(
        employee=employee,
        schedule=schedule,
        **salary_data
    )
    return salary

@router.put("/salaries/{salary_id}/", response=SalarySchema)
def update_salary(request, salary_id: int, data: SalaryCreateSchema):
    salary = Salary.objects.get(id=salary_id)
    for attr, value in data.dict().items():
        if attr not in ["employee_id", "schedule_id"]:
            setattr(salary, attr, value)
    
    # Recalculate if needed
    if data.payment_type == "fixed":
        salary.total_payment = data.days_worked * data.daily_rate
    elif data.payment_type == "percent":
        salary.total_payment = data.percent_rate
    elif data.payment_type == "combined":
        salary.total_payment = (data.days_worked * data.daily_rate) + data.percent_rate
    
    salary.save()
    return salary

@router.delete("/salaries/{salary_id}/")
def delete_salary(request, salary_id: int):
    Salary.objects.filter(id=salary_id).delete()
    return {"success": True}