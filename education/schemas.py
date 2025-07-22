from datetime import datetime
from ninja import Schema

class RegulationSchema(Schema):
    id: int
    title: str
    file: str
    uploaded_at: datetime

class RegulationCreateSchema(Schema):
    title: str
    file: str