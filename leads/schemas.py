from ninja import Schema
from datetime import date, datetime
from typing import Optional

class LeadSchema(Schema):
    id: int
    status: str
    source: str
    added_date: date
    phone: str
    parent_name: str
    interest: str
    comment: str
    callback_date: Optional[datetime] = None

class LeadCreateSchema(Schema):
    status: str
    source: str
    phone: str
    parent_name: str = ""
    interest: str = ""
    comment: str = ""
    callback_date: Optional[datetime] = None