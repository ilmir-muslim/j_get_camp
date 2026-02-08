from ninja import Schema
from typing import Optional
from datetime import date
from datetime import date as date_type


class SquadSchema(Schema):
    id: int
    name: str
    leader_id: Optional[int]
    schedule_id: int
    # Добавьте это поле для информации о вожатом
    leader: Optional[dict] = None

    @staticmethod
    def resolve_leader(obj, info):
        if obj.leader:
            return {
                "id": obj.leader.id,
                "full_name": obj.leader.full_name,
                "position": obj.leader.position.name if obj.leader.position else None,
            }
        return None


class StudentSchema(Schema):
    id: int
    squad_id: Optional[int]
    full_name: str
    phone: Optional[str]
    parent_name: Optional[str]
    schedule_id: Optional[int]
    attendance_type: str
    attendance_dates: Optional[list] = None
    default_price: float
    individual_price: Optional[float]
    price_comment: Optional[str]
    # Добавьте эти поля для удобства
    squad_name: Optional[str] = None
    squad_leader_name: Optional[str] = None

    @staticmethod
    def resolve_squad_name(obj, info):
        return obj.squad.name if obj.squad else None

    @staticmethod
    def resolve_squad_leader_name(obj, info):
        if obj.squad and obj.squad.leader:
            return obj.squad.leader.full_name
        return None


class StudentCreateSchema(Schema):
    squad_id: Optional[int] = None
    full_name: str
    phone: Optional[str] = ""
    parent_name: Optional[str] = ""
    schedule_id: Optional[int] = None
    attendance_type: str
    default_price: Optional[float] = None
    individual_price: Optional[float] = None
    price_comment: Optional[str] = ""


class StudentUpdateSchema(Schema):
    squad_id: Optional[int] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    schedule_id: Optional[int] = None
    attendance_type: Optional[str] = None
    default_price: Optional[float] = None
    individual_price: Optional[float] = None
    price_comment: Optional[str] = None


class AttendanceSchema(Schema):
    id: int
    student_id: int
    date: date
    present: bool


class AttendanceCreateSchema(Schema):
    date: date
    present: bool = True


class AttendanceUpdateSchema(Schema):
    date: Optional[date_type] = None
    present: Optional[bool] = None


class PaymentSchema(Schema):
    id: int
    student_id: int
    schedule_id: int
    amount: float
    date: date
    comment: str


class PaymentCreateSchema(Schema):
    schedule_id: int
    amount: float
    date: date
    comment: str = ""


class PaymentUpdateSchema(Schema):
    schedule_id: Optional[int] = None
    amount: Optional[float] = None
    date: Optional[date_type] = None
    comment: Optional[str] = None
