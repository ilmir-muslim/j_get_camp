from ninja import Schema
from pydantic import Field
from typing import Optional
from datetime import date


class EmployeeSchema(Schema):
    id: int
    full_name: str
    position: str
    branch_id: Optional[int] = None
    schedule_id: Optional[int] = None
    rate_per_day: float


class EmployeeCreateSchema(Schema):
    full_name: str
    position: str
    branch_id: Optional[int] = None
    schedule_id: Optional[int] = None
    rate_per_day: float


class EmployeeAttendanceSchema(Schema):
    id: int
    employee_id: int
    date: date
    comment: Optional[str] = None


class EmployeeAttendanceCreateSchema(Schema):
    employee_id: int
    date: date
    comment: Optional[str] = None


class EmployeeAttendanceUpdateSchema(Schema):
    date: date
    comment: str = ""
