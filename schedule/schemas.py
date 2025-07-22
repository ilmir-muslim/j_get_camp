from ninja import Schema
from datetime import date
from typing import Optional

class ScheduleSchema(Schema):
    id: int
    name: str
    branch_id: int
    start_date: date
    end_date: date
    theme: str
    color: str 

class ScheduleCreateSchema(Schema):
    name: str
    branch_id: int
    start_date: date
    end_date: date
    theme: str
    color: Optional[str] = None  # Необязательный параметр