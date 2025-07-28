from ninja import Schema
from pydantic import Field
from typing import Optional

from datetime import date
from datetime import date as date_type


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
    present: bool 
    comment: Optional[str] = None


class EmployeeAttendanceCreateSchema(Schema):
    employee_id: int
    date: date
    present: bool = True
    comment: Optional[str] = None


class EmployeeAttendanceUpdateSchema(Schema):
    date: Optional[date_type] = None
    present: Optional[bool] = None
    comment: Optional[str] = None
