from ninja import Schema

class ExpenseSchema(Schema):
    id: int
    schedule_id: int
    category: str
    comment: str
    amount: float

class ExpenseCreateSchema(Schema):
    schedule_id: int
    category: str
    comment: str = ""
    amount: float

class SalarySchema(Schema):
    id: int
    employee_id: int
    schedule_id: int
    payment_type: str
    days_worked: int
    daily_rate: float
    percent_rate: float
    total_payment: float
    is_paid: bool

class SalaryCreateSchema(Schema):
    employee_id: int
    schedule_id: int
    payment_type: str
    days_worked: int
    daily_rate: float
    percent_rate: float = 0
    is_paid: bool = False