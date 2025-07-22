from ninja import Schema

class BranchSchema(Schema):
    id: int
    name: str
    address: str

class BranchCreateSchema(Schema):
    name: str
    address: str