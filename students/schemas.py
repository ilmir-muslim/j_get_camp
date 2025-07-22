from ninja import Schema
from typing import Optional


class StudentSchema(Schema):
    id: int
    full_name: str
    phone: Optional[str]
    parent_name: Optional[str]
    schedule_id: Optional[int]
    attendance_type: str
    default_price: float
    individual_price: Optional[float]
    price_comment: Optional[str]


class StudentCreateSchema(Schema):
    full_name: str
    phone: Optional[str] = ""
    parent_name: Optional[str] = ""
    schedule_id: Optional[int] = None
    attendance_type: str
    default_price: float
    individual_price: Optional[float] = None
    price_comment: Optional[str] = ""


class StudentUpdateSchema(Schema):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    schedule_id: Optional[int] = None
    attendance_type: Optional[str] = None
    default_price: Optional[float] = None
    individual_price: Optional[float] = None
    price_comment: Optional[str] = None